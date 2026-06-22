import oracledb
import pandas as pd

try:
    conn = oracledb.connect('CONSULTA/CONSULTA@192.168.0.11:1521/vbox')
    
    query = """
    SELECT NUMERONF, SERIENF, NROEMPRESA, DTAEMISSAO, DTAENTRADA, VLRTOTALNF, SITUACAO, SEQNOTAFISCAL, SEQAUXNOTAFISCAL, SEQPESSOA, STATUSNF, USUARIOLANCAMENTO, NFECHAVEACESSO, CODGERALOPER
    FROM MLF_NOTAFISCAL
    WHERE NUMERONF IN (916725, 174296)
      AND SEQPESSOA = 5894
    """
    df = pd.read_sql(query, conn)
    print(df)
except Exception as e:
    print(f"Error: {e}")
