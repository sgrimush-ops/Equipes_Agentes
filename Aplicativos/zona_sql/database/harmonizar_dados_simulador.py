import sqlite3
import os

DB_PATH = r"c:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\zona_sql\database\banco_simulador_consinco.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("[*] Verificando integridade de capas e itens...")

# 1. Obter capas de MLFV_BASENFE
c.execute("""
    SELECT SEQNF, NROEMPRESA, NUMERONF, SERIENF, TIPNOTAFISCAL, SEQPESSOA, DTAEMISSAO, CODGERALOPER 
    FROM MLFV_BASENFE 
    WHERE SEQNF IS NOT NULL AND NUMERONF IS NOT NULL
""")
capas = c.fetchall()
print(f"Capas em MLFV_BASENFE: {len(capas)}")

# 2. Obter produtos válidos de MAP_PRODUTO
c.execute("SELECT SEQPRODUTO FROM MAP_PRODUTO WHERE SEQPRODUTO IS NOT NULL")
produtos = [r[0] for r in c.fetchall()]
print(f"Produtos em MAP_PRODUTO: {len(produtos)}")

# 3. Obter itens de MFLV_BASEDFITEM
c.execute("SELECT ROWID, SEQPRODUTO, QUANTIDADE, VLRITEM FROM MFLV_BASEDFITEM")
itens = c.fetchall()
print(f"Itens em MFLV_BASEDFITEM: {len(itens)}")

if capas and itens:
    print("[*] Sincronizando chaves de MFLV_BASEDFITEM com as capas de MLFV_BASENFE...")
    updates = []
    num_capas = len(capas)
    num_prods = len(produtos) if produtos else 1

    for idx, item in enumerate(itens):
        capa = capas[idx % num_capas]
        rowid = item[0]
        prod_id = produtos[idx % num_prods] if (item[1] is None or int(item[1]) not in produtos) else item[1]
        
        updates.append((
            str(capa['SEQNF']),
            str(capa['NROEMPRESA']),
            str(capa['NUMERONF']),
            str(capa['SERIENF']),
            str(capa['TIPNOTAFISCAL']),
            str(capa['SEQPESSOA']),
            str(prod_id),
            rowid
        ))

    c.executemany("""
        UPDATE MFLV_BASEDFITEM
        SET SEQNF = ?,
            NROEMPRESA = ?,
            NUMERODF = ?,
            SERIEDF = ?,
            TIPNOTAFISCAL = ?,
            SEQPESSOA = ?,
            SEQPRODUTO = ?
        WHERE ROWID = ?
    """, updates)
    conn.commit()
    print(f"  -> [OK] {len(updates)} itens de saída alinhados perfeitamente com as capas de NF!")

# 4. Sincronizar itens de entrada MLF_NFITEM com produtos válidos
c.execute("SELECT COUNT(*) FROM MLF_NFITEM WHERE SEQPRODUTO IN (SELECT SEQPRODUTO FROM MAP_PRODUTO)")
matched_prods_in = c.fetchone()[0]
print(f"Itens de entrada MLF_NFITEM com produto válido: {matched_prods_in}")

conn.close()
print("[*] Harmonização concluída com sucesso!")
