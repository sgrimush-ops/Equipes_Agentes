# Consulta Criação: Produtos Exclusivos Loja (Sem CD)

## 1. Objetivo da consulta
Identificar produtos ativos que entraram (foram comprados e recebidos) diretamente nas lojas (CGO 1) nos últimos 180 dias e que **nunca** tiveram entrada em um CD no mesmo período, caracterizando-os como produtos exclusivos das lojas (abastecimento direto). A finalidade é analisar o que pode/deve ser mudado no fluxo de abastecimento.

## 2. SQL Principal
```sql
SELECT * FROM (
    WITH ENTRADAS_LOJA AS (
        SELECT /*+ MATERIALIZE */ DISTINCT B.SEQPRODUTO
        FROM MLF_NOTAFISCAL A
        INNER JOIN MLF_NFITEM B ON A.SEQAUXNOTAFISCAL = B.SEQAUXNOTAFISCAL
        WHERE A.DTAENTRADA >= TRUNC(SYSDATE) - 180
          AND A.CODGERALOPER = 1
          AND A.STATUSNF != 'C'
          AND A.NROEMPRESA IN (1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 17, 18)
    ),
    ENTRADAS_CD AS (
        SELECT /*+ MATERIALIZE */ DISTINCT B.SEQPRODUTO
        FROM MLF_NOTAFISCAL A
        INNER JOIN MLF_NFITEM B ON A.SEQAUXNOTAFISCAL = B.SEQAUXNOTAFISCAL
        WHERE A.DTAENTRADA >= TRUNC(SYSDATE) - 180
          AND A.CODGERALOPER = 1
          AND A.STATUSNF != 'C'
          AND A.NROEMPRESA NOT IN (1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 17, 18)
    )
    SELECT DISTINCT
        P.SEQPRODUTO AS COD_PRODUTO,
        P.DESCCOMPLETA AS DESC_PRODUTO,
        C.CATEGORIA AS DEPARTAMENTO,
        COMP.COMPRADOR AS COMPRADOR,
        FD.FORMAABASTECIMENTO AS FORMA_ABASTECIMENTO,
        NVL(EST_CD.ESTOQUE_CD, 0) AS ESTOQUE_CD
    FROM MAP_PRODUTO P
    INNER JOIN MAP_FAMILIA F ON P.SEQFAMILIA = F.SEQFAMILIA
    INNER JOIN ENTRADAS_LOJA EL ON P.SEQPRODUTO = EL.SEQPRODUTO
    LEFT JOIN ENTRADAS_CD ECD ON P.SEQPRODUTO = ECD.SEQPRODUTO
    LEFT JOIN (
        SELECT FDC.SEQFAMILIA, C.CATEGORIA
        FROM MAP_FAMDIVCATEG FDC
        INNER JOIN MAP_CATEGORIA C ON FDC.SEQCATEGORIA = C.SEQCATEGORIA AND C.NRODIVISAO = 1
        WHERE FDC.NRODIVISAO = 1 AND FDC.STATUS = 'A' AND C.TIPCATEGORIA = 'M' AND C.NIVELHIERARQUIA = 1
        GROUP BY FDC.SEQFAMILIA, C.CATEGORIA
    ) C ON C.SEQFAMILIA = F.SEQFAMILIA
    LEFT JOIN MAP_FAMDIVISAO FD ON F.SEQFAMILIA = FD.SEQFAMILIA AND FD.NRODIVISAO = 1
    LEFT JOIN MAX_COMPRADOR COMP ON FD.SEQCOMPRADOR = COMP.SEQCOMPRADOR
    LEFT JOIN (
        SELECT 
            SEQPRODUTO,
            SUM(NVL(ESTQLOJA, 0) + NVL(ESTQDEPOSITO, 0) - NVL(QTDRESERVADAVDA, 0) - NVL(QTDRESERVADARECEB, 0) - NVL(QTDRESERVADAFIXA, 0)) AS ESTOQUE_CD
        FROM MRL_PRODUTOEMPRESA
        WHERE NROEMPRESA NOT IN (1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 17, 18)
        GROUP BY SEQPRODUTO
    ) EST_CD ON P.SEQPRODUTO = EST_CD.SEQPRODUTO
    WHERE ECD.SEQPRODUTO IS NULL
      AND (:LS1 = 'TODOS OS DEPARTAMENTOS' OR C.CATEGORIA = :LS1)
      AND (:LS2 = '0 - TODOS' OR NVL(FD.SEQCOMPRADOR, 0) = TO_NUMBER(SUBSTR(:LS2, 1, INSTR(:LS2, ' - ') - 1)))
      AND EXISTS (
          SELECT 1 
          FROM MRL_PRODUTOEMPRESA PE
          WHERE PE.SEQPRODUTO = P.SEQPRODUTO
            AND PE.STATUSCOMPRA = 'A'
            AND PE.NROEMPRESA IN (1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 17, 18)
      )
      AND INSTR(UPPER(NVL(:LT1, 'L,M,C,I')), UPPER(FD.FORMAABASTECIMENTO)) > 0
)
ORDER BY DESC_PRODUTO ASC
```

## 3. Variáveis para cadastrar em `Var - F7`

### Filtro 1: Departamento
- **Variável**: `LS1`
- **Tipo**: Lista
- **Descrição**: Selecione o Departamento
- **Valor padrão**: ` TODOS OS DEPARTAMENTOS`

### Filtro 2: Comprador
- **Variável**: `LS2`
- **Tipo**: Lista
- **Descrição**: Selecione o Comprador
- **Valor padrão**: ` TODOS OS COMPRADORES`

### Filtro 3: Tipo de Abastecimento
- **Variável**: `LT1`
- **Tipo**: Literal
- **Descrição**: Tipo Abastecimento (L,M,C,I)
- **Valor padrão**: `L,M,C,I`

## 4. SQL das Listas LSx

### Para LS1 (Departamento):
```sql
SELECT 'TODOS OS DEPARTAMENTOS' AS DEPARTAMENTO FROM DUAL
UNION
SELECT CATEGORIA FROM MAP_CATEGORIA WHERE NIVELHIERARQUIA = 1
```

### Para LS2 (Comprador):
```sql
SELECT '0 - TODOS' AS COMPRADOR FROM DUAL
UNION
SELECT DISTINCT TO_CHAR(C.SEQCOMPRADOR) || ' - ' || NVL(C.APELIDO, C.COMPRADOR) FROM MAX_COMPRADOR C WHERE C.SEQCOMPRADOR IS NOT NULL
```

## 5. Passo a Passo de Configuração

1. Acesse o **Totvs Consinco > SGI > Consulta Criação**.
2. Cole o **SQL Principal** na área de texto.
3. Clique em **Var - F7** no menu superior.
4. Cadastre a variável **LS1** (Lista), informando a descrição e colando o script SQL da lista LS1 dentro do campo correspondente.
5. Cadastre a variável **LS2** (Lista), informando a descrição e colando o script SQL da lista LS2 dentro do campo correspondente.
6. Cadastre a variável **LT1** (Literal), coloque a descrição "Tipo Abastecimento (L,M,C,I)" e defina o valor padrão como `L,M,C,I`.
7. Pressione **Ok** e depois **Executar (F8)**. As caixas de seleção aparecerão antes do carregamento dos dados.
