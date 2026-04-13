import os
import pandas as pd
from pathlib import Path

if __name__ == '__main__':
    os.chdir(Path(__file__).parent.resolve())

base_dir = Path(__file__).parent.resolve()

arquivo_txt     = base_dir.parent / 'abc_comprador.txt'
arquivo_parquet = base_dir / 'abc_comprador.parquet'

if not arquivo_txt.exists():
    print(f"Arquivo nao encontrado: {arquivo_txt}")
    raise SystemExit(1)

print(f"Lendo: {arquivo_txt}")

df = pd.read_csv(
    arquivo_txt,
    sep=';',
    encoding='cp1252',
    dtype=str,
    low_memory=False
)

print(f"   {len(df)} registros carregados - colunas: {list(df.columns)}")

# Colunas inteiras: sem casas decimais, tipo Int64
colunas_inteiras = [
    'CODIGO_PRODUTO', 'EMBALAGEM', 'QTD_VENDIDA',
    'ESTOQUE_MINIMO', 'ESTOQUE_MAXIMO', 'ESTOQUE_LOJA', 'ESTOQUE_DEPOSITO'
]

# Colunas decimais: manter virgula como separador decimal (padrao BR)
colunas_decimais = [
    'PERC_ACM', 'PRECO_CUSTO', 'PRECO_VENDA',
    'MARGEM_ATUAL', 'MARGEM_OBJETIVA'
]

for col in colunas_inteiras:
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col].str.strip().str.replace(',', '.', regex=False),
            errors='coerce'
        ).round(0).astype('Int64')

for col in colunas_decimais:
    if col in df.columns:
        df[col] = df[col].str.strip()

for col in df.select_dtypes(include=['object']).columns:
    df[col] = df[col].str.strip()

df.to_parquet(arquivo_parquet, index=False)
print(f"Parquet gerado: {arquivo_parquet}")

import subprocess
import sys
subprocess.run([sys.executable, str(base_dir / '2-abc_compr_verific.py')], check=True)
subprocess.run([sys.executable, str(base_dir / '3-dashboard_comprador.py')], check=True)