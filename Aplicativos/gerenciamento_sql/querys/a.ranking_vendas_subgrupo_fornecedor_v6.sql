SELECT TO_CHAR(B.CODIGO_FORNECEDOR) AS COD_F,
       NVL(B.FORNECEDOR_PRINCIPAL,'SEM DESCRICAO') AS FORNECEDOR,
       DECODE(NVL(UPPER(TRIM(:LT2)),'D'),'C','CONSOLIDADO',MIN(B.COMPRADOR)) AS COMPRADOR,
       COUNT(DISTINCT B.SEQPRODUTO) AS QTD_SKU,
       'R$ ' || TO_CHAR(ROUND(SUM(B.VLR_VENDA),2),'999G999G999G990D00') AS VLR_VENDA,
       'R$ ' || TO_CHAR(ROUND(SUM(B.VLR_COMPRA),2),'999G999G999G990D00') AS VLR_COMPRA,
       'R$ ' || TO_CHAR(ROUND(SUM(B.VLR_DEVOLUCAO_COMPRA),2),'999G999G999G990D00') AS VLR_DEVOLUCAO_COMPRA,
       'R$ ' || TO_CHAR(ROUND(SUM(B.VLR_TROCA_COMPRA),2),'999G999G999G990D00') AS VLR_TROCA_COMPRA,
       'R$ ' || TO_CHAR(ROUND(SUM(B.VLR_BONIFICADO),2),'999G999G999G990D00') AS VLR_BONIFICADO,
       'R$ ' || TO_CHAR(ROUND(SUM(B.VLR_CUSTO_CD),2),'999G999G999G990D00') AS VLR_CUSTO_CD,
       'R$ ' || TO_CHAR(ROUND(SUM(B.VLR_CUSTO_LOJAS),2),'999G999G999G990D00') AS VLR_CUSTO_LOJAS,
       'R$ ' || TO_CHAR(ROUND(SUM(B.VLR_CUSTO_CD + B.VLR_CUSTO_LOJAS),2),'999G999G999G990D00') AS VLR_CUSTO_EMPRESA,
       TO_CHAR(ROUND(SUM(B.QTD_INCINERACAO_ANO),2),'999G999G999G990D00') AS QTD_INCINERACAO_ANO
  FROM (
        SELECT FP.CODIGO_FORNECEDOR,
               FP.FORNECEDOR_PRINCIPAL,
               NVL(COMP.COMPRADOR,'SEM GESTOR') AS COMPRADOR,
               A.SEQPRODUTO,
               NVL(INCI.QTD_INCINERACAO_ANO,0) AS QTD_INCINERACAO_ANO,
               NVL(VF.VLR_VENDA,0) AS VLR_VENDA,
               NVL(E.VLR_COMPRADO,0) AS VLR_COMPRA,
               NVL(DEV.VLR_DEVOLUCAO_COMPRA,0) AS VLR_DEVOLUCAO_COMPRA,
               NVL(DEV.VLR_TROCA_COMPRA,0) AS VLR_TROCA_COMPRA,
               NVL(E.VLR_BONIFICADO,0) AS VLR_BONIFICADO,
               NVL(CS.VLR_CUSTO_ESTOQUE_CD,0) AS VLR_CUSTO_CD,
               NVL(CS.VLR_CUSTO_ESTOQUE_LOJAS,0) AS VLR_CUSTO_LOJAS
          FROM MAP_PRODUTO A
          LEFT JOIN MAP_FAMDIVISAO FD ON A.SEQFAMILIA = FD.SEQFAMILIA AND FD.NRODIVISAO = 1
          LEFT JOIN MAX_COMPRADOR COMP ON COMP.SEQCOMPRADOR = FD.SEQCOMPRADOR
          LEFT JOIN (SELECT F.SEQFAMILIA, MAX(F.SEQFORNECEDOR) CODIGO_FORNECEDOR, MAX(P.NOMERAZAO) FORNECEDOR_PRINCIPAL
                       FROM MAP_FAMFORNEC F JOIN GE_PESSOA P ON P.SEQPESSOA = F.SEQFORNECEDOR
                      WHERE F.PRINCIPAL = 'S'
                      GROUP BY F.SEQFAMILIA) FP ON FP.SEQFAMILIA = A.SEQFAMILIA
          JOIN (
                SELECT V2.SEQPRODUTO,
                       SUM(NVL(V2.VLRITEM,0) - NVL(V2.VLRDESCITEM,0)) VLR_VENDA
                  FROM MLFV_BASENFE V1
                  JOIN MFLV_BASEDFITEM V2 ON V2.NROEMPRESA = V1.NROEMPRESA
                                         AND V2.SEQNF = V1.SEQNF
                                         AND V2.TIPNOTAFISCAL = V1.TIPNOTAFISCAL
                                         AND V2.SERIEDF = V1.SERIENF
                                         AND V2.NUMERODF = V1.NUMERONF
                                         AND V2.SEQPESSOA = V1.SEQPESSOA
                 WHERE V1.TIPNOTAFISCAL = 'S'
                   AND V1.CODGERALOPER NOT IN (831,917,918,919,920,904,905)
                   AND V1.DTAEMISSAO >= TRUNC(:DT1)
                   AND V1.DTAEMISSAO < TRUNC(:DT2) + 1
                   AND V1.NROEMPRESA IN (1,2,3,4,5,6,7,8,11,12,13,14,17,18)
                   GROUP BY V2.SEQPRODUTO
          ) VF ON VF.SEQPRODUTO = A.SEQPRODUTO
          LEFT JOIN (
                     SELECT X.SEQPRODUTO,
                            SUM(CASE WHEN X.CGO_EFETIVA IN (1,28,32,200,290) THEN X.VLRITEM ELSE 0 END) VLR_COMPRADO,
                            SUM(CASE WHEN X.CGO_EFETIVA IN (100,101,103) THEN X.VLRITEM ELSE 0 END) VLR_BONIFICADO
                       FROM (
                             SELECT N.SEQPRODUTO,
                                    NVL(N.VLRITEM,0) VLRITEM,
                                    CASE WHEN N.TIPPEDCOMPRAITEM IN ('B','E') AND NF.TIPPEDIDOCOMPRA = 'C' AND REGEXP_LIKE(MP.VALOR, '^[0-9]+$') THEN TO_NUMBER(MP.VALOR)
                                         ELSE CGO.CODGERALOPER END CGO_EFETIVA
                              FROM MLF_NFITEM N
                              JOIN MLF_NOTAFISCAL NF ON NF.NUMERONF = N.NUMERONF AND NF.SERIENF = N.SERIENF
                                                   AND NF.NROEMPRESA = N.NROEMPRESA AND NF.TIPNOTAFISCAL = N.TIPNOTAFISCAL
                                                   AND NVL(NF.SEQNF,0) = NVL(N.SEQNF,NVL(NF.SEQNF,0))
                              JOIN MAX_CODGERALOPER CGO ON CGO.CODGERALOPER = NF.CODGERALOPER
                              LEFT JOIN MAX_PARAMETRO MP ON MP.NROEMPRESA = NF.NROEMPRESA AND MP.PARAMETRO = 'CGO_ENTR_BONIF_NFCOMPRA'
                             WHERE NF.TIPNOTAFISCAL = 'E'
                               AND NF.NROEMPRESA IN (1,2,3,4,5,6,7,8,11,12,13,14,15,16,17,18,50)
                               AND NF.DTAENTRADA >= TRUNC(:DT1)
                               AND NF.DTAENTRADA < TRUNC(:DT2) + 1
                               AND NF.STATUSNF <> 'C'
                               AND NF.NUMERONF IS NOT NULL
                               AND N.TIPNOTAFISCAL = 'E'
                               AND N.TIPITEM = 'R'
                            ) X
                      GROUP BY X.SEQPRODUTO
                    ) E ON E.SEQPRODUTO = A.SEQPRODUTO
          LEFT JOIN (
                SELECT I.SEQPRODUTO,
                       SUM(CASE WHEN N.CODGERALOPER = 802 THEN NVL(I.VLRITEM, 0) + NVL(I.VLRIPI, 0) + NVL(I.VLRICMSST, 0) ELSE 0 END) VLR_DEVOLUCAO_COMPRA,
                       SUM(CASE WHEN N.CODGERALOPER = 860 THEN NVL(I.VLRITEM, 0) + NVL(I.VLRIPI, 0) + NVL(I.VLRICMSST, 0) ELSE 0 END) VLR_TROCA_COMPRA
                  FROM MLFV_BASENFE N
                  JOIN MFLV_BASEDFITEM I ON I.SEQNF = N.SEQNF 
                                        AND I.NROEMPRESA = N.NROEMPRESA 
                                        AND I.TIPNOTAFISCAL = N.TIPNOTAFISCAL
                 WHERE N.CODGERALOPER IN (802, 860)
                   AND N.DTAEMISSAO BETWEEN :DT1 AND :DT2
                   AND N.STATUSNF != 'C'
                   AND N.NROEMPRESA IN (1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18, 50)
                 GROUP BY I.SEQPRODUTO
          ) DEV ON DEV.SEQPRODUTO = A.SEQPRODUTO
          LEFT JOIN (
                    SELECT X.SEQPRODUTO,
                           SUM(CASE WHEN X.NROEMPRESA IN (15,16,50) THEN X.VLR_CUSTO ELSE 0 END) VLR_CUSTO_ESTOQUE_CD,
                           SUM(CASE WHEN X.NROEMPRESA IN (1,2,3,4,5,6,7,8,11,12,13,14,17,18) THEN X.VLR_CUSTO ELSE 0 END) VLR_CUSTO_ESTOQUE_LOJAS
                      FROM (
                            SELECT PE.SEQPRODUTO,
                                   PE.NROEMPRESA,
                              (NVL(PE.ESTQLOJA,0)+NVL(PE.ESTQDEPOSITO,0))
                                   *
                                   (NVL(PE.CMULTVLRNF,0)+NVL(PE.CMULTIPI,0)+NVL(PE.CMULTICMSST,0)+NVL(PE.CMULTDESPNF,0)+NVL(PE.CMULTDESPFORANF,0)) VLR_CUSTO
                              FROM MRL_PRODUTOEMPRESA PE
                             WHERE PE.NROEMPRESA IN (1,2,3,4,5,6,7,8,11,12,13,14,15,16,17,18,50)
                           ) X
                     GROUP BY X.SEQPRODUTO
                    ) CS ON CS.SEQPRODUTO = A.SEQPRODUTO
          LEFT JOIN (
                    SELECT I.SEQPRODUTO,
                           SUM(NVL(I.QUANTIDADE,0)) QTD_INCINERACAO_ANO
                      FROM MLFV_BASENFE N
                      JOIN MFLV_BASEDFITEM I ON I.NROEMPRESA = N.NROEMPRESA
                                            AND I.SEQNF = N.SEQNF
                                            AND I.TIPNOTAFISCAL = N.TIPNOTAFISCAL
                                            AND I.SERIEDF = N.SERIENF
                                            AND I.NUMERODF = N.NUMERONF
                                            AND I.SEQPESSOA = N.SEQPESSOA
                     WHERE N.CODGERALOPER = 831
                       AND N.TIPNOTAFISCAL = 'S'
                       AND NVL(N.MODELO,'0') <> '65'
                       AND N.NROEMPRESA IN (1,2,3,4,5,6,7,8,9,11,12,13,14,15,16,17,18,50)
                       AND N.DTAEMISSAO >= TRUNC(SYSDATE,'YYYY')
                       AND N.DTAEMISSAO < TRUNC(SYSDATE) + 1
                     GROUP BY I.SEQPRODUTO
                   ) INCI ON INCI.SEQPRODUTO = A.SEQPRODUTO
         WHERE ((:LS1 = '0 - TODOS') OR NVL(FD.SEQCOMPRADOR, 0) = TO_NUMBER(SUBSTR(:LS1, 1, INSTR(:LS1, ' - ') - 1)))
           AND (:NR1 = '0' OR FP.CODIGO_FORNECEDOR = TO_NUMBER(:NR1))
           AND NOT EXISTS (
                 SELECT 1
                   FROM MAP_FAMDIVCATEG XF
                   JOIN MAP_CATEGORIA YF ON XF.SEQCATEGORIA = YF.SEQCATEGORIA
                  WHERE XF.SEQFAMILIA = A.SEQFAMILIA
                    AND YF.NIVELHIERARQUIA = 1
                    AND (UPPER(YF.CATEGORIA) IN ('ALMOXARIFADO') )
              )
       ) B
 WHERE NVL(UPPER(TRIM(:LT2)),'D') IN ('D','C')
 GROUP BY B.CODIGO_FORNECEDOR,
          B.FORNECEDOR_PRINCIPAL,
          CASE WHEN NVL(UPPER(TRIM(:LT2)),'D') = 'C' THEN '1' ELSE B.COMPRADOR END
HAVING SUM(B.VLR_VENDA) > 0 OR SUM(B.VLR_COMPRA) > 0 OR SUM(B.VLR_BONIFICADO) > 0
 ORDER BY SUM(B.VLR_COMPRA) DESC, 2 ASC
