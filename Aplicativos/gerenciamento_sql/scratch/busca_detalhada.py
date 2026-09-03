import sqlite3

conn = sqlite3.connect('dicionario_consinco.db')
c = conn.cursor()

def ver_tabela(tab):
    print(f"\n{'='*20} {tab} {'='*20}")
    c.execute(f"""
        SELECT NOME_COLUNA, TIPO_DADOS, DESCRICAO_COLUNA 
        FROM colunas 
        WHERE NOME_TABELA = '{tab}' 
        ORDER BY CAST(ORDEM AS INTEGER)
    """)
    for col, tipo, desc in c.fetchall():
        print(f"{col:<30} | {tipo:<15} | {desc or ''}")

for t in ['MSU_PSITEMRECEBIDO', 'MSU_PSITEMEXPEDIDO', 'MSU_PEDIDOSUPRIM', 'MSU_PSITEMRECEBER', 'MSU_PSITEMEXPEDIR']:
    ver_tabela(t)

print("\n=== TODAS AS TABELAS COM RECEBIDO OU EXPEDIDO OU CANCEL ===")
c.execute("""
    SELECT DISTINCT NOME_TABELA 
    FROM colunas 
    WHERE NOME_TABELA LIKE 'MSU_%' 
      AND (NOME_TABELA LIKE '%RECEBIDO%' OR NOME_TABELA LIKE '%EXPEDIDO%' OR NOME_TABELA LIKE '%CANC%')
    ORDER BY NOME_TABELA
""")
for r in c.fetchall():
    print(r[0])

conn.close()
