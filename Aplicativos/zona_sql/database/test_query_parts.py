import sys, sqlite3
sys.path.append('c:/Users/usr/Downloads/Equipes_Agentes/Aplicativos/zona_sql')
import server

conn = server.get_db_connection()
c = conn.cursor()

c.execute("PRAGMA table_info(MFLV_BASEDFITEM)")
mflv_cols = [r[1] for r in c.fetchall()]
print("MFLV_BASEDFITEM columns:", mflv_cols)

c.execute("PRAGMA table_info(MLF_NFITEM)")
mlf_cols = [r[1] for r in c.fetchall()]
print("\nMLF_NFITEM columns:", mlf_cols)

# Amostra de MFLV
cols_mflv_select = [col for col in ['SEQPRODUTO', 'QUANTIDADE', 'VLRITEM', 'VLRTOTAL', 'VLRCONTABIL', 'VLRDESCONTO', 'VLRACRESCIMO'] if col in mflv_cols]
c.execute(f"SELECT {', '.join(cols_mflv_select)} FROM MFLV_BASEDFITEM LIMIT 5")
print("\nMFLV sample:")
for r in c.fetchall():
    print(dict(r))

# Amostra de MLF
cols_mlf_select = [col for col in ['SEQPRODUTO', 'QUANTIDADE', 'VLRITEM', 'VLRTOTAL', 'VLRCONTABIL', 'VLRDESCONTO', 'VLRACRESCIMO'] if col in mlf_cols]
c.execute(f"SELECT {', '.join(cols_mlf_select)} FROM MLF_NFITEM LIMIT 5")
print("\nMLF sample:")
for r in c.fetchall():
    print(dict(r))
