import pandas as pd

# Caminhos dos arquivos
parquet_path = r'c:/Users/usr/Downloads/Equipes_Agentes/Aplicativos/import_querys/query.parquet'
excel_path = r'c:/Users/usr/Downloads/Equipes_Agentes/Aplicativos/ruptura/mix.xlsx'

# 1. Soma QTD_VENDIDA por produto no parquet

df_parquet = pd.read_parquet(parquet_path)
# Garante que QTD_VENDIDA é numérico
df_parquet['QTD_VENDIDA'] = pd.to_numeric(df_parquet['QTD_VENDIDA'], errors='coerce').fillna(0)
soma_parquet = df_parquet.groupby('CODIGO_PRODUTO')['QTD_VENDIDA'].sum().reset_index()
soma_parquet.rename(columns={'QTD_VENDIDA': 'VENDA_PARQUET'}, inplace=True)

# 2. Lê a planilha mix.xlsx

df_mix = pd.read_excel(excel_path)
# Garante que VENDA_QUERY é numérico
if 'VENDA_QUERY' in df_mix.columns:
	df_mix['VENDA_QUERY'] = pd.to_numeric(df_mix['VENDA_QUERY'], errors='coerce').fillna(0)

# 3. Faz o merge para comparar
comparativo = df_mix.merge(soma_parquet, on='CODIGO_PRODUTO', how='left')

# 4. Mostra divergências
divergentes = comparativo[comparativo['VENDA_QUERY'] != comparativo['VENDA_PARQUET']]
print(divergentes[['CODIGO_PRODUTO', 'DESCRICAO_PRODUTO', 'VENDA_QUERY', 'VENDA_PARQUET']])