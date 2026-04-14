# Var-F7 - abc_vendas_formato_comprador

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/abc_vendas_formato_comprador.sql`

## Objetivo
Consulta ABC de vendas no formato comprador com filtros antes do Run para:
- data inicial de venda
- data final de venda
- codigo do fornecedor
- comprador digitado
- quantidade vendida maior que

## Versao homologada
- Status: homologada como padrao atual para Consulta Criacao com filtros opcionais estaveis.
- Estrategia validada:
	- `DT1` e `DT2` para periodo.
	- `LT2` literal com `0 = todos` para fornecedor.
	- `LT3` literal com `TODOS = todos` para comprador.
	- `NR1` aplicado cedo em subquery agregada para cortar volume antes dos joins pesados.
- Motivo da homologacao:
	- remove dependencia de lista `LSx` em filtro opcional sensivel.
	- evita depender de campo vazio para liberar Run.
	- reduz risco de parser do SGI falhar em listas e macros.
	- melhora desempenho quando o usuario informa `TODOS` no comprador.

## Variaveis para cadastrar em Var - F7

### DT1
- Tipo: Data
- Descricao: Data Inicial Venda
- Valor padrao: definir conforme rotina do usuario
- Instrucao p/ o usuario: Informe a data inicial do periodo de venda

### DT2
- Tipo: Data
- Descricao: Data Final Venda
- Valor padrao: Data de hoje
- Instrucao p/ o usuario: Informe a data final do periodo de venda

### LT2
- Tipo: Literal
- Descricao: Codigo Fornecedor
- Valor padrao: 0
- Instrucao p/ o usuario: Informe o codigo do fornecedor. Use 0 para considerar todos

### LT3
- Tipo: Literal
- Descricao: Comprador
- Valor padrao: TODOS
- Instrucao p/ o usuario: Informe o comprador exatamente como cadastrado ou use TODOS

### NR1
- Tipo: Numerico
- Descricao: Qtd Vendida Maior Que
- Valor padrao: 0
- Instrucao p/ o usuario: Informe a quantidade vendida minima para o filtro

## Passo a passo operacional
1. Abrir a consulta na tela Consulta Criacao.
2. Clicar em Var - F7.
3. Cadastrar DT1 na aba Data com descricao Data Inicial Venda.
4. Cadastrar DT2 na aba Data com descricao Data Final Venda.
5. Cadastrar LT2 na aba Literal com descricao Codigo Fornecedor.
6. Definir LT2 com valor padrao 0 para considerar todos os fornecedores.
7. Cadastrar LT3 na aba Literal com descricao Comprador.
8. Definir LT3 com valor padrao TODOS.
9. Cadastrar NR1 na aba Numerico com descricao Qtd Vendida Maior Que.
10. Salvar as variaveis.
11. Executar a consulta.

## Observacoes
- As colunas originais da consulta foram preservadas.
- O periodo de venda agora e controlado por DT1 e DT2.
- O fornecedor e filtrado por codigo digitado em `LT2`; use `0` para considerar todos.
- O comprador agora usa um campo literal `LT3`; use `TODOS` para nao restringir o filtro.
- Essa troca remove a dependencia do parser de lista `LS2`, que estava causando os erros do SGI.
- A consulta retorna apenas itens com quantidade vendida maior que `NR1`.
- O corte de `NR1` foi movido para uma subquery agregada antes dos joins mais caros, reduzindo custo quando o filtro de comprador estiver amplo.
