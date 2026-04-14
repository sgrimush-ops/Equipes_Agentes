import os
import pandas as pd
from pathlib import Path
if __name__ == '__main__':
    Path(__file__).parent.resolve()
base_dir = Path(__file__).parent.resolve()
arquivo_parquet = base_dir / 'abc_comprador.parquet'
if not arquivo_parquet.exists():
    print(f"Arquivo nao encontrado: {arquivo_parquet}")
    raise SystemExit(1)
print(f"Lendo: {arquivo_parquet}")
df = pd.read_parquet(arquivo_parquet)

#converter para csv
arquivo_csv = base_dir / 'abc_comprador.csv'
df.to_csv(arquivo_csv, index=False, sep=';', encoding='cp1252')
print(f"CSV gerado: {arquivo_csv}")

os.system('cls')
print("Conversao concluida.")