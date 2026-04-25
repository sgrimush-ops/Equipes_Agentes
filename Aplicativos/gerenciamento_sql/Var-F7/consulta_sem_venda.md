# Var-F7 - consulta_sem_venda

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/consulta_sem_venda.sql`

## Objetivo
Listar produtos com baixa venda no periodo de ontem ate 90 dias antes, com filtros de corte para venda, estoque, pedido pendente e idade de cadastro do item.

## SQL principal
- Janela de venda aplicada de forma automatica e fixa: de ontem para tras em 90 dias (`TRUNC(SYSDATE) - 90` ate `< TRUNC(SYSDATE)`).
- Nao precisa digitar datas no filtro.
- Filtros aplicados:
  - Somente itens ativos para compra (`STATUSCOMPRA = 'A'`)
  - Quantidade vendida menor que `:NR1` (padrao 2)
  - Estoque menor que `:NR2` (padrao 2)
  - Pedido pendente menor que `:NR3` (padrao 2)
  - Cadastrado a mais de `:NR4` dias (se `:NR4 = 0`, nao filtra por idade de cadastro)
- Coluna `DATA_CADASTRO_PRODUTO`: usa `TO_CHAR(TRUNC(MAP_PRODUTO.DTAHORINCLUSAO), 'DD/MM/YYYY')` para retornar apenas data formatada (DD/MM/YYYY).

## Variaveis para cadastrar em Var - F7

### LT1
- Tipo: Literal
- Descricao: Departamento
- Valor padrao: TODOS
- Instrucao p/ o usuario: Informe o departamento exatamente como cadastrado ou use TODOS para trazer todos

### NR1
- Tipo: Numerico
- Descricao: Qtd Vendida Menor Que
- Valor padrao: 2

### NR2
- Tipo: Numerico
- Descricao: Estoque Menor Que
- Valor padrao: 2

### NR3
- Tipo: Numerico
- Descricao: Pedido Pendente Menor Que
- Valor padrao: 2

### NR4
- Tipo: Numerico
- Descricao: Cadastrado A Mais De Dias
- Valor padrao: 0
- Instrucao p/ o usuario: Informe a quantidade de dias para trazer apenas itens cadastrados ha mais tempo (ex.: 30). Use 0 para nao aplicar esse filtro.

## Passo a passo operacional
1. Abrir a consulta na tela Consulta Criacao.
2. Clicar em Var - F7.
3. Cadastrar LT1 (Departamento) com padrao TODOS.
4. Cadastrar NR1 (Qtd Vendida Menor Que) com padrao 2.
5. Cadastrar NR2 (Estoque Menor Que) com padrao 2.
6. Cadastrar NR3 (Pedido Pendente Menor Que) com padrao 2.
7. Cadastrar NR4 (Cadastrado A Mais De Dias) com padrao 0.
8. Salvar e executar.

## Observacao importante
Os filtros visuais antes do Run dependem do cadastro de variaveis na tela Var - F7; nao sao criados apenas pelo SQL.
