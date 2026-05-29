import pandas as pd
import os

# Caminho do arquivo parquet e saída
parquet_path = r'c:/Users/usr/Downloads/Equipes_Agentes/Aplicativos/import_querys/query.parquet'
output_path = r'c:/Users/usr/Downloads/Equipes_Agentes/Aplicativos/ruptura/debug_todas_lojas_venda.csv'

# Carrega o parquet
parquet = pd.read_parquet(parquet_path)

# Filtra apenas produtos com venda > 0 em qualquer loja
qtd_vendida_str = parquet['QTD_VENDIDA'].astype(str).str.replace(',', '.')
filtro = pd.to_numeric(qtd_vendida_str, errors='coerce').fillna(0) < 3

df = parquet.loc[filtro, [
    'CODIGO_EMPRESA',
    'CODIGO_PRODUTO',
    'DESCRICAO_PRODUTO',
    'QUANTIDADE_DISPONIVEL',
    'QTD_VENDIDA',
    'QUANTIDADE_ESTOQUE_MINIMO',
    'QUANTIDADE_ESTOQUE_MAXIMO'
]].drop_duplicates()


# Adiciona coluna ESTOQUE_CD15 (estoque da empresa 15 para cada produto)
estoque_cd15 = parquet[parquet['CODIGO_EMPRESA'] == 15][['CODIGO_PRODUTO', 'QUANTIDADE_DISPONIVEL']].drop_duplicates('CODIGO_PRODUTO')
estoque_cd15 = estoque_cd15.rename(columns={'QUANTIDADE_DISPONIVEL': 'ESTOQUE_CD15'})
df = df.merge(estoque_cd15, on='CODIGO_PRODUTO', how='left')

# Remove linhas da empresa 15
df = df[df['CODIGO_EMPRESA'] != 15]

# Garante que QTD_VENDIDA está como float e converte para string com vírgula decimal para exportação
df['QTD_VENDIDA'] = df['QTD_VENDIDA'].astype(str).str.replace(',', '.')
df['QTD_VENDIDA'] = pd.to_numeric(df['QTD_VENDIDA'], errors='coerce').fillna(0)
df['QTD_VENDIDA'] = df['QTD_VENDIDA'].map(lambda x: f'{x:.1f}'.replace('.', ','))

# Salva CSV
output_path = os.path.join(os.path.dirname(__file__), output_path)
df.to_csv(output_path, index=False, encoding='utf-8-sig', sep=';')
print(f'Arquivo gerado: {output_path} ({len(df)} registros)')
