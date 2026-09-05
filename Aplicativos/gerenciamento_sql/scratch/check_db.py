import sqlite3

db_path = r'c:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\zona_sql\database\banco_simulador_consinco.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tabs = c.fetchall()
print(f"Total de tabelas no banco: {len(tabs)}")
for t in sorted(tabs):
    table_name = t[0]
    try:
        c.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        cnt = c.fetchone()[0]
        print(f"  {table_name}: {cnt:,} linhas")
    except Exception as e:
        print(f"  {table_name}: erro ({e})")
conn.close()
