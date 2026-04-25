from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

try:
    import plotly.graph_objects as go
    from plotly.io import to_html
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Dependencia ausente: plotly. Instale com: pip install plotly"
    ) from exc


def carregar_base(caminho_excel: Path) -> pd.DataFrame:
    if not caminho_excel.exists():
        raise FileNotFoundError(f"Arquivo Excel nao encontrado: {caminho_excel}")

    df = pd.read_excel(caminho_excel)
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df


def montar_resumo_departamento(df: pd.DataFrame) -> pd.DataFrame:
    if "DEPARTAMENTO" not in df.columns:
        raise KeyError("Coluna obrigatoria nao encontrada: DEPARTAMENTO")

    item_col = "CODIGO_PRODUTO" if "CODIGO_PRODUTO" in df.columns else None

    base = df.copy()
    base["DEPARTAMENTO"] = base["DEPARTAMENTO"].astype(str).str.strip()
    base = base[base["DEPARTAMENTO"].ne("") & base["DEPARTAMENTO"].notna()]

    if item_col:
        resumo = (
            base.groupby("DEPARTAMENTO", as_index=False)[item_col]
            .nunique()
            .rename(columns={item_col: "QTD_ITENS"})
        )
    else:
        resumo = (
            base.groupby("DEPARTAMENTO", as_index=False)
            .size()
            .rename(columns={"size": "QTD_ITENS"})
        )

    total = resumo["QTD_ITENS"].sum()
    resumo["PERCENTUAL"] = (resumo["QTD_ITENS"] / total * 100).round(2)
    resumo = resumo.sort_values("QTD_ITENS", ascending=False).reset_index(drop=True)
    return resumo


def gerar_dashboard_html(resumo: pd.DataFrame, destino_html: Path) -> Path:
    fig = go.Figure(
        data=[
            go.Pie(
                labels=resumo["DEPARTAMENTO"],
                values=resumo["QTD_ITENS"],
                customdata=resumo[["QTD_ITENS", "PERCENTUAL"]].to_numpy(),
                textinfo="label+percent",
                hovertemplate=(
                    "Departamento: %{label}<br>"
                    "Itens: %{customdata[0]:,.0f}<br>"
                    "Participacao: %{customdata[1]:.2f}%<extra></extra>"
                ),
            )
        ]
    )

    fig.update_layout(
        title="Comparativo de Itens Sem Venda por Departamento",
        legend_title="Departamento",
    )

    grafico_html = to_html(fig, include_plotlyjs="cdn", full_html=False)
    tabela_html = resumo.to_html(index=False)

    html_final = f"""
<!DOCTYPE html>
<html lang=\"pt-br\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Dashboard Sem Venda</title>
  <style>
    body {{ font-family: Segoe UI, Tahoma, sans-serif; margin: 24px; background: #f5f7fa; color: #1b1f24; }}
    h1 {{ margin-bottom: 8px; }}
    .subtitulo {{ margin-top: 0; margin-bottom: 20px; color: #4b5563; }}
    .card {{ background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; margin-bottom: 16px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; }}
    th {{ background: #eef2f7; }}
  </style>
</head>
<body>
  <h1>Sem Venda - Comparativo por Departamento</h1>
  <p class=\"subtitulo\">Quantidade de itens e percentual de representacao por departamento.</p>
  <div class=\"card\">{grafico_html}</div>
  <div class=\"card\">{tabela_html}</div>
</body>
</html>
""".strip()

    destino_html.parent.mkdir(parents=True, exist_ok=True)
    destino_html.write_text(html_final, encoding="utf-8")
    return destino_html


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera dashboard pizza por departamento a partir do Excel de sem_venda."
    )
    parser.add_argument(
        "--origem",
        type=Path,
        default=Path(__file__).resolve().parent / "sem_venda.xlsx",
        help="Arquivo Excel de origem (padrao: sem_venda.xlsx na mesma pasta).",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=Path(__file__).resolve().parent / "dashboard_sem_venda.html",
        help="Arquivo HTML de saida.",
    )
    args = parser.parse_args()

    df = carregar_base(args.origem)
    resumo = montar_resumo_departamento(df)
    caminho_html = gerar_dashboard_html(resumo, args.saida)

    print(f"Dashboard gerado com sucesso em: {caminho_html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
