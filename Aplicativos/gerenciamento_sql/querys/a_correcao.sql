SELECT * FROM (
    WITH CTE_PRODUTOS_ATIVOS AS (
        SELECT /*+ MATERIALIZE */ DISTINCT
            PE.SEQPRODUTO
        FROM MRL_PRODUTOEMPRESA PE
        WHERE PE.STATUSCOMPRA = 'A'
          AND PE.NROEMPRESA IN (3, 11)
    ),
    CTE_PRECOS_LOJAS AS (
        SELECT /*+ MATERIALIZE */
            S.SEQPRODUTO                                                          AS CODIGO_PRODUTO,
            S.QTDEMBALAGEM                                                        AS EMBALAGEM,
            MAX(CASE
                WHEN S.NROEMPRESA = 3 THEN
                    ROUND(NVL(NULLIF(S.PRECOVALIDPROMOC, 0), S.PRECOVALIDNORMAL), 2)
            END)                                                                  AS PRECO_PRATICADO_LOJA3,
            MAX(CASE
                WHEN S.NROEMPRESA = 11 THEN
                    ROUND(NVL(NULLIF(S.PRECOVALIDPROMOC, 0), S.PRECOVALIDNORMAL), 2)
            END)                                                                  AS PRECO_PRATICADO_LOJA11
        FROM MRL_PRODEMPSEG S
        WHERE S.NROEMPRESA IN (3, 11)
        GROUP BY S.SEQPRODUTO, S.QTDEMBALAGEM
    )
    SELECT
        A.SEQPRODUTO                                                              AS CODIGO_PRODUTO,
        A.DESCCOMPLETA                                                            AS DESCRICAO_PRODUTO,
        NVL(P.PRECO_PRATICADO_LOJA3, 0)                                           AS PRECO_PRATICADO_LOJA3,
        NVL(P.PRECO_PRATICADO_LOJA11, 0)                                          AS PRECO_PRATICADO_LOJA11
    FROM CTE_PRODUTOS_ATIVOS PA
    INNER JOIN MAP_PRODUTO A
      ON A.SEQPRODUTO = PA.SEQPRODUTO
    LEFT JOIN MAP_FAMDIVISAO FD
      ON FD.SEQFAMILIA = A.SEQFAMILIA
     AND FD.NRODIVISAO = 1
    LEFT JOIN MAD_FAMSEGMENTO FS
      ON FS.SEQFAMILIA = A.SEQFAMILIA
     AND FS.NROSEGMENTO = 1
    LEFT JOIN CTE_PRECOS_LOJAS P
      ON P.CODIGO_PRODUTO = A.SEQPRODUTO
     AND P.EMBALAGEM = NVL(FS.PADRAOEMBVENDA, 1)
    WHERE NVL(FD.FINALIDADEFAMILIA, 'R') = 'R'
    ORDER BY A.SEQPRODUTO
)
