import pandas as pd

try:
    df = pd.read_parquet('consumo.parquet')
    print("Columns in parquet file:")
    for col in df.columns:
        print(f"- {col}")
except Exception as e:
    print(e)
