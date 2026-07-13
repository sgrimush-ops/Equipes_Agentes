# Aprendizado e Padrão de Referência: Relatórios em Grade Pivoteados com Linha de Cabeçalho de Pedidos (Oracle / Consinco)

## 1. Contexto e Desafio Operacional
No desenvolvimento de relatórios e consultas para o **Consulta Criação do Totvs Consinco SGI**, frequentemente surge a necessidade de exibir dados pivoteados horizontalmente por filial (`L1, L2, L3 ... L18`), como na impressão de pedidos de compra ou distribuição de grade por loja.

O desafio comum no Oracle SQL estático é:
- Como informar ao usuário **qual foi o número do pedido emitido para cada loja** sem "sujar" as células de quantidade dos produtos com textos ou strings concatenadas (ex: `'200 * 93372'`), o que impediria somas numéricas, fórmulas no Excel e totalizações automáticas no grid?

---

## 2. A Solução Padrão de Ouro: "Linha 0 de Cabeçalho do Pedido + Linhas Numéricas"

Para relatórios de grade pivoteada por loja em pedidos, adota-se a arquitetura em duas camadas via `UNION ALL` ordenado por uma coluna de controle (`ORDEM`):

### A. Linha 0 (`ORDEM = 0`): Topo da Grade com o Número dos Pedidos
- Retorna uma única linha no topo do relatório onde:
  - `FORN` = `0`
  - `SEQPRODUTO` = `0`
  - `CODIGO_EAN` = `''`
  - `DESCRICAO` = `'>>> NÚMERO DO PEDIDO DA LOJA >>>'`
  - `EMBALAGEM` = `0`
  - Colunas `L1` até `L18`: Exibem o **Número do Pedido (`NROPEDIDOSUPRIM`)** emitido para aquela filial no período (ou `0` se não houve pedido).
  - `TOTAL_QTD` = `0`

### B. Linhas 1+ (`ORDEM = 1`): Itens e Quantidades Numéricas Puras
- Retornam os produtos efetivamente solicitados nos pedidos:
  - `FORN`: Código do fornecedor do pedido (`R.SEQFORNECEDOR`).
  - `SEQPRODUTO`: Código interno do produto (`P.SEQPRODUTO`).
  - `CODIGO_EAN`: EAN principal comercial (`MAP_PRODCODIGO`).
  - `DESCRICAO`: Descrição completa (`DESCCOMPLETA`).
  - `EMBALAGEM`: Embalagem padrão de compra (`PADRAOEMBCOMPRA`).
  - Colunas `L1` até `L18`: Exibem **exclusivamente o valor numérico da quantidade pedida** (`SUM(QTDSOLICITADA)`).
  - `TOTAL_QTD`: Somatório numérico de toda a rede.

---

## 3. Padrões de Performance e Resiliência Consinco

1. **Fonte de Dados de Pedidos (`MACV_PSITEMRECEBER`):**
   - Utilizar a view consolidada `MACV_PSITEMRECEBER` para capturar itens de pedidos de compra em suprimentos (`TIPPEDIDOSUPRIM = 'C'`), garantindo paridade com o monitor SQL nativo do ERP.
2. **Filtro de Fornecedor Direto na Tabela de Pedidos (`R.SEQFORNECEDOR`):**
   - Aplicar o filtro de fornecedor (`:LS1`) diretamente em `R.SEQFORNECEDOR`. Isso assegura que todos os itens presentes no pedido empenhado para aquele CNPJ sejam exibidos, independentemente de estarem vinculados a outro fornecedor principal no cadastro geral de famílias.
3. **Tolerância a CGO em Pedidos de Suprimento (`:LT2`):**
   - Em pedidos de suprimento não faturados/recebidos, o campo `CODGERALOPER` na tabela `MSU_PEDIDOSUPRIM` pode estar nulo (`NULL`) ou zerado (`0`). O filtro de CGO deve tolerar essa condição:
     ```sql
     AND (
         NVL(TRIM(:LT2), 'TODOS') IN ('TODOS', '0', '')
         OR PS.CODGERALOPER IS NULL
         OR PS.CODGERALOPER = 0
         OR INSTR(',' || REPLACE(TRIM(:LT2), ' ', '') || ',', ',' || TO_CHAR(PS.CODGERALOPER) || ',') > 0
     )
     ```
4. **Conformidade SGI:**
   - Envelopamento obrigatório `SELECT * FROM ( WITH ... SELECT ... )`.
   - Uso de `/*+ MATERIALIZE */` em todas as CTEs.
   - Ausência total de comentários (`--` ou `/* */`) no script `.sql`.

---

## 4. Estrutura SQL de Referência

```sql
SELECT * FROM (
    WITH ITENS_PEDIDO_PERIODO AS (
        SELECT /*+ MATERIALIZE */
            R.SEQFORNECEDOR,
            R.SEQPRODUTO,
            R.NROEMPRESA,
            R.NROPEDIDOSUPRIM,
            SUM(R.QTDSOLICITADA) AS QTDSOLICITADA
        FROM MACV_PSITEMRECEBER R
        LEFT JOIN MSU_PEDIDOSUPRIM PS
            ON PS.NROPEDIDOSUPRIM = R.NROPEDIDOSUPRIM
           AND PS.NROEMPRESA = R.NROEMPRESA
           AND PS.CENTRALLOJA = R.CENTRALLOJA
        WHERE TRUNC(R.DTAEMISSAO) BETWEEN TRUNC(:DT1) AND TRUNC(:DT2)
          AND R.TIPPEDIDOSUPRIM = 'C'
          AND NVL(R.STATUSITEM, 'A') != 'C'
          AND NVL(R.SITUACAOPED, 'A') != 'C'
          AND R.NROEMPRESA IN (1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 17, 18)
          AND (
              NVL(TRIM(:LS1), 'TODOS') IN ('TODOS', '0 - TODOS', '0', '')
              OR INSTR(TRIM(:LS1), 'TODOS') > 0
              OR TO_CHAR(R.SEQFORNECEDOR) = TRIM(:LS1)
              OR INSTR(TRIM(:LS1), TO_CHAR(R.SEQFORNECEDOR) || ' - ') = 1
              OR INSTR(TRIM(:LS1), TO_CHAR(R.SEQFORNECEDOR) || '-') = 1
          )
        GROUP BY R.SEQFORNECEDOR, R.SEQPRODUTO, R.NROEMPRESA, R.NROPEDIDOSUPRIM
    ),
    PEDIDOS_LOJA AS (
        SELECT /*+ MATERIALIZE */
            NROEMPRESA,
            MAX(NROPEDIDOSUPRIM) AS NROPEDIDOSUPRIM
        FROM ITENS_PEDIDO_PERIODO
        GROUP BY NROEMPRESA
    ),
    LINHA_CABECALHO AS (
        SELECT /*+ MATERIALIZE */
            0 AS ORDEM,
            0 AS CODIGO_FORNECEDOR,
            0 AS CODIGO_PRODUTO,
            '               ' AS CODIGO_EAN,
            '>>> NÚMERO DO PEDIDO DA LOJA >>>' AS DESCRICAO,
            0 AS EMBALAGEM,
            NVL(MAX(CASE WHEN NROEMPRESA = 1 THEN NROPEDIDOSUPRIM END), 0) AS L1,
            NVL(MAX(CASE WHEN NROEMPRESA = 11 THEN NROPEDIDOSUPRIM END), 0) AS L11,
            NVL(MAX(CASE WHEN NROEMPRESA = 12 THEN NROPEDIDOSUPRIM END), 0) AS L12,
            0 AS TOTAL_QTD
        FROM PEDIDOS_LOJA
    ),
    GRADE_LOJAS AS (
        SELECT /*+ MATERIALIZE */
            I.SEQFORNECEDOR AS CODIGO_FORNECEDOR,
            I.SEQPRODUTO,
            SUM(CASE WHEN I.NROEMPRESA = 1 THEN I.QTDSOLICITADA END) AS L1,
            SUM(CASE WHEN I.NROEMPRESA = 11 THEN I.QTDSOLICITADA END) AS L11,
            SUM(CASE WHEN I.NROEMPRESA = 12 THEN I.QTDSOLICITADA END) AS L12,
            SUM(I.QTDSOLICITADA) AS TOTAL_QTD
        FROM ITENS_PEDIDO_PERIODO I
        GROUP BY I.SEQFORNECEDOR, I.SEQPRODUTO
    ),
    LINHAS_ITENS AS (
        SELECT /*+ MATERIALIZE */
            1 AS ORDEM,
            G.CODIGO_FORNECEDOR,
            P.SEQPRODUTO AS CODIGO_PRODUTO,
            NVL(E.CODIGO_EAN, ' ') AS CODIGO_EAN,
            P.DESCCOMPLETA AS DESCRICAO,
            NVL(FD.PADRAOEMBCOMPRA, 1) AS EMBALAGEM,
            G.L1, G.L11, G.L12, G.TOTAL_QTD
        FROM GRADE_LOJAS G
        INNER JOIN MAP_PRODUTO P ON P.SEQPRODUTO = G.SEQPRODUTO
        INNER JOIN MAP_FAMDIVISAO FD ON FD.SEQFAMILIA = P.SEQFAMILIA AND FD.NRODIVISAO = 1
        LEFT JOIN EAN_PRODUTO E ON E.SEQPRODUTO = G.SEQPRODUTO
    )
    SELECT
        CODIGO_FORNECEDOR AS FORN,
        CODIGO_PRODUTO AS SEQPRODUTO,
        CODIGO_EAN,
        DESCRICAO,
        EMBALAGEM,
        L1, L11, L12, TOTAL_QTD
    FROM (
        SELECT * FROM LINHA_CABECALHO
        UNION ALL
        SELECT * FROM LINHAS_ITENS
    )
    ORDER BY ORDEM ASC, DESCRICAO ASC, CODIGO_PRODUTO ASC
)
```
