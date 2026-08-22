# Var-F7 - consulta_min_max_geral

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/consulta_min_max_geral.sql`

## Objetivo
Consulta unificada de Mínimo e Máximo (Secos, Bebidas, Perfumaria, Limpeza, Pet, Leite, Carvão e Perecíveis em geral) contemplando todas as lojas e CDs (incluindo CD 16), pedidos de compra pendentes, pedidos de transferência, trânsito, vendas no período, pontos extras e **Fornecedor Principal** da família do produto.

## Colunas de Saída
- `DEPARTAMENTO`
- `COMPRADOR`
- `CODIGO_EMPRESA`
- `CODIGO_PRODUTO`
- `DESCRICAO_PRODUTO`
- `FORMA_ABASTECIMENTO`
- `DATA_CADASTRO_PRODUTO`
- `STATUS_COMPRA`
- `EMBL_COMPRA`
- `EMBL_TRANSFERENCIA`
- `QUANTIDADE_DISPONIVEL`
- `QTD_PEND_PEDCOMPRA`
- `QTD_PEND_PEDTRANSF`
- `QTD_EM_TRANSITO`
- `QTD_VENDIDA_PERIODO`
- `QUANTIDADE_ESTOQUE_MINIMO`
- `QUANTIDADE_ESTOQUE_MAXIMO`
- `MINIMO_PONTO_EXTRA`
- `MAXIMO_PONTO_EXTRA`
- `DIAS_PESQUISA`
- `COD_FORNECEDOR`
- `FORNECEDOR`

## Variáveis para cadastrar em Var - F7

### NR1
- Tipo: Numérico
- Descrição: Dias de venda (ontem para trás)
- Valor padrão: `90`
- Regra aplicada no SQL:
  - Data inicial: `TRUNC(SYSDATE) - NVL(:NR1, 90)`
  - Data final: `< TRUNC(SYSDATE)`

### NR2
- Tipo: Numérico
- Descrição: Código do Produto (Opcional - 0 para todos)
- Valor padrão: `0`
- Regra aplicada no SQL:
  - `(NVL(:NR2, 0) = 0 OR A.SEQPRODUTO = :NR2)`

## Passo a passo operacional
1. Abrir a consulta na tela Consulta Criação (Consinco).
2. Clicar em `Var - F7`.
3. Cadastrar `NR1` na aba Numérico com descrição `Dias de venda (ontem para trás)` e padrão `90`.
4. Cadastrar `NR2` na aba Numérico com descrição `Código do Produto` e padrão `0`.
5. Salvar as variáveis.
6. Executar a consulta.
