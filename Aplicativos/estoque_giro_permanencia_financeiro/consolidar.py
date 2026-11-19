import calendar
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


BASE_DIR = Path(__file__).resolve().parent
TXT_DIR = BASE_DIR / "txt_mes"
CSV_SAIDA = BASE_DIR / "consolidado_mensal.csv"
HTML_SAIDA = BASE_DIR / "dashboard_estoque_permanencia.html"

COLUNAS_NUMERICAS = [
    "ESTQ_INICIAL_VLR",
    "ESTQ_FINAL_VLR",
    "ESTQ_MEDIO_VLR",
    "ESTQ_SEM_GIRO_VLR",
    "VLR_COMPRA",
    "VENDA_LIQUIDA",
    "CMV_LIQUIDO",
    "MARGEM_BRUTA_VLR",
    "GIRO_ESTOQUE",
    "MEDIA_PERMANENCIA_DIAS",
]


def fmt_brl(valor: float) -> str:
    s = f"{valor:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_num(valor: float, casas: int = 1) -> str:
    s = f"{valor:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def dias_da_competencia(comp: str) -> int:
    ano, mes = map(int, str(comp).split("-"))
    return calendar.monthrange(ano, mes)[1]


def carregar_dados() -> pd.DataFrame:
    arquivos = sorted(TXT_DIR.glob("*.txt"))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo .txt encontrado em {TXT_DIR}")

    frames = []
    for arq in arquivos:
        lido = None
        for enc in ("utf-8-sig", "latin1"):
            try:
                lido = pd.read_csv(arq, sep=";", decimal=",", encoding=enc)
                break
            except UnicodeDecodeError:
                continue
        if lido is None:
            raise ValueError(f"Nao foi possivel decodificar {arq.name}")
        lido.columns = [c.strip() for c in lido.columns]
        frames.append(lido)

    df = pd.concat(frames, ignore_index=True)
    df["NROEMPRESA"] = pd.to_numeric(df["NROEMPRESA"], errors="coerce").fillna(0).astype(int)
    df["COMPETENCIA"] = df["COMPETENCIA"].astype(str).str.strip()
    df["DEPARTAMENTO"] = df["DEPARTAMENTO"].astype(str).str.strip()

    for col in COLUNAS_NUMERICAS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        else:
            df[col] = 0.0

    df["DIAS_CALENDARIO"] = df["COMPETENCIA"].apply(dias_da_competencia)

    # Detecta dias efetivos da competencia (ex: mes parcial ate dia 18) a partir da formula do SQL
    mask_dias = (df["CMV_LIQUIDO"] > 100) & (df["ESTQ_MEDIO_VLR"] > 0) & (df["MEDIA_PERMANENCIA_DIAS"] > 0)
    dias_calc = df.loc[mask_dias].copy()
    dias_calc["DIAS_EST"] = (dias_calc["MEDIA_PERMANENCIA_DIAS"] * dias_calc["CMV_LIQUIDO"]) / dias_calc["ESTQ_MEDIO_VLR"]
    mapa_dias = dias_calc.groupby("COMPETENCIA")["DIAS_EST"].median().round().astype(int).to_dict()

    df["DIAS_MES"] = df["COMPETENCIA"].map(mapa_dias).fillna(df["DIAS_CALENDARIO"]).astype(int)
    df["IS_PARCIAL"] = df["DIAS_MES"] < df["DIAS_CALENDARIO"]
    df["COMPETENCIA_LBL"] = np.where(
        df["IS_PARCIAL"],
        df["COMPETENCIA"] + " (" + df["DIAS_MES"].astype(str) + "d)",
        df["COMPETENCIA"],
    )
    df = df.sort_values(["NROEMPRESA", "COMPETENCIA", "DEPARTAMENTO"]).reset_index(drop=True)
    df.to_csv(CSV_SAIDA, sep=";", decimal=",", encoding="utf-8-sig", index=False)
    return df


def agregar_rede(df: pd.DataFrame) -> pd.DataFrame:
    cols_soma = [
        "ESTQ_INICIAL_VLR",
        "ESTQ_FINAL_VLR",
        "ESTQ_SEM_GIRO_VLR",
        "VLR_COMPRA",
        "VENDA_LIQUIDA",
        "CMV_LIQUIDO",
        "MARGEM_BRUTA_VLR",
    ]
    rede = (
        df.groupby(["COMPETENCIA", "COMPETENCIA_LBL", "IS_PARCIAL", "DEPARTAMENTO", "DIAS_MES"], as_index=False)[cols_soma]
        .sum()
    )
    rede["ESTQ_MEDIO_VLR"] = (rede["ESTQ_INICIAL_VLR"] + rede["ESTQ_FINAL_VLR"]) / 2.0
    rede["GIRO_ESTOQUE"] = np.where(
        rede["ESTQ_MEDIO_VLR"] > 0,
        rede["CMV_LIQUIDO"] / rede["ESTQ_MEDIO_VLR"],
        0.0,
    )
    rede["MEDIA_PERMANENCIA_DIAS"] = np.where(
        rede["CMV_LIQUIDO"] > 0,
        (rede["ESTQ_MEDIO_VLR"] / rede["CMV_LIQUIDO"]) * rede["DIAS_MES"],
        0.0,
    )
    return rede


def badge_permanencia(dias: float, cmv: float, estq_final: float) -> str:
    if cmv <= 0 and estq_final <= 0:
        return '<span class="badge badge-neutral">0,0 d</span>'
    if cmv <= 0 and estq_final > 0:
        return '<span class="badge badge-danger">Sem venda</span>'
    if dias <= 30:
        classe = "badge-ok"
    elif dias <= 60:
        classe = "badge-warn"
    else:
        classe = "badge-danger"
    return f'<span class="badge {classe}">{fmt_num(dias, 1)} d</span>'


def compilar_visao(view_id: str, nome_visao: str, curr_df: pd.DataFrame) -> str:
    mensal = (
        curr_df.groupby(["COMPETENCIA", "COMPETENCIA_LBL", "DIAS_MES"], as_index=False)[
            [
                "ESTQ_INICIAL_VLR",
                "ESTQ_FINAL_VLR",
                "ESTQ_SEM_GIRO_VLR",
                "VLR_COMPRA",
                "VENDA_LIQUIDA",
                "CMV_LIQUIDO",
                "MARGEM_BRUTA_VLR",
            ]
        ]
        .sum()
        .sort_values("COMPETENCIA")
    )
    mensal["ESTQ_MEDIO_VLR"] = (mensal["ESTQ_INICIAL_VLR"] + mensal["ESTQ_FINAL_VLR"]) / 2.0
    mensal["PERMANENCIA_DIAS"] = np.where(
        mensal["CMV_LIQUIDO"] > 0,
        (mensal["ESTQ_MEDIO_VLR"] / mensal["CMV_LIQUIDO"]) * mensal["DIAS_MES"],
        0.0,
    )
    mensal["GIRO_MENSAL"] = np.where(
        mensal["ESTQ_MEDIO_VLR"] > 0,
        mensal["CMV_LIQUIDO"] / mensal["ESTQ_MEDIO_VLR"],
        0.0,
    )

    ult_comp = mensal["COMPETENCIA"].iloc[-1]
    ult_lbl = mensal["COMPETENCIA_LBL"].iloc[-1]
    pri_comp = mensal["COMPETENCIA"].iloc[0]
    estq_final_ult = float(mensal["ESTQ_FINAL_VLR"].iloc[-1])
    estq_final_pri = float(mensal["ESTQ_FINAL_VLR"].iloc[0])
    estq_sem_giro_ult = float(mensal["ESTQ_SEM_GIRO_VLR"].iloc[-1])
    pct_sem_giro = (estq_sem_giro_ult / estq_final_ult * 100.0) if estq_final_ult > 0 else 0.0
    var_estq_pct = ((estq_final_ult - estq_final_pri) / estq_final_pri * 100.0) if estq_final_pri > 0 else 0.0

    estq_medio_periodo = float(mensal["ESTQ_MEDIO_VLR"].mean())
    cmv_total = float(mensal["CMV_LIQUIDO"].sum())
    venda_total = float(mensal["VENDA_LIQUIDA"].sum())
    margem_total = float(mensal["MARGEM_BRUTA_VLR"].sum())
    margem_pct = (margem_total / venda_total * 100.0) if venda_total > 0 else 0.0
    dias_total = int(mensal["DIAS_MES"].sum())
    pmr_periodo = (estq_medio_periodo / cmv_total * dias_total) if cmv_total > 0 else 0.0
    giro_medio_mensal = (float(mensal["CMV_LIQUIDO"].mean()) / estq_medio_periodo) if estq_medio_periodo > 0 else 0.0

    # Grafico 1: Evolucao Mensal (Barras + Linha PMR)
    fig_evol = make_subplots(specs=[[{"secondary_y": True}]])
    fig_evol.add_trace(
        go.Bar(
            x=mensal["COMPETENCIA_LBL"],
            y=mensal["ESTQ_FINAL_VLR"],
            name="Estoque Final (R$)",
            marker_color="#2563eb",
            hovertemplate="Comp: %{x}<br>Estoque Final: R$ %{y:,.2f}<extra></extra>",
        ),
        secondary_y=False,
    )
    fig_evol.add_trace(
        go.Bar(
            x=mensal["COMPETENCIA_LBL"],
            y=mensal["ESTQ_SEM_GIRO_VLR"],
            name="Sem Giro no Mês (R$)",
            marker_color="#f59e0b",
            hovertemplate="Comp: %{x}<br>Sem Giro: R$ %{y:,.2f}<extra></extra>",
        ),
        secondary_y=False,
    )
    fig_evol.add_trace(
        go.Bar(
            x=mensal["COMPETENCIA_LBL"],
            y=mensal["CMV_LIQUIDO"],
            name="CMV Líquido (R$)",
            marker_color="#10b981",
            hovertemplate="Comp: %{x}<br>CMV Líquido: R$ %{y:,.2f}<extra></extra>",
        ),
        secondary_y=False,
    )
    fig_evol.add_trace(
        go.Scatter(
            x=mensal["COMPETENCIA_LBL"],
            y=mensal["PERMANENCIA_DIAS"],
            name="Permanência (Dias)",
            mode="lines+markers+text",
            text=[fmt_num(v, 1) + "d" for v in mensal["PERMANENCIA_DIAS"]],
            textposition="top center",
            line=dict(color="#ef4444", width=3),
            marker=dict(size=8),
            hovertemplate="Comp: %{x}<br>Permanência: %{y:.1f} dias<extra></extra>",
        ),
        secondary_y=True,
    )
    fig_evol.update_layout(
        title=f"Evolução Mensal: Estoque, CMV e Permanência — {nome_visao}",
        barmode="group",
        template="plotly_white",
        height=400,
        margin=dict(l=50, r=50, t=55, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig_evol.update_xaxes(type="category")
    fig_evol.update_yaxes(title_text="Valores (R$)", secondary_y=False)
    fig_evol.update_yaxes(title_text="Permanência (Dias)", secondary_y=True, showgrid=False)
    html_evol = fig_evol.to_html(full_html=False, include_plotlyjs=False)

    # Grafico 2: Heatmap Departamento x Competencia (Permanencia em Dias)
    piv_pmr = curr_df.pivot_table(
        index="DEPARTAMENTO",
        columns="COMPETENCIA",
        values="MEDIA_PERMANENCIA_DIAS",
        aggfunc="sum",
        fill_value=0.0,
    )
    piv_estq = curr_df.pivot_table(
        index="DEPARTAMENTO",
        columns="COMPETENCIA",
        values="ESTQ_FINAL_VLR",
        aggfunc="sum",
        fill_value=0.0,
    )
    # Remove linhas completamente zeradas no periodo
    mask_ativo = (piv_estq.sum(axis=1) > 0) | (piv_pmr.sum(axis=1) > 0)
    piv_pmr = piv_pmr[mask_ativo]
    # Ordena por maior estoque no ultimo mes
    ordem_depts = (
        curr_df.groupby("DEPARTAMENTO")["ESTQ_FINAL_VLR"]
        .mean()
        .reindex(piv_pmr.index)
        .sort_values(ascending=True)
        .index
    )
    piv_pmr = piv_pmr.reindex(ordem_depts)
    mapa_lbl = curr_df.drop_duplicates("COMPETENCIA").set_index("COMPETENCIA")["COMPETENCIA_LBL"].to_dict()
    col_labels = [mapa_lbl.get(c, c) for c in piv_pmr.columns]

    texto_heat = [[f"{fmt_num(val, 0)}d" if val > 0 else "-" for val in row] for row in piv_pmr.values]
    fig_heat = go.Figure(
        data=go.Heatmap(
            z=piv_pmr.values,
            x=col_labels,
            y=list(piv_pmr.index),
            text=texto_heat,
            texttemplate="%{text}",
            colorscale="RdYlGn_r",
            zmin=0,
            zmax=150,
            colorbar=dict(title="Dias (teto 150d)"),
            hovertemplate="Dept: %{y}<br>Comp: %{x}<br>Permanência: %{z:.1f} dias<extra></extra>",
        )
    )
    fig_heat.update_xaxes(type="category")
    fig_heat.update_layout(
        title=f"Mapa de Calor: Média de Permanência (Dias) por Departamento — {nome_visao}",
        template="plotly_white",
        height=max(360, 34 * len(piv_pmr.index) + 110),
        margin=dict(l=160, r=30, t=55, b=40),
    )
    html_heat = fig_heat.to_html(full_html=False, include_plotlyjs=False)

    # Tabela Analitica
    tab_df = curr_df.sort_values(["COMPETENCIA", "ESTQ_FINAL_VLR"], ascending=[False, False]).copy()
    linhas_tb = []
    for _, r in tab_df.iterrows():
        badge = badge_permanencia(r["MEDIA_PERMANENCIA_DIAS"], r["CMV_LIQUIDO"], r["ESTQ_FINAL_VLR"])
        linhas_tb.append(
            f"<tr data-comp='{r['COMPETENCIA']}' data-dias='{int(r['DIAS_MES'])}' "
            f"data-ei='{r['ESTQ_INICIAL_VLR']:.2f}' data-ef='{r['ESTQ_FINAL_VLR']:.2f}' "
            f"data-em='{r['ESTQ_MEDIO_VLR']:.2f}' data-sg='{r['ESTQ_SEM_GIRO_VLR']:.2f}' "
            f"data-co='{r['VLR_COMPRA']:.2f}' data-vd='{r['VENDA_LIQUIDA']:.2f}' "
            f"data-cmv='{r['CMV_LIQUIDO']:.2f}' data-mg='{r['MARGEM_BRUTA_VLR']:.2f}'>"
            f"<td>{r['COMPETENCIA_LBL']}</td>"
            f"<td><b>{r['DEPARTAMENTO']}</b></td>"
            f"<td class='num'>{fmt_brl(r['ESTQ_INICIAL_VLR'])}</td>"
            f"<td class='num'>{fmt_brl(r['ESTQ_FINAL_VLR'])}</td>"
            f"<td class='num'>{fmt_brl(r['ESTQ_MEDIO_VLR'])}</td>"
            f"<td class='num'>{fmt_brl(r['ESTQ_SEM_GIRO_VLR'])}</td>"
            f"<td class='num'>{fmt_brl(r['VLR_COMPRA'])}</td>"
            f"<td class='num'>{fmt_brl(r['VENDA_LIQUIDA'])}</td>"
            f"<td class='num'>{fmt_brl(r['CMV_LIQUIDO'])}</td>"
            f"<td class='num'>{fmt_brl(r['MARGEM_BRUTA_VLR'])}</td>"
            f"<td class='num'>{fmt_num(r['GIRO_ESTOQUE'], 2)}x</td>"
            f"<td class='center'>{badge}</td>"
            f"</tr>"
        )
    linhas_html = "\n".join(linhas_tb)

    sinal_var = "+" if var_estq_pct >= 0 else ""
    return f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">Estoque Final ({ult_lbl})</div>
            <div class="kpi-value">{fmt_brl(estq_final_ult)}</div>
            <div class="kpi-sub">{sinal_var}{fmt_num(var_estq_pct, 1)}% vs {pri_comp}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Estoque Médio Mensal</div>
            <div class="kpi-value">{fmt_brl(estq_medio_periodo)}</div>
            <div class="kpi-sub">Sem giro ({ult_lbl}): {fmt_brl(estq_sem_giro_ult)} ({fmt_num(pct_sem_giro, 1)}%)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">CMV Líquido Acumulado</div>
            <div class="kpi-value">{fmt_brl(cmv_total)}</div>
            <div class="kpi-sub">Venda Líq: {fmt_brl(venda_total)} | Margem: {fmt_num(margem_pct, 1)}%</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Permanência Média (PMR)</div>
            <div class="kpi-value">{fmt_num(pmr_periodo, 1)} dias</div>
            <div class="kpi-sub">Giro médio mensal: {fmt_num(giro_medio_mensal, 2)}x ({dias_total} dias no período)</div>
        </div>
    </div>

    <div class="card">
        {html_evol}
    </div>

    <div class="card" style="margin-top: 16px;">
        {html_heat}
    </div>

    <div class="card" style="margin-top: 16px;">
        <div class="table-header">
            <h3>Detalhamento Mês a Mês por Departamento — {nome_visao}</h3>
            <input type="text" class="search-input" placeholder="Filtrar departamento ou mês (ex: 2026-10 ou BEBIDAS)..." oninput="filtrarTabela('{view_id}', this.value)" onkeyup="filtrarTabela('{view_id}', this.value)">
        </div>
        <div class="table-wrap">
            <table id="tbl_{view_id}">
                <thead>
                    <tr>
                        <th>Competência</th>
                        <th>Departamento</th>
                        <th class="num">Estq. Inicial</th>
                        <th class="num">Estq. Final</th>
                        <th class="num">Estq. Médio</th>
                        <th class="num">Sem Giro</th>
                        <th class="num">Compras</th>
                        <th class="num">Venda Líq.</th>
                        <th class="num">CMV Líq.</th>
                        <th class="num">Margem Bruta</th>
                        <th class="num">Giro</th>
                        <th class="center">Permanência</th>
                    </tr>
                </thead>
                <tbody>
                    {linhas_html}
                </tbody>
                <tfoot id="tfoot_{view_id}">
                    <tr>
                        <td colspan="2">TOTAL (0 linhas)</td>
                        <td class="num">R$ 0,00</td>
                        <td class="num">R$ 0,00</td>
                        <td class="num">R$ 0,00</td>
                        <td class="num">R$ 0,00</td>
                        <td class="num">R$ 0,00</td>
                        <td class="num">R$ 0,00</td>
                        <td class="num">R$ 0,00</td>
                        <td class="num">R$ 0,00</td>
                        <td class="num">0,00x</td>
                        <td class="center">-</td>
                    </tr>
                </tfoot>
            </table>
        </div>
    </div>
    """


def gerar_dashboard(df: pd.DataFrame) -> None:
    rede_df = agregar_rede(df)

    visoes_html = []
    opcoes_select = []

    conteudo_global = compilar_visao("global", "Todas as Lojas (Consolidado Rede)", rede_df)
    visoes_html.append(f'<div id="view_global" class="sub-view" style="display:block;">{conteudo_global}</div>')
    opcoes_select.append('<option value="global">Todas as Lojas (Consolidado Rede)</option>')

    for emp in sorted(df["NROEMPRESA"].unique()):
        df_emp = df[df["NROEMPRESA"] == emp]
        vid = f"loja_{emp}"
        titulo = f"Loja {emp}"
        conteudo_emp = compilar_visao(vid, titulo, df_emp)
        visoes_html.append(f'<div id="view_{vid}" class="sub-view" style="display:none;">{conteudo_emp}</div>')
        opcoes_select.append(f'<option value="{vid}">{titulo}</option>')

    html_final = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Financeiro de Estoque, CMV e Permanência</title>
    <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
    <style>
        :root {{
            --bg: #f1f5f9;
            --card: #ffffff;
            --text: #0f172a;
            --muted: #64748b;
            --border: #e2e8f0;
            --primary: #1d4ed8;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
        }}
        .topbar {{
            position: sticky;
            top: 0;
            z-index: 100;
            background: #0f172a;
            color: #fff;
            padding: 14px 24px;
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        .topbar h1 {{
            margin: 0;
            font-size: 18px;
            font-weight: 600;
        }}
        .topbar select {{
            padding: 8px 14px;
            border-radius: 6px;
            border: 1px solid #334155;
            background: #1e293b;
            color: #fff;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
        }}
        .container {{
            max-width: 1560px;
            margin: 20px auto;
            padding: 0 20px 40px;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-bottom: 16px;
        }}
        .kpi-card {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px 18px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }}
        .kpi-label {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: var(--muted);
            font-weight: 600;
        }}
        .kpi-value {{
            font-size: 24px;
            font-weight: 700;
            margin: 6px 0 4px;
            color: var(--text);
        }}
        .kpi-sub {{
            font-size: 12.5px;
            color: var(--muted);
        }}
        .chart-grid-2 {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(520px, 1fr));
            gap: 16px;
        }}
        .card {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }}
        .table-header {{
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }}
        .table-header h3 {{ margin: 0; font-size: 16px; }}
        .search-input {{
            padding: 8px 12px;
            border: 1px solid var(--border);
            border-radius: 6px;
            width: 320px;
            max-width: 100%;
            font-size: 13px;
        }}
        .table-wrap {{
            overflow-x: auto;
            max-height: 540px;
            overflow-y: auto;
            border: 1px solid var(--border);
            border-radius: 8px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        thead th {{
            position: sticky;
            top: 0;
            background: #f8fafc;
            border-bottom: 2px solid var(--border);
            padding: 10px 10px;
            text-align: left;
            font-weight: 600;
            color: #334155;
            white-space: nowrap;
        }}
        tbody td {{
            padding: 8px 10px;
            border-bottom: 1px solid #f1f5f9;
            white-space: nowrap;
        }}
        tbody tr:hover {{ background: #f8fafc; }}
        tfoot td {{
            position: sticky;
            bottom: 0;
            background: #e2e8f0;
            color: #0f172a;
            font-weight: 700;
            padding: 10px 10px;
            border-top: 2px solid #94a3b8;
            white-space: nowrap;
            z-index: 2;
        }}
        .num {{ text-align: right; font-variant-numeric: tabular-nums; }}
        .center {{ text-align: center; }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 999px;
            font-size: 11.5px;
            font-weight: 600;
        }}
        .badge-ok {{ background: #dcfce7; color: #166534; }}
        .badge-warn {{ background: #fef9c3; color: #854d0e; }}
        .badge-danger {{ background: #fee2e2; color: #991b1b; }}
        .badge-neutral {{ background: #f1f5f9; color: #475569; }}
    </style>
</head>
<body>
    <div class="topbar">
        <h1>Estoque Financeiro, CMV & Permanência por Departamento</h1>
        <div>
            <label for="FiltroMestre" style="font-size:13px;color:#cbd5e1;margin-right:8px;">Visão:</label>
            <select id="FiltroMestre" onchange="trocarVisao()">
                {''.join(opcoes_select)}
            </select>
        </div>
    </div>

    <div class="container">
        {''.join(visoes_html)}
    </div>

    <script>
        function trocarVisao() {{
            var selecionado = document.getElementById("FiltroMestre").value;
            var abas = document.getElementsByClassName("sub-view");
            for (var i = 0; i < abas.length; i++) {{
                abas[i].style.display = (abas[i].id === "view_" + selecionado) ? "block" : "none";
            }}
            window.dispatchEvent(new Event('resize'));
        }}

        function fmtBRL(v) {{
            return v.toLocaleString('pt-BR', {{ style: 'currency', currency: 'BRL' }});
        }}

        function fmtNum(v, casas) {{
            return v.toLocaleString('pt-BR', {{ minimumFractionDigits: casas, maximumFractionDigits: casas }});
        }}

        function atualizarTotalizador(viewId) {{
            var tabela = document.getElementById("tbl_" + viewId);
            var tfoot = document.getElementById("tfoot_" + viewId);
            if (!tabela || !tfoot) return;

            var linhas = tabela.getElementsByTagName("tbody")[0].getElementsByTagName("tr");
            var visiveis = 0;
            var ei = 0, ef = 0, em = 0, sg = 0, co = 0, vd = 0, cmv = 0, mg = 0;
            var compsDias = new Map();

            for (var i = 0; i < linhas.length; i++) {{
                if (linhas[i].style.display === "none") continue;
                visiveis++;
                var ds = linhas[i].dataset;
                ei += parseFloat(ds.ei || 0);
                ef += parseFloat(ds.ef || 0);
                em += parseFloat(ds.em || 0);
                sg += parseFloat(ds.sg || 0);
                co += parseFloat(ds.co || 0);
                vd += parseFloat(ds.vd || 0);
                cmv += parseFloat(ds.cmv || 0);
                mg += parseFloat(ds.mg || 0);
                if (ds.comp && !compsDias.has(ds.comp)) {{
                    compsDias.set(ds.comp, parseInt(ds.dias || 30, 10));
                }}
            }}

            var nComps = compsDias.size || 1;
            var somaDias = 0;
            compsDias.forEach(function(d) {{ somaDias += d; }});
            var estqMedioPeriodo = em / nComps;
            var giro = estqMedioPeriodo > 0 ? (cmv / estqMedioPeriodo) : 0;
            var pmr = (cmv > 0 && estqMedioPeriodo > 0) ? ((estqMedioPeriodo / cmv) * somaDias) : 0;

            var badgeCls = pmr <= 0 ? "badge-neutral" : (pmr <= 30 ? "badge-ok" : (pmr <= 60 ? "badge-warn" : "badge-danger"));
            var pmrTxt = (cmv <= 0 && ef > 0) ? "Sem venda" : (fmtNum(pmr, 1) + " d");

            var cells = tfoot.getElementsByTagName("tr")[0].getElementsByTagName("td");
            cells[0].textContent = "TOTAL (" + visiveis + (visiveis === 1 ? " linha)" : " linhas)");
            cells[1].textContent = fmtBRL(ei);
            cells[2].textContent = fmtBRL(ef);
            cells[3].textContent = fmtBRL(em);
            cells[4].textContent = fmtBRL(sg);
            cells[5].textContent = fmtBRL(co);
            cells[6].textContent = fmtBRL(vd);
            cells[7].textContent = fmtBRL(cmv);
            cells[8].textContent = fmtBRL(mg);
            cells[9].textContent = fmtNum(giro, 2) + "x";
            cells[10].innerHTML = '<span class="badge ' + badgeCls + '">' + pmrTxt + '</span>';
        }}

        function filtrarTabela(viewId, termo) {{
            var filtro = termo.toUpperCase().trim();
            var tabela = document.getElementById("tbl_" + viewId);
            if (!tabela) return;
            var linhas = tabela.getElementsByTagName("tbody")[0].getElementsByTagName("tr");
            for (var i = 0; i < linhas.length; i++) {{
                var texto = linhas[i].textContent || linhas[i].innerText;
                linhas[i].style.display = texto.toUpperCase().indexOf(filtro) > -1 ? "" : "none";
            }}
            atualizarTotalizador(viewId);
        }}

        document.addEventListener("DOMContentLoaded", function() {{
            var tabelas = document.querySelectorAll("table[id^='tbl_']");
            for (var i = 0; i < tabelas.length; i++) {{
                atualizarTotalizador(tabelas[i].id.replace("tbl_", ""));
            }}
        }});
    </script>
</body>
</html>
"""
    HTML_SAIDA.write_text(html_final, encoding="utf-8")


def main() -> None:
    df = carregar_dados()
    gerar_dashboard(df)
    print(f"Consolidado CSV salvo em: {CSV_SAIDA}")
    print(f"Dashboard HTML salvo em: {HTML_SAIDA}")
    print(f"Linhas processadas: {len(df)} | Lojas: {sorted(df['NROEMPRESA'].unique().tolist())} | Meses: {sorted(df['COMPETENCIA'].unique().tolist())}")


if __name__ == "__main__":
    main()
