import sqlite3

conn = sqlite3.connect('dicionario_consinco.db')
c = conn.cursor()

c.execute("SELECT NOME_COLUNA FROM colunas WHERE NOME_TABELA = 'GE_PESSOA' AND NOME_COLUNA IN ('SEQPESSOA', 'NOMERAZAO', 'FANTASIA', 'APELIDO')")
print(c.fetchall())

conn.close()
