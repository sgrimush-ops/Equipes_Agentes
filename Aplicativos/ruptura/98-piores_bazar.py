from pathlib import Path
import os
import sys
import unicodedata
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
	arquivo_origem = base_dir.parent / "import_querys" / "query_bz.parquet"
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


def normalizar_texto(valor: object) -> str:
	texto = str(valor or "").strip().upper()
	return "".join(
		ch for ch in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(ch)
	)


def filtrar_departamento_nao_alimentos(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
	colunas_departamento = [
		"DEPARTAMENTO",
		"DESC_DEPARTAMENTO",
		"DESCRICAO_DEPARTAMENTO",
		"DEPARTAMENTO_DESCRICAO",
		"DIVISAO",
		"DESC_DIVISAO",
		"DESCRICAO_DIVISAO",
	]

	for coluna in colunas_departamento:
		if coluna not in df.columns:
			continue

		serie_normalizada = df[coluna].map(normalizar_texto)
		mask_nao_alimentos = serie_normalizada.str.contains(
			r"\bNAO\s+ALIMENTOS?\b", na=False
		)
		return df.loc[mask_nao_alimentos].copy(), (
			f"Filtro de departamento aplicado: NAO ALIMENTOS (coluna {coluna})."
		)

	return df.copy(), (
		"Nao foi encontrada coluna de departamento para aplicar filtro de NAO ALIMENTOS."
	)


def main() -> None:
	base_dir = Path(__file__).resolve().parent
	pasta_historico = base_dir / "historico_ruptura"
	arquivo_saida = base_dir / "bz_mix.xlsx"
	arquivo_origem = base_dir.parent / "import_querys" / "query_bz.parquet"

	if arquivo_origem.exists():
		df = pd.read_parquet(arquivo_origem)
		origem_dados = arquivo_origem.name
	else:
		ultimo_parquet = obter_ultimo_parquet(pasta_historico)
		df = pd.read_parquet(ultimo_parquet)
		origem_dados = ultimo_parquet.name

	if "QTD_VENDIDA" not in df.columns and "QTD_VENDIDA_PERIODO" in df.columns:
		df["QTD_VENDIDA"] = df["QTD_VENDIDA_PERIODO"]

	colunas_obrigatorias = [
		"CODIGO_PRODUTO",
		"DESCRICAO_PRODUTO",
		"QUANTIDADE_DISPONIVEL",
		"QTD_PEND_PEDCOMPRA",
		"QTD_VENDIDA",
	]
	faltantes = obter_faltantes(df, colunas_obrigatorias)
	if faltantes:
		# No levantamento do bazar priorizamos o query_bz.parquet bruto.
		# Se faltarem colunas nele, encerramos com saida vazia para evitar
		# misturar com snapshots potencialmente filtrados por outro fluxo.
		pass

	if faltantes:
		df_saida = montar_saida_vazia()
		motivo = (
			"Base atual nao contem detalhes por produto "
			f"(faltando: {', '.join(faltantes)})."
		)
	else:
		df, motivo_departamento = filtrar_departamento_nao_alimentos(df)

		for col in ["QUANTIDADE_DISPONIVEL", "QTD_PEND_PEDCOMPRA", "QTD_VENDIDA"]:
			df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

		# Mantem venda e pedidos pendentes, e bloqueia itens com estoque no CD (empresa 15).
		df_produto = (
			df.groupby(["CODIGO_PRODUTO", "DESCRICAO_PRODUTO"], as_index=False)
			.agg(
				PEDIDOS_PENDENTES=("QTD_PEND_PEDCOMPRA", "sum"),
				QTD_VENDIDA=("QTD_VENDIDA", "sum"),
			)
		)

		estoque_cd = pd.Series(0, index=df_produto.index, dtype="float64")
		if "CODIGO_EMPRESA" in df.columns:
			df_cd = df.loc[df["CODIGO_EMPRESA"] == 15].copy()
			if not df_cd.empty:
				df_estoque_cd = (
					df_cd.groupby("CODIGO_PRODUTO", as_index=False)
					.agg(ESTOQUE_CD=("QUANTIDADE_DISPONIVEL", "sum"))
				)
				df_produto = df_produto.merge(df_estoque_cd, on="CODIGO_PRODUTO", how="left")
				estoque_cd = pd.to_numeric(df_produto["ESTOQUE_CD"], errors="coerce").fillna(0)

		filtro = (
			(df_produto["PEDIDOS_PENDENTES"] <= 0)
			& (df_produto["QTD_VENDIDA"] < 2)
			& (estoque_cd <= 0)
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

		df_saida["EMPRESA"] = "CD"
		df_saida["STATUS"] = "TI"
		motivo = f"{motivo_departamento} Filtros aplicados com sucesso."

	df_saida.to_excel(arquivo_saida, index=False)

	os.system("cls" if os.name == "nt" else "clear")
	print(
		f"[OK] bz_mix.xlsx criado com {len(df_saida)} registros a partir de {origem_dados}."
	)
	print(f"[INFO] {motivo}")


if __name__ == "__main__":
	try:
		main()
	except Exception as erro:
		print(f"[ERRO] Falha ao gerar bz_mix.xlsx: {erro}")
		sys.exit(1)
