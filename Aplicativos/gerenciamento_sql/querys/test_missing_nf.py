import cx_Oracle
import pandas as pd

conn = cx_Oracle.connect('CONSULTA/CONSULTA@192.168.0.11:1521/vbox')

query = """
SELECT N.NUMERONF, N.DTAENTRADA, N.CODGERALOPER, N.SITUACAO, N.VLRTOTALNF,
       I.SEQPRODUTO, I.TIPPEDCOMPRAITEM, I.VLRITEM
FROM MLF_NOTAFISCAL N
JOIN MLF_NFITEM I ON I.SEQNOTAFISCAL = N.SEQNOTAFISCAL
WHERE N.NUMERONF IN (916725, 174296)
  AND N.SEQPESSOA = 5894
"""

try:
    df = pd.read_sql(query, conn)
    print(df)
except Exception as e:
    print(f"Error: {e}")
