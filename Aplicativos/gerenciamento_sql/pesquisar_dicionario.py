import sqlite3
import argparse
import os

db_path = os.path.join(os.path.dirname(__file__), 'dicionario_consinco.db')

def search(tabela=None, coluna=None):
    if not os.path.exists(db_path):
        print(f"Erro: Banco de dados nao encontrado em {db_path}")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT NOME_TABELA, NOME_COLUNA, TIPO_DADOS, DESCRICAO_COLUNA FROM colunas WHERE 1=1"
    params = []

    if tabela:
        query += " AND NOME_TABELA LIKE ?"
        params.append(f"%{tabela.upper()}%")
    if coluna:
        query += " AND NOME_COLUNA LIKE ?"
        params.append(f"%{coluna.upper()}%")

    query += " ORDER BY NOME_TABELA, CAST(ORDEM AS INTEGER) LIMIT 200"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    if not rows:
        print("Nenhum resultado encontrado.")
    else:
        print(f"{'TABELA':<30} | {'COLUNA':<30} | {'TIPO':<15} | {'DESCRICAO'}")
        print("-" * 110)
        for r in rows:
            desc = (r['DESCRICAO_COLUNA'] or '')[:50]
            print(f"{r['NOME_TABELA']:<30} | {r['NOME_COLUNA']:<30} | {r['TIPO_DADOS']:<15} | {desc}")
    
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pesquisa no Dicionario de Dados Totvs Consinco")
    parser.add_argument("-t", "--tabela", help="Nome da tabela (aceita parte do nome)")
    parser.add_argument("-c", "--coluna", help="Nome da coluna (aceita parte do nome)")
    
    args = parser.parse_args()
    
    if not args.tabela and not args.coluna:
        print("Forneca pelo menos uma tabela (-t) ou coluna (-c) para pesquisar.")
    else:
        search(args.tabela, args.coluna)
