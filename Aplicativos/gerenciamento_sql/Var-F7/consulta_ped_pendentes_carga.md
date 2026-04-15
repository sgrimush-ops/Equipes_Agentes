# Var-F7 - consulta_ped_pendentes_carga

## Query vinculada
- Arquivo SQL: Aplicativos/gerenciamento_sql/querys/consulta_ped_pendentes_carga.sql

## Objetivo
Consulta de pedidos pendentes de carga com filtros antes do Run para:
- data inicial
- data final
- departamento

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

## SQL das listas
- Nao ha LSx nesta consulta.
- O filtro de departamento foi revertido para LT1 literal com sentinela TODOS para evitar erro de parser e expansao de macro no Consinco.

## Passo a passo operacional
1. Abrir a consulta na tela Consulta Criacao.
2. Clicar em Var - F7.
3. Cadastrar DT1 na aba Data com descricao Data Inicial Emissao.
4. Cadastrar DT2 na aba Data com descricao Data Final Emissao.
5. Cadastrar LT1 na aba Literal com descricao Departamento.
6. Definir LT1 com valor padrao TODOS.
7. Salvar as variaveis.
8. Executar a consulta e informar os filtros antes do Run.

## Observacoes
- Os filtros visuais antes do Run nao nascem apenas do SQL; eles dependem do cadastro manual em Var - F7.
- O departamento e filtrado pelo nivel 1 da hierarquia em MAP_CATEGORIA, vinculado a familia do produto.
- O ORA-00907 observado nesta consulta e compativel com falha de expansao da variavel LS1 no parser do Consinco.
- O fallback estavel do workspace para esse caso e usar LT1 literal com sentinela TODOS.
- A data e o usuario da conferencia sao buscados em MLO_ATIVIDADE, MLO_TAREFA, MLO_TAREFAPRODUT e MLO_PRODUTIVO.
- O filtro operacional usado e CODTIPATIVIDADE = 'CS', conforme evidencia do monitoramento da rotina.
- As chaves usadas nessa busca sao NROCARGA, CODDEPOSSEPAR, SEQLOTE, NROQUEBRA e NROEMPRESA, vinculadas a partir da MLO_CARGAECOLETOR.
- Se nao houver atividade CS correspondente ou se a tarefa nao tiver produtivo vinculado, as colunas DATA_CONFERENCIA e USUARIO_CONFERENCIA podem ficar vazias.
