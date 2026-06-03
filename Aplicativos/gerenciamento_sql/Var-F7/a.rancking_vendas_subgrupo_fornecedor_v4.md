# Var-F7 - a.rancking_vendas_subgrupo_fornecedor_v4

## Query vinculada
- Arquivo SQL: [Aplicativos/gerenciamento_sql/querys/a.rancking_vendas_subgrupo_fornecedor_v4.sql](../querys/a.rancking_vendas_subgrupo_fornecedor_v4.sql)

## Objetivo
Ranking de vendas, compras, bonificacoes, custo e incineracao por fornecedor, com filtros de periodo, empresas e modo de exibicao informados antes do Run na Consulta Criacao.

## SQL principal
A query consome os filtros abaixo:
- `#LS1` para comprador.
- `:DT1` e `:DT2` para periodo.
- `:LT2` para consolidado ou detalhado.

## Variaveis para cadastrar em Var - F7

### LS1
- Tipo: Lista
- Descricao: Comprador
- Instrucao p/ o usuario: Selecione o comprador no formato codigo - comprador. A lista deve retornar o texto ja montado.

### LT2
- Tipo: Literal
- Descricao: Consolidado
- Valor padrao: D
- Instrucao p/ o usuario: Use C para consolidado e D para detalhado.

### DT1
- Tipo: Data
- Descricao: Data Inicial
- Valor padrao: 01/05/2026
- Instrucao p/ o usuario: Informe a data inicial do periodo.

### DT2
- Tipo: Data
- Descricao: Data Final
- Valor padrao: 01/06/2026
- Instrucao p/ o usuario: Informe a data final do periodo.

## Passo a passo operacional
1. Abrir a consulta na tela Consulta Criacao.
2. Clicar em Var - F7.
3. Cadastrar DT1 e DT2 com o periodo desejado.
4. Cadastrar LS1 com a SQL da lista de comprador.
5. Cadastrar LT2 com valor D ou C.
6. Salvar as variaveis e executar a consulta.

## Observacoes
- O filtro de comprador agora e informado pelo usuario via `#LS1`.
- Para manter a consulta mais rapida, o corte de categoria continua antes dos joins pesados.
