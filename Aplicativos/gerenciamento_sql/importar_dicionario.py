import pandas as pd
import sqlite3
import os

txt_path = r"C:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\import_querys\dicionario_consico.txt"
db_path = r"C:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\gerenciamento_sql\dicionario_consinco.db"

try:
    df = pd.read_csv(txt_path, sep=';', dtype=str, keep_default_na=False, encoding='utf-8')
except Exception:
    df = pd.read_csv(txt_path, sep=';', dtype=str, keep_default_na=False, encoding='latin1')

conn = sqlite3.connect(db_path)
df.to_sql('colunas', conn, if_exists='replace', index=False)

# Criar indices para busca rapida
cursor = conn.cursor()
cursor.execute("CREATE INDEX IF NOT EXISTS idx_tabela ON colunas (NOME_TABELA)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_coluna ON colunas (NOME_COLUNA)")
conn.commit()
conn.close()

if os.path.exists(txt_path):
    os.remove(txt_path)

print(f"Sucesso! {len(df)} colunas importadas para SQLite e arquivo de texto apagado.")
