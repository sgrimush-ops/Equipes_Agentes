from __future__ import annotations

from pathlib import Path

import pandas as pd


def normalizar_preco_virgula(serie: pd.Series) -> pd.Series:
	"""Converte strings com virgula decimal para numero float."""
	return pd.to_numeric(
		serie.astype(str).str.strip().str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
		errors="coerce",
	)


def identificar_coluna_ean(colunas: list[str]) -> str | None:
	"""Identifica a coluna de EAN pelo nome mais comum encontrado no arquivo."""
	candidatas = [
		"EAN",
		"CODIGO_EAN",
		"COD_EAN",
		"EAN_PRODUTO",
		"CODIGO_BARRAS",
		"COD_BARRAS",
		"CODBARRA",
	]
	colunas_upper = {col.upper(): col for col in colunas}
	for nome in candidatas:
		if nome in colunas_upper:
			return colunas_upper[nome]
	return None


def gerar_preco_dia_tratado(
	arquivo_entrada: Path,
	arquivo_saida: Path,
	lojas_permitidas: tuple[str, str] = ("3", "11"),
) -> dict[str, int | str]:
	"""Gera arquivo Excel tratado com preco praticado separado por loja."""
	df = pd.read_csv(arquivo_entrada, sep=";", dtype=str, encoding="utf-8")
	df.columns = [col.strip() for col in df.columns]
	coluna_ean = identificar_coluna_ean(df.columns.tolist())

	colunas_obrigatorias = {
		"CODIGO_PRODUTO",
		"DESCRICAO_PRODUTO",
		"CODIGO_EMPRESA",
		"PRECO_PRATICADO_DIA",
	}
	faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
	if faltantes:
		raise ValueError(f"Colunas obrigatorias ausentes no arquivo: {', '.join(faltantes)}")

	colunas_normalizar = ["CODIGO_PRODUTO", "DESCRICAO_PRODUTO", "CODIGO_EMPRESA", "PRECO_PRATICADO_DIA"]
	if coluna_ean:
		colunas_normalizar.append(coluna_ean)

	for col in colunas_normalizar:
		df[col] = df[col].astype(str).str.strip()

	linhas_entrada = len(df)
	df = df[df["CODIGO_EMPRESA"].isin(lojas_permitidas)].copy()
	linhas_filtradas = len(df)

	df["PRECO_PRATICADO_DIA"] = normalizar_preco_virgula(df["PRECO_PRATICADO_DIA"])
	colunas_indice = ["CODIGO_PRODUTO", "DESCRICAO_PRODUTO"]
	if coluna_ean:
		colunas_indice.insert(1, coluna_ean)

	# Pivot para remover duplicidade de linha por loja e manter uma linha por produto.
	saida_df = (
		df.pivot_table(
			index=colunas_indice,
			columns="CODIGO_EMPRESA",
			values="PRECO_PRATICADO_DIA",
			aggfunc="first",
		)
		.rename(
			columns={
				"3": "PRECO_PRATICADO_DIA_LOJA_3",
				"11": "PRECO_PRATICADO_DIA_LOJA_11",
			}
		)
		.reset_index()
	)

	for col in ["PRECO_PRATICADO_DIA_LOJA_3", "PRECO_PRATICADO_DIA_LOJA_11"]:
		if col not in saida_df.columns:
			saida_df[col] = pd.NA

	colunas_saida = ["CODIGO_PRODUTO"]
	if coluna_ean:
		colunas_saida.append(coluna_ean)
	colunas_saida.extend([
		"DESCRICAO_PRODUTO",
		"PRECO_PRATICADO_DIA_LOJA_3",
		"PRECO_PRATICADO_DIA_LOJA_11",
	])
	saida_df = saida_df[colunas_saida]

	saida_df["_ord"] = pd.to_numeric(saida_df["CODIGO_PRODUTO"], errors="coerce")
	saida_df = saida_df.sort_values(["_ord", "CODIGO_PRODUTO"]).drop(columns=["_ord"])

	with pd.ExcelWriter(arquivo_saida, engine="openpyxl") as writer:
		saida_df.to_excel(writer, index=False, sheet_name="preco_dia")
		ws = writer.sheets["preco_dia"]

		headers = {cell.value: idx for idx, cell in enumerate(ws[1], start=1)}
		for col in ["PRECO_PRATICADO_DIA_LOJA_3", "PRECO_PRATICADO_DIA_LOJA_11"]:
			col_idx = headers.get(col)
			if not col_idx:
				continue
			for row in range(2, ws.max_row + 1):
				cell = ws.cell(row=row, column=col_idx)
				if cell.value is not None:
					cell.number_format = "R$ #,##0.00"

	return {
		"arquivo_entrada": str(arquivo_entrada),
		"arquivo_saida": str(arquivo_saida),
		"coluna_ean": coluna_ean or "nao_encontrada",
		"linhas_entrada": linhas_entrada,
		"linhas_filtradas_lojas_3_11": linhas_filtradas,
		"linhas_saida_unicas": len(saida_df),
	}


def main() -> None:
	pasta_script = Path(__file__).resolve().parent
	arquivo_entrada = pasta_script / "preco_dia.txt"
	arquivo_saida = pasta_script / "preco_dia_tratado.xlsx"

	if not arquivo_entrada.exists():
		raise FileNotFoundError(f"Arquivo de entrada nao encontrado: {arquivo_entrada}")

	resumo = gerar_preco_dia_tratado(arquivo_entrada=arquivo_entrada, arquivo_saida=arquivo_saida)

	print("Tratamento concluido com sucesso.")
	print(f"Entrada: {resumo['arquivo_entrada']}")
	print(f"Saida: {resumo['arquivo_saida']}")
	print(f"Coluna EAN usada: {resumo['coluna_ean']}")
	print(f"Linhas de entrada: {resumo['linhas_entrada']}")
	print(f"Linhas lojas 3 e 11: {resumo['linhas_filtradas_lojas_3_11']}")
	print(f"Linhas finais unicas: {resumo['linhas_saida_unicas']}")


if __name__ == "__main__":
	main()
