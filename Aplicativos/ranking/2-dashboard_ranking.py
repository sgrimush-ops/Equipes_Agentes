from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

# Edite apenas o lado direito de cada linha para encurtar nomes no dashboard.
# Formato: NOME_ORIGINAL=NOME_EXIBICAO
RENOMEAR_COLUNAS = [
	"COD_F=COD",
	"FORNECEDOR=FORNECEDOR",
	"COMPRADOR=COMPRADOR",
	"QTD_SKU=SKUS",
	"VLR_VENDA=VENDA",
	"VLR_COMPRA=COMPRA",
	"VLR_DEVOLUCAO_COMPRA=DEVOL",
	"VLR_BONIFICADO=BONIF",
	"VLR_CUSTO_CD=CUSTO_CD",
	"VLR_CUSTO_LOJAS=CUSTO_LOJ",
	"VLR_CUSTO_TOTAL_EMPRESA=T_EMPRESA",
	"QTD_INCINERACAO_ANO=INCINER",
]


def carregar_dados(caminho_excel: Path) -> pd.DataFrame:
	if not caminho_excel.exists():
		raise FileNotFoundError(f"Arquivo nao encontrado: {caminho_excel}")

	df = pd.read_excel(caminho_excel)
	if df.empty:
		raise ValueError("O arquivo Excel esta vazio.")

	return df


def aplicar_renomeacao_colunas(df: pd.DataFrame) -> pd.DataFrame:
	df = df.copy()
	df.columns = [str(col).strip() for col in df.columns]

	mapa = {}
	for linha in RENOMEAR_COLUNAS:
		if "=" not in linha:
			continue

		origem, destino = linha.split("=", 1)
		origem = origem.strip()
		destino = destino.strip()

		if origem and destino:
			mapa[origem] = destino

	if mapa:
		df = df.rename(columns=mapa)

	return df


def adicionar_percentual_compra_venda(df: pd.DataFrame) -> pd.DataFrame:
	df = df.copy()
	col_venda = "VENDA" if "VENDA" in df.columns else ("VLR_VENDA" if "VLR_VENDA" in df.columns else None)
	col_compra = "COMPRA" if "COMPRA" in df.columns else ("VLR_COMPRA" if "VLR_COMPRA" in df.columns else None)

	if col_venda and col_compra:
		venda = pd.to_numeric(df[col_venda], errors="coerce").fillna(0.0)
		compra = pd.to_numeric(df[col_compra], errors="coerce").fillna(0.0)
		
		# Calcular percentual (compra / venda * 100), evitando divisão por zero
		df["% COMPRA/VENDA"] = (compra / venda.replace(0, pd.NA)).fillna(0.0) * 100.0

		# Posicionar logo após a coluna de COMPRA (ou VLR_COMPRA)
		cols = list(df.columns)
		if col_compra in cols and "% COMPRA/VENDA" in cols:
			cols.remove("% COMPRA/VENDA")
			idx = cols.index(col_compra) + 1
			cols.insert(idx, "% COMPRA/VENDA")
			df = df[cols]

	return df


def preparar_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str], list[str]]:
	df = df.copy()
	df.columns = [str(col).strip() for col in df.columns]

	colunas_decimais = []
	colunas_inteiras = []

	for coluna in ["CODIGO_FORNECEDOR", "QTD_SKU"]:
		if coluna in df.columns:
			df[coluna] = pd.to_numeric(df[coluna], errors="coerce").fillna(0).astype("Int64")
			colunas_inteiras.append(coluna)

	for coluna in df.columns:
		if coluna.upper().startswith("VLR") or "%" in coluna or coluna.upper().startswith("PERC"):
			df[coluna] = pd.to_numeric(df[coluna], errors="coerce").fillna(0.0)
			colunas_decimais.append(coluna)

	for coluna in df.columns:
		if coluna in colunas_decimais or coluna in colunas_inteiras:
			continue

		serie_convertida = pd.to_numeric(df[coluna], errors="coerce")
		if serie_convertida.notna().sum() > 0 and serie_convertida.notna().sum() >= (len(df) * 0.7):
			# Demais colunas numericas seguem como inteiras para manter leitura limpa.
			df[coluna] = serie_convertida.fillna(0).round(0).astype("Int64")
			colunas_inteiras.append(coluna)

	for coluna in df.columns:
		if coluna not in colunas_decimais and coluna not in colunas_inteiras:
			df[coluna] = df[coluna].fillna("").astype(str)

	colunas_texto = [
		col
		for col in df.columns
		if col not in colunas_decimais and col not in colunas_inteiras
	]
	return df, colunas_decimais, colunas_inteiras, colunas_texto


def calcular_larguras_colunas(
	df: pd.DataFrame,
	colunas_decimais: list[str],
	colunas_inteiras: list[str],
) -> list[str]:
	larguras = []
	primeira_coluna = df.columns[0] if len(df.columns) > 0 else ""

	for coluna in df.columns:
		serie = df[coluna]

		if "%" in coluna or coluna.upper().startswith("PERC"):
			textos = serie.fillna(0).map(lambda v: f"{float(v):,.2f}%".replace(",", "X").replace(".", ",").replace("X", "."))
		elif coluna in colunas_decimais:
			textos = serie.fillna(0).map(lambda v: f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
		elif coluna == primeira_coluna and coluna in colunas_inteiras:
			textos = serie.fillna(0).map(lambda v: str(int(float(v))))
		elif coluna in colunas_inteiras:
			textos = serie.fillna(0).map(lambda v: f"{int(float(v)):,}".replace(",", "."))
		else:
			textos = serie.fillna("").astype(str)

		max_len = int(textos.map(len).max()) if len(textos) else 10

		# Largura guiada pelo valor exibido, com limites para evitar distorcoes.
		largura_ch = max(8, min(max_len + 2, 42))
		larguras.append(f"{largura_ch}ch")

	return larguras


def calcular_totais_exibicao(
	df: pd.DataFrame,
	colunas_decimais: list[str],
	colunas_inteiras: list[str],
	colunas_texto: list[str],
) -> list[str]:
	if df.empty:
		return []

	primeira_coluna = df.columns[0]
	valores_totais: list[str] = []
	coluna_texto_principal = colunas_texto[0] if colunas_texto else ""

	col_venda = "VENDA" if "VENDA" in df.columns else ("VLR_VENDA" if "VLR_VENDA" in df.columns else None)
	col_compra = "COMPRA" if "COMPRA" in df.columns else ("VLR_COMPRA" if "VLR_COMPRA" in df.columns else None)
	total_venda = float(pd.to_numeric(df[col_venda], errors="coerce").fillna(0).sum()) if col_venda else 0.0
	total_compra = float(pd.to_numeric(df[col_compra], errors="coerce").fillna(0).sum()) if col_compra else 0.0

	for coluna in df.columns:
		if "%" in coluna or coluna.upper().startswith("PERC"):
			if total_venda > 0:
				perc_total = (total_compra / total_venda) * 100.0
				valores_totais.append(f"{perc_total:,.2f}%".replace(",", "X").replace(".", ",").replace("X", "."))
			else:
				valores_totais.append("0,00%")
		elif coluna in colunas_decimais:
			total = float(pd.to_numeric(df[coluna], errors="coerce").fillna(0).sum())
			valores_totais.append(f"{total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
		elif coluna in colunas_inteiras:
			total = int(pd.to_numeric(df[coluna], errors="coerce").fillna(0).sum())
			if coluna == primeira_coluna:
				valores_totais.append("TOTAL")
			else:
				valores_totais.append(f"{total:,}".replace(",", "."))
		elif coluna == coluna_texto_principal:
			valores_totais.append("TOTAL")
		else:
			valores_totais.append("-")

	return valores_totais


def gerar_html(
	df: pd.DataFrame,
	colunas_decimais: list[str],
	colunas_inteiras: list[str],
	larguras_colunas: list[str],
	totais_exibicao: list[str],
	destino_html: Path,
	titulo: str,
) -> Path:
	cabecalhos = "\n".join(f"            <th>{col}</th>" for col in df.columns)
	colunas_js = []
	primeira_coluna = df.columns[0] if len(df.columns) > 0 else ""
	total_celulas_html = "\n".join(
		f"\t\t\t\t\t<th>{valor}</th>" for valor in totais_exibicao
	)

	for col in df.columns:
		if "%" in col or col.upper().startswith("PERC"):
			colunas_js.append(
				"{"
				f"data: '{col}', className: 'dt-body-right', "
				"render: function(data, type) {"
				"if (type === 'display') {"
				"return Number(data || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + '%';"
				"}"
				"return Number(data || 0);"
				"}"
				"}"
			)
		elif col in colunas_decimais:
			colunas_js.append(
				"{"
				f"data: '{col}', className: 'dt-body-right', "
				"render: function(data, type) {"
				"if (type === 'display') {"
				"return Number(data || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});"
				"}"
				"return Number(data || 0);"
				"}"
				"}"
			)
		elif col in colunas_inteiras:
			if col == primeira_coluna:
				colunas_js.append(
					"{"
					f"data: '{col}', className: 'dt-body-right', "
					"render: function(data, type) {"
					"if (type === 'display') {"
					"return String(Math.trunc(Number(data || 0)));"
					"}"
					"return Number(data || 0);"
					"}"
					"}"
				)
			else:
				colunas_js.append(
					"{"
					f"data: '{col}', className: 'dt-body-right', "
					"render: function(data, type) {"
					"if (type === 'display') {"
					"return Number(data || 0).toLocaleString('pt-BR', {maximumFractionDigits: 0});"
					"}"
					"return Number(data || 0);"
					"}"
					"}"
				)
		else:
			colunas_js.append(f"{{data: '{col}'}}")

	dados_json = df.to_json(orient="records", force_ascii=False)
	definicao_colunas_js = ",\n                ".join(colunas_js)
	column_defs_js = ",\n                ".join(
		f"{{targets: {idx}, width: '{largura}'}}" for idx, largura in enumerate(larguras_colunas)
	)

	html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
	<meta charset="utf-8" />
	<meta name="viewport" content="width=device-width, initial-scale=1" />
	<title>{titulo}</title>
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
	<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap" rel="stylesheet">
	<link rel="stylesheet" href="https://cdn.datatables.net/1.13.8/css/jquery.dataTables.min.css" />
	<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
	<script src="https://cdn.datatables.net/1.13.8/js/jquery.dataTables.min.js"></script>
	<style>
		:root {{
			--bg-1: #f5efe4;
			--bg-2: #f8fafc;
			--ink: #1f2937;
			--ink-soft: #6b7280;
			--brand: #a8550f;
			--brand-strong: #7c2d12;
			--card: #ffffff;
			--line: #e5e7eb;
		}}

		* {{ box-sizing: border-box; }}

		body {{
			margin: 0;
			font-family: 'Manrope', sans-serif;
			color: var(--ink);
			background:
				radial-gradient(circle at 0% 0%, #fde68a 0%, transparent 35%),
				radial-gradient(circle at 100% 100%, #bfdbfe 0%, transparent 30%),
				linear-gradient(160deg, var(--bg-1), var(--bg-2));
			min-height: 100vh;
			padding: 24px;
		}}

		.container {{
			max-width: 98%;
			margin: 0 auto;
		}}

		.hero {{
			background: linear-gradient(120deg, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.82));
			border: 1px solid rgba(255, 255, 255, 0.9);
			border-radius: 18px;
			padding: 24px;
			box-shadow: 0 12px 40px rgba(15, 23, 42, 0.08);
			margin-bottom: 18px;
			animation: riseIn 450ms ease-out;
		}}

		h1 {{
			margin: 0;
			color: var(--brand-strong);
			font-size: clamp(1.35rem, 2.2vw, 2.15rem);
			letter-spacing: -0.02em;
		}}

		.sub {{
			margin-top: 8px;
			color: var(--ink-soft);
			font-size: 0.95rem;
		}}

		.card {{
			background: var(--card);
			border: 1px solid var(--line);
			border-radius: 16px;
			padding: 14px;
			box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
			animation: riseIn 500ms ease-out;
		}}

		.hint {{
			margin: 0 0 12px 0;
			color: var(--ink-soft);
			font-size: 0.9rem;
		}}

		table.dataTable thead th {{
			background: #fff7ed;
			color: #9a3412;
			border-bottom: 1px solid #fed7aa;
			font-weight: 800;
			white-space: normal;
			word-break: break-word;
		}}

		table.dataTable tbody tr:hover {{
			background: #fffbeb;
		}}

		table.dataTable tbody td {{
			white-space: nowrap;
		}}

		table.dataTable thead tr.totais-row th {{
			background: #ffedd5;
			border-top: 1px solid #fed7aa;
			border-bottom: 1px solid #fed7aa;
			font-weight: 800;
			padding: 8px;
			text-align: right;
			white-space: nowrap;
			color: #7c2d12;
		}}

		table.dataTable thead tr.totais-row th:first-child {{
			text-align: left;
		}}

		.dataTables_wrapper .dataTables_filter input,
		.dataTables_wrapper .dataTables_length select {{
			border: 1px solid #d1d5db;
			border-radius: 10px;
			padding: 6px 10px;
			background: #fff;
		}}

		.dataTables_wrapper .dataTables_paginate .paginate_button.current {{
			background: #fdba74 !important;
			color: #7c2d12 !important;
			border: 1px solid #fb923c !important;
			border-radius: 8px;
		}}

		@keyframes riseIn {{
			from {{ opacity: 0; transform: translateY(8px); }}
			to {{ opacity: 1; transform: translateY(0); }}
		}}

		@media (max-width: 700px) {{
			body {{ padding: 14px; }}
			.hero {{ padding: 18px; }}
			.card {{ padding: 10px; }}
		}}

		/* Forçar orientação de paisagem para impressão/salvar em PDF */
		@media print {{
			@page {{
				size: landscape;
				margin: 10mm;
			}}
			body {{
				background: none !important;
				padding: 0 !important;
			}}
			.container {{
				max-width: 100% !important;
				width: 100% !important;
			}}
			.hero {{
				box-shadow: none !important;
				border: none !important;
				padding: 0 0 10px 0 !important;
				margin-bottom: 10px !important;
				background: transparent !important;
			}}
			.card {{
				box-shadow: none !important;
				border: none !important;
				padding: 0 !important;
			}}
			.dataTables_length, .dataTables_filter, .dataTables_paginate, .dataTables_info, .hint {{
				display: none !important;
			}}
		}}
	</style>
</head>
<body>
	<div class="container">
		<section class="hero">
			<h1>{titulo}</h1>
			<p class="sub">Clique no nome de qualquer coluna para reordenar os dados (crescente/decrescente).</p>
		</section>

		<section class="card">
			<p class="hint">Use o campo de busca para filtrar rapidamente fornecedores, compradores e demais colunas.</p>
			<div style="overflow-x: auto; width: 100%;">
				<table id="tabelaRanck" class="display stripe hover" style="width:100%">
					<thead>
						<tr>
{cabecalhos}
						</tr>
						<tr class="totais-row">
{total_celulas_html}
						</tr>
					</thead>
				</table>
			</div>
		</section>
	</div>

	<script>
		const dados = {dados_json};

		$(document).ready(function() {{
			$('#tabelaRanck').DataTable({{
				data: dados,
				columns: [
				{definicao_colunas_js}
				],
				columnDefs: [
				{column_defs_js}
				],
				pageLength: 25,
				order: [],
				autoWidth: false,
				responsive: false,
				scrollX: true,
				language: {{
					decimal: ',',
					thousands: '.',
					search: 'Buscar:',
					lengthMenu: 'Mostrar _MENU_ linhas',
					info: 'Exibindo _START_ a _END_ de _TOTAL_ registros',
					infoEmpty: 'Exibindo 0 a 0 de 0 registros',
					zeroRecords: 'Nenhum registro encontrado',
					paginate: {{
						first: 'Primeira',
						last: 'Ultima',
						next: 'Proxima',
						previous: 'Anterior'
					}}
				}}
			}});
		}});
	</script>
</body>
</html>
""".strip()

	destino_html.parent.mkdir(parents=True, exist_ok=True)
	destino_html.write_text(html, encoding="utf-8")
	return destino_html


def main() -> int:
	parser = argparse.ArgumentParser(
		description="Gera dashboard interativo (HTML) a partir de ranking.xlsx com ordenacao por clique nas colunas."
	)
	parser.add_argument(
		"--origem",
		type=Path,
		default=Path(__file__).resolve().parent / "ranking.xlsx",
		help="Arquivo Excel de origem.",
	)
	parser.add_argument(
		"--saida",
		type=Path,
		default=Path(__file__).resolve().parent / "dashboard_ranking.html",
		help="Arquivo HTML de saida.",
	)
	parser.add_argument(
		"--titulo",
		type=str,
		default="Dashboard Ranking de Fornecedores",
		help="Titulo exibido no dashboard.",
	)
	args = parser.parse_args()

	df = carregar_dados(args.origem)
	df = aplicar_renomeacao_colunas(df)
	df = adicionar_percentual_compra_venda(df)
	df, colunas_decimais, colunas_inteiras, colunas_texto = preparar_dataframe(df)
	totais_exibicao = calcular_totais_exibicao(df, colunas_decimais, colunas_inteiras, colunas_texto)
	larguras_colunas = calcular_larguras_colunas(df, colunas_decimais, colunas_inteiras)
	destino = gerar_html(
		df,
		colunas_decimais,
		colunas_inteiras,
		larguras_colunas,
		totais_exibicao,
		args.saida,
		args.titulo,
	)

	print(f"Dashboard gerado com sucesso: {destino}")
	print("Ordenacao por clique habilitada em todas as colunas.")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
