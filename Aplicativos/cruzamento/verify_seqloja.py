
import pandas as pd
import os

parquet_path = os.path.join('bd', 'gerencial_atualizado.parquet')

if not os.path.exists(parquet_path):
    print("Arquivo parquet não encontrado.")
    exit()

df = pd.read_parquet(parquet_path)

# Check for seqloja format issues (should not contain '.0-')
invalid_seqloja = df[df['seqloja'].astype(str).str.contains(r'\.0-')]

if not invalid_seqloja.empty:
    print(f"FAILED: Encontrados {len(invalid_seqloja)} registros com formato inválido em seqloja.")
    print(invalid_seqloja[['seqloja']].head())
else:
    print("SUCCESS: Nenhum formato inválido '.0-' encontrado em seqloja.")

# Check specific example if possible
examples = df['seqloja'].head(5).tolist()
print(f"Exemplos de seqloja: {examples}")
