from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd
import pdfplumber


RE_NRO_SERIE = re.compile(r"Nro\s*/\s*S[ée]rie\s*:?\s*(\d+)\s+(\d+)", re.IGNORECASE)
RE_ITEM = re.compile(
	r"^(\d+)\s+(.+?)\s+(\d+(?:[.,]\d+)?)\s+((?:\d{1,3}(?:\.\d{3})*|\d+),\d{2})\s+"
)


def extrair_linhas_pdf(pdf_path: Path) -> list[dict[str, str]]:
	"""Extrai itens de um PDF no formato de conferência de notas."""
	linhas_extraidas: list[dict[str, str]] = []
	nro_serie_atual = ""

	with pdfplumber.open(pdf_path) as pdf:
		for page in pdf.pages:
			texto = page.extract_text() or ""
			for linha in texto.splitlines():
				linha = linha.strip()
				if not linha:
					continue

				m_nro_serie = RE_NRO_SERIE.search(linha)
				if m_nro_serie:
					nro_serie_atual = f"{m_nro_serie.group(1)} {m_nro_serie.group(2)}"
					continue

				# Ignora cabeçalhos e linhas de separação.
				if (
					linha.startswith("Código Ref Descrição")
					or linha.startswith("Valor Nota:")
					or linha.startswith("Vctos:")
					or set(linha) == {"-"}
				):
					continue

				m_item = RE_ITEM.match(linha)
				if not m_item or not nro_serie_atual:
					continue

				linhas_extraidas.append(
					{
						"Nro / Série": nro_serie_atual,
						"Código": m_item.group(1),
						"Descrição": m_item.group(2).strip(),
						"Qtd": m_item.group(3),
						"Custo Nt": m_item.group(4),
					}
				)

	return linhas_extraidas


def converter_pdfs_para_excel(input_dir: Path, output_file: Path) -> None:
	"""Lê todos os PDFs da pasta e consolida os itens em um único Excel."""
	pdfs = sorted(input_dir.glob("*.pdf"))
	if not pdfs:
		raise FileNotFoundError(f"Nenhum PDF encontrado em: {input_dir}")

	registros: list[dict[str, str]] = []
	for pdf in pdfs:
		print(f"Processando: {pdf.name}")
		registros.extend(extrair_linhas_pdf(pdf))

	df = pd.DataFrame(registros, columns=["Nro / Série", "Código", "Descrição", "Qtd", "Custo Nt"])
	df.to_excel(output_file, index=False)
	print(f"Planilha gerada: {output_file}")
	print(f"Total de linhas extraídas: {len(df)}")


def main() -> None:
	parser = argparse.ArgumentParser(
		description="Extrai itens de PDFs e salva no Excel com as colunas selecionadas."
	)
	parser.add_argument(
		"--input-dir",
		type=Path,
		default=Path(__file__).parent,
		help="Pasta contendo os PDFs (padrão: pasta do script)",
	)
	parser.add_argument(
		"--output",
		type=Path,
		default=Path(__file__).parent / "itens_extraidos.xlsx",
		help="Arquivo Excel de saída",
	)
	args = parser.parse_args()

	converter_pdfs_para_excel(args.input_dir, args.output)


if __name__ == "__main__":
	main()
