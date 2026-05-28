from pathlib import Path
import os
import sys
from datetime import date

import pandas as pd


def obter_ultimo_parquet(pasta_historico: Path) -> Path:
	arquivos = list(pasta_historico.glob("ruptura_snapshot_*.parquet"))
	if not arquivos:
		arquivos = list(pasta_historico.glob("*.parquet"))

	if not arquivos:
		raise FileNotFoundError(
			f"Nenhum arquivo parquet encontrado em: {pasta_historico}"
		)

	return max(arquivos, key=lambda p: p.stat().st_mtime)


def obter_faltantes(df: pd.DataFrame, colunas_obrigatorias: list[str]) -> list[str]:
	return [col for col in colunas_obrigatorias if col not in df.columns]


def montar_saida_vazia() -> pd.DataFrame:
	return pd.DataFrame(
		columns=["CODIGO_PRODUTO", "DESCRICAO_PRODUTO", "EMPRESA", "STATUS"]
	)


def carregar_codigos_cadastro_novo(base_dir: Path) -> set[int]:
	arquivo_cadastro_novo = base_dir.parent / "cadastros_novos" / "cadastro_novo.csv"
	if not arquivo_cadastro_novo.exists():
		return set()

	df_cadastro = pd.read_csv(
		arquivo_cadastro_novo,
		sep=";",
		encoding="utf-8-sig",
	)

	if "CODIGO_PRODUTO" not in df_cadastro.columns:
		return set()

	serie_codigos = pd.to_numeric(df_cadastro["CODIGO_PRODUTO"], errors="coerce")
	serie_codigos = serie_codigos.dropna().astype("Int64")
	return set(serie_codigos.tolist())


def tentar_gerar_snapshot_detalhado(
	base_dir: Path,
	pasta_historico: Path,
	colunas_obrigatorias: list[str],
) -> Path | None:
	arquivo_origem = base_dir.parent / "import_querys" / "query.parquet"
	if not arquivo_origem.exists():
		return None

	df_origem = pd.read_parquet(arquivo_origem)
	faltantes_origem = obter_faltantes(df_origem, colunas_obrigatorias)
	if faltantes_origem:
		return None

	pasta_historico.mkdir(parents=True, exist_ok=True)
	arquivo_detalhado = (
		pasta_historico / f"ruptura_snapshot_{date.today().strftime('%Y-%m-%d')}_detalhe.parquet"
	)
	df_origem.to_parquet(arquivo_detalhado, index=False)
	return arquivo_detalhado


def main() -> None:
	base_dir = Path(__file__).resolve().parent
	pasta_historico = base_dir / "historico_ruptura"
	arquivo_saida = base_dir / "mix.xlsx"

	ultimo_parquet = obter_ultimo_parquet(pasta_historico)
	df = pd.read_parquet(ultimo_parquet)

	colunas_obrigatorias = [
		"CODIGO_PRODUTO",
		"DESCRICAO_PRODUTO",
		"QUANTIDADE_DISPONIVEL",
		"QTD_PEND_PEDCOMPRA",
		"QTD_VENDIDA",
	]
	faltantes = obter_faltantes(df, colunas_obrigatorias)
	if faltantes:
		arquivo_detalhado = tentar_gerar_snapshot_detalhado(
			base_dir=base_dir,
			pasta_historico=pasta_historico,
			colunas_obrigatorias=colunas_obrigatorias,
		)
		if arquivo_detalhado is not None:
			ultimo_parquet = arquivo_detalhado
			df = pd.read_parquet(ultimo_parquet)
			faltantes = obter_faltantes(df, colunas_obrigatorias)

	if faltantes:
		df_saida = montar_saida_vazia()
		motivo = (
			"Snapshot atual nao contem detalhes por produto "
			f"(faltando: {', '.join(faltantes)})."
		)
	elif df is not None and not df.empty:
		for col in ["QUANTIDADE_DISPONIVEL", "QTD_PEND_PEDCOMPRA", "QTD_VENDIDA"]:
			df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

		# Consolida por produto para avaliar o cenário global no snapshot mais recente.
		df_produto = (
			df.groupby(["CODIGO_PRODUTO", "DESCRICAO_PRODUTO"], as_index=False)
			.agg(
				ESTOQUE_TOTAL=("QUANTIDADE_DISPONIVEL", "sum"),
				PEDIDOS_PENDENTES=("QTD_PEND_PEDCOMPRA", "sum"),
				QTD_VENDIDA=("QTD_VENDIDA", "sum"),
			)
		)

		filtro = (
			(df_produto["ESTOQUE_TOTAL"] <= 0)
			& (df_produto["PEDIDOS_PENDENTES"] <= 0)
			& (df_produto["QTD_VENDIDA"] < 2)
		)

		df_saida = df_produto.loc[
			filtro, ["CODIGO_PRODUTO", "DESCRICAO_PRODUTO"]
		].copy()
		df_saida["CODIGO_PRODUTO"] = pd.to_numeric(
			df_saida["CODIGO_PRODUTO"], errors="coerce"
		).astype("Int64")

		codigos_cadastro_novo = carregar_codigos_cadastro_novo(base_dir)
		if codigos_cadastro_novo:
			df_saida = df_saida.loc[
				~df_saida["CODIGO_PRODUTO"].isin(codigos_cadastro_novo)
			].copy()

		# Adiciona coluna de venda do produto do query.parquet
		arquivo_query = base_dir.parent / "import_querys" / "query.parquet"
		if arquivo_query.exists():
			df_query = pd.read_parquet(arquivo_query)
			# Remove duplicidades exatas para garantir soma correta
			df_query = df_query.drop_duplicates()
			# Garante que os códigos e vendas são numéricos para merge e soma corretos
			df_query["CODIGO_PRODUTO"] = pd.to_numeric(df_query["CODIGO_PRODUTO"], errors="coerce").astype("Int64")
			if "QTD_VENDIDA" in df_query.columns:
				df_query["QTD_VENDIDA"] = pd.to_numeric(df_query["QTD_VENDIDA"], errors="coerce").fillna(0)
			col_venda = "QTD_VENDIDA" if "QTD_VENDIDA" in df_query.columns else None
			if col_venda:
				# Soma QTD_VENDIDA para cada produto
				df_venda = (
					df_query.groupby("CODIGO_PRODUTO", as_index=False)[col_venda].sum()
					.rename(columns={col_venda: "VENDA_QUERY"})
				)
				# Garante que df_saida não tem duplicidade antes do merge
				df_saida = df_saida.drop_duplicates(subset=["CODIGO_PRODUTO", "DESCRICAO_PRODUTO"])
				df_saida = df_saida.merge(
					df_venda,
					on="CODIGO_PRODUTO", how="left"
				)
		df_saida["EMPRESA"] = "CD"
		df_saida["STATUS"] = "TI"
		# Adiciona coluna LOJAS_ATIVAS após VENDA_QUERY, se possível
		# Sempre usa CODIGO_EMPRESA como coluna de loja para LOJAS_ATIVAS
		if "VENDA_QUERY" in df_saida.columns:
			if arquivo_query.exists() and "CODIGO_EMPRESA" in df_query.columns:
				lojas_ativas = (
					df_query.groupby("CODIGO_PRODUTO")["CODIGO_EMPRESA"]
					.apply(lambda x: ','.join(sorted(map(str, set(x.dropna())))))
					.reset_index()
					.rename(columns={"CODIGO_EMPRESA": "LOJAS_ATIVAS"})
				)
				df_saida = df_saida.merge(lojas_ativas, on="CODIGO_PRODUTO", how="left")
			if "LOJAS_ATIVAS" not in df_saida.columns:
				df_saida["LOJAS_ATIVAS"] = ""
			cols = [col for col in df_saida.columns if col not in ["VENDA_QUERY", "LOJAS_ATIVAS"]] + ["VENDA_QUERY", "LOJAS_ATIVAS"]
			df_saida = df_saida[cols]
		motivo = "Filtros aplicados com sucesso."
	else:
		# Caso extremo: df está vazio ou None, saída vazia
		df_saida = montar_saida_vazia()
		motivo = "Snapshot vazio ou não carregado."

	df_saida.to_excel(arquivo_saida, index=False)

	os.system("cls" if os.name == "nt" else "clear")
	print(
		f"[OK] mix.xlsx criado com {len(df_saida)} registros a partir de {ultimo_parquet.name}."
	)
	print(f"[INFO] {motivo}")


if __name__ == "__main__":
	try:
		main()
	except Exception as erro:
		print(f"[ERRO] Falha ao gerar mix.xlsx: {erro}")
		sys.exit(1)
