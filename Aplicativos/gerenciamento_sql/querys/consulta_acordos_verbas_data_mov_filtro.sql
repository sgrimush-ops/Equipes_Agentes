SELECT * FROM (
    WITH CTE_TITULOS_ACORDO AS (
        SELECT /*+ MATERIALIZE */ DISTINCT
            NROACORDO,
            NROEMPRESA,
            SEQTITULO,
            OBRIGDIREITO,
            ABERTOQUITADO,
            VLRPAGO,
            DTAVENCIMENTO,
            DTAQUITACAO
        FROM (
            SELECT
                TR.NROACORDO,
                NVL(TR.NROEMPRACORDOPROMOC, T.NROEMPRESA) AS NROEMPRESA,
                T.SEQTITULO,
                T.OBRIGDIREITO,
                T.ABERTOQUITADO,
                NVL(T.VLRPAGO, 0) AS VLRPAGO,
                T.DTAVENCIMENTO,
                T.DTAQUITACAO
            FROM FI_TITULO T
            INNER JOIN MSU_ACORDOTITULORECEB TR
                ON TR.LINKERP = T.SEQTITULO
               AND T.NROEMPRESA = NVL(TR.NROEMPRACORDOPROMOC, T.NROEMPRESA)
            WHERE T.SITUACAO != 'C'
              AND (
                    NVL(TRIM(:LT4), '0') IN ('0', 'TODOS')
                    OR INSTR(',' || UPPER(REPLACE(:LT4, ' ', '')) || ',', ',' || UPPER(TRIM(T.CODESPECIE)) || ',') > 0
              )

            UNION

            SELECT
                TR.NROACORDO,
                NVL(TR.NROEMPRACORDOPROMOC, T.NROEMPRESA) AS NROEMPRESA,
                T.SEQTITULO,
                T.OBRIGDIREITO,
                T.ABERTOQUITADO,
                NVL(T.VLRPAGO, 0) AS VLRPAGO,
                T.DTAVENCIMENTO,
                T.DTAQUITACAO
            FROM FI_TITULO T
            INNER JOIN MSU_ACORDOTITULORECEB TR
                ON TR.NUMERONF = T.NRODOCUMENTO
               AND TR.SEQPESSOA = T.SEQPESSOA
               AND T.NROEMPRESA = NVL(TR.NROEMPRACORDOPROMOC, T.NROEMPRESA)
            WHERE T.SITUACAO != 'C'
              AND T.OBRIGDIREITO = 'D'
              AND (
                    NVL(TRIM(:LT4), '0') IN ('0', 'TODOS')
                    OR INSTR(',' || UPPER(REPLACE(:LT4, ' ', '')) || ',', ',' || UPPER(TRIM(T.CODESPECIE)) || ',') > 0
              )

            UNION

            SELECT
                CC.NROACORDO,
                NVL(CC.NROEMPRESAACORDO, T.NROEMPRESA) AS NROEMPRESA,
                T.SEQTITULO,
                T.OBRIGDIREITO,
                T.ABERTOQUITADO,
                NVL(T.VLRPAGO, 0) AS VLRPAGO,
                T.DTAVENCIMENTO,
                T.DTAQUITACAO
            FROM FI_TITULO T
            INNER JOIN MSU_CCACORDOPROMOC CC
                ON CC.SEQTITULO = T.SEQTITULO
               AND T.NROEMPRESA = NVL(CC.NROEMPRESAACORDO, T.NROEMPRESA)
            WHERE CC.SEQTITULO IS NOT NULL
              AND T.SITUACAO != 'C'
              AND (
                    NVL(TRIM(:LT4), '0') IN ('0', 'TODOS')
                    OR INSTR(',' || UPPER(REPLACE(:LT4, ' ', '')) || ',', ',' || UPPER(TRIM(T.CODESPECIE)) || ',') > 0
              )

            UNION

            SELECT
                CD.NROACORDO,
                NVL(CD.NROEMPRESA, T.NROEMPRESA) AS NROEMPRESA,
                T.SEQTITULO,
                T.OBRIGDIREITO,
                T.ABERTOQUITADO,
                NVL(T.VLRPAGO, 0) AS VLRPAGO,
                T.DTAVENCIMENTO,
                T.DTAQUITACAO
            FROM FI_TITULO T
            INNER JOIN MSU_CCDIVIDA CD
                ON CD.SEQTITULO = T.SEQTITULO
               AND T.NROEMPRESA = NVL(CD.NROEMPRESA, T.NROEMPRESA)
            WHERE CD.SEQTITULO IS NOT NULL
              AND T.SITUACAO != 'C'
              AND (
                    NVL(TRIM(:LT4), '0') IN ('0', 'TODOS')
                    OR INSTR(',' || UPPER(REPLACE(:LT4, ' ', '')) || ',', ',' || UPPER(TRIM(T.CODESPECIE)) || ',') > 0
              )

            UNION

            SELECT
                A.NROACORDO,
                A.NROEMPRESA,
                T.SEQTITULO,
                T.OBRIGDIREITO,
                T.ABERTOQUITADO,
                NVL(T.VLRPAGO, 0) AS VLRPAGO,
                T.DTAVENCIMENTO,
                T.DTAQUITACAO
            FROM MSU_ACORDOPROMOC A
            INNER JOIN FI_TITOPERACAO TOA
                ON TOA.NROPROCESSO = A.SEQPROCESSO
               AND TOA.USUCANCELOU IS NULL
            INNER JOIN FI_TITULO T
                ON T.SEQTITULO = TOA.SEQTITULO
               AND T.NROEMPRESA = A.NROEMPRESA
            WHERE T.SITUACAO != 'C'
              AND (
                    NVL(TRIM(:LT4), '0') IN ('0', 'TODOS')
                    OR INSTR(',' || UPPER(REPLACE(:LT4, ' ', '')) || ',', ',' || UPPER(TRIM(T.CODESPECIE)) || ',') > 0
              )

            UNION

            SELECT
                A.NROACORDO,
                A.NROEMPRESA,
                T.SEQTITULO,
                T.OBRIGDIREITO,
                T.ABERTOQUITADO,
                NVL(T.VLRPAGO, 0) AS VLRPAGO,
                T.DTAVENCIMENTO,
                T.DTAQUITACAO
            FROM FI_TITULO T
            INNER JOIN MSU_ACORDOPROMOC A
                ON A.SEQFORNECEDOR = T.SEQPESSOA
               AND T.NROEMPRESA = A.NROEMPRESA
               AND (
                    T.NRODOCUMENTO = A.NROACORDO
                    OR T.NROTITULO = A.NROACORDO
                    OR (A.SEQPROCESSO IS NOT NULL AND (T.NRODOCUMENTO = A.SEQPROCESSO OR T.NROTITULO = A.SEQPROCESSO))
               )
            WHERE T.SITUACAO != 'C'
              AND T.OBRIGDIREITO = 'D'
              AND (
                    T.SERIEDOC IN ('ACO', 'ACR', 'VRB', 'VER', 'BON', 'DEV')
                    OR T.CODESPECIE IN (
                        'DESPRE',
                        'VERBA',
                        'ACORDO',
                        'ACRCIM',
                        'ACRCOM',
                        'ACRINT',
                        'ACRLOG',
                        'ACRMKT',
                        'ACRPRE',
                        'ACRTRO',
                        'DEVREC',
                        'BONIF',
                        'VEXTRA'
                    )
              )
              AND (
                    NVL(TRIM(:LT4), '0') IN ('0', 'TODOS')
                    OR INSTR(',' || UPPER(REPLACE(:LT4, ' ', '')) || ',', ',' || UPPER(TRIM(T.CODESPECIE)) || ',') > 0
              )
        )
    ),

    CTE_OPERACOES_TITULO AS (
        SELECT /*+ MATERIALIZE */
            O.SEQTITULO,
            MAX(O.DTAOPERACAO) AS MAX_DTAOPERACAO,
            MAX(NVL(O.DTAHORAALTERACAO, O.DTAALTERACAO)) AS MAX_DTAHORAALTERACAO,
            MAX(O.USUALTERACAO) KEEP (
                DENSE_RANK LAST 
                ORDER BY NVL(O.DTAHORAALTERACAO, O.DTAALTERACAO) NULLS FIRST, O.SEQTITOPERACAO
            ) AS USUALTERACAO,
            MAX(O.VLROPERACAO) KEEP (
                DENSE_RANK LAST 
                ORDER BY NVL(O.DTAHORAALTERACAO, O.DTAALTERACAO) NULLS FIRST, O.SEQTITOPERACAO
            ) AS VLROPERACAO
        FROM FI_TITOPERACAO O
        INNER JOIN CTE_TITULOS_ACORDO TA
            ON TA.SEQTITULO = O.SEQTITULO
        WHERE O.OPCANCELADA IS NULL
          AND O.USUCANCELOU IS NULL
        GROUP BY
            O.SEQTITULO
    ),

    CTE_TITULOS_GLOBAL AS (
        SELECT /*+ MATERIALIZE */
            TA.NROACORDO,
            TA.NROEMPRESA,
            TA.SEQTITULO,
            DENSE_RANK() OVER (
                PARTITION BY TA.NROACORDO, TA.NROEMPRESA 
                ORDER BY TA.DTAVENCIMENTO, TA.SEQTITULO
            ) AS NROPARCELA,
            COUNT(*) OVER (
                PARTITION BY TA.NROACORDO, TA.NROEMPRESA
            ) AS QTDPARCELA,
            TA.ABERTOQUITADO,
            NVL(TA.VLRPAGO, 0) AS VLRPAGO,
            TA.DTAVENCIMENTO,
            TA.DTAQUITACAO,
            CASE
                WHEN TA.OBRIGDIREITO = 'D' THEN 'Direito'
                WHEN TA.OBRIGDIREITO = 'O' THEN 'Obrigação'
                ELSE TA.OBRIGDIREITO
            END AS DIREITO_OBRIGACAO,
            OP.MAX_DTAOPERACAO,
            NVL(OP.MAX_DTAHORAALTERACAO, CAST(TA.DTAQUITACAO AS DATE)) AS DTA_ULTIMA_ALTERACAO,
            NVL(OP.USUALTERACAO, CASE WHEN TA.DTAQUITACAO IS NOT NULL THEN 'QUITADO' END) AS USU_ULTIMA_ALTERACAO,
            NVL(OP.VLROPERACAO, TA.VLRPAGO) AS VLR_ULTIMA_OPERACAO,
            CASE 
                WHEN (TA.DTAQUITACAO IS NOT NULL AND TRUNC(TA.DTAQUITACAO) BETWEEN :DT1 AND :DT2)
                  OR (OP.MAX_DTAOPERACAO IS NOT NULL AND TRUNC(OP.MAX_DTAOPERACAO) BETWEEN :DT1 AND :DT2)
                  OR (OP.MAX_DTAHORAALTERACAO IS NOT NULL AND TRUNC(OP.MAX_DTAHORAALTERACAO) BETWEEN :DT1 AND :DT2)
                THEN 1 ELSE 0 
            END AS TEVE_MOV_QUITACAO_PERIODO
        FROM CTE_TITULOS_ACORDO TA
        LEFT JOIN CTE_OPERACOES_TITULO OP
            ON OP.SEQTITULO = TA.SEQTITULO
    ),

    CTE_ACORDO_RESUMO_GLOBAL AS (
        SELECT /*+ MATERIALIZE */
            TG.NROACORDO,
            TG.NROEMPRESA,
            COUNT(*) AS TOTAL_TITULOS,
            SUM(CASE WHEN TG.ABERTOQUITADO = 'A' THEN 1 ELSE 0 END) AS TITULOS_ABERTOS,
            SUM(CASE WHEN TG.ABERTOQUITADO = 'Q' THEN 1 ELSE 0 END) AS TITULOS_QUITADOS,
            NVL(SUM(TG.VLRPAGO), 0) AS GLOBAL_VLR_QUITADO,
            MIN(CASE WHEN TG.ABERTOQUITADO = 'A' THEN TG.DTAVENCIMENTO END) AS MIN_DTAVENCIMENTO_ABERTO,
            MAX(TG.DTAVENCIMENTO) AS MAX_DTAVENCIMENTO,
            MAX(TG.DTAQUITACAO) AS MAX_DTAQUITACAO,
            MAX(TG.DIREITO_OBRIGACAO) AS DIREITO_OBRIGACAO
        FROM CTE_TITULOS_GLOBAL TG
        GROUP BY
            TG.NROACORDO,
            TG.NROEMPRESA
    ),

    CTE_VALORES_BRUTOS AS (
        SELECT /*+ MATERIALIZE */
            A.NROEMPRESA,
            A.NROACORDO,
            TG.SEQTITULO,
            TG.NROPARCELA,
            TG.QTDPARCELA,
            AC.SEQPROCESSO,
            B.SEQPESSOA AS SEQFORNECEDOR,
            B.NOMERAZAO,
            A.DESCACORDO,
            A.DTAEMISSAO,
            C.APELIDO,
            MAX(A.STATUS) AS STATUS,
            A.TIPOACORDO,
            A.SEQPRODUTO,

            NVL(
                (
                    SELECT SUM(VC.QTDUTILIZADAVERBA)
                    FROM MRLV_VERBACONSUMIDA VC
                    WHERE VC.APPORIGEM = 2
                      AND VC.STATUSVERBA != 'R'
                      AND VC.NROACORDO = A.NROACORDO
                      AND VC.NROEMPRESAACORDO = A.NROEMPRESA
                      AND VC.SEQPRODUTO = A.SEQPRODUTO
                ),
                MAX(A.QTDUTILIZADAVERBA)
            ) AS QTDUTILIZADAVERBA,

            A.DTAFINALVERBA,
            NVL(TG.DTAVENCIMENTO, RG.MIN_DTAVENCIMENTO_ABERTO) AS DTAVENCIMENTO,
            NVL(TG.DTAQUITACAO, TG.DTA_ULTIMA_ALTERACAO) AS ULTIMO_RECEBIMENTO,
            MAX(SUBSTR(A.NUMERONF, 1, 250)) AS NUMERONF,
            A.NROPEDIDOSUPRIM,
            NVL(TG.DIREITO_OBRIGACAO, RG.DIREITO_OBRIGACAO) AS DIREITO_OBRIGACAO,

            CASE 
                WHEN NVL(RG.TOTAL_TITULOS, 0) > 0 THEN 
                    CASE 
                        WHEN NVL(RG.TITULOS_ABERTOS, 0) > 0 THEN 'Aberto' 
                        ELSE 'Quitado' 
                    END 
                ELSE 'Sem Título' 
            END AS ABERTO_QUITADO,

            NVL(
                MAX(A.VLRFINVENCIDO),
                MAX(fValorTitAcordo(
                    A.NROACORDO,
                    A.NROEMPRESA,
                    B.SEQPESSOA,
                    'V'
                ))
            ) AS RAW_VLRFINVENCIDO,

            NVL(
                MAX(A.VLRFINAVENCER),
                MAX(fValorTitAcordo(
                    A.NROACORDO,
                    A.NROEMPRESA,
                    B.SEQPESSOA,
                    'A'
                ))
            ) AS RAW_VLRFINAVENCER,

            A.VLRACORDO AS RAW_VLRACORDO,
            NVL(RG.GLOBAL_VLR_QUITADO, 0) AS RAW_VLRQUITADO,

            NVL(
                (
                    SELECT SUM(VC.VLRUTILIZADOVERBA)
                    FROM MRLV_VERBACONSUMIDA VC
                    WHERE VC.APPORIGEM = 2
                      AND VC.STATUSVERBA != 'R'
                      AND VC.NROACORDO = A.NROACORDO
                      AND VC.NROEMPRESAACORDO = A.NROEMPRESA
                      AND VC.SEQPRODUTO = A.SEQPRODUTO
                ),
                MAX(A.VLRUTILPROD)
            ) AS VLRUTILPROD,

            GREATEST(
                NVL(
                    (
                        SELECT COUNT(*)
                        FROM MSU_ACORDOPROMOCPARCELA P
                        WHERE P.NROACORDO = A.NROACORDO
                          AND P.NROEMPRESA = A.NROEMPRESA
                    ),
                    0
                ),
                NVL(RG.TOTAL_TITULOS, NVL(TG.QTDPARCELA, 1))
            ) AS TOTAL_PARCELAS,

            NVL(RG.TITULOS_QUITADOS, 0) AS PARCELAS_PAGAS,

            GREATEST(
                0,
                GREATEST(
                    NVL(
                        (
                            SELECT COUNT(*)
                            FROM MSU_ACORDOPROMOCPARCELA P
                            WHERE P.NROACORDO = A.NROACORDO
                              AND P.NROEMPRESA = A.NROEMPRESA
                        ),
                        0
                    ),
                    NVL(RG.TOTAL_TITULOS, NVL(TG.QTDPARCELA, 1))
                )
                -
                NVL(RG.TITULOS_QUITADOS, 0)
            ) AS PARCELAS_PENDENTES,

            CASE
                WHEN A.SEQPRODUTO IS NOT NULL
                 AND NVL(MAX(A.VLRUTILPROD), 0) > 0
                THEN
                    NVL(MAX(A.VLRUTILPROD), 0)
                ELSE
                    A.VLRACORDO
            END AS PROD_PESO,

            TG.USU_ULTIMA_ALTERACAO,
            TG.DTA_ULTIMA_ALTERACAO,
            TG.VLR_ULTIMA_OPERACAO,
            MAX(AC.RESPACORDONOME) AS RESPONSAVEL_ACORDO,
            MAX(NVL(DBMS_LOB.SUBSTR(AC.REFACORDOOBS, 4000), AC.OBSACORDO)) AS OBSERVACAO_CONTRATO

        FROM MSUV_ACORDOPROMOC A
        INNER JOIN GE_PESSOA B
            ON B.SEQPESSOA = A.SEQFORNECEDOR
        INNER JOIN MAX_COMPRADOR C
            ON C.SEQCOMPRADOR = A.SEQCOMPRADOR
        LEFT JOIN MSU_ACORDOPROMOC AC
            ON AC.NROACORDO = A.NROACORDO
           AND AC.NROEMPRESA = A.NROEMPRESA
        INNER JOIN CTE_TITULOS_GLOBAL TG
            ON TG.NROACORDO = A.NROACORDO
           AND TG.NROEMPRESA = A.NROEMPRESA
           AND TG.TEVE_MOV_QUITACAO_PERIODO = 1
        INNER JOIN CTE_ACORDO_RESUMO_GLOBAL RG
            ON RG.NROACORDO = A.NROACORDO
           AND RG.NROEMPRESA = A.NROEMPRESA

        WHERE (
                NVL(TRIM(:LT1), '0') IN ('0', 'TODOS')
                OR INSTR(',' || UPPER(REPLACE(:LT1, ' ', '')) || ',', ',' || TO_CHAR(A.NROEMPRESA) || ',') > 0
              )
          AND (
                NVL(TRIM(:LT2), '0') = '0'
                OR INSTR(',' || UPPER(REPLACE(:LT2, ' ', '')) || ',', ',' || TO_CHAR(A.STATUS) || ',') = 0
              )
          AND (NVL(TO_NUMBER(:NR1), 0) = 0 OR A.NROACORDO = TO_NUMBER(:NR1))

          AND (
                NVL(TRIM(:LT3), '0') IN ('0', 'TODOS')
                OR INSTR(',' || UPPER(REPLACE(:LT3, ' ', '')) || ',', ',' || UPPER(TRIM(TG.USU_ULTIMA_ALTERACAO)) || ',') > 0
          )

          AND (
                NVL(TRIM(:LS1), '0 - TODOS')
                IN ('0 - TODOS', 'TODOS', '0')
                OR (
                    INSTR(:LS1, ' - ') > 0
                    AND C.SEQCOMPRADOR =
                        TO_NUMBER(
                            SUBSTR(
                                :LS1,
                                1,
                                INSTR(:LS1, ' - ') - 1
                            )
                        )
                )
          )

          AND (
                NVL(TRIM(:LS2), '0 - TODOS')
                IN ('0 - TODOS', 'TODOS', '0')
                OR (
                    INSTR(:LS2, ' - ') > 0
                    AND B.SEQPESSOA =
                        TO_NUMBER(
                            SUBSTR(
                                :LS2,
                                1,
                                INSTR(:LS2, ' - ') - 1
                            )
                        )
                )
          )

          AND (
                :LS4 = ' TODAS AS REDES'
                OR NVL(TRIM(:LS4), '0') IN ('0', 'TODOS', 'TODAS AS REDES')
                OR EXISTS (
                    SELECT 1
                    FROM GE_REDEPESSOA RP
                    INNER JOIN GE_REDE R
                        ON R.SEQREDE = RP.SEQREDE
                    WHERE RP.SEQPESSOA = B.SEQPESSOA
                      AND (R.DESCRICAO = :LS4 OR UPPER(TRIM(R.DESCRICAO)) = UPPER(TRIM(:LS4)))
                )
          )

        GROUP BY
            A.NROEMPRESA,
            A.NROACORDO,
            TG.SEQTITULO,
            TG.NROPARCELA,
            TG.QTDPARCELA,
            TG.DTAVENCIMENTO,
            TG.DTAQUITACAO,
            TG.DIREITO_OBRIGACAO,
            TG.USU_ULTIMA_ALTERACAO,
            TG.DTA_ULTIMA_ALTERACAO,
            TG.VLR_ULTIMA_OPERACAO,
            RG.TOTAL_TITULOS,
            RG.TITULOS_ABERTOS,
            RG.TITULOS_QUITADOS,
            RG.GLOBAL_VLR_QUITADO,
            RG.MIN_DTAVENCIMENTO_ABERTO,
            RG.DIREITO_OBRIGACAO,
            AC.SEQPROCESSO,
            B.SEQPESSOA,
            B.NOMERAZAO,
            A.DESCACORDO,
            A.DTAEMISSAO,
            C.APELIDO,
            A.TIPOACORDO,
            A.SEQPRODUTO,
            A.DTAFINALVERBA,
            A.NROPEDIDOSUPRIM,
            A.VLRACORDO
    ),

    CTE_ACORDO_HEADER AS (
        SELECT /*+ MATERIALIZE */
            NROEMPRESA,
            NROACORDO,
            MAX(RAW_VLRQUITADO) AS ACORDO_RAW_QUITADO,
            MAX(RAW_VLRFINVENCIDO) AS ACORDO_RAW_VENCIDO,
            MAX(RAW_VLRFINAVENCER) AS ACORDO_RAW_AVENCER,
            SUM(PROD_PESO) AS ACORDO_SUM_PESO,

            GREATEST(
                CASE
                    WHEN COUNT(DISTINCT SEQPRODUTO) > 1
                     AND SUM(PROD_PESO) > 0
                    THEN SUM(PROD_PESO)
                    ELSE MAX(RAW_VLRACORDO)
                END,
                NVL(MAX(RAW_VLRQUITADO), 0)
                + NVL(MAX(RAW_VLRFINVENCIDO), 0)
                + NVL(MAX(RAW_VLRFINAVENCER), 0),
                NVL(MAX(RAW_VLRFINVENCIDO), 0)
                + NVL(MAX(RAW_VLRFINAVENCER), 0)
            ) AS ACORDO_VLR_TOTAL
        FROM CTE_VALORES_BRUTOS
        GROUP BY
            NROEMPRESA,
            NROACORDO
    ),

    CTE_ACORDO_FINANCEIRO AS (
        SELECT /*+ MATERIALIZE */
            H.NROEMPRESA,
            H.NROACORDO,
            H.ACORDO_VLR_TOTAL AS VLR_TOTAL_ACORDO,
            H.ACORDO_SUM_PESO,

            CASE
                WHEN NVL(H.ACORDO_RAW_QUITADO, 0) > 0
                THEN LEAST(H.ACORDO_VLR_TOTAL, H.ACORDO_RAW_QUITADO)
                ELSE 0
            END AS ACORDO_VLR_QUITADO,

            GREATEST(
                0,
                H.ACORDO_VLR_TOTAL - LEAST(H.ACORDO_VLR_TOTAL, NVL(H.ACORDO_RAW_QUITADO, 0))
            ) AS ACORDO_VLR_ABERTO,

            LEAST(
                GREATEST(
                    0,
                    H.ACORDO_VLR_TOTAL - LEAST(H.ACORDO_VLR_TOTAL, NVL(H.ACORDO_RAW_QUITADO, 0))
                ),
                NVL(H.ACORDO_RAW_VENCIDO, 0)
            ) AS ACORDO_VLR_VENCIDO

        FROM CTE_ACORDO_HEADER H
    ),

    CTE_VALORES_PRE AS (
        SELECT
            B.NROEMPRESA,
            B.NROACORDO,
            B.SEQTITULO,
            B.NROPARCELA,
            B.QTDPARCELA,
            B.SEQPROCESSO,
            B.SEQFORNECEDOR,
            B.NOMERAZAO,
            B.DESCACORDO,
            B.DTAEMISSAO,
            B.APELIDO,
            B.STATUS,
            B.TIPOACORDO,
            B.SEQPRODUTO,
            B.QTDUTILIZADAVERBA,
            B.DTAFINALVERBA,
            B.DTAVENCIMENTO,
            B.ULTIMO_RECEBIMENTO,
            B.NUMERONF,
            B.NROPEDIDOSUPRIM,
            B.DIREITO_OBRIGACAO,
            B.ABERTO_QUITADO,

            F.VLR_TOTAL_ACORDO AS VLRACORDO,
            F.ACORDO_VLR_QUITADO AS CALC_VLRQUITADO,

            CASE
                WHEN F.ACORDO_SUM_PESO > 0
                THEN
                    ROUND(F.VLR_TOTAL_ACORDO * (B.PROD_PESO / F.ACORDO_SUM_PESO), 2)
                    -
                    ROUND(F.ACORDO_VLR_QUITADO * (B.PROD_PESO / F.ACORDO_SUM_PESO), 2)
                ELSE F.ACORDO_VLR_ABERTO
            END AS CALC_VLR_EM_ABERTO,

            CASE
                WHEN F.ACORDO_SUM_PESO > 0
                THEN
                    LEAST(
                        ROUND(F.VLR_TOTAL_ACORDO * (B.PROD_PESO / F.ACORDO_SUM_PESO), 2) - ROUND(F.ACORDO_VLR_QUITADO * (B.PROD_PESO / F.ACORDO_SUM_PESO), 2),
                        ROUND(F.ACORDO_VLR_VENCIDO * (B.PROD_PESO / F.ACORDO_SUM_PESO), 2)
                    )
                ELSE
                    LEAST(F.ACORDO_VLR_ABERTO, F.ACORDO_VLR_VENCIDO)
            END AS CALC_VLRFINVENCIDO,

            B.VLRUTILPROD,
            B.TOTAL_PARCELAS,
            B.PARCELAS_PAGAS,
            B.PARCELAS_PENDENTES,
            B.USU_ULTIMA_ALTERACAO,
            B.DTA_ULTIMA_ALTERACAO,
            B.VLR_ULTIMA_OPERACAO,
            B.RESPONSAVEL_ACORDO,
            B.OBSERVACAO_CONTRATO

        FROM CTE_VALORES_BRUTOS B
        INNER JOIN CTE_ACORDO_FINANCEIRO F
            ON F.NROEMPRESA = B.NROEMPRESA
           AND F.NROACORDO = B.NROACORDO
    ),

    CTE_BASE AS (
        SELECT DISTINCT
            NROEMPRESA,
            NROACORDO,
            SEQTITULO,
            NROPARCELA,
            QTDPARCELA,
            SEQPROCESSO,
            SEQFORNECEDOR,
            NOMERAZAO,
            DESCACORDO,
            DTAEMISSAO,
            APELIDO,
            STATUS,
            TIPOACORDO,
            SEQPRODUTO,
            QTDUTILIZADAVERBA,
            DTAFINALVERBA,
            DTAVENCIMENTO,
            ULTIMO_RECEBIMENTO,
            NUMERONF,
            NROPEDIDOSUPRIM,
            DIREITO_OBRIGACAO,
            ABERTO_QUITADO,

            CALC_VLRFINVENCIDO AS VLRFINVENCIDO,
            VLRACORDO,
            CALC_VLR_EM_ABERTO AS VLR_EM_ABERTO,
            CALC_VLRQUITADO AS VLR_JA_QUITADO,
            VLRUTILPROD,

            TOTAL_PARCELAS,
            PARCELAS_PAGAS,
            PARCELAS_PENDENTES,
            USU_ULTIMA_ALTERACAO,
            DTA_ULTIMA_ALTERACAO,
            VLR_ULTIMA_OPERACAO,
            RESPONSAVEL_ACORDO,
            OBSERVACAO_CONTRATO

        FROM CTE_VALORES_PRE
    ),

    CTE_CLASSIFICADA_PRE AS (
        SELECT /*+ MATERIALIZE */
            X.*,

            CASE
                WHEN X.STATUS = 1 THEN 'Aprovado'
                WHEN X.STATUS = 2 THEN 'Cancelado'
                WHEN X.STATUS = 3 THEN 'Concluido'
                WHEN X.STATUS = 4 THEN 'Interrompido'
                ELSE 'Pendente'
            END AS STATUS_ACORDO,

            CASE
                WHEN X.STATUS = 2 THEN 'Cancelado'
                WHEN NVL(X.TOTAL_PARCELAS, 0) > 0 THEN 'Financeiro'
                ELSE 'Pendente'
            END AS SITUACAO_ACORDO,

            CASE
                WHEN NVL(X.VLR_EM_ABERTO, 0) > 0
                THEN X.DTAVENCIMENTO
                ELSE NULL
            END AS VENCIMENTO_EM_ABERTO

        FROM CTE_BASE X
    ),

    CTE_CLASSIFICADA AS (
        SELECT /*+ MATERIALIZE */
            C.*
        FROM CTE_CLASSIFICADA_PRE C
        WHERE (
            NVL(TRIM(:LS3), '0 - TODOS') IN ('0 - TODOS', 'TODOS', '0')
            OR (
                (SUBSTR(TRIM(:LS3), 1, 1) = '1' OR INSTR(UPPER(:LS3), 'QUITADO') > 0)
                AND C.ABERTO_QUITADO = 'Quitado'
            )
            OR (
                (SUBSTR(TRIM(:LS3), 1, 1) = '2' OR (SUBSTR(TRIM(:LS3), 1, 1) = '3' AND INSTR(UPPER(:LS3), 'ABERTO') > 0))
                AND C.ABERTO_QUITADO = 'Aberto'
            )
            OR (
                (SUBSTR(TRIM(:LS3), 1, 1) = '4' OR INSTR(UPPER(:LS3), 'PARCELA') > 0 OR INSTR(UPPER(:LS3), 'TITULO') > 0 OR INSTR(UPPER(:LS3), 'PENDENTE') > 0)
                AND C.ABERTO_QUITADO = 'Sem Título'
            )
            OR (
                (SUBSTR(TRIM(:LS3), 1, 1) = '5' OR INSTR(UPPER(:LS3), 'CANCEL') > 0)
                AND C.STATUS_ACORDO = 'Cancelado'
            )
            OR C.ABERTO_QUITADO = TRIM(:LS3)
        )
    ),

    CTE_TOTAIS_VALORES AS (
        SELECT
            NVL(SUM(VLRACORDO), 0) AS TOTAL_VLRACORDO,
            NVL(SUM(VLRFINVENCIDO), 0) AS TOTAL_VLRFINVENCIDO,
            NVL(SUM(VLRUTILPROD), 0) AS TOTAL_VLRUTILPROD,
            NVL(SUM(VLR_JA_QUITADO), 0) AS TOTAL_VLR_QUITADO,
            NVL(SUM(VLR_ULTIMA_OPERACAO), 0) AS TOTAL_VLR_OPERACAO
        FROM (
            SELECT
                NROACORDO,
                NROEMPRESA,
                MAX(VLRACORDO) AS VLRACORDO,
                MAX(VLRFINVENCIDO) AS VLRFINVENCIDO,
                MAX(VLRUTILPROD) AS VLRUTILPROD,
                MAX(VLR_JA_QUITADO) AS VLR_JA_QUITADO,
                SUM(VLR_ULTIMA_OPERACAO) AS VLR_ULTIMA_OPERACAO
            FROM CTE_CLASSIFICADA
            GROUP BY
                NROACORDO,
                NROEMPRESA
        )
    ),

    CTE_TOTAIS_PARCELAS AS (
        SELECT
            NVL(SUM(TOTAL_PARCELAS), 0) AS TOTAL_PARC_GERADAS,
            NVL(SUM(PARCELAS_PAGAS), 0) AS TOTAL_PARC_PAGAS,
            NVL(SUM(PARCELAS_PENDENTES), 0) AS TOTAL_PARC_PENDENTES
        FROM (
            SELECT
                NROACORDO,
                NROEMPRESA,
                MAX(TOTAL_PARCELAS) AS TOTAL_PARCELAS,
                MAX(PARCELAS_PAGAS) AS PARCELAS_PAGAS,
                MAX(PARCELAS_PENDENTES) AS PARCELAS_PENDENTES
            FROM CTE_CLASSIFICADA
            GROUP BY
                NROACORDO,
                NROEMPRESA
        )
    ),

    CTE_TOTAIS AS (
        SELECT
            V.TOTAL_VLRACORDO,
            V.TOTAL_VLRFINVENCIDO,
            V.TOTAL_VLRUTILPROD,
            V.TOTAL_VLR_QUITADO,
            V.TOTAL_VLR_OPERACAO,
            P.TOTAL_PARC_GERADAS,
            P.TOTAL_PARC_PAGAS,
            P.TOTAL_PARC_PENDENTES
        FROM CTE_TOTAIS_VALORES V
        CROSS JOIN CTE_TOTAIS_PARCELAS P
    )

    SELECT
        CODIGO_EMPRESA,
        NUMERO_ACORDO,
        NUMERO_PROCESSO,
        CODIGO_FORNECEDOR,
        FORNECEDOR,
        DESCRICAO_ACORDO,
        DATA_EMISSAO,
        COMPRADOR,
        STATUS_ACORDO,
        SITUACAO_ACORDO,
        DIREITO_OBRIGACAO,
        ABERTO_QUITADO,
        TIPO_ACORDO,
        CODIGO_PRODUTO,
        QTD_UTILIZADA_VERBA,
        DATA_FINAL_VERBA,
        VENCIMENTO_EM_ABERTO,
        ULTIMO_RECEBIMENTO,
        NUMERO_NF,
        NUMERO_PEDIDO_SUPRIMENTO,
        VALOR_ACORDO,
        VLR_FIN_VENCIDO,
        VLR_JA_QUITADO,
        VALOR_UTILIZADO_PRODUTO,
        TOTAL_PARCELAS,
        PARCELAS_PAGAS,
        PARCELAS_PENDENTES,
        VALOR_ULTIMO_PAGAMENTO,
        USUARIO_DATA_HORA_ALTERACAO,
        RESPONSAVEL_ACORDO,
        OBSERVACAO_CONTRATO
    FROM (
        SELECT
            1 AS ORDEM_LINHA,
            X.NROACORDO AS ORDEM_ACORDO,
            NVL(X.NROPARCELA, 1) AS ORDEM_PARCELA,
            TO_CHAR(X.NROEMPRESA) AS CODIGO_EMPRESA,
            TO_CHAR(X.NROACORDO) AS NUMERO_ACORDO,
            TO_CHAR(X.SEQPROCESSO) AS NUMERO_PROCESSO,
            TO_CHAR(X.SEQFORNECEDOR) AS CODIGO_FORNECEDOR,
            X.NOMERAZAO AS FORNECEDOR,
            X.DESCACORDO AS DESCRICAO_ACORDO,
            TO_CHAR(X.DTAEMISSAO, 'DD/MM/YYYY') AS DATA_EMISSAO,
            X.APELIDO AS COMPRADOR,
            X.STATUS_ACORDO AS STATUS_ACORDO,
            X.SITUACAO_ACORDO AS SITUACAO_ACORDO,
            NVL(X.DIREITO_OBRIGACAO, 'Sem Título') AS DIREITO_OBRIGACAO,
            NVL(X.ABERTO_QUITADO, 'Sem Título') AS ABERTO_QUITADO,
            CASE WHEN X.TIPOACORDO = 1 THEN 'VERBA EXTRA' WHEN X.TIPOACORDO = 2 THEN 'SELL-OUT' WHEN X.TIPOACORDO = 3 THEN 'SELL-IN' END AS TIPO_ACORDO,
            TO_CHAR(X.SEQPRODUTO) AS CODIGO_PRODUTO,
            TO_CHAR(X.QTDUTILIZADAVERBA) AS QTD_UTILIZADA_VERBA,
            TO_CHAR(X.DTAFINALVERBA, 'DD/MM/YYYY') AS DATA_FINAL_VERBA,
            TO_CHAR(X.VENCIMENTO_EM_ABERTO, 'DD/MM/YYYY') AS VENCIMENTO_EM_ABERTO,
            TO_CHAR(NVL(X.ULTIMO_RECEBIMENTO, X.DTA_ULTIMA_ALTERACAO), 'DD/MM/YYYY') AS ULTIMO_RECEBIMENTO,
            X.NUMERONF AS NUMERO_NF,
            TO_CHAR(X.NROPEDIDOSUPRIM) AS NUMERO_PEDIDO_SUPRIMENTO,
            'R$ ' || TO_CHAR(NVL(X.VLRACORDO, 0), 'FM999G999G990D00') AS VALOR_ACORDO,
            'R$ ' || TO_CHAR(NVL(X.VLRFINVENCIDO, 0), 'FM999G999G990D00') AS VLR_FIN_VENCIDO,
            'R$ ' || TO_CHAR(NVL(X.VLR_JA_QUITADO, 0), 'FM999G999G990D00') AS VLR_JA_QUITADO,
            'R$ ' || TO_CHAR(NVL(X.VLRUTILPROD, 0), 'FM999G999G990D00') AS VALOR_UTILIZADO_PRODUTO,
            TO_CHAR(X.TOTAL_PARCELAS) AS TOTAL_PARCELAS,
            TO_CHAR(X.PARCELAS_PAGAS) AS PARCELAS_PAGAS,
            TO_CHAR(X.PARCELAS_PENDENTES) AS PARCELAS_PENDENTES,
            'R$ ' || TO_CHAR(NVL(X.VLR_ULTIMA_OPERACAO, 0), 'FM999G999G990D00') AS VALOR_ULTIMO_PAGAMENTO,
            CASE WHEN X.USU_ULTIMA_ALTERACAO IS NOT NULL AND X.DTA_ULTIMA_ALTERACAO IS NOT NULL THEN X.USU_ULTIMA_ALTERACAO || ' - ' || TO_CHAR(X.DTA_ULTIMA_ALTERACAO, 'DD/MM/YYYY HH24:MI:SS') || CASE WHEN X.NROPARCELA IS NOT NULL THEN ' (Parc. ' || TO_CHAR(X.NROPARCELA) || NVL('/' || TO_CHAR(X.QTDPARCELA), '') || ')' ELSE '' END WHEN X.USU_ULTIMA_ALTERACAO IS NOT NULL THEN X.USU_ULTIMA_ALTERACAO || CASE WHEN X.NROPARCELA IS NOT NULL THEN ' (Parc. ' || TO_CHAR(X.NROPARCELA) || NVL('/' || TO_CHAR(X.QTDPARCELA), '') || ')' ELSE '' END WHEN X.DTA_ULTIMA_ALTERACAO IS NOT NULL THEN TO_CHAR(X.DTA_ULTIMA_ALTERACAO, 'DD/MM/YYYY HH24:MI:SS') ELSE NULL END AS USUARIO_DATA_HORA_ALTERACAO,
            X.RESPONSAVEL_ACORDO AS RESPONSAVEL_ACORDO,
            X.OBSERVACAO_CONTRATO AS OBSERVACAO_CONTRATO
        FROM CTE_CLASSIFICADA X

        UNION ALL

        SELECT
            2 AS ORDEM_LINHA,
            9999999999 AS ORDEM_ACORDO,
            9999999999 AS ORDEM_PARCELA,
            NULL AS CODIGO_EMPRESA,
            NULL AS NUMERO_ACORDO,
            NULL AS NUMERO_PROCESSO,
            NULL AS CODIGO_FORNECEDOR,
            'TOTAL GERAL ->' AS FORNECEDOR,
            NULL AS DESCRICAO_ACORDO,
            NULL AS DATA_EMISSAO,
            NULL AS COMPRADOR,
            NULL AS STATUS_ACORDO,
            NULL AS SITUACAO_ACORDO,
            NULL AS DIREITO_OBRIGACAO,
            NULL AS ABERTO_QUITADO,
            NULL AS TIPO_ACORDO,
            NULL AS CODIGO_PRODUTO,
            NULL AS QTD_UTILIZADA_VERBA,
            NULL AS DATA_FINAL_VERBA,
            NULL AS VENCIMENTO_EM_ABERTO,
            NULL AS ULTIMO_RECEBIMENTO,
            NULL AS NUMERO_NF,
            NULL AS NUMERO_PEDIDO_SUPRIMENTO,
            'R$ ' || TO_CHAR(NVL(T.TOTAL_VLRACORDO, 0), 'FM999G999G990D00') AS VALOR_ACORDO,
            'R$ ' || TO_CHAR(NVL(T.TOTAL_VLRFINVENCIDO, 0), 'FM999G999G990D00') AS VLR_FIN_VENCIDO,
            'R$ ' || TO_CHAR(NVL(T.TOTAL_VLR_QUITADO, 0), 'FM999G999G990D00') AS VLR_JA_QUITADO,
            'R$ ' || TO_CHAR(NVL(T.TOTAL_VLRUTILPROD, 0), 'FM999G999G990D00') AS VALOR_UTILIZADO_PRODUTO,
            TO_CHAR(T.TOTAL_PARC_GERADAS) AS TOTAL_PARCELAS,
            TO_CHAR(T.TOTAL_PARC_PAGAS) AS PARCELAS_PAGAS,
            TO_CHAR(T.TOTAL_PARC_PENDENTES) AS PARCELAS_PENDENTES,
            'R$ ' || TO_CHAR(NVL(T.TOTAL_VLR_OPERACAO, 0), 'FM999G999G990D00') AS VALOR_ULTIMO_PAGAMENTO,
            NULL AS USUARIO_DATA_HORA_ALTERACAO,
            NULL AS RESPONSAVEL_ACORDO,
            NULL AS OBSERVACAO_CONTRATO
        FROM CTE_TOTAIS T
    )
    ORDER BY
        ORDEM_LINHA,
        ORDEM_ACORDO,
        ORDEM_PARCELA
)
