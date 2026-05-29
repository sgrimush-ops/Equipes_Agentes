import pandas as pd

parquet_path = r'c:/Users/usr/Downloads/Equipes_Agentes/Aplicativos/import_querys/query.parquet'
output_path = r'c:/Users/usr/Downloads/Equipes_Agentes/Aplicativos/ruptura/debug_loja1_venda_baixa.csv'

# Lê o parquet e garante que QTD_VENDIDA é numérico
parquet = pd.read_parquet(parquet_path)
parquet['QTD_VENDIDA'] = pd.to_numeric(parquet['QTD_VENDIDA'], errors='coerce').fillna(0)

# Filtra loja 1 e produtos com venda < 3
filtro = (parquet['CODIGO_EMPRESA'] == 1) & (parquet['QTD_VENDIDA'] < 3)
df = parquet.loc[filtro, [
    'CODIGO_PRODUTO',
    'DESCRICAO_PRODUTO',
    'QUANTIDADE_DISPONIVEL',
    'QTD_VENDIDA',
    'QUANTIDADE_ESTOQUE_MINIMO',
    'QUANTIDADE_ESTOQUE_MAXIMO'
]].drop_duplicates()
# Garante que QTD_VENDIDA está como float
df['QTD_VENDIDA'] = pd.to_numeric(df['QTD_VENDIDA'], errors='coerce').fillna(0)
df['QTD_VENDIDA'] = df['QTD_VENDIDA'].map(lambda x: f'{x:.1f}'.replace('.', ','))

df.to_csv(output_path, index=False, encoding='utf-8-sig', sep=';')
print(f'Arquivo gerado: {output_path} ({len(df)} registros)')
