import sqlite3

conn = sqlite3.connect('dicionario_consinco.db')
c = conn.cursor()

print("=== BUSCA POR APPORIGEM NO DICIONARIO ===")
c.execute("""
    SELECT NOME_TABELA, NOME_COLUNA, DESCRICAO_COLUNA 
    FROM colunas 
    WHERE DESCRICAO_COLUNA LIKE '%APPORIGEM%' OR NOME_COLUNA LIKE '%APPORIGEM%'
""")
for r in c.fetchall():
    print(f"{r[0]:<30} | {r[1]:<25} | {r[2] or ''}")

print("\n=== BUSCA POR DESCRICAO DE TABELAS MSU ===")
c.execute("""
    SELECT DISTINCT NOME_TABELA, DESCRICAO_TABELA 
    FROM tabelas 
    WHERE NOME_TABELA LIKE 'MSU_%'
""")
for r in c.fetchall():
    if r[1]:
        print(f"{r[0]:<30} | {r[1]}")

conn.close()
