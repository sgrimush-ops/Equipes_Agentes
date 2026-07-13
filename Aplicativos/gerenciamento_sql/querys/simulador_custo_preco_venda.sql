SELECT * FROM (
    WITH CTE_CUSTOS_PRODUTO AS (
        SELECT /*+ MATERIALIZE */
            PE.SEQPRODUTO,
            COUNT(CASE WHEN NVL(PE.CMULTVLRNF, 0) > 0 THEN 1 END) AS QTD_LOJAS_COM_CUSTO,
            ROUND(NVL(MAX(PE.CMULTVLRNF), 0), 4)                  AS CUSTO_NF_BRUTO,
            ROUND(NVL(MAX(PE.CMULTIPI), 0), 4)                    AS CUSTO_IPI,
            ROUND(NVL(MAX(PE.CMULTICMSST), 0), 4)                 AS CUSTO_ICMS_ST,
            ROUND(NVL(MAX(PE.CMULTDESPNF), 0), 4)                 AS CUSTO_DESP_NF,
            ROUND(NVL(MAX(PE.CMULTDESPFORANF), 0), 4)             AS CUSTO_DESP_FORA_NF,
            ROUND(NVL(MAX(PE.CMULTCREDICMS), 0), 4)               AS CREDITO_ICMS,
            ROUND(NVL(MAX(PE.CMULTCREDPIS), 0), 4)                AS CREDITO_PIS,
            ROUND(NVL(MAX(PE.CMULTCREDCOFINS), 0), 4)             AS CREDITO_COFINS,
            ROUND(NVL(MAX(PE.CMULTDCTOFORANF), 0), 4)             AS DESCONTO_FORA_NF,
            ROUND(NVL(MAX(PE.CMULTVLRVERBA), 0), 4)               AS DESCONTO_VERBA,
            ROUND(
                NVL(AVG(
                    CASE
                        WHEN (
                            NVL(PE.CMULTVLRNF, 0)
                            + NVL(PE.CMULTIPI, 0)
                            - NVL(PE.CMULTCREDICMS, 0)
                            + NVL(PE.CMULTICMSST, 0)
                            + NVL(PE.CMULTDESPNF, 0)
                            + NVL(PE.CMULTDESPFORANF, 0)
                            - NVL(PE.CMULTDCTOFORANF, 0)
                            - NVL(PE.CMULTCREDPIS, 0)
                            - NVL(PE.CMULTCREDCOFINS, 0)
                            - NVL(PE.CMULTVLRVERBA, 0)
                        ) > 0 THEN (
                            NVL(PE.CMULTVLRNF, 0)
                            + NVL(PE.CMULTIPI, 0)
                            - NVL(PE.CMULTCREDICMS, 0)
                            + NVL(PE.CMULTICMSST, 0)
                            + NVL(PE.CMULTDESPNF, 0)
                            + NVL(PE.CMULTDESPFORANF, 0)
                            - NVL(PE.CMULTDCTOFORANF, 0)
                            - NVL(PE.CMULTCREDPIS, 0)
                            - NVL(PE.CMULTCREDCOFINS, 0)
                            - NVL(PE.CMULTVLRVERBA, 0)
                        )
                    END
                ), 0),
                4
            )                                                     AS CUSTO_LIQUIDO
        FROM MRL_PRODUTOEMPRESA PE
        WHERE PE.STATUSCOMPRA = 'A'
          AND PE.NROEMPRESA IN (1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18)
          AND (NVL(:NR1, 0) = 0 OR PE.NROEMPRESA = :NR1)
          AND (NVL(:NR2, 0) = 0 OR PE.SEQPRODUTO = :NR2)
        GROUP BY PE.SEQPRODUTO
    ),
    CTE_PRECOS_PRODUTO AS (
        SELECT /*+ MATERIALIZE */
            S.SEQPRODUTO,
            S.QTDEMBALAGEM,
            ROUND(NVL(AVG(CASE WHEN S.PRECOVALIDNORMAL > 0 THEN S.PRECOVALIDNORMAL END), MAX(S.PRECOVALIDNORMAL)), 2) AS PRECO_VENDA_NORMAL,
            ROUND(NVL(AVG(CASE WHEN NVL(NULLIF(S.PRECOVALIDPROMOC, 0), S.PRECOVALIDNORMAL) > 0 THEN NVL(NULLIF(S.PRECOVALIDPROMOC, 0), S.PRECOVALIDNORMAL) END), MAX(NVL(NULLIF(S.PRECOVALIDPROMOC, 0), S.PRECOVALIDNORMAL))), 2) AS PRECO_VENDA_PRATICADO
        FROM MRL_PRODEMPSEG S
        WHERE S.NROEMPRESA IN (1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18)
          AND (NVL(:NR1, 0) = 0 OR S.NROEMPRESA = :NR1)
          AND (NVL(:NR2, 0) = 0 OR S.SEQPRODUTO = :NR2)
        GROUP BY S.SEQPRODUTO, S.QTDEMBALAGEM
    ),
    CTE_BASE_CONDENSADA AS (
        SELECT /*+ MATERIALIZE */
            A.SEQPRODUTO                                         AS CODIGO_PRODUTO,
            A.DESCCOMPLETA                                       AS DESCRICAO_PRODUTO,
            NVL(FS.PADRAOEMBVENDA, 1)                            AS EMBALAGEM_VENDA,
            C.QTD_LOJAS_COM_CUSTO                                AS QTD_LOJAS_COM_CUSTO,
            NVL(PR.PRECO_VENDA_NORMAL, 0)                        AS PRECO_VENDA_NORMAL,
            NVL(PR.PRECO_VENDA_PRATICADO, 0)                     AS PRECO_VENDA_PRATICADO,
            C.CUSTO_NF_BRUTO                                     AS CUSTO_NF_BRUTO,
            C.CUSTO_IPI                                          AS CUSTO_IPI,
            C.CUSTO_ICMS_ST                                      AS CUSTO_ICMS_ST,
            C.CUSTO_DESP_NF                                      AS CUSTO_DESP_NF,
            C.CUSTO_DESP_FORA_NF                                 AS CUSTO_DESP_FORA_NF,
            C.CREDITO_ICMS                                       AS CREDITO_ICMS,
            C.CREDITO_PIS                                        AS CREDITO_PIS,
            C.CREDITO_COFINS                                     AS CREDITO_COFINS,
            C.DESCONTO_FORA_NF                                   AS DESCONTO_FORA_NF,
            C.DESCONTO_VERBA                                     AS DESCONTO_VERBA,
            C.CUSTO_LIQUIDO                                      AS CUSTO_LIQUIDO,
            ROUND(NVL(FC5MARGEMPRECOCADDESPOPER(A.SEQPRODUTO, 1, 1, NVL(FS.PADRAOEMBVENDA, 1), 'M'), 0), 2) AS MARGEM_OBJETIVA,
            NVL((
                SELECT MAX(NVL(T.PERALIQUOTAICMS, 0))
                FROM TABLE(Pkg_Carregaimposto.fc_BuscaTributacao(
                    A.SEQPRODUTO, 'S', NVL(FD.NROTRIBUTACAO, 1), 'SN',
                    0, 'RS', 'RS', 1, 3, TRUNC(SYSDATE)
                )) T
            ), 0)                                                AS ALIQ_ICMS_VENDA,
            NVL((
                SELECT MAX(NVL(T.PERALIQUOTAPIS, 0))
                FROM TABLE(Pkg_Carregaimposto.fc_BuscaTributacao(
                    A.SEQPRODUTO, 'S', NVL(FD.NROTRIBUTACAO, 1), 'SN',
                    0, 'RS', 'RS', 1, 3, TRUNC(SYSDATE)
                )) T
            ), 0)                                                AS ALIQ_PIS_VENDA,
            NVL((
                SELECT MAX(NVL(T.PERALIQUOTACOFINS, 0))
                FROM TABLE(Pkg_Carregaimposto.fc_BuscaTributacao(
                    A.SEQPRODUTO, 'S', NVL(FD.NROTRIBUTACAO, 1), 'SN',
                    0, 'RS', 'RS', 1, 3, TRUNC(SYSDATE)
                )) T
            ), 0)                                                AS ALIQ_COFINS_VENDA
        FROM MAP_PRODUTO A
        INNER JOIN CTE_CUSTOS_PRODUTO C
          ON C.SEQPRODUTO = A.SEQPRODUTO
        LEFT JOIN MAP_FAMDIVISAO FD
          ON FD.SEQFAMILIA = A.SEQFAMILIA
         AND FD.NRODIVISAO = 1
        LEFT JOIN MAD_FAMSEGMENTO FS
          ON FS.SEQFAMILIA = A.SEQFAMILIA
         AND FS.NROSEGMENTO = 1
        LEFT JOIN CTE_PRECOS_PRODUTO PR
          ON PR.SEQPRODUTO = A.SEQPRODUTO
         AND PR.QTDEMBALAGEM = NVL(FS.PADRAOEMBVENDA, 1)
        WHERE NVL(FD.FINALIDADEFAMILIA, 'R') = 'R'
    )
    SELECT
        B.CODIGO_PRODUTO                                     AS CODIGO_PRODUTO,
        B.DESCRICAO_PRODUTO                                  AS DESCRICAO_PRODUTO,
        B.EMBALAGEM_VENDA                                    AS EMBALAGEM_VENDA,
        B.QTD_LOJAS_COM_CUSTO                                AS QTD_LOJAS_COM_CUSTO,
        ROUND(B.PRECO_VENDA_NORMAL, 2)                       AS PRECO_VENDA_NORMAL,
        ROUND(B.PRECO_VENDA_PRATICADO, 2)                    AS PRECO_VENDA_PRATICADO,
        ROUND(B.CUSTO_NF_BRUTO, 4)                           AS CUSTO_NF_BRUTO,
        ROUND(B.CUSTO_IPI, 4)                                AS CUSTO_IPI,
        ROUND(B.CUSTO_ICMS_ST, 4)                            AS CUSTO_ICMS_ST,
        ROUND(B.CUSTO_DESP_NF, 4)                            AS CUSTO_DESP_NF,
        ROUND(B.CUSTO_DESP_FORA_NF, 4)                       AS CUSTO_DESP_FORA_NF,
        ROUND(B.CREDITO_ICMS, 4)                             AS CREDITO_ICMS,
        ROUND(B.CREDITO_PIS, 4)                              AS CREDITO_PIS,
        ROUND(B.CREDITO_COFINS, 4)                           AS CREDITO_COFINS,
        ROUND(B.DESCONTO_FORA_NF, 4)                         AS DESCONTO_FORA_NF,
        ROUND(B.DESCONTO_VERBA, 4)                           AS DESCONTO_VERBA,
        ROUND(B.CUSTO_LIQUIDO, 4)                            AS CUSTO_LIQUIDO,
        ROUND(B.ALIQ_ICMS_VENDA, 2)                          AS ALIQ_ICMS_VENDA,
        ROUND(B.ALIQ_PIS_VENDA, 2)                           AS ALIQ_PIS_VENDA,
        ROUND(B.ALIQ_COFINS_VENDA, 2)                        AS ALIQ_COFINS_VENDA,
        ROUND(B.ALIQ_ICMS_VENDA + B.ALIQ_PIS_VENDA + B.ALIQ_COFINS_VENDA, 2) AS ALIQ_IMPOSTOS_TOTAL,
        ROUND(B.PRECO_VENDA_PRATICADO * ((B.ALIQ_ICMS_VENDA + B.ALIQ_PIS_VENDA + B.ALIQ_COFINS_VENDA) / 100), 4) AS VALOR_IMPOSTOS_VENDA,
        ROUND(B.PRECO_VENDA_PRATICADO * (1 - (B.ALIQ_ICMS_VENDA + B.ALIQ_PIS_VENDA + B.ALIQ_COFINS_VENDA) / 100), 4) AS PRECO_VENDA_LIQUIDO,
        ROUND((B.PRECO_VENDA_PRATICADO * (1 - (B.ALIQ_ICMS_VENDA + B.ALIQ_PIS_VENDA + B.ALIQ_COFINS_VENDA) / 100)) - B.CUSTO_LIQUIDO, 4) AS LUCRO_VALOR,
        ROUND(
            DECODE(
                NVL(B.PRECO_VENDA_PRATICADO, 0),
                0, 0,
                (((B.PRECO_VENDA_PRATICADO * (1 - (B.ALIQ_ICMS_VENDA + B.ALIQ_PIS_VENDA + B.ALIQ_COFINS_VENDA) / 100)) - B.CUSTO_LIQUIDO) / B.PRECO_VENDA_PRATICADO) * 100
            ),
            2
        )                                                    AS MARGEM_REALIZADA,
        ROUND(B.MARGEM_OBJETIVA, 2)                          AS MARGEM_OBJETIVA,
        ROUND(
            DECODE(
                NVL(NULLIF(1 - (B.MARGEM_OBJETIVA + B.ALIQ_ICMS_VENDA + B.ALIQ_PIS_VENDA + B.ALIQ_COFINS_VENDA) / 100, 0), 0),
                0, B.PRECO_VENDA_NORMAL,
                B.CUSTO_LIQUIDO / (1 - (B.MARGEM_OBJETIVA + B.ALIQ_ICMS_VENDA + B.ALIQ_PIS_VENDA + B.ALIQ_COFINS_VENDA) / 100)
            ),
            2
        )                                                    AS PRECO_SUGERIDO
    FROM CTE_BASE_CONDENSADA B
    ORDER BY B.CODIGO_PRODUTO
)
