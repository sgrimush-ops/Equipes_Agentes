# Var-F7 - consulta_ped_pendentes_carga

## Query vinculada
- Arquivo SQL: Aplicativos/gerenciamento_sql/querys/consulta_ped_pendentes_carga.sql

## Objetivo
Consulta de pedidos pendentes de carga com filtros antes do Run para:
- data inicial
- data final
- departamento
- loja destino
- item

A consulta tambem retorna o departamento no grid, o estoque disponivel do CD e, ao final do relatorio, o estoque disponivel da loja destino.
A consulta tambem tenta retornar a data e o usuario da conferencia pela trilha operacional de atividades de conferencia CS.

## Variaveis para cadastrar em Var - F7

### DT1
- Tipo: Data
- Descricao: Data Inicial Emissao
- Valor padrao: definir conforme rotina do usuario
- Instrucao p/ o usuario: Informe a data inicial do periodo

### DT2
- Tipo: Data
- Descricao: Data Final Emissao
- Valor padrao: data atual
- Instrucao p/ o usuario: Informe a data final do periodo

### LT1
- Tipo: Literal
- Descricao: Departamento
- Valor padrao: TODOS
- Instrucao p/ o usuario: Informe o nome do departamento exatamente como cadastrado ou use TODOS para considerar todos

### LT2
- Tipo: Literal
- Descricao: Loja Destino
- Valor padrao: TODOS
- Instrucao p/ o usuario: Informe TODOS para considerar todas, ou informe a loja como codigo (11) ou texto contendo o codigo (11 - LOJA 11)

### NR1
- Tipo: Numerico
- Descricao: Codigo Produto
- Valor padrao: 0
- Instrucao p/ o usuario: Informe o codigo do item para filtrar um produto especifico ou mantenha 0 para trazer todos

## SQL das listas
- Nao ha LSx nesta consulta.
- Os filtros de departamento e loja usam Literais (LT1 e LT2) com sentinela TODOS para evitar falhas de parser e permitir execucao ampla por padrao.
- No filtro LT2, a consulta extrai automaticamente os digitos informados; assim, tanto 11 quanto 11 - LOJA 11 funcionam.
- O filtro de item usa Numerico (NR1) com sentinela 0 para trazer todos quando nao houver codigo informado.

## Passo a passo operacional
1. Abrir a consulta na tela Consulta Criacao.
2. Clicar em Var - F7.
3. Cadastrar DT1 na aba Data com descricao Data Inicial Emissao.
4. Cadastrar DT2 na aba Data com descricao Data Final Emissao.
5. Cadastrar LT1 na aba Literal com descricao Departamento.
6. Definir LT1 com valor padrao TODOS.
7. Cadastrar LT2 na aba Literal com descricao Loja Destino e valor padrao TODOS.
8. Cadastrar NR1 na aba Numerico com descricao Codigo Produto e valor padrao 0.
9. Salvar as variaveis.
10. Executar a consulta e informar os filtros antes do Run.

## Observacoes
- Os filtros visuais antes do Run nao nascem apenas do SQL; eles dependem do cadastro manual em Var - F7.
- O departamento e filtrado pelo nivel 1 da hierarquia em MAP_CATEGORIA, vinculado a familia do produto.
- O ORA-00907 observado nesta consulta e compativel com falha de expansao da variavel LS1 no parser do Consinco.
- O fallback estavel do workspace para esse caso e usar LT1 literal com sentinela TODOS.
- O filtro de loja utiliza LT2 literal com sentinela TODOS.
- O filtro de item utiliza NR1 numerico com sentinela 0.
- A data e o usuario da conferencia sao buscados em MLO_ATIVIDADE, MLO_TAREFA, MLO_TAREFAPRODUT e MLO_PRODUTIVO.
- O filtro operacional usado e CODTIPATIVIDADE = 'CS', conforme evidencia do monitoramento da rotina.
- As chaves usadas nessa busca sao NROCARGA, CODDEPOSSEPAR, SEQLOTE, NROQUEBRA e NROEMPRESA, vinculadas a partir da MLO_CARGAECOLETOR.
- Se nao houver atividade CS correspondente ou se a tarefa nao tiver produtivo vinculado, as colunas DATA_CONFERENCIA e USUARIO_CONFERENCIA podem ficar vazias.
