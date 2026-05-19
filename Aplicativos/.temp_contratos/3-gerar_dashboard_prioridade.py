from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from html import escape
from pathlib import Path

from pdfs import prepare_records_for_output, resolve_priority_order


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "saida"
CONSOLIDATED_JSON_PATH = OUTPUT_DIR / "contratos_consolidados.json"
OUTPUT_HTML_PATH = OUTPUT_DIR / "dashboard_prioridade_contratos.html"

MISSING_TEXT = "Nao informado"
PROBLEM_LAYOUTS = {"NAO_IDENTIFICADO", "PENDENTE_EXTRAIR"}


def load_priority_records() -> list[dict[str, object]]:
    if not CONSOLIDATED_JSON_PATH.exists():
        raise FileNotFoundError(
            f"Arquivo nao encontrado: {CONSOLIDATED_JSON_PATH}"
        )

    payload = json.loads(CONSOLIDATED_JSON_PATH.read_text(encoding="utf-8"))
    records = prepare_records_for_output(payload)

    priority_records: list[dict[str, object]] = []
    for record in records:
        supplier_name = (
            record.get("fornecedor_descricao_atual")
            or record.get("fornecedor_nome")
            or ""
        )
        priority_order = resolve_priority_order(
            supplier_name,
            record.get("codigo_fornecedor_consinco"),
            record.get("cnpj"),
        )
        if priority_order >= 10**9:
            continue

        normalized = dict(record)
        normalized["fornecedor_dashboard"] = supplier_name
        normalized["ordem_prioridade"] = int(priority_order) + 1
        priority_records.append(normalized)

    priority_records.sort(
        key=lambda record: (
            int(record.get("ordem_prioridade", 10**9)),
            str(record.get("fornecedor_dashboard", "")),
            str(record.get("arquivo_pdf", "")),
        )
    )
    return priority_records


def format_text(value: object, fallback: str = "Nao informado") -> str:
    text = str(value or "").strip()
    return text if text else fallback


def format_number(value: object, decimals: int = 1) -> str:
    if value in (None, ""):
        return "Nao informado"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "Nao informado"
    return f"{number:.{decimals}f}".replace(".", ",")


def format_integer(value: object) -> str:
    if value in (None, ""):
        return "Nao informado"
    try:
        return str(int(float(value)))
    except (TypeError, ValueError):
        return "Nao informado"


def is_missing_display(value: str) -> bool:
    return value.strip().lower() == MISSING_TEXT.lower()


def missing_class(value: str) -> str:
    return " missing-value" if is_missing_display(value) else ""


def is_problem_record(record: dict[str, object]) -> bool:
    layout = str(record.get("layout_tipo") or "").strip().upper()
    if layout in PROBLEM_LAYOUTS:
        return True

    required_fields = [
        record.get("cnpj"),
        record.get("data_assinatura"),
        record.get("forma_pagamento"),
        record.get("prazo_pagamento_dias"),
    ]
    return any(value in (None, "") for value in required_fields)


def build_problem_badges(record: dict[str, object]) -> list[str]:
    badges: list[str] = []

    if str(record.get("layout_tipo") or "").strip().upper() in PROBLEM_LAYOUTS:
        badges.append("Layout critico")
    if record.get("cnpj") in (None, ""):
        badges.append("Sem CNPJ")
    if record.get("data_assinatura") in (None, ""):
        badges.append("Sem assinatura")
    if record.get("forma_pagamento") in (None, ""):
        badges.append("Sem pagamento")
    if record.get("prazo_pagamento_dias") in (None, ""):
        badges.append("Sem prazo")

    return badges


def format_counter_bars(counter: Counter, empty_label: str) -> str:
    if not counter:
        return '<div class="empty-state">Sem dados para este recorte.</div>'

    max_value = max(counter.values()) or 1
    rows: list[str] = []
    for label, value in counter.most_common(8):
        safe_label = escape(label or empty_label)
        width = max(8, round((value / max_value) * 100))
        rows.append(
            "<div class='bar-row'>"
            f"<div class='bar-meta'><span>{safe_label}</span><strong>{value}</strong></div>"
            f"<div class='bar-track'><div class='bar-fill' style='width:{width}%'></div></div>"
            "</div>"
        )
    return "".join(rows)


def build_kpis(records: list[dict[str, object]]) -> list[tuple[str, str, str]]:
    total = len(records)
    with_cnpj = sum(1 for record in records if str(record.get("cnpj") or "").strip())
    with_payment = sum(
        1
        for record in records
        if str(record.get("forma_pagamento") or "").strip()
    )
    with_signature = sum(
        1
        for record in records
        if str(record.get("data_assinatura") or "").strip()
    )

    bonus_values = [
        float(record["bonus_percentual"])
        for record in records
        if record.get("bonus_percentual") not in (None, "")
    ]
    prazo_values = [
        int(float(record["prazo_pagamento_dias"]))
        for record in records
        if record.get("prazo_pagamento_dias") not in (None, "")
    ]

    avg_bonus = (
        f"{sum(bonus_values) / len(bonus_values):.1f}%".replace(".", ",")
        if bonus_values else "Nao informado"
    )
    avg_prazo = (
        f"{round(sum(prazo_values) / len(prazo_values))} dias"
        if prazo_values else "Nao informado"
    )
    problem_count = sum(1 for record in records if is_problem_record(record))

    return [
        ("Contratos no recorte", str(total), "Fornecedores priorizados visiveis"),
        ("Com CNPJ", str(with_cnpj), "Registros com identificacao fiscal"),
        ("Pagamento identificado", str(with_payment), "Forma de pagamento preenchida"),
        ("Data de assinatura", str(with_signature), "Contratos com data capturada"),
      ("Com pendencia", str(problem_count), "Contratos com layout critico ou campos essenciais faltantes"),
        ("Bonus medio", avg_bonus, "Media entre contratos com percentual preenchido"),
        ("Prazo medio", avg_prazo, "Media entre contratos com prazo preenchido"),
    ]


def build_priority_table(records: list[dict[str, object]]) -> str:
  if not records:
    return '<div class="empty-state">Nenhum contrato priorizado encontrado.</div>'

  rows: list[str] = []
  for record in records:
    layout = format_text(record.get("layout_tipo"))
    pagamento = format_text(record.get("forma_pagamento"))
    bonus = format_number(record.get("bonus_percentual"))
    prazo = format_integer(record.get("prazo_pagamento_dias"))
    assinatura = format_text(record.get("data_assinatura"))
    fornecedor = format_text(record.get("fornecedor_dashboard"))
    row_class = " problem-row" if is_problem_record(record) else ""
    rows.append(
      f"<tr class='{row_class.strip()}'>"
      f"<td>{record.get('ordem_prioridade', '')}</td>"
      f"<td>{escape(fornecedor)}</td>"
      f"<td class='{missing_class(layout).strip()}'>{escape(layout)}</td>"
      f"<td class='{missing_class(pagamento).strip()}'>{escape(pagamento)}</td>"
      f"<td class='{missing_class(bonus).strip()}'>{escape(bonus)}</td>"
      f"<td class='{missing_class(prazo).strip()}'>{escape(prazo)}</td>"
      f"<td class='{missing_class(assinatura).strip()}'>{escape(assinatura)}</td>"
      f"<td>{escape(format_text(record.get('arquivo_pdf')))}</td>"
      "</tr>"
    )

    return (
        "<table class='priority-table'>"
        "<thead><tr>"
        "<th>Posicao</th><th>Fornecedor</th><th>Layout</th><th>Pagamento</th>"
        "<th>Bonus %</th><th>Prazo</th><th>Assinatura</th><th>Arquivo PDF</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def build_supplier_cards(records: list[dict[str, object]]) -> str:
  if not records:
    return '<div class="empty-state">Nenhum contrato priorizado encontrado.</div>'

  cards: list[str] = []
  for record in records:
    supplier = escape(format_text(record.get("fornecedor_dashboard")))
    layout = format_text(record.get("layout_tipo"))
    pagamento = format_text(record.get("forma_pagamento"))
    bonus = format_number(record.get("bonus_percentual"))
    prazo = format_integer(record.get("prazo_pagamento_dias"))
    cnpj = format_text(record.get("cnpj"))
    badges = build_problem_badges(record)
    badges_html = "".join(
      f"<span class='problem-badge'>{escape(badge)}</span>"
      for badge in badges
    )
    cards.append(
      f"<article class='supplier-card{' supplier-card-problem' if badges else ''}'>"
      f"<div class='supplier-rank'>#{record.get('ordem_prioridade', '')}</div>"
      f"<h3>{supplier}</h3>"
      f"<div class='problem-badges'>{badges_html}</div>"
      f"<p><strong>Layout:</strong> <span class='{missing_class(layout).strip()}'>{escape(layout)}</span></p>"
      f"<p><strong>Pagamento:</strong> <span class='{missing_class(pagamento).strip()}'>{escape(pagamento)}</span></p>"
      f"<p><strong>Bonus:</strong> <span class='{missing_class(bonus).strip()}'>{escape(bonus)}{'%' if not is_missing_display(bonus) else ''}</span></p>"
      f"<p><strong>Prazo:</strong> <span class='{missing_class(prazo).strip()}'>{escape(prazo)}{' dias' if not is_missing_display(prazo) else ''}</span></p>"
      f"<p><strong>CNPJ:</strong> <span class='{missing_class(cnpj).strip()}'>{escape(cnpj)}</span></p>"
      f"<p><strong>Arquivo:</strong> {escape(format_text(record.get('arquivo_pdf')))}</p>"
      "</article>"
    )
    return "".join(cards)


def build_view_html(view_id: str, title: str, records: list[dict[str, object]]) -> str:
    kpis = "".join(
        "<div class='kpi-card'>"
        f"<span class='kpi-label'>{escape(label)}</span>"
        f"<strong class='kpi-value'>{escape(value)}</strong>"
        f"<span class='kpi-help'>{escape(help_text)}</span>"
        "</div>"
        for label, value, help_text in build_kpis(records)
    )

    layout_counter = Counter(
        format_text(record.get("layout_tipo"), "Sem layout")
        for record in records
    )
    payment_counter = Counter(
        format_text(record.get("forma_pagamento"), "Sem informacao")
        for record in records
    )

    return (
        f"<section id='view_{view_id}' class='dashboard-view'>"
        f"<div class='view-head'><h2>{escape(title)}</h2>"
        f"<p>{len(records)} contrato(s) priorizado(s) neste recorte.</p></div>"
        f"<div class='kpi-grid'>{kpis}</div>"
        "<div class='analytics-grid'>"
        "<div class='panel'><h3>Layouts detectados</h3>"
        f"{format_counter_bars(layout_counter, 'Sem layout')}</div>"
        "<div class='panel'><h3>Formas de pagamento</h3>"
        f"{format_counter_bars(payment_counter, 'Sem informacao')}</div>"
        "</div>"
        "<div class='panel'><h3>Top fornecedores deste recorte</h3>"
        f"<div class='supplier-grid'>{build_supplier_cards(records)}</div></div>"
        "<div class='panel table-panel'><h3>Tabela resumida</h3>"
        f"{build_priority_table(records)}</div>"
        "</section>"
    )


def build_dashboard_html(records: list[dict[str, object]]) -> str:
    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")
    problem_records = [
        record for record in records if is_problem_record(record)
    ]
    views = [
        ("top10", "Top 10 da prioridade", records[:10]),
        ("top20", "Top 20 da prioridade", records[:20]),
        ("top50", "Top 50 da prioridade", records[:50]),
        ("todos", "Todos os contratos priorizados", records),
        (
            "problemas",
            "Contratos priorizados problematicos",
            problem_records,
        ),
    ]

    options_html = "".join(
        f"<button class='view-button{' active' if index == 0 else ''}' data-view='{view_id}'>{escape(title)}</button>"
        for index, (view_id, title, _) in enumerate(views)
    )
    views_html = "".join(
        build_view_html(view_id, title, view_records)
        for view_id, title, view_records in views
    )

    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dashboard de Contratos Prioritarios</title>
  <style>
    :root {{
      --bg: #f4efe6;
      --paper: #fffaf2;
      --ink: #1d1a16;
      --muted: #6f675f;
      --line: #d9c9b6;
      --accent: #9c3d1f;
      --accent-2: #d8a94a;
      --ok: #476c51;
      --danger: #a42b2b;
      --danger-soft: #fce7e5;
      --shadow: 0 18px 40px rgba(71, 48, 22, 0.12);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(216,169,74,.18), transparent 28%),
        radial-gradient(circle at bottom right, rgba(156,61,31,.12), transparent 26%),
        var(--bg);
    }}
    .shell {{
      max-width: 1460px;
      margin: 0 auto;
      padding: 28px 20px 40px;
    }}
    .hero {{
      background: linear-gradient(135deg, rgba(255,250,242,.94), rgba(247,239,226,.98));
      border: 1px solid rgba(217,201,182,.9);
      border-radius: 28px;
      padding: 28px;
      box-shadow: var(--shadow);
      position: relative;
      overflow: hidden;
    }}
    .hero::after {{
      content: "";
      position: absolute;
      inset: auto -60px -80px auto;
      width: 220px;
      height: 220px;
      background: radial-gradient(circle, rgba(216,169,74,.25), rgba(216,169,74,0));
      pointer-events: none;
    }}
    .eyebrow {{
      display: inline-block;
      font-size: 12px;
      letter-spacing: .24em;
      text-transform: uppercase;
      color: var(--accent);
      margin-bottom: 12px;
    }}
    h1 {{
      margin: 0;
      font-size: clamp(32px, 4vw, 56px);
      line-height: 1.02;
      max-width: 860px;
    }}
    .hero p {{
      max-width: 860px;
      font-size: 18px;
      line-height: 1.55;
      color: var(--muted);
      margin: 14px 0 0;
    }}
    .hero-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 22px;
    }}
    .hero-chip {{
      border: 1px solid rgba(156,61,31,.18);
      border-radius: 999px;
      padding: 10px 14px;
      background: rgba(255,255,255,.7);
      font-size: 14px;
      color: var(--ink);
    }}
    .toolbar {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin: 24px 0 18px;
    }}
    .view-button {{
      border: 1px solid var(--line);
      background: rgba(255,250,242,.8);
      color: var(--ink);
      border-radius: 999px;
      padding: 12px 18px;
      font-size: 15px;
      cursor: pointer;
      transition: .18s ease;
    }}
    .view-button:hover {{ border-color: var(--accent); transform: translateY(-1px); }}
    .view-button.active {{
      background: linear-gradient(135deg, var(--accent), #7e2b12);
      border-color: transparent;
      color: #fff8f2;
    }}
    .dashboard-view {{ display: none; animation: fade .18s ease; }}
    .dashboard-view.active {{ display: block; }}
    @keyframes fade {{ from {{opacity:0; transform: translateY(6px);}} to {{opacity:1; transform: translateY(0);}} }}
    .view-head h2 {{ margin: 0 0 6px; font-size: 32px; }}
    .view-head p {{ margin: 0 0 18px; color: var(--muted); font-size: 16px; }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(7, minmax(0, 1fr));
      gap: 14px;
      margin-bottom: 18px;
    }}
    .kpi-card, .panel {{
      background: var(--paper);
      border: 1px solid rgba(217,201,182,.94);
      border-radius: 22px;
      box-shadow: var(--shadow);
    }}
    .kpi-card {{ padding: 18px; min-height: 142px; display: flex; flex-direction: column; justify-content: space-between; }}
    .kpi-label {{ color: var(--muted); font-size: 13px; text-transform: uppercase; letter-spacing: .08em; }}
    .kpi-value {{ font-size: 34px; line-height: 1; color: var(--accent); }}
    .kpi-help {{ font-size: 13px; color: var(--muted); line-height: 1.35; }}
    .analytics-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
      margin-bottom: 18px;
    }}
    .panel {{ padding: 20px; }}
    .panel h3 {{ margin: 0 0 14px; font-size: 22px; }}
    .bar-row + .bar-row {{ margin-top: 12px; }}
    .bar-meta {{ display: flex; justify-content: space-between; gap: 10px; font-size: 14px; margin-bottom: 6px; }}
    .bar-track {{ height: 12px; background: rgba(217,201,182,.45); border-radius: 999px; overflow: hidden; }}
    .bar-fill {{ height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--accent), var(--accent-2)); }}
    .supplier-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }}
    .supplier-card {{
      border: 1px solid rgba(217,201,182,.94);
      border-radius: 18px;
      padding: 16px;
      background: linear-gradient(180deg, rgba(255,255,255,.68), rgba(249,240,229,.86));
    }}
    .supplier-card-problem {{ border-color: rgba(164,43,43,.35); background: linear-gradient(180deg, rgba(255,248,247,.95), rgba(252,231,229,.85)); }}
    .supplier-rank {{ font-size: 12px; letter-spacing: .16em; color: var(--accent); text-transform: uppercase; margin-bottom: 8px; }}
    .supplier-card h3 {{ margin: 0 0 10px; font-size: 20px; min-height: 52px; }}
    .supplier-card p {{ margin: 6px 0 0; color: var(--muted); font-size: 14px; line-height: 1.35; }}
    .problem-badges {{ display: flex; flex-wrap: wrap; gap: 6px; min-height: 26px; margin-bottom: 4px; }}
    .problem-badge {{ background: var(--danger-soft); color: var(--danger); border: 1px solid rgba(164,43,43,.18); border-radius: 999px; font-size: 11px; padding: 4px 8px; text-transform: uppercase; letter-spacing: .06em; }}
    .table-panel {{ overflow: hidden; }}
    .priority-table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    .priority-table th {{ text-align: left; padding: 12px 10px; background: rgba(216,169,74,.18); border-bottom: 1px solid var(--line); }}
    .priority-table td {{ padding: 11px 10px; border-bottom: 1px solid rgba(217,201,182,.6); vertical-align: top; }}
    .priority-table tbody tr:hover {{ background: rgba(255,248,235,.9); }}
    .priority-table tbody tr.problem-row {{ background: rgba(252,231,229,.45); }}
    .missing-value {{ color: var(--danger); font-weight: 700; }}
    .empty-state {{ padding: 22px; border: 1px dashed var(--line); border-radius: 18px; color: var(--muted); background: rgba(255,255,255,.5); }}
    .footer-note {{ text-align: right; color: var(--muted); font-size: 13px; margin-top: 18px; }}
    @media (max-width: 1200px) {{
      .kpi-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
      .supplier-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 760px) {{
      .shell {{ padding: 16px; }}
      .hero {{ padding: 20px; border-radius: 20px; }}
      .analytics-grid, .kpi-grid, .supplier-grid {{ grid-template-columns: 1fr; }}
      .priority-table {{ display: block; overflow-x: auto; white-space: nowrap; }}
      .view-head h2 {{ font-size: 26px; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <span class="eyebrow">ZContratos</span>
      <h1>Resumo dos contratos no topo da lista de prioridade</h1>
      <p>Painel estatico gerado a partir do consolidado atual, destacando primeiro os fornecedores que aparecem na lista de prioridade e exibindo visoes por recorte do topo da fila.</p>
      <div class="hero-meta">
        <span class="hero-chip">Contratos priorizados: {len(records)}</span>
        <span class="hero-chip">Gerado em: {generated_at}</span>
        <span class="hero-chip">Fonte: contratos_consolidados.json</span>
      </div>
    </section>

    <div class="toolbar">{options_html}</div>
    {views_html}
    <div class="footer-note">Arquivo gerado em {escape(str(OUTPUT_HTML_PATH))}</div>
  </div>

  <script>
    const buttons = Array.from(document.querySelectorAll('.view-button'));
    const views = Array.from(document.querySelectorAll('.dashboard-view'));

    function activateView(viewId) {{
      buttons.forEach((button) => {{
        button.classList.toggle('active', button.dataset.view === viewId);
      }});
      views.forEach((view) => {{
        view.classList.toggle('active', view.id === `view_${{viewId}}`);
      }});
    }}

    buttons.forEach((button) => {{
      button.addEventListener('click', () => activateView(button.dataset.view));
    }});

    activateView('top10');
  </script>
</body>
</html>
"""


def main() -> None:
    records = load_priority_records()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML_PATH.write_text(
        build_dashboard_html(records),
        encoding="utf-8",
    )
    print(f"Dashboard gerado em: {OUTPUT_HTML_PATH}")
    print(f"Contratos priorizados considerados: {len(records)}")


if __name__ == "__main__":
    main()