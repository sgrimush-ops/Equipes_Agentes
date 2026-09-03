import sqlite3

conn = sqlite3.connect('dicionario_consinco.db')
c = conn.cursor()

def listar_tudo(tab):
    print(f"\n{'='*20} {tab} {'='*20}")
    c.execute(f"""
        SELECT NOME_COLUNA, TIPO_DADOS, DESCRICAO_COLUNA 
        FROM colunas 
        WHERE NOME_TABELA = '{tab}' 
        ORDER BY CAST(ORDEM AS INTEGER)
    """)
    for col, tipo, desc in c.fetchall():
        print(f"{col:<30} | {tipo:<15} | {desc or ''}")

listar_tudo('MSU_PSITEMRECEBIDO')
listar_tudo('MSU_PSITEMEXPEDIDO')
listar_tudo('MSU_PEDIDOSUPRIM')
listar_tudo('MSUX_CANCELAPEDIDOSUPRIM')

conn.close()
