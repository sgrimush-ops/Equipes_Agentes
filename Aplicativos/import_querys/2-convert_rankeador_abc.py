# convert_rankeador_abc.py
# Converte rankeador_abc_produtos.txt -> rankeador_abc_produtos.parquet
# e move o resultado para a pasta Aplicativos/min_e_max
import os
import shutil
from pathlib import Path
import pandas as pd


def carregar_txt(caminho_txt: Path) -> pd.DataFrame:
    """Lê o arquivo TXT tentando codificações padrão do ambiente Consinco/Windows."""
    for enc in ("utf-8-sig", "cp1252", "latin1"):
        try:
            df = pd.read_csv(
                caminho_txt,
                sep=";",
                encoding=enc,
                dtype=str,
                low_memory=False,
            )
            print(f"[INFO] Arquivo lido com sucesso (encoding={enc}): {caminho_txt}")
            return df
        except UnicodeDecodeError:
            continue
    raise ValueError(f"[ERRO] Não foi possível decodificar o arquivo: {caminho_txt}")


def tratar_dados(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitiza textos e converte colunas numéricas para tipos compatíveis com Parquet."""
    df = df.copy()
    df.columns = [str(c).strip().upper() for c in df.columns]

    # Limpeza de colunas de texto
    cols_texto = [
        "COMPRADOR",
        "DEPARTAMENTO",
        "SUBGRUPO",
        "DESCRICAO",
        "STATUS_COMPRA",
        "RANK",
    ]
    for col in cols_texto:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    # Conversão do código do produto (inteiro sem decimal)
    if "SEQCODIGO" in df.columns:
        df["SEQCODIGO"] = (
            pd.to_numeric(df["SEQCODIGO"].astype(str).str.strip(), errors="coerce")
            .fillna(0)
            .astype("int64")
        )

    # Conversão das colunas numéricas decimais (padrão Pt-BR com vírgula)
    cols_decimais = ["VALOR_VENDIDO", "PERC_PARTICIPACAO", "PERC_ACUMULADO"]
    for col in cols_decimais:
        if col in df.columns:
            s_clean = (
                df[col]
                .astype(str)
                .str.strip()
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
            )
            df[col] = pd.to_numeric(s_clean, errors="coerce").fillna(0.0).astype("float64")

    # Garante tipagem string compatível com Parquet nas colunas de texto restantes
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].astype("string")

    return df


def converter_e_mover_rankeador_abc() -> Path:
    base_dir = Path(__file__).parent.resolve()
    arquivo_txt = base_dir / "rankeador_abc_produtos.txt"
    arquivo_parquet_temp = base_dir / "rankeador_abc_produtos.parquet"

    pasta_destino = base_dir.parent / "min_e_max"
    pasta_destino.mkdir(parents=True, exist_ok=True)
    arquivo_parquet_destino = pasta_destino / "rankeador_abc_produtos.parquet"

    if not arquivo_txt.exists():
        print(f"[ERRO] Arquivo de origem não encontrado: {arquivo_txt}")
        raise SystemExit(1)

    # 1. Carregar e tratar dados do TXT
    df_bruto = carregar_txt(arquivo_txt)
    print(f"   {len(df_bruto)} registros carregados — colunas: {list(df_bruto.columns)}")

    df_limpo = tratar_dados(df_bruto)

    # 2. Gerar arquivo Parquet na pasta local e mover para min_e_max
    df_limpo.to_parquet(arquivo_parquet_temp, index=False)
    print(f"[INFO] Parquet gerado: {arquivo_parquet_temp}")

    if arquivo_parquet_destino.exists():
        arquivo_parquet_destino.unlink()
    shutil.move(str(arquivo_parquet_temp), str(arquivo_parquet_destino))
    print(f"[SUCESSO] Arquivo movido para: {arquivo_parquet_destino}")

    # 3. Validação de integridade no destino final
    df_check = pd.read_parquet(arquivo_parquet_destino)
    if df_check.shape == df_limpo.shape:
        print(
            f"[OK] Validação concluída: {df_check.shape[0]} linhas × {df_check.shape[1]} colunas intactas em '{arquivo_parquet_destino.name}'."
        )
    else:
        print(
            f"[ALERTA] Divergência detectada: origem {df_limpo.shape} vs destino {df_check.shape}"
        )

    return arquivo_parquet_destino


if __name__ == "__main__":
    os.chdir(Path(__file__).parent.resolve())
    converter_e_mover_rankeador_abc()
