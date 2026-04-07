# data.py
import pandas as pd
from datetime import datetime
import os

# Descobre o diretório real onde o data.py está localizado na máquina
base_dir = os.path.dirname(os.path.abspath(__file__))

# Registra a data atual do computador
data_hoje = datetime.now().strftime('%d_%m_%Y')

# 1. Carregar os arquivos query txt do mesmo diretório
arquivo_origem = os.path.join(base_dir, 'query.txt')
df_query = pd.read_csv(arquivo_origem, sep=';')

# 2. Sanitizar e Salvar o resultado
# REGRA ESTRUTURAL OBRIGATÓRIA: NUNCA alterar as vírgulas (,). O ponto (.) desconfigura planilhas Excel adjacentes que os visualizam, agindo localmente como milhar.
# Força apenas a conversão genérica (object) para string definitiva (evitando falha do Parquet PyArrow em tipos mistos).
for coluna in df_query.select_dtypes(include=['object']).columns:
    df_query[coluna] = df_query[coluna].astype(str)

arquivo_parquet = os.path.join(base_dir, 'query.parquet')
df_query.to_parquet(arquivo_parquet, index=False)

dir_csv = os.path.join(base_dir, 'arquivo_csv')
os.makedirs(dir_csv, exist_ok=True)
nome_arquivo_csv = f'query_{data_hoje}.csv'
arquivo_csv = os.path.join(dir_csv, nome_arquivo_csv)
df_query.to_csv(arquivo_csv, index=False, sep=';', encoding='utf-8-sig')

print(f"Conversão concluída! Arquivos salvos na pasta:")
print(f" -> {arquivo_parquet}")
print(f" -> {arquivo_csv}")

# 3. Teste de Validação e Comparação de Integridade
print("\nIniciando verificação de integridade entre os arquivos...")
df_check_parquet = pd.read_parquet(arquivo_parquet)
df_check_csv = pd.read_csv(arquivo_csv, sep=';', encoding='utf-8-sig')

# Comparando se a quantidade de linhas e colunas batem perfeitamente
linhas_pq, cols_pq = df_check_parquet.shape
linhas_csv, cols_csv = df_check_csv.shape

if (linhas_pq == linhas_csv) and (cols_pq == cols_csv):
    print(f"✅ SUCESSO: COMPARAÇÃO OK! Ambos os arquivos contêm {linhas_pq} linhas e {cols_pq} colunas intactas.")
else:
    print(f"❌ ALERTA! Divergência detectada. Parquet ({linhas_pq}x{cols_pq}) vs CSV ({linhas_csv}x{cols_csv}).")
