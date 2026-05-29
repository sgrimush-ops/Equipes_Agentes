import pandas as pd

parquet_path = r'c:/Users/usr/Downloads/Equipes_Agentes/Aplicativos/import_querys/query.parquet'

# Lê o parquet e garante que QTD_VENDIDA é numérico
parquet = pd.read_parquet(parquet_path)
parquet['QTD_VENDIDA'] = pd.to_numeric(parquet['QTD_VENDIDA'], errors='coerce').fillna(0)

# Filtra produto 2329 e soma todas as lojas
soma = parquet.loc[parquet['CODIGO_PRODUTO'] == 2329, 'QTD_VENDIDA'].sum()
print(f'Soma total de QTD_VENDIDA para o produto 2329: {soma}')
