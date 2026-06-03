from pathlib import Path
import re

import pandas as pd


def br_to_float(value):
	"""Converte valores no formato brasileiro para float."""
	if pd.isna(value):
		return 0.0

	text = str(value).strip()
	if text == "":
		return 0.0

	# Remove moeda, espacos comuns/NBSP e qualquer caractere nao numerico relevante.
	text = re.sub(r"[^\d,\.\-]", "", text)

	if text in {"", "-", ".", ","}:
		return 0.0

	# Padrao brasileiro: ponto como milhar e virgula como decimal.
	if "," in text:
		text = text.replace(".", "").replace(",", ".")

	try:
		return float(text)
	except ValueError:
		return 0.0


def main():
	base_dir = Path(__file__).resolve().parent
	input_path = base_dir.parent / "import_querys" / "ranking.txt"
	output_path = base_dir / "ranking.xlsx"

	if not input_path.exists():
		raise FileNotFoundError(f"Arquivo nao encontrado: {input_path}")

	df = None
	for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin1"):
		try:
			df = pd.read_csv(input_path, sep=";", encoding=encoding)
			break
		except UnicodeDecodeError:
			continue

	if df is None:
		raise UnicodeDecodeError(
			"codec",
			b"",
			0,
			1,
			f"Nao foi possivel ler o arquivo com os encodings suportados: {input_path}",
		)

	# Evita problemas de mapeamento por espacos ocultos no cabecalho.
	df.columns = [str(col).strip() for col in df.columns]

	monetary_columns = [col for col in df.columns if col.startswith("VLR_")]
	for col in monetary_columns:
		df[col] = df[col].apply(br_to_float)

	if "QTD_SKU" in df.columns:
		df["QTD_SKU"] = pd.to_numeric(df["QTD_SKU"], errors="coerce").fillna(0).round(0).astype("Int64")

	# Essa coluna chega no TXT como "R$ x.xxx,xx"; precisa passar pelo parser BR.
	if "QTD_INCINERACAO_ANO_ATUAL" in df.columns:
		df["QTD_INCINERACAO_ANO_ATUAL"] = (
			df["QTD_INCINERACAO_ANO_ATUAL"].apply(br_to_float).round(0).astype("Int64")
		)

	try:
		df.to_excel(output_path, index=False)
	except ImportError as exc:
		raise ImportError(
			"Dependencia para gerar Excel ausente. Instale: pip install openpyxl"
		) from exc

	print(f"Excel gerado com sucesso: {output_path}")


if __name__ == "__main__":
	main()

