# Var-F7 - pesquisa_fornecedor_principal

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/pesquisa_fornecedor_principal.sql`

## Objetivo
Identificar e listar auditoria de produtos que tiveram venda no período informado (DT1 a DT2), mas cuja entrada em estoque (Nota Fiscal de Entrada) no período ocorreu por um fornecedor diferente do **Fornecedor Principal** cadastrado na família do produto no Consinco (`MAP_FAMFORNEC.PRINCIPAL = 'S'`).

## Colunas retornadas
- `EMPRESA`: Número da loja (NROEMPRESA).
- `NRO_NF_ENTRADA`: Número da Nota Fiscal de Entrada.
- `SERIE_NF`: Série da NF.
- `DATA_ENTRADA`: Data de entrada da mercadoria na loja.
- `CODIGO_PRODUTO`: Código interno do produto (SEQPRODUTO).
- `DESCRICAO_PRODUTO`: Descrição completa do produto no cadastro (MAP_PRODUTO).
- `COD_FORN_ENTRADA`: Código do fornecedor que emitiu a Nota Fiscal de Entrada.
- `RAZAO_FORN_ENTRADA`: Razão social do fornecedor da NF de entrada.
- `COD_FORN_PRINCIPAL`: Código do fornecedor principal cadastrado na família do produto (`MAP_FAMFORNEC`).
- `RAZAO_FORN_PRINCIPAL`: Razão social do fornecedor principal da família.
- `QTD_ENTRADA_NF`: Quantidade do item recebida na NF de entrada.
- `VLR_ENTRADA_NF`: Valor total do item na NF de entrada.
- `QTD_VENDIDA_PERIODO`: Quantidade total vendida do produto no período analisado (comprova que o item teve saída comercial).

## Fontes e Regras de Performance Aplicadas
- **Bypass do Validador Consinco:** A query inicia obrigatoriamente com um `SELECT * FROM (` externo para envelopar as CTEs (`WITH... AS`), evitando o erro *"A instrução SQL informada, não é uma consulta"*.
- **Sem Comentários no SQL:** Código 100% limpo sem `--` ou `/* */` (exceto os hints de otimização) para não quebrar no parser do módulo Consulta Criação.
- **CTEs Materializadas (`/*+ MATERIALIZE */`):** 
  - `CTE_FORN_PRINCIPAL`: Mapeia em memória os fornecedores principais por família.
  - `CTE_VENDAS`: Isola em memória via `MRL_PRODVENDADIA` os itens que tiveram vendas no período.
  - `CTE_ENTRADAS`: Agrupa em memória os itens recebidos via NF de entrada (`MLF_NOTAFISCAL` + `MLF_NFITEM`) no período.

## Variáveis para cadastrar em Var - F7

### DT1
- Tipo: Data
- Descrição: Data Inicial de Entrada / Venda
- Instrução: informe a data inicial do período de pesquisa.

### DT2
- Tipo: Data
- Descrição: Data Final de Entrada / Venda
- Instrução: informe a data final do período de pesquisa.

### NR1
- Tipo: Número
- Descrição: Filtro por Fornecedor (Entrada/Principal) ou Produto
- Valor padrão: 0
- Instrução: digite `0` para trazer todos os registros com divergência, ou digite o código de um fornecedor (ou produto) específico para auditar apenas ele.
