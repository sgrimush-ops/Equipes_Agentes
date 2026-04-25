from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def ler_txt_resiliente(caminho_txt: Path, separador: str = ";") -> tuple[pd.DataFrame, str]:
	"""Le um TXT tentando encodings comuns de exportacao Windows."""
	tentativas = ["utf-8", "cp1252", "latin1"]

	ultimo_erro: Exception | None = None
	for encoding in tentativas:
		try:
			df = pd.read_csv(caminho_txt, sep=separador, encoding=encoding)
			return df, encoding
		except UnicodeDecodeError as exc:
			ultimo_erro = exc

	raise RuntimeError(
		"Nao foi possivel ler o arquivo com os encodings testados: "
		f"{', '.join(tentativas)}"
	) from ultimo_erro


def converter_txt_para_excel(
	origem_txt: Path,
	destino_xlsx: Path | None = None,
	separador: str = ";",
) -> Path:
	if not origem_txt.exists():
		raise FileNotFoundError(f"Arquivo de origem nao encontrado: {origem_txt}")

	if destino_xlsx is None:
		destino_xlsx = origem_txt.with_suffix(".xlsx")

	destino_xlsx.parent.mkdir(parents=True, exist_ok=True)

	df, encoding_usado = ler_txt_resiliente(origem_txt, separador=separador)
	df.to_excel(destino_xlsx, index=False)

	print("Conversao concluida.")
	print(f"Origem: {origem_txt}")
	print(f"Destino: {destino_xlsx}")
	print(f"Encoding usado: {encoding_usado}")
	print(f"Linhas: {len(df)} | Colunas: {len(df.columns)}")

	return destino_xlsx


def main() -> int:
	parser = argparse.ArgumentParser(description="Converte TXT delimitado para XLSX.")
	parser.add_argument(
		"--origem",
		type=Path,
		default=Path(__file__).resolve().parents[1] / "import_querys" / "sem_venda.txt",
		help="Caminho do arquivo TXT de origem.",
	)
	parser.add_argument(
		"--destino",
		type=Path,
		default=Path(__file__).resolve().parent / "sem_venda.xlsx",
		help="Caminho do arquivo XLSX de destino.",
	)
	parser.add_argument(
		"--sep",
		default=";",
		help="Separador de colunas do TXT (padrao: ;).",
	)

	args = parser.parse_args()

	converter_txt_para_excel(
		origem_txt=args.origem,
		destino_xlsx=args.destino,
		separador=args.sep,
	)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
