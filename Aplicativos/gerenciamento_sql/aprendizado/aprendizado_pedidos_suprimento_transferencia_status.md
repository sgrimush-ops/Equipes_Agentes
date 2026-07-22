# Aprendizado: Pedidos de Suprimento e Transferência no Consinco (Capa vs Item, Expedição e Listas LS1)

Este documento consolida o conhecimento técnico, arquitetural e prático adquirido na homologação de consultas de histórico e auditoria de atendimento de **Pedidos de Transferência e Reposição (`MSU_PEDIDOSUPRIM` / `MSU_PSITEMRECEBER` / `MSU_PSITEMEXPEDIR`)** no ecossistema **Totvs Consinco SGI (Oracle)**.

---

## 1. Arquitetura de Pedidos: Compras vs. Transferências Internas

No módulo de Suprimentos / Estoque do Consinco, a tabela principal de cabeçalho (`MSU_PEDIDOSUPRIM`) armazena tanto pedidos de compra externa (fornecedores CNPJ) quanto pedidos de transferência/abastecimento interno entre o CD e as filiais de varejo:

- **Diferenciação via `TIPPEDIDOSUPRIM`:**
  - `TIPPEDIDOSUPRIM = 'C'`: Compra externa de fornecedor.
  - `TIPPEDIDOSUPRIM != 'C'` (geralmente `'T'` ou outros tipos de abastecimento): Transferências e reposição interna do CD para as lojas (`SEQFORNECEDOR` aponta para a empresa/CD emissor, ex: 15, 16 ou 50).

---

## 2. Status da Capa (`SITUACAOPED`) vs. Status do Item (`STATUSITEM`)

### Por que eles divergem e por que isso não é falha do Consinco?
Um pedido de transferência (`MSU_PEDIDOSUPRIM`) é um **documento guarda-chuva** que agrupa dezenas ou centenas de produtos diferentes emitidos na mesma rodada de reposição.

Quando o pedido está em separação no CD (`SITUACAOPED = 'P - EM PROCESSO / PRÉ-SEPARAÇÃO'` ou `'S - EM SEPARAÇÃO'`), ocorrem duas dinâmicas:
1. **Corte Parcial por Ruptura:** Se apenas o item A (ex: Molho de Tomate) estiver em falta no CD, o separador/sistema corta a linha do item (`STATUSITEM = 'C - CANCELADO / CORTADO'`). No entanto, **a capa do pedido (`MSU_PEDIDOSUPRIM.SITUACAOPED`) DEVE continuar como `P`, `S`, `W` ou `F`**, pois os demais 49 itens do pedido continuam ativos e serão embarcados na carreta.
2. **Corte em Lote:** Mesmo em cortes totais de linhas no WMS, o status individual da linha (`MSU_PSITEMRECEBER.STATUSITEM`) é atualizado imediatamente para `'C'`, enquanto a capa (`SITUACAOPED`) pode permanecer com o status de processamento até o fechamento do lote ou execução de rotinas noturnas de faxina/fechamento.

### Regra de Ouro da Auditoria
> Para relatórios e auditorias focadas no histórico de um **produto específico (`SEQPRODUTO`)**, a soberania é sempre do **`STATUSITEM` (da tabela `MSU_PSITEMRECEBER`)** em conjunto com as quantidades físicas (`QTDSOLICITADA`, `QTDEXPEDIDA`, `QTDRECEBIDA`). O status da capa não deve ser utilizado como classificador de atendimento do produto, pois gera ruídos e contradições com os outros itens do documento.

---

## 3. Por que Pedidos Não Atendidos "Somem" da Consulta Simples?

Quando o motor de sugestão de abastecimento roda periodicamente, os saldos não atendidos ou cortados de rodadas anteriores nas tabelas operacionais ativas (`MSU_PSITEMRECEBER` e `MSU_PSITEMEXPEDIR`) são expurgados ou cancelados para não reter reservas falsas e dar lugar à nova geração de pedidos.

### Onde fica o Rastro de Auditoria?
O Consinco preserva o histórico imutável nas tabelas nativas de log:
- **`MSU_PEDIDOSUPRIMLOG`** / **`MSU_PEDIDOSUPRIM_LOG`**: Auditoria das transições de status da capa.
- **`MSU_PSITEMRECEBERLOG`** / **`MSU_PSITEMRECEBER_LOG`**: Histórico linha a linha das alterações de quantidade (`QTDSOLICITADAORIGINAL`, `QTDSOLICITADA`, `QTDTOTRECEBIDA`, `QTDTOTCANCELADA`, `STATUSITEM` e `DTAALTERACAO`).
- **`MSU_PSITEMEXPEDIR_HIST`**: Histórico dos cortes ocorridos durante o processo de expedição no CD.

---

## 4. Tratamento Crítico: Data de Expedição em Branco (`NVL`)

Em consultas de histórico de atendimento que cruzam o pedido com a expedição (`MSU_PSITEMEXPEDIDO`) e o recebimento (`MSU_PSITEMRECEBIDO`), foi verificado que itens **ATENDIDOS TOTAIS OU PARCIAIS** muitas vezes apresentavam a `DATA_EXPEDICAO` em branco quando a consulta lia apenas a data da tabela de expedição (`X.DTA_EXPEDICAO_CD`).

- **Causa:** Quando a nota dá entrada direta ou o fluxo de faturamento grava o movimento prioritariamente no recebimento da loja (`MSU_PSITEMRECEBIDO`), a tabela de expedição pode ficar sem registro ou com data nula no join por item.
- **Solução Homologada:** Sempre aplicar fallback (`NVL`) entre a expedição do CD e o recebimento da Loja:
  ```sql
  TO_CHAR(NVL(X.DTA_EXPEDICAO_CD, REC.DTA_RECEBIMENTO_LOJA), 'DD/MM/YYYY') AS DATA_EXPEDICAO
  ```
  Isso garante que **todo atendimento com nota fiscal emitida apresente a data real do faturamento/recebimento sem ficar em branco**.

---

## 5. Superando o Limite e Corte de Caracteres no Combo Box `LS1` (`Var - F7`)

Na tela de configuração de variáveis da **Consulta Criação** no Consinco (`Definir Variável: LISTA`), o campo **`Instrução SQL ou Constantes da Lista`** possui um limite de caracteres (~200 a 250 posições) e comportamento específico ao conversar com o driver Delphi (BDE/dbExpress).

### A Armadilha de `SELECT COLUMN_VALUE FROM TABLE(SYS.ODCIVARCHAR2LIST(...))`
Ao usar o `SYS.ODCIVARCHAR2LIST` direto sem tipagem explicitada para encurtar múltiplos `UNION ALL`, o driver Delphi interroga o Oracle sobre a largura do campo `COLUMN_VALUE` da coleção e, muitas vezes, infere a largura do menor literal (ex: 3 caracteres), cortando as opções no drop-down para `0 -`, `ATE`, `CAN`, `EM `.

### Solução 1: Constantes da Lista (Sem SQL - Padrão Mais Leve e Recomendado)
O campo aceita **Constantes da Lista** diretamente sem usar `SELECT`. Quando o texto não começa com `SELECT`, o Consinco não aciona o banco de dados e popula o combo box instantaneamente quebrando os itens pelo separador ponto e vírgula `;` ou quebra de linha.
- **Como usar (apenas 102 caracteres):**
  ```text
  0 - TODOS;ATENDIDO TOTAL;ATENDIDO PARCIAL;EM TRANSITO;EM SEPARACAO CD;CANCELADO;CORTADO NF;NAO ATENDIDO
  ```

### Solução 2: SQL com `CAST` Explícito de Largura (Para Casos onde `SELECT` for obrigatório)
Se a rotina exigir uma consulta SQL no Oracle, deve-se envolver o `COLUMN_VALUE` com um `CAST(... AS VARCHAR2(50))` para forçar o driver Delphi a alocar 50 caracteres para cada item da lista (199 caracteres):
```sql
SELECT CAST(COLUMN_VALUE AS VARCHAR2(50)) FROM TABLE(SYS.ODCIVARCHAR2LIST('0 - TODOS','ATENDIDO TOTAL','ATENDIDO PARCIAL','EM TRANSITO','EM SEPARACAO CD','CANCELADO','CORTADO NF','NAO ATENDIDO'))
```

---

## 6. Query Canônica Homologada: Histórico e Status de Atendimento por Produto

Abaixo está o SQL oficial otimizado com CTEs materializadas, sem comentários internamente para evitar quebra no parser Consinco, com junções antecipadas (`INNER JOIN CAPA_PEDIDOS`) para máxima performance em grandes volumes, e alinhado com as variáveis da tela `Var - F7` (`NR1`, `DT1`, `DT2`, `LT1`, `LT2`, `LS1`):

```sql
SELECT * FROM (
    WITH CAPA_PEDIDOS AS (
        SELECT /*+ MATERIALIZE */
            P.NROPEDIDOSUPRIM,
            P.NROEMPRESA AS LOJA_DESTINO,
            P.SEQFORNECEDOR AS CD_ORIGEM,
            P.DTAEMISSAO,
            P.SITUACAOPED,
            P.TIPPEDIDOSUPRIM
        FROM MSU_PEDIDOSUPRIM P
        WHERE P.TIPPEDIDOSUPRIM != 'C'
          AND TRUNC(P.DTAEMISSAO) BETWEEN TRUNC(:DT1) AND TRUNC(:DT2)
          AND (
              NVL(TRIM(:LT1), 'TODOS') IN ('TODOS', '0 - TODOS', '0', '')
              OR INSTR(',' || REPLACE(TRIM(:LT1), ' ', '') || ',', ',' || TO_CHAR(P.NROEMPRESA) || ',') > 0
          )
          AND (
              NVL(TRIM(:LT2), 'TODOS') IN ('TODOS', '0 - TODOS', '0', '')
              OR INSTR(',' || REPLACE(TRIM(:LT2), ' ', '') || ',', ',' || TO_CHAR(P.SEQFORNECEDOR) || ',') > 0
          )
    ),
    ITENS_SOLICITADOS AS (
        SELECT /*+ MATERIALIZE */
            R.NROPEDIDOSUPRIM,
            R.NROEMPRESA,
            R.SEQPRODUTO,
            SUM(NVL(R.QTDSOLICITADAORIGINAL, R.QTDSOLICITADA)) AS QTD_SOLICITADA,
            SUM(NVL(R.QTDTOTTRANSITO, 0)) AS QTD_TRANSITO_ATUAL,
            SUM(NVL(R.QTDTOTCANCELADA, 0)) AS QTD_CANCELADA_ATUAL,
            MAX(R.STATUSITEM) AS STATUS_ITEM_ATUAL
        FROM MSU_PSITEMRECEBER R
        INNER JOIN CAPA_PEDIDOS C ON C.NROPEDIDOSUPRIM = R.NROPEDIDOSUPRIM AND C.LOJA_DESTINO = R.NROEMPRESA
        WHERE R.SEQPRODUTO = TO_NUMBER(:NR1)
        GROUP BY R.NROPEDIDOSUPRIM, R.NROEMPRESA, R.SEQPRODUTO
    ),
    ITENS_EXPEDIDOS_CD AS (
        SELECT /*+ MATERIALIZE */
            E.NROPEDIDOSUPRIM,
            E.NROEMPDESTINO AS NROEMPRESA,
            E.SEQPRODUTO,
            SUM(NVL(E.QTDEXPEDIDA, 0)) AS QTD_EXPEDIDA_CD,
            SUM(NVL(E.QTDCANCELADA, 0)) AS QTD_CORTADA_CD,
            MAX(E.NUMERONF) AS NF_SAIDA_CD,
            MAX(NVL(E.DTAINCLUSAO, E.DTAALTERACAO)) AS DTA_EXPEDICAO_CD
        FROM MSU_PSITEMEXPEDIDO E
        INNER JOIN CAPA_PEDIDOS C ON C.NROPEDIDOSUPRIM = E.NROPEDIDOSUPRIM AND C.LOJA_DESTINO = E.NROEMPDESTINO
        WHERE E.SEQPRODUTO = TO_NUMBER(:NR1)
        GROUP BY E.NROPEDIDOSUPRIM, E.NROEMPDESTINO, E.SEQPRODUTO
    ),
    ITENS_RECEBIDOS_LOJA AS (
        SELECT /*+ MATERIALIZE */
            L.NROPEDIDOSUPRIM,
            L.NROEMPRESA,
            L.SEQPRODUTO,
            SUM(NVL(L.QTDRECEBIDA, 0)) AS QTD_RECEBIDA_LOJA,
            MAX(L.NUMERONF) AS NF_ENTRADA_LOJA,
            MAX(NVL(L.DTAMOVIMENTO, L.DTAINCLUSAO)) AS DTA_RECEBIMENTO_LOJA
        FROM MSU_PSITEMRECEBIDO L
        INNER JOIN CAPA_PEDIDOS C ON C.NROPEDIDOSUPRIM = L.NROPEDIDOSUPRIM AND C.LOJA_DESTINO = L.NROEMPRESA
        WHERE L.SEQPRODUTO = TO_NUMBER(:NR1)
        GROUP BY L.NROPEDIDOSUPRIM, L.NROEMPRESA, L.SEQPRODUTO
    ),
    DADOS_PRODUTO AS (
        SELECT /*+ MATERIALIZE */
            MP.SEQPRODUTO,
            MP.DESCCOMPLETA
        FROM MAP_PRODUTO MP
        WHERE MP.SEQPRODUTO = TO_NUMBER(:NR1)
    ),
    BASE_RELATORIO AS (
        SELECT /*+ MATERIALIZE */
            C.NROPEDIDOSUPRIM AS NUMERO_PEDIDO,
            C.CD_ORIGEM,
            C.LOJA_DESTINO,
            C.DTAEMISSAO AS DATA_EMISSAO_ORDEM,
            TO_CHAR(C.DTAEMISSAO, 'DD/MM/YYYY') AS DATA_EMISSAO,
            S.SEQPRODUTO AS CODIGO_PRODUTO,
            PR.DESCCOMPLETA AS DESCRICAO_PRODUTO,
            S.QTD_SOLICITADA,
            NVL(X.QTD_CORTADA_CD, S.QTD_CANCELADA_ATUAL) AS QTD_CORTADA_CD,
            NVL(X.QTD_EXPEDIDA_CD, 0) AS QTD_EXPEDIDA_CD,
            S.QTD_TRANSITO_ATUAL AS QTD_EM_TRANSITO,
            NVL(REC.QTD_RECEBIDA_LOJA, 0) AS QTD_RECEBIDA_LOJA,
            NVL(X.NF_SAIDA_CD, REC.NF_ENTRADA_LOJA) AS NUMERO_NOTA_FISCAL,
            TO_CHAR(NVL(X.DTA_EXPEDICAO_CD, REC.DTA_RECEBIMENTO_LOJA), 'DD/MM/YYYY') AS DATA_EXPEDICAO,
            CASE
                WHEN NVL(REC.QTD_RECEBIDA_LOJA, 0) >= S.QTD_SOLICITADA AND S.QTD_SOLICITADA > 0 THEN 'ATENDIDO TOTAL'
                WHEN NVL(REC.QTD_RECEBIDA_LOJA, 0) > 0 AND NVL(REC.QTD_RECEBIDA_LOJA, 0) < S.QTD_SOLICITADA THEN 'ATENDIDO PARCIAL'
                WHEN NVL(X.QTD_EXPEDIDA_CD, 0) > 0 AND NVL(REC.QTD_RECEBIDA_LOJA, 0) = 0 THEN 'EM TRANSITO'
                WHEN S.QTD_TRANSITO_ATUAL > 0 THEN 'EM TRANSITO'
                WHEN C.SITUACAOPED = 'C' OR S.STATUS_ITEM_ATUAL = 'C' THEN 'CANCELADO'
                WHEN C.SITUACAOPED IN ('D', 'A', 'L', 'P', 'S', 'W', 'R') AND NVL(X.QTD_EXPEDIDA_CD, 0) = 0 THEN 'EM SEPARACAO CD'
                WHEN C.SITUACAOPED = 'F' AND NVL(X.QTD_EXPEDIDA_CD, 0) = 0 THEN 'CORTADO NF'
                ELSE 'NAO ATENDIDO'
            END AS STATUS_ATENDIMENTO
        FROM ITENS_SOLICITADOS S
        INNER JOIN CAPA_PEDIDOS C ON C.NROPEDIDOSUPRIM = S.NROPEDIDOSUPRIM AND C.LOJA_DESTINO = S.NROEMPRESA
        INNER JOIN DADOS_PRODUTO PR ON PR.SEQPRODUTO = S.SEQPRODUTO
        LEFT JOIN ITENS_EXPEDIDOS_CD X ON X.NROPEDIDOSUPRIM = S.NROPEDIDOSUPRIM AND X.NROEMPRESA = S.NROEMPRESA AND X.SEQPRODUTO = S.SEQPRODUTO
        LEFT JOIN ITENS_RECEBIDOS_LOJA REC ON REC.NROPEDIDOSUPRIM = S.NROPEDIDOSUPRIM AND REC.NROEMPRESA = S.NROEMPRESA AND REC.SEQPRODUTO = S.SEQPRODUTO
    )
    SELECT
        NUMERO_PEDIDO,
        CD_ORIGEM,
        LOJA_DESTINO,
        DATA_EMISSAO,
        CODIGO_PRODUTO,
        DESCRICAO_PRODUTO,
        QTD_SOLICITADA,
        QTD_CORTADA_CD,
        QTD_EXPEDIDA_CD,
        QTD_EM_TRANSITO,
        QTD_RECEBIDA_LOJA,
        NUMERO_NOTA_FISCAL,
        DATA_EXPEDICAO,
        STATUS_ATENDIMENTO
    FROM BASE_RELATORIO
    WHERE (
        NVL(TRIM(:LS1), 'TODOS') IN ('TODOS', '0 - TODOS', '0', '')
        OR INSTR(TRIM(:LS1), 'TODOS') > 0
        OR STATUS_ATENDIMENTO = TRIM(:LS1)
        OR INSTR(STATUS_ATENDIMENTO, TRIM(:LS1)) > 0
        OR INSTR(TRIM(:LS1), STATUS_ATENDIMENTO) > 0
    )
    ORDER BY DATA_EMISSAO_ORDEM DESC, NUMERO_PEDIDO DESC
)
```
