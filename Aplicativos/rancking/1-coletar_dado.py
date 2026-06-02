from pathlib import Path

import pandas as pd


def br_to_float(value):
	"""Converte valores no formato brasileiro para float."""
	if pd.isna(value):
		return 0.0

	text = str(value).strip()
	if text == "":
		return 0.0

	text = text.replace("R$", "").replace(" ", "")
	text = text.replace(".", "").replace(",", ".")

	try:
		return float(text)
	except ValueError:
		return 0.0


def main():
	base_dir = Path(__file__).resolve().parent
	input_path = base_dir.parent / "import_querys" / "ranck.txt"
	output_path = base_dir / "ranck.xlsx"

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

	monetary_columns = [col for col in df.columns if col.startswith("VLR_")]
	for col in monetary_columns:
		df[col] = df[col].apply(br_to_float)

	numeric_columns = ["QTD_SKU", "QTD_INCINERACAO_ANO_ATUAL"]
	for col in numeric_columns:
		if col in df.columns:
			df[col] = (
				df[col]
				.astype(str)
				.str.replace(".", "", regex=False)
				.str.replace(",", ".", regex=False)
			)
			df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

	try:
		df.to_excel(output_path, index=False)
	except ImportError as exc:
		raise ImportError(
			"Dependencia para gerar Excel ausente. Instale: pip install openpyxl"
		) from exc

	print(f"Excel gerado com sucesso: {output_path}")


if __name__ == "__main__":
	main()
