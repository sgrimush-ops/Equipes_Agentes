# Var-F7 - pesquisa_fornecedor_principal

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/pesquisa_fornecedor_principal.sql`

## Objetivo
Auditar produtos do cadastro e seus respectivos **Fornecedores Principais** (`MAP_FAMFORNEC.PRINCIPAL = 'S'`), cruzando com as Notas Fiscais de Entrada no período (`DT1` a `DT2`) para identificar se a mercadoria entrou pelo fornecedor correto (`MATCH`) ou por outro fornecedor (`DIVERGENCIA`), exibindo o produto mesmo quando não houver compras no período (quando um produto específico for consultado via `NR1`).

## Colunas retornadas
- `EMPRESA`: Número da loja (`NROEMPRESA`). Exibe `0` se o produto não teve entrada no período.
- `NRO_NF_ENTRADA`: Número da Nota Fiscal de Entrada (ou vazio se não houve compra).
- `SERIE_NF`: Série da NF.
- `DATA_ENTRADA`: Data de entrada da mercadoria na loja.
- `CODIGO_PRODUTO`: Código interno do produto (`SEQPRODUTO`).
- `DESCRICAO_PRODUTO`: Descrição completa do produto no cadastro (`MAP_PRODUTO`).
- `COD_FORN_PRINCIPAL`: Código do fornecedor principal cadastrado na família do produto (`MAP_FAMFORNEC`).
- `RAZAO_FORN_PRINCIPAL`: Razão social do fornecedor principal da família.
- `COD_FORN_ENTRADA`: Código do fornecedor que emitiu a Nota Fiscal de Entrada.
- `RAZAO_FORN_ENTRADA`: Razão social do fornecedor da NF de entrada.
- `STATUS_AUDITORIA`: Indicador do resultado da conferência:
  - `SEM COMPRA NO PERIODO`: O produto não teve NF de entrada no intervalo `DT1` a `DT2`.
  - `MATCH - FORNECEDOR PRINCIPAL`: A NF de entrada foi emitida pelo fornecedor marcado como principal na família.
  - `DIVERGENCIA - OUTRO FORNECEDOR`: A NF de entrada foi emitida por um fornecedor diferente do principal.
- `QTD_ENTRADA_NF`: Quantidade do item recebida na NF de entrada.
- `VLR_ENTRADA_NF`: Valor total do item na NF de entrada de compra.

## Fontes e Regras de Performance Aplicadas
- **Bypass do Validador Consinco:** A query inicia obrigatoriamente com um `SELECT * FROM (` externo para envelopar as CTEs (`WITH... AS`), evitando o erro *"A instrução SQL informada, não é uma consulta"*.
- **Sem Comentários no SQL:** Código 100% limpo sem `--` ou `/* */` (exceto os hints de otimização) para não quebrar no parser do módulo Consulta Criação.
- **CTEs Materializadas (`/*+ MATERIALIZE */`):** 
  - `CTE_FORN_PRINCIPAL`: Mapeia em memória os fornecedores principais por família.
  - `CTE_ENTRADAS`: Agrupa em memória os itens recebidos via NF de entrada (`MLF_NOTAFISCAL` + `MLF_NFITEM`) cruzados com `MAX_CODGERALOPER` onde `TIPUSO = 'C'` (filtrando exclusivamente compras reais e descartando entradas de transferência entre filiais/depósitos).

## Colunas adicionais retornadas
- `DEPARTAMENTO`: Nome do Departamento (Categoria Nível 1, Mercadológica).
- `COMPRADOR`: Nome/Apelido do Comprador responsável pela Divisão 1 da família.

## Variáveis para cadastrar em Var - F7

### DT1
- Tipo: Data
- Descrição: Data Inicial de Entrada de Compra
- Instrução: informe a data inicial do período de pesquisa.

### DT2
- Tipo: Data
- Descrição: Data Final de Entrada de Compra
- Instrução: informe a data final do período de pesquisa.

### NR1
- Tipo: Número
- Descrição: Filtro por Código de Produto (`SEQPRODUTO`)
- Valor padrão: 0
- Instrução: digite `0` para listar todos os produtos que tiveram entrada em estoque no período (com seus respectivos status de Match ou Divergência), ou informe o código interno de um produto específico (`SEQPRODUTO`) para auditar apenas ele (exibindo o fornecedor principal mesmo que não tenha tido compra).

### LS1
- Tipo: Lista (Seleção Combobox / `SUBSTR`)
- Descrição: Filtro por Departamento (Categoria Nível 1)
- Instrução: selecione `0 - TODOS` para todos os departamentos, ou escolha um departamento específico.
- SQL da Lista (`LS1`):
```sql
SELECT '0 - TODOS' FROM DUAL
UNION ALL
SELECT TO_CHAR(C.SEQCATEGORIA) || ' - ' || C.CATEGORIA
FROM MAP_CATEGORIA C
WHERE C.NIVELHIERARQUIA = 1
  AND C.TIPCATEGORIA = 'M'
  AND C.STATUSCATEGOR = 'A'
```

### LS2
- Tipo: Lista (Seleção Combobox / `SUBSTR`)
- Descrição: Filtro por Comprador
- Instrução: selecione `0 - TODOS` para todos os compradores, ou escolha um comprador específico.
- SQL da Lista (`LS2`):
```sql
SELECT '0 - TODOS' FROM DUAL
UNION ALL
SELECT TO_CHAR(C.SEQCOMPRADOR) || ' - ' || C.COMPRADOR
FROM MAX_COMPRADOR C
WHERE C.STATUS = 'A'
```

### LS3
- Tipo: Lista (Seleção Combobox / `SUBSTR`)
- Descrição: Filtro por Status da Auditoria (Match vs Divergência)
- Instrução: selecione `0 - TODOS` para ver todos os status, ou filtre especificamente apenas itens em Match ou com Divergência.
- SQL da Lista (`LS3`):
```sql
SELECT '0 - TODOS' FROM DUAL
UNION ALL
SELECT '1 - MATCH (PRINCIPAL)' FROM DUAL
UNION ALL
SELECT '2 - DIVERGENCIA (OUTRO)' FROM DUAL
```
