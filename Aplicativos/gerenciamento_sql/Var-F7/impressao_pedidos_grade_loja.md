# Consulta Criação: Impressão de Pedidos em Grade por Loja (impressao_pedidos_grade_loja.sql)

## Objetivo
Apresentar uma grade de impressão limpa e estruturada dos itens com pedidos emitidos em um período (`DT1` a `DT2`), mantendo as células de quantidade **100% numéricas** e indicando o **número do pedido emitido de cada loja diretamente no topo da grade**, trazendo na primeira coluna o **Código do Fornecedor (`FORN`)** e na segunda coluna o **Código do Produto (`SEQPRODUTO`)**.

---

## 1. Funcionamento da Abordagem de Grade (Linha Topo + Linhas Numéricas)

1. **Linha 0 (Topo do Grid - Cabeçalho do Número do Pedido):**
   - A primeira linha retornada pela consulta exibe na coluna `DESCRICAO` o texto `>>> NÚMERO DO PEDIDO DA LOJA >>>`.
   - Nas colunas de cada loja (`L1` a `L18`), aparece o **Número do Pedido** emitido para aquela loja no período (exemplo: `L11` = `93372`, `L12` = `93373`).
   - Se a loja não teve pedido, exibe `0`.

2. **Linhas 1+ (Itens Pedidos):**
   - Apresentam na primeira coluna o **Código do Fornecedor (`FORN`)**, seguido por **`SEQPRODUTO`**, EAN, descrição e embalagem de compra.
   - Nas colunas das lojas (`L1` a `L18`), apresentam **apenas o valor numérico da quantidade solicitada** (exemplo: `200`, `100`, `80`), permitindo somas, fórmulas ou totalizações no Excel e relatórios sem interferência de strings.

---

## 2. Mapeamento de Variáveis (`Var - F7`)

| Variável | Tipo | Retorno | Padrão | Descrição |
| :--- | :--- | :--- | :--- | :--- |
| **`DT1`** | Data | Data | Data inicial | Data inicial de emissão do pedido (`R.DTAEMISSAO`) |
| **`DT2`** | Data | Data | Data final | Data final de emissão do pedido (`R.DTAEMISSAO`) |
| **`LS1`** | Lista | Literal | `0 - TODOS` | Fornecedor do Pedido (`R.SEQFORNECEDOR`) |
| **`LS2`** | Lista | Literal | `TODOS` | Comprador do Pedido (`SEQCOMPRADOR`) |
| **`LT1`** | Literal | Literal | `1,2,3,4,5,6,7,8,11,12,13,14,17,18` | Lojas discriminadas para filtrar os pedidos emitidos |
| **`LT2`** | Literal | Literal | `1,28,32,200,290` | Tipos de CGO (`CODGERALOPER`) dos pedidos de compra |

---

## 3. Exemplo de Visualização no Grid / Excel

| FORN | SEQPRODUTO | CODIGO_EAN | DESCRICAO | EMBALAGEM | L1 | ... | L11 | L12 | TOTAL_QTD |
| :---: | :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **0** | **0** | | **>>> NÚMERO DO PEDIDO DA LOJA >>>** | 0 | 0 | ... | **93372** | **93373** | 0 |
| **7365** | **2632** | 7896801014079 | ERVA MATE CRISTALINA 1KG SUAVE | 20 | | ... | **200** | **100** | 300 |
| **7365** | **2635** | 7896801014017 | ERVA MATE CRISTALINA 1KG TRAD | 20 | | ... | **80** | **40** | 120 |
