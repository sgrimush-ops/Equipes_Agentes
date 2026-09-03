import sqlite3

conn = sqlite3.connect('dicionario_consinco.db')
c = conn.cursor()

print('=== 1. TABELAS MSU_* E MACV_* RELACIONADAS A CANCELAMENTO/PEDIDO ===')
c.execute("""
    SELECT DISTINCT NOME_TABELA 
    FROM colunas 
    WHERE (NOME_TABELA LIKE 'MSU_%' OR NOME_TABELA LIKE 'MACV_%' OR NOME_TABELA LIKE 'MAD_%') 
      AND (NOME_TABELA LIKE '%CANC%' OR NOME_TABELA LIKE '%PED%' OR NOME_TABELA LIKE '%ITEM%' OR NOME_TABELA LIKE '%HIST%' OR NOME_TABELA LIKE '%LOG%' OR NOME_TABELA LIKE '%AUDIT%')
    ORDER BY NOME_TABELA
""")
for r in c.fetchall():
    print(r[0])

print('\n=== 2. COLUNAS EM MSU_PEDIDOSUPRIM, MSU_PSITEMRECEBER, MSU_PSITEMEXPEDIR ===')
for tab in ['MSU_PEDIDOSUPRIM', 'MSU_PSITEMRECEBER', 'MSU_PSITEMEXPEDIR', 'MACV_PSITEMRECEBER', 'MACV_PSITEMEXPEDIR']:
    print(f"\n--- {tab} ---")
    c.execute(f"SELECT NOME_COLUNA, TIPO_DADOS, DESCRICAO_COLUNA FROM colunas WHERE NOME_TABELA = '{tab}' ORDER BY CAST(ORDEM AS INTEGER)")
    for col, tipo, desc in c.fetchall():
        if any(k in col.upper() for k in ['CANC', 'STATUS', 'SITUAC', 'MOTIV', 'USU', 'DTA', 'IND', 'APP']):
            print(f"  {col:<30} | {tipo:<15} | {desc or ''}")

print('\n=== 3. COLUNAS COM CANCEL/MOTIVO/USU EM QUALQUER TABELA MSU_ ===')
c.execute("""
    SELECT NOME_TABELA, NOME_COLUNA, TIPO_DADOS, DESCRICAO_COLUNA 
    FROM colunas 
    WHERE NOME_TABELA LIKE 'MSU_%' 
      AND (NOME_COLUNA LIKE '%CANC%' OR NOME_COLUNA LIKE '%MOTIVO%')
    ORDER BY NOME_TABELA, NOME_COLUNA
""")
for r in c.fetchall():
    print(f"{r[0]:<30} | {r[1]:<25} | {r[2]:<15} | {r[3] or ''}")

conn.close()
