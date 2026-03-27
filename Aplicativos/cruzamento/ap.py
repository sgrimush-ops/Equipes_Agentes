import pandas as pd
import glob
import os

# Caminho para a pasta 'bd'
pasta_bd = 'bd'

# Encontrar todos os arquivos .parquet na pasta 'bd'
arquivos_parquet = glob.glob(os.path.join(pasta_bd, '*.parquet'))
print(f"Arquivos encontrados: {arquivos_parquet}")

# Iterar sobre cada arquivo encontrado
for arquivo in arquivos_parquet:
    print(f"\n{'='*40}")
    print(f"Lendo arquvio: {arquivo}")
    print(f"{'='*40}")
    
    try:
        # Ler o arquivo Parquet
        df = pd.read_parquet(arquivo)
        
        # Visualizar as colunas
        cols = df.columns.tolist()
        print(f"Total de colunas: {len(cols)}")
        print(f"Colunas: {cols}")
        
        # Visualizar as primeiras 3 linhas
        print("\nPrimeiras 3 linhas:")
        print(df.head(3))
        
    except Exception as e:
        print(f"Erro ao ler o arquivo {arquivo}: {e}")
