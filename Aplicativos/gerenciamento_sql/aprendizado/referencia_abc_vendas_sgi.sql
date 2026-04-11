SELECT A.SEQCATEGORIA
Into :NRA
From MAP_CATEGORIA A
WHERE A.SEQCATEGORIA || '-' || A.CATEGORIA = #LS1;

SELECT 
   b.qtdvda qtdvdaloja,
   b.seqproduto,
   b.desccompleta,
   b.seqfornecedor,
   b.fornecedor,
   b.nroempresa,
:DT1 dtainicialvda,
:DT2 dtafinalvda,
:LT1 empresas,

   fcodacessoproduto(b.seqproduto,'E','S',NULL,NULL) AS codean,

   b.embvda,
   b.embcompra,
   b.seqcategoria || '-' || b.categoria as categoria,

   NVL(NULLIF(b.precovalidpromoc,0), b.precovalidnormal) AS preco,

   ROUND(fc5margempreco(
      b.seqproduto,
      to_number(b.nroempresa),
      b.nrosegmentoprinc,
      b.embvda,
      NULL,
      NVL(NULLIF(b.precovalidpromoc,0), b.precovalidnormal),
      NULL,
      NULL
   ),2) AS margem,

   fc5MargemPrecoCadDespOper(
      b.seqproduto,
      to_number(b.nroempresa),
      b.nrosegmentoprinc,
      b.embvda,
      'M'
   ) AS mgmcadastro,

   b.estqminimoloja,
   b.estqmaximoloja,
   b.vlrcustoliqloja,

   (b.estqlojalj + b.estqdepositolj - b.qtdreservadavdalj -
    b.qtdreservadareceblj - b.qtdreservadafixalj) AS estqdisponivellj,

   (b.estqloja + b.estqdeposito - b.qtdreservadavda -
    b.qtdreservadareceb - b.qtdreservadafixa) AS estqdisponivelcd,

   b.qtdultcompra,
   b.dtaultcompra

FROM (

  SELECT 
    v.qtdvda,
    A.SEQPRODUTO,
    A.DESCCOMPLETA,
    J.SEQFORNECEDOR,
    K.NOMERAZAO fornecedor,
    B.NROEMPRESA,
    C.NROSEGMENTOPRINC,
    C.NRODIVISAO,

    D.ESTQLOJA,
    D.ESTQDEPOSITO,
    D.QTDRESERVADAVDA,
    D.QTDRESERVADARECEB,
    D.QTDRESERVADAFIXA,

    B.ESTQLOJA estqlojalj,
    B.ESTQDEPOSITO estqdepositolj,
    B.QTDRESERVADAVDA qtdreservadavdalj,
    B.QTDRESERVADARECEB qtdreservadareceblj,
    B.QTDRESERVADAFIXA qtdreservadafixalj,

    (B.CMULTVLRNF + B.CMULTIPI - B.CMULTCREDICMS + B.CMULTICMSST +
     B.CMULTDESPNF + B.CMULTDESPFORANF - B.CMULTDCTOFORANF 
     - B.CMULTCREDPIS - B.CMULTCREDCOFINS - NVL(B.CMULTVLRVERBA,0)) vlrcustoliqloja,

    B.ESTQMINIMOLOJA,
    B.ESTQMAXIMOLOJA,
    D.QTDULTCOMPRA,
    D.DTAULTCOMPRA,

    G.PADRAOEMBVENDA embvda,
    F.PRECOVALIDNORMAL,
    F.PRECOVALIDPROMOC,

    L.PADRAOEMBCOMPRA embcompra,
    M.SEQCATEGORIA,
    N.CATEGORIA

  FROM MAP_PRODUTO A

  JOIN (
      SELECT 
         SEQPRODUTO,
         NROEMPRESA,
         SUM(QTDVDA) qtdvda
      FROM MRL_PRODVENDADIA
      WHERE DTAVDA BETWEEN :DT1 AND :DT2
      GROUP BY SEQPRODUTO, NROEMPRESA
  ) V
    ON A.SEQPRODUTO = V.SEQPRODUTO

  JOIN MRL_PRODUTOEMPRESA B 
    ON A.SEQPRODUTO = B.SEQPRODUTO
   AND B.NROEMPRESA = V.NROEMPRESA

  JOIN MAX_EMPRESA C 
    ON B.NROEMPRESA = C.NROEMPRESA

  JOIN MRL_PRODUTOEMPRESA D 
    ON A.SEQPRODUTO = D.SEQPRODUTO
   AND D.NROEMPRESA = 15

  JOIN MAD_FAMSEGMENTO G 
    ON A.SEQFAMILIA = G.SEQFAMILIA 
   AND C.NROSEGMENTOPRINC = G.NROSEGMENTO

  JOIN MRL_PRODEMPSEG F 
    ON A.SEQPRODUTO = F.SEQPRODUTO 
   AND B.NROEMPRESA = F.NROEMPRESA   
   AND C.NROSEGMENTOPRINC = F.NROSEGMENTO
   AND G.PADRAOEMBVENDA = F.QTDEMBALAGEM

  JOIN MAP_FAMDIVISAO H 
    ON A.SEQFAMILIA = H.SEQFAMILIA
   AND C.NRODIVISAO = H.NRODIVISAO

  JOIN MAP_FAMFORNEC J 
    ON A.SEQFAMILIA = J.SEQFAMILIA  

  JOIN GE_PESSOA K 
    ON J.SEQFORNECEDOR = K.SEQPESSOA

  JOIN MAP_FAMDIVISAO L 
    ON A.SEQFAMILIA = L.SEQFAMILIA
   AND C.NRODIVISAO = L.NRODIVISAO 

  JOIN MAP_FAMDIVCATEG M 
    ON A.SEQFAMILIA = M.SEQFAMILIA
   AND C.NRODIVISAO = M.NRODIVISAO
   AND M.STATUS = 'A'

  JOIN MAP_CATEGORIA N 
    ON M.SEQCATEGORIA = N.SEQCATEGORIA
   AND C.NRODIVISAO = N.NRODIVISAO
   AND N.STATUSCATEGOR = 'A'
   AND N.TIPCATEGORIA = 'M'
   AND N.NIVELHIERARQUIA = 4

  WHERE B.NROEMPRESA IN  (#LT1)
    AND F.STATUSVENDA = 'A'
    AND H.FINALIDADEFAMILIA = 'R'
    AND A.DESCCOMPLETA NOT LIKE '%EXCLUIR%'
    AND A.DESCCOMPLETA NOT LIKE 'INA%'
    AND J.PRINCIPAL = 'S'
    AND M.SEQCATEGORIA = :NRA

) b

ORDER BY b.fornecedor, b.categoria, b.desccompleta,  b.nroempresa
