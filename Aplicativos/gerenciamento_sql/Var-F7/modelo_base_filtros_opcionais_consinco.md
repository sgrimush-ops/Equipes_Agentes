# Var-F7 - modelo_base_filtros_opcionais_consinco

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/modelo_base_filtros_opcionais_consinco.sql`

## Objetivo
Modelo-base para novas consultas Consinco na tela Consulta Criacao com filtros opcionais estaveis antes do Run.

Este modelo foi criado para reaproveitar o padrao que se mostrou mais seguro no workspace:
- periodo com `DTx`
- conjunto de empresas com `#LTx`
- fornecedor opcional com literal e sentinela `0`
- comprador opcional com literal e sentinela `TODOS`
- corte de venda minima aplicado cedo em subquery agregada

## Quando reaproveitar
- Quando a nova consulta precisar filtros antes do Run sem depender de `LSx` sensivel.
- Quando houver risco de alto volume e for necessario cortar produtos cedo.
- Quando fornecedor e comprador puderem ser informados manualmente pelo usuario.

## Versao homologada
- Status: modelo-base homologado para novos desenvolvimentos no workspace.
- Regra principal: nao trocar `LT2` e `LT3` por lista `LSx` sem evidencia de que a lista e realmente necessaria e estavel.

## Variaveis para cadastrar em Var - F7

### LT1
- Tipo: Literal
- Descricao: Empresas
- Valor padrao: 1,2,3
- Instrucao p/ o usuario: Informe as empresas separadas por virgula, sem aspas

### DT1
- Tipo: Data
- Descricao: Data Inicial Venda
- Valor padrao: definir conforme rotina do usuario
- Instrucao p/ o usuario: Informe a data inicial do periodo

### DT2
- Tipo: Data
- Descricao: Data Final Venda
- Valor padrao: Data de hoje
- Instrucao p/ o usuario: Informe a data final do periodo

### LT2
- Tipo: Literal
- Descricao: Codigo Fornecedor
- Valor padrao: 0
- Instrucao p/ o usuario: Informe o codigo do fornecedor ou use 0 para considerar todos

### LT3
- Tipo: Literal
- Descricao: Comprador
- Valor padrao: TODOS
- Instrucao p/ o usuario: Informe o comprador exatamente como cadastrado ou use TODOS

### NR1
- Tipo: Numerico
- Descricao: Qtd Vendida Maior Que
- Valor padrao: 0
- Instrucao p/ o usuario: Informe a quantidade vendida minima

## Passo a passo operacional
1. Abrir a consulta na tela Consulta Criacao.
2. Clicar em Var - F7.
3. Cadastrar LT1 na aba Literal com descricao Empresas.
4. Cadastrar DT1 na aba Data com descricao Data Inicial Venda.
5. Cadastrar DT2 na aba Data com descricao Data Final Venda.
6. Cadastrar LT2 na aba Literal com descricao Codigo Fornecedor.
7. Definir LT2 com valor padrao 0.
8. Cadastrar LT3 na aba Literal com descricao Comprador.
9. Definir LT3 com valor padrao TODOS.
10. Cadastrar NR1 na aba Numerico com descricao Qtd Vendida Maior Que.
11. Salvar as variaveis.
12. Executar a consulta.

## Observacoes
- Esse modelo evita depender de lista `LSx` para filtros opcionais que podem ser digitados.
- Se uma futura consulta realmente precisar lista, so introduzir `LSx` depois de validar que a tela aceita a SQL da lista sem erro.
- Se o volume da consulta crescer, manter o filtro seletivo dentro da subquery agregada de vendas antes dos joins caros.