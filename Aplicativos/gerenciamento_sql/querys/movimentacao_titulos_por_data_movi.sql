SELECT * FROM (
    WITH CTE_OPERACOES AS (
        SELECT /*+ MATERIALIZE */
            O.SEQTITULO,
            MAX(O.DTAOPERACAO) AS MAX_DTAOPERACAO,
            MAX(NVL(O.DTAHORAALTERACAO, O.DTAALTERACAO)) AS MAX_DTAHORAALTERACAO,
            MAX(O.USUALTERACAO) KEEP (
                DENSE_RANK LAST 
                ORDER BY NVL(O.DTAHORAALTERACAO, O.DTAALTERACAO) NULLS FIRST, O.SEQTITOPERACAO
            ) AS USUALTERACAO
        FROM FI_TITOPERACAO O
        WHERE O.OPCANCELADA IS NULL
          AND O.USUCANCELOU IS NULL
          AND (
              TRUNC(O.DTAOPERACAO) BETWEEN :DT1 AND :DT2
              OR TRUNC(NVL(O.DTAHORAALTERACAO, O.DTAALTERACAO)) BETWEEN :DT1 AND :DT2
          )
        GROUP BY
            O.SEQTITULO
    ),
    CTE_TITULOS_MOV AS (
        SELECT /*+ MATERIALIZE */
            T.SEQTITULO,
            T.NROEMPRESA,
            T.SEQPESSOA,
            T.NROTITULO,
            T.NROPARCELA,
            T.CODESPECIE,
            T.DTAVENCIMENTO,
            T.DTAINCLUSAO,
            T.DTAQUITACAO,
            T.VLRNOMINAL,
            T.VLRPAGO,
            T.ABERTOQUITADO,
            T.SITUACAO,
            T.OBSERVACAO,
            OP.USUALTERACAO AS USU_ULT_OPERACAO,
            NVL(OP.MAX_DTAHORAALTERACAO, CAST(T.DTAQUITACAO AS DATE)) AS DTA_ULT_OPERACAO
        FROM FI_TITULO T
        LEFT JOIN CTE_OPERACOES OP
            ON OP.SEQTITULO = T.SEQTITULO
        WHERE T.SITUACAO != 'C'
          AND (
              OP.SEQTITULO IS NOT NULL
              OR (T.DTAQUITACAO IS NOT NULL AND TRUNC(T.DTAQUITACAO) BETWEEN :DT1 AND :DT2)
              OR (T.DTAMOVIMENTO IS NOT NULL AND TRUNC(T.DTAMOVIMENTO) BETWEEN :DT1 AND :DT2)
          )
          AND (
              :LT1 = '0'
              OR T.CODESPECIE IN (
                  SELECT UPPER(TRIM(REGEXP_SUBSTR(:LT1, '[^,]+', 1, LEVEL)))
                  FROM DUAL
                  CONNECT BY REGEXP_SUBSTR(:LT1, '[^,]+', 1, LEVEL) IS NOT NULL
              )
          )
          AND (:NR1 = 0 OR T.NROTITULO = :NR1)
          AND (
              :LT2 = '0'
              OR T.SEQPESSOA IN (
                  SELECT TO_NUMBER(REGEXP_SUBSTR(:LT2, '[^,]+', 1, LEVEL))
                  FROM DUAL
                  CONNECT BY REGEXP_SUBSTR(:LT2, '[^,]+', 1, LEVEL) IS NOT NULL
              )
          )
          AND (
              :LT3 = '0'
              OR T.ABERTOQUITADO IN (
                  SELECT UPPER(TRIM(REGEXP_SUBSTR(:LT3, '[^,]+', 1, LEVEL)))
                  FROM DUAL
                  CONNECT BY REGEXP_SUBSTR(:LT3, '[^,]+', 1, LEVEL) IS NOT NULL
              )
          )
          AND (
              NVL(TRIM(:LT4), '0') IN ('0', 'TODOS', '')
              OR UPPER(TRIM(OP.USUALTERACAO)) IN (
                  SELECT UPPER(TRIM(REGEXP_SUBSTR(:LT4, '[^,]+', 1, LEVEL)))
                  FROM DUAL
                  CONNECT BY REGEXP_SUBSTR(:LT4, '[^,]+', 1, LEVEL) IS NOT NULL
              )
          )
          AND (
              :LS1 = ' TODAS AS REDES'
              OR EXISTS (
                  SELECT 1
                  FROM GE_REDEPESSOA RP
                  JOIN GE_REDE R ON RP.SEQREDE = R.SEQREDE
                  WHERE RP.SEQPESSOA = T.SEQPESSOA
                    AND R.DESCRICAO = :LS1
              )
          )
    )
    SELECT
        T.NROEMPRESA AS EMPRESA,
        T.SEQPESSOA AS FORNECEDOR,
        P.NOMERAZAO AS NOME_FORNECEDOR,
        T.NROTITULO AS NRO_TITULO,
        T.NROPARCELA AS PARCELA,
        T.CODESPECIE AS ESPECIE,
        TO_CHAR(T.DTAVENCIMENTO, 'DD/MM/YYYY') AS DTA_VENCIMENTO,
        TO_CHAR(T.DTAINCLUSAO, 'DD/MM/YYYY') AS DTA_INCLUSAO,
        TO_CHAR(T.DTAQUITACAO, 'DD/MM/YYYY') AS DTA_QUITACAO,
        TO_CHAR(T.VLRNOMINAL, 'FM999G999G990D00', 'NLS_NUMERIC_CHARACTERS='',.''') AS VLR_NOMINAL,
        TO_CHAR(T.VLRPAGO, 'FM999G999G990D00', 'NLS_NUMERIC_CHARACTERS='',.''') AS VLR_PAGO,
        T.ABERTOQUITADO AS STATUS_PAGTO,
        T.SITUACAO AS SITUACAO,
        T.OBSERVACAO AS OBSERVACAO,
        T.USU_ULT_OPERACAO,
        TO_CHAR(T.DTA_ULT_OPERACAO, 'DD/MM/YYYY HH24:MI:SS') AS DTA_ULT_OPERACAO
    FROM CTE_TITULOS_MOV T
    LEFT JOIN GE_PESSOA P
        ON P.SEQPESSOA = T.SEQPESSOA
    ORDER BY
        T.DTA_ULT_OPERACAO DESC NULLS LAST,
        T.DTAVENCIMENTO DESC,
        T.SEQPESSOA
)
