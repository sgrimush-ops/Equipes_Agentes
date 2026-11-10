# Aprendizado: Consulta de Preços do Dia (MRL_PRODEMPSEG) e Filtro por Comprador

Este documento consolida as regras técnicas e estruturais para descobrir os preços vigentes do dia no ERP Totvs Consinco e integrar filtros de Comprador e Loja na Consulta Criação (`Var - F7`).

## Descobertas Principais sobre Preços do Dia (`MRL_PRODEMPSEG`)
1. **Armazenamento Oficial**: Os preços de venda no Consinco por loja, produto e embalagem ficam na tabela `MRL_PRODEMPSEG`.
2. **Separação Normal vs. Promocional**: A tabela mantém colunas distintas:
   - `PRECOVALIDNORMAL`: Preço normal vigente da tabela.
   - `PRECOVALIDPROMOC`: Preço promocional vigente (quando 0 ou nulo, indica que não há promoção ativa no dia).
3. **Fórmula do Preço Praticado (Preço do Dia)**:
   - A regra canônica para obter o preço real vigente no dia é:
     ```sql
     NVL(NULLIF(PRECOVALIDPROMOC, 0), PRECOVALIDNORMAL)
     ```
   - *Explicação*: O `NULLIF` transforma o 0 em `NULL`, fazendo o `NVL` capturar o preço promocional apenas quando for positivo; caso contrário, assume o `PRECOVALIDNORMAL`.
4. **Join Obrigatório de Embalagem Padrão**:
   - Para evitar duplicação de registros por múltiplas embalagens de venda (unitário, caixa, fardo), deve-se juntar com `MAD_FAMSEGMENTO FS` filtrando pela quantidade padrão de venda do segmento:
     ```sql
     ON S.SEQPRODUTO = A.SEQPRODUTO
    AND S.NROEMPRESA = ME.NROEMPRESA
    AND S.NROSEGMENTO = ME.NROSEGMENTOPRINC
    AND S.QTDEMBALAGEM = NVL(FS.PADRAOEMBVENDA, 1)
     ```

## Estrutura para Vínculo e Filtro por Comprador (`LS1`)
1. **Origem do Comprador do Produto**: O comprador é definido no nível de família e divisão na tabela `MAP_FAMDIVISAO` (`FD.SEQCOMPRADOR`), com o cadastro de nomes/apelidos em `MAX_COMPRADOR`.
2. **Exibição Padronizada**:
   - Para facilitar a conferência e ordenação na grade, exponha a coluna combinada:
     ```sql
     TO_CHAR(FD.SEQCOMPRADOR) || ' - ' || NVL(C.APELIDO, C.COMPRADOR) AS COMPRADOR
     ```
3. **Regra de Filtro na Cláusula WHERE (`LS1`)**:
   - Para permitir escolha de um comprador ou todos no SGI Client (`Var - F7`), utilize a expressão anti-falha:
     ```sql
     AND ((:LS1 = '0 - TODOS') OR NVL(FD.SEQCOMPRADOR, 0) = TO_NUMBER(SUBSTR(:LS1, 1, INSTR(:LS1, ' - ') - 1)))
     ```
   - A lista `LS1` deve ser cadastrada retornando `TO_CHAR(C.SEQCOMPRADOR) || ' - ' || REPLACE(NVL(C.APELIDO, C.COMPRADOR), '''', '')` unida a `'0 - TODOS'`, sem trailing `UNION` no final para não conflitar com o `ORDER BY 1` automático da tela.

## Extração de EAN Principal (`MAP_PRODCODIGO`)
1. **Origem dos Códigos de Barra**: Para evitar duplicidade ou subconsultas repetitivas e pegar o EAN principal, deve-se utilizar a tabela `MAP_PRODCODIGO` filtrando `TIPCODIGO IN ('E', 'D')` (`'E'` = EAN unitário comercial, `'D'` = DUN/Caixa).
2. **Priorização e Desduplicação (CTE Materializada)**:
   - Utiliza-se `ROW_NUMBER() OVER (PARTITION BY C.SEQPRODUTO ORDER BY DECODE(C.TIPCODIGO, 'E', 1, 'D', 2, 3) ASC, C.CODACESSO ASC)` para priorizar o EAN unitário (`'E'`) em primeiro lugar, escolhendo de forma determinística o primeiro código em caso de múltiplas ocorrências (`RN = 1`).
   - A CTE `EAN_PRODUTO` recebe `/*+ MATERIALIZE */` e é ligada via `LEFT JOIN` para garantir que o produto sempre retorne mesmo caso não possua EAN cadastrado.
3. **Bypass do Validador Consulta Criação**:
   - Como a CTE começa com a palavra-chave `WITH`, toda a consulta é envelopada com `SELECT * FROM ( WITH ... SELECT ... )` para passar pelo validador do Totvs Consinco SGI Client.

## Query Base Validada de Preços do Dia com Comprador e EAN Principal
```sql
SELECT * FROM (
    WITH EAN_PRODUTO AS (
        SELECT /*+ MATERIALIZE */
            SEQPRODUTO,
            CODACESSO AS EAN
        FROM (
            SELECT
                C.SEQPRODUTO,
                C.CODACESSO,
                ROW_NUMBER() OVER (PARTITION BY C.SEQPRODUTO ORDER BY DECODE(C.TIPCODIGO, 'E', 1, 'D', 2, 3) ASC, C.CODACESSO ASC) AS RN
            FROM MAP_PRODCODIGO C
            WHERE C.TIPCODIGO IN ('E', 'D')
        )
        WHERE RN = 1
    )
    SELECT
        A.SEQPRODUTO AS CODIGO_PRODUTO,
        E.EAN AS EAN,
        A.DESCCOMPLETA AS DESCRICAO_PRODUTO,
        ME.NROEMPRESA AS CODIGO_EMPRESA,
        NVL(FS.PADRAOEMBVENDA, 1) AS EMBALAGEM_VENDA,
        TO_CHAR(FD.SEQCOMPRADOR) || ' - ' || NVL(C.APELIDO, C.COMPRADOR) AS COMPRADOR,
        ROUND(NVL(S.PRECOVALIDNORMAL, 0), 2) AS PRECO_NORMAL,
        ROUND(NVL(S.PRECOVALIDPROMOC, 0), 2) AS PRECO_PROMOCIONAL,
        ROUND(NVL(NULLIF(S.PRECOVALIDPROMOC, 0), S.PRECOVALIDNORMAL), 2) AS PRECO_PRATICADO_DIA
    FROM MAP_PRODUTO A
    JOIN MRL_PRODUTOEMPRESA PE ON PE.SEQPRODUTO = A.SEQPRODUTO
    JOIN MAX_EMPRESA ME ON ME.NROEMPRESA = PE.NROEMPRESA
    LEFT JOIN EAN_PRODUTO E ON E.SEQPRODUTO = A.SEQPRODUTO
    LEFT JOIN MAP_FAMDIVISAO FD ON FD.SEQFAMILIA = A.SEQFAMILIA
                               AND FD.NRODIVISAO = ME.NRODIVISAO
    LEFT JOIN MAX_COMPRADOR C ON C.SEQCOMPRADOR = FD.SEQCOMPRADOR
    LEFT JOIN MAD_FAMSEGMENTO FS ON FS.SEQFAMILIA = A.SEQFAMILIA
                                AND FS.NROSEGMENTO = ME.NROSEGMENTOPRINC
    LEFT JOIN MRL_PRODEMPSEG S ON S.SEQPRODUTO = A.SEQPRODUTO
                              AND S.NROEMPRESA = ME.NROEMPRESA
                              AND S.NROSEGMENTO = ME.NROSEGMENTOPRINC
                              AND S.QTDEMBALAGEM = NVL(FS.PADRAOEMBVENDA, 1)
    WHERE PE.NROEMPRESA IN (1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 17, 18)
      AND PE.STATUSCOMPRA = 'A'
      AND ((:LS1 = '0 - TODOS') OR NVL(FD.SEQCOMPRADOR, 0) = TO_NUMBER(SUBSTR(:LS1, 1, INSTR(:LS1, ' - ') - 1)))
      AND (NVL(:NR1, 0) = 0 OR PE.NROEMPRESA = :NR1)
      AND (NVL(:NR2, 0) = 0 OR A.SEQPRODUTO = :NR2)
    ORDER BY PE.NROEMPRESA, A.SEQPRODUTO
)
```

## Arquivos Relacionados
- **Consulta SQL**: `Aplicativos/gerenciamento_sql/querys/consulta_precos_dia_comprador.sql`
- **Configuração Var-F7**: `Aplicativos/gerenciamento_sql/Var-F7/consulta_precos_dia_comprador.md`
- **Simulador Completo (com Custo/Margem)**: `Aplicativos/gerenciamento_sql/querys/levantamento_custos_precos.sql`
