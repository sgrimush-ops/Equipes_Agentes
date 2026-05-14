import os
from pathlib import Path

import pandas as pd


def _normalize_for_parquet(df: pd.DataFrame) -> pd.DataFrame:
    """Tenta converter colunas de texto numericas e padroniza o restante como string."""
    result = df.copy()

    for col in result.columns:
        if result[col].dtype != object:
            continue

        series = result[col].astype(str).str.strip()
        series = series.replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})

        numeric = pd.to_numeric(series.str.replace(",", ".", regex=False), errors="coerce")
        filled_ratio = numeric.notna().mean()

        if filled_ratio >= 0.95:
            result[col] = numeric
        else:
            result[col] = series.astype("string")

    return result

def generate_query_bz():
    base_dir = Path(__file__).resolve().parent
    source_file = base_dir / "query_bz.txt"
    output_file = base_dir / "query_bz.parquet"

    if not source_file.exists():
        raise FileNotFoundError(f"Arquivo base nao encontrado: {source_file}")

    content = source_file.read_text(encoding="utf-8", errors="ignore").strip()
    is_sql = content.lower().startswith(("select", "with"))

    if is_sql:
        db_url = os.getenv("DB_URL", "").strip()
        if not db_url:
            raise ValueError(
                "query_bz.txt contem SQL, mas a variavel de ambiente DB_URL nao foi informada."
            )

        from sqlalchemy import create_engine

        engine = create_engine(db_url)
        with engine.connect() as connection:
            df = pd.read_sql(content, connection, params={"NR1": 30})
    else:
        try:
            df = pd.read_csv(source_file, sep=";", encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(source_file, sep=";", encoding="latin-1")

    df = _normalize_for_parquet(df)
    df.to_parquet(output_file, index=False)

    print(f"Arquivo {output_file} gerado com sucesso.")

if __name__ == "__main__":
    generate_query_bz()