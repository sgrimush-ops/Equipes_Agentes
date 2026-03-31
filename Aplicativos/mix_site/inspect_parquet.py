import pandas as pd
import os

parquet_file = r'resultado/con5cod.parquet'

if os.path.exists(parquet_file):
    try:
        df = pd.read_parquet(parquet_file)
        print(f"Total de colunas: {len(df.columns)}")
        print("Nomes das colunas:")
        for col in df.columns:
            print(f"- {col}")
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
else:
    print("Arquivo não encontrado.")
