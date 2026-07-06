from pathlib import Path
import re

import pandas as pd


def normalizar_ean(valor: object) -> str:
	if pd.isna(valor):
		return ""
	texto = str(valor).strip()
	return re.sub(r"\D", "", texto)


def main() -> None:
	base_dir = Path(__file__).resolve().parent
	arquivo_elo = base_dir / "elo.xlsx"
	arquivo_base = base_dir / "ean_dun_marg_venda.xlsx"
	arquivo_saida = base_dir / "lista_elo.xlsx"

	df_elo = pd.read_excel(arquivo_elo, dtype=str)
	df_base = pd.read_excel(arquivo_base, dtype=str)

	if "Eans" not in df_elo.columns:
		raise ValueError("A planilha elo.xlsx nao possui a coluna 'Eans'.")

	colunas_necessarias = {"EAN_DUN", "SEQPRODUTO", "DESCRICAO_PRODUTO"}
	faltantes = colunas_necessarias - set(df_base.columns)
	if faltantes:
		raise ValueError(
			"A planilha ean_dun_marg_venda.xlsx nao possui as colunas esperadas: "
			+ ", ".join(sorted(faltantes))
		)

	# A coluna Eans pode vir com varios EANs separados por virgula em cada linha.
	eans_elo = (
		df_elo["Eans"]
		.fillna("")
		.str.split(",")
		.explode()
		.astype(str)
		.map(normalizar_ean)
	)
	eans_elo = set(ean for ean in eans_elo if ean)

	df_base["EAN_VINCULO"] = df_base["EAN_DUN"].map(normalizar_ean)
	df_filtrado = df_base[df_base["EAN_VINCULO"].isin(eans_elo)].copy()

	df_saida = (
		df_filtrado[["SEQPRODUTO", "DESCRICAO_PRODUTO", "EAN_VINCULO"]]
		.rename(
			columns={
				"SEQPRODUTO": "CODIGO_PRODUTO",
				"DESCRICAO_PRODUTO": "DESCRICAO_PRODUTO",
				"EAN_VINCULO": "EAN",
			}
		)
		.drop_duplicates()
		.sort_values(["DESCRICAO_PRODUTO", "CODIGO_PRODUTO", "EAN"])
	)

	df_saida.to_excel(arquivo_saida, index=False)

	print(f"Arquivo criado: {arquivo_saida}")
	print(f"EANs na elo.xlsx: {len(eans_elo)}")
	print(f"Produtos encontrados: {len(df_saida)}")


if __name__ == "__main__":
	main()
