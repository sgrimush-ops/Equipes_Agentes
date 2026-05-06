SELECT
    ME.NROEMPRESA                                  AS NROEMPRESA,
    A.SEQPRODUTO                                   AS CODIGO_PRODUTO,
    A.DESCCOMPLETA                                 AS DESCRICAO_PRODUTO,
    ROUND(NVL(PE.CMULTVLRNF, 0), 2)               AS CUSTO_BRUTO,
    ROUND(
        NVL(PE.CMULTVLRNF, 0)
        + NVL(PE.CMULTIPI, 0)
        - NVL(PE.CMULTCREDICMS, 0)
        + NVL(PE.CMULTICMSST, 0)
        + NVL(PE.CMULTDESPNF, 0)
        + NVL(PE.CMULTDESPFORANF, 0)
        - NVL(PE.CMULTDCTOFORANF, 0)
        - NVL(PE.CMULTCREDPIS, 0)
        - NVL(PE.CMULTCREDCOFINS, 0)
        - NVL(CV.VLRUNITVERBA, NVL(PE.CMULTVLRVERBA, 0))
    , 2)                                           AS CUSTO_LIQUIDO,
    ROUND(NVL(FC5MARGEMPRECOCADDESPOPER(A.SEQPRODUTO, ME.NROEMPRESA, ME.NROSEGMENTOPRINC, NVL(FS.PADRAOEMBVENDA, 1), 'M'), 0), 2) AS MARGEM_OBJETIVA,
    ROUND(
        DECODE(
            NVL(FC5MARGEMPRECOCADDESPOPER(A.SEQPRODUTO, ME.NROEMPRESA, ME.NROSEGMENTOPRINC, NVL(FS.PADRAOEMBVENDA, 1), 'M'), 0),
            0, NVL(SEG.PRECOVALIDNORMAL, 0),
            (
                NVL(PE.CMULTVLRNF, 0)
                + NVL(PE.CMULTIPI, 0)
                - NVL(PE.CMULTCREDICMS, 0)
                + NVL(PE.CMULTICMSST, 0)
                + NVL(PE.CMULTDESPNF, 0)
                + NVL(PE.CMULTDESPFORANF, 0)
                - NVL(PE.CMULTDCTOFORANF, 0)
                - NVL(PE.CMULTCREDPIS, 0)
                - NVL(PE.CMULTCREDCOFINS, 0)
                - NVL(CV.VLRUNITVERBA, NVL(PE.CMULTVLRVERBA, 0))
            ) / NULLIF(
                1 - (
                    NVL(FC5MARGEMPRECOCADDESPOPER(A.SEQPRODUTO, ME.NROEMPRESA, ME.NROSEGMENTOPRINC, NVL(FS.PADRAOEMBVENDA, 1), 'M'), 0)
                    + NVL((
                        SELECT MAX(NVL(T.PERALIQUOTAICMS, 0))
                        FROM TABLE(Pkg_Carregaimposto.fc_BuscaTributacao(
                            A.SEQPRODUTO, 'S', NVL(FD.NROTRIBUTACAO, ME.NROSEGMENTOPRINC),
                            DECODE(MD.TIPDIVISAO, 'A', 'SC', 'SN'),
                            0, ME.UF, NVL(MSG.UFPADRAOSUGPRECO, ME.UF),
                            ME.NROEMPRESA, 3, TRUNC(SYSDATE)
                        )) T
                    ), 0)
                    + NVL((
                        SELECT MAX(NVL(T.PERALIQUOTAPIS, 0))
                        FROM TABLE(Pkg_Carregaimposto.fc_BuscaTributacao(
                            A.SEQPRODUTO, 'S', NVL(FD.NROTRIBUTACAO, ME.NROSEGMENTOPRINC),
                            DECODE(MD.TIPDIVISAO, 'A', 'SC', 'SN'),
                            0, ME.UF, NVL(MSG.UFPADRAOSUGPRECO, ME.UF),
                            ME.NROEMPRESA, 3, TRUNC(SYSDATE)
                        )) T
                    ), 0)
                    + NVL((
                        SELECT MAX(NVL(T.PERALIQUOTACOFINS, 0))
                        FROM TABLE(Pkg_Carregaimposto.fc_BuscaTributacao(
                            A.SEQPRODUTO, 'S', NVL(FD.NROTRIBUTACAO, ME.NROSEGMENTOPRINC),
                            DECODE(MD.TIPDIVISAO, 'A', 'SC', 'SN'),
                            0, ME.UF, NVL(MSG.UFPADRAOSUGPRECO, ME.UF),
                            ME.NROEMPRESA, 3, TRUNC(SYSDATE)
                        )) T
                    ), 0)
                ) / 100,
                0
            )
        )
    , 2)                                           AS PRECO_SUGERIDO,
    ROUND(
        NVL(NULLIF(SEG.PRECOVALIDPROMOC, 0), SEG.PRECOVALIDNORMAL)
    , 2)                                           AS PRECO_VENDA,
    ROUND(
        DECODE(
            NVL(NULLIF(SEG.PRECOVALIDPROMOC, 0), SEG.PRECOVALIDNORMAL),
            0, 0,
            (
                (
                    NVL(NULLIF(SEG.PRECOVALIDPROMOC, 0), SEG.PRECOVALIDNORMAL)
                    * (1 - (
                        NVL((
                            SELECT MAX(NVL(T.PERALIQUOTAICMS, 0))
                            FROM TABLE(Pkg_Carregaimposto.fc_BuscaTributacao(
                                A.SEQPRODUTO, 'S', NVL(FD.NROTRIBUTACAO, ME.NROSEGMENTOPRINC),
                                DECODE(MD.TIPDIVISAO, 'A', 'SC', 'SN'),
                                0, ME.UF, NVL(MSG.UFPADRAOSUGPRECO, ME.UF),
                                ME.NROEMPRESA, 3, TRUNC(SYSDATE)
                            )) T
                        ), 0)
                        + NVL((
                            SELECT MAX(NVL(T.PERALIQUOTAPIS, 0))
                            FROM TABLE(Pkg_Carregaimposto.fc_BuscaTributacao(
                                A.SEQPRODUTO, 'S', NVL(FD.NROTRIBUTACAO, ME.NROSEGMENTOPRINC),
                                DECODE(MD.TIPDIVISAO, 'A', 'SC', 'SN'),
                                0, ME.UF, NVL(MSG.UFPADRAOSUGPRECO, ME.UF),
                                ME.NROEMPRESA, 3, TRUNC(SYSDATE)
                            )) T
                        ), 0)
                        + NVL((
                            SELECT MAX(NVL(T.PERALIQUOTACOFINS, 0))
                            FROM TABLE(Pkg_Carregaimposto.fc_BuscaTributacao(
                                A.SEQPRODUTO, 'S', NVL(FD.NROTRIBUTACAO, ME.NROSEGMENTOPRINC),
                                DECODE(MD.TIPDIVISAO, 'A', 'SC', 'SN'),
                                0, ME.UF, NVL(MSG.UFPADRAOSUGPRECO, ME.UF),
                                ME.NROEMPRESA, 3, TRUNC(SYSDATE)
                            )) T
                        ), 0)
                    ) / 100)
                )
                - (
                    NVL(PE.CMULTVLRNF, 0)
                    + NVL(PE.CMULTIPI, 0)
                    - NVL(PE.CMULTCREDICMS, 0)
                    + NVL(PE.CMULTICMSST, 0)
                    + NVL(PE.CMULTDESPNF, 0)
                    + NVL(PE.CMULTDESPFORANF, 0)
                    - NVL(PE.CMULTDCTOFORANF, 0)
                    - NVL(PE.CMULTCREDPIS, 0)
                    - NVL(PE.CMULTCREDCOFINS, 0)
                    - NVL(CV.VLRUNITVERBA, NVL(PE.CMULTVLRVERBA, 0))
                )
            ) / NVL(NULLIF(SEG.PRECOVALIDPROMOC, 0), SEG.PRECOVALIDNORMAL) * 100
        )
    , 2)                                           AS MARGEM_REALIZADA

FROM MAP_PRODUTO A
JOIN MRL_PRODUTOEMPRESA PE
  ON PE.SEQPRODUTO = A.SEQPRODUTO
JOIN MAX_EMPRESA ME
  ON ME.NROEMPRESA = PE.NROEMPRESA
JOIN MAX_DIVISAO MD
  ON MD.NRODIVISAO = ME.NRODIVISAO
LEFT JOIN MAP_FAMDIVISAO FD
  ON FD.SEQFAMILIA = A.SEQFAMILIA
 AND FD.NRODIVISAO = ME.NRODIVISAO
LEFT JOIN MAD_SEGMENTO MSG
  ON MSG.NROSEGMENTO = ME.NROSEGMENTOPRINC
LEFT JOIN MAD_FAMSEGMENTO FS
  ON FS.SEQFAMILIA = A.SEQFAMILIA
 AND FS.NROSEGMENTO = ME.NROSEGMENTOPRINC
LEFT JOIN (
    SELECT S.SEQPRODUTO, S.NROEMPRESA, S.QTDEMBALAGEM,
        MAX(ROUND(NVL(NULLIF(S.PRECOVALIDPROMOC, 0), S.PRECOVALIDNORMAL), 2)) AS PRECOVALIDPROMOC,
        MAX(ROUND(NVL(S.PRECOVALIDNORMAL, 0), 2))                             AS PRECOVALIDNORMAL
    FROM MRL_PRODEMPSEG S
    GROUP BY S.SEQPRODUTO, S.NROEMPRESA, S.QTDEMBALAGEM
) SEG ON SEG.SEQPRODUTO = A.SEQPRODUTO
     AND SEG.NROEMPRESA = ME.NROEMPRESA
     AND SEG.QTDEMBALAGEM = NVL(FS.PADRAOEMBVENDA, 1)
LEFT JOIN (
    SELECT CV2.SEQPRODUTO, CV2.NROEMPRESA,
        SUM(CV2.VLRUNITVERBA) AS VLRUNITVERBA
    FROM MRL_CUSTOVERBA CV2
    WHERE CV2.STATUSVERBA = 'A'
      AND TRUNC(SYSDATE) BETWEEN CV2.DTAINICIAL AND CV2.DTAFINAL
    GROUP BY CV2.SEQPRODUTO, CV2.NROEMPRESA
) CV ON CV.SEQPRODUTO = A.SEQPRODUTO
    AND CV.NROEMPRESA = PE.NROEMPRESA
WHERE PE.NROEMPRESA IN (1,2,3,4,5,6,7,8,11,12,13,14,15,17,18)
  AND (NVL(:NR1, 0) = 0 OR PE.NROEMPRESA = :NR1)
  AND (NVL(:NR2, 0) = 0 OR A.SEQPRODUTO = :NR2)

ORDER BY ME.NROEMPRESA, A.SEQPRODUTO
