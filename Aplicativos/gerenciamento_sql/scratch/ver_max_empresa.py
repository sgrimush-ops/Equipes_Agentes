import sqlite3

conn = sqlite3.connect('dicionario_consinco.db')
c = conn.cursor()

c.execute("SELECT NOME_COLUNA, TIPO_DADOS FROM colunas WHERE NOME_TABELA = 'MAX_EMPRESA' ORDER BY CAST(ORDEM AS INTEGER) LIMIT 20")
for r in c.fetchall():
    print(r[0], r[1])

conn.close()
