# Var-F7 - consulta_xmls_pendentes_completo

## Query vinculada
- Arquivo SQL: Aplicativos/gerenciamento_sql/querys/consulta_xmls_pendentes_completo.sql

## Objetivo
Consultar notas de entrada com situacao, fornecedor e itens, com filtros antes do Run na Consulta Criacao.

## SQL principal
A SQL principal esta no arquivo acima e agora inclui:
- LS1 para filtro direto de situacao.
- LS2 para modo inverso (exclusao), removendo a situacao escolhida em LS1.
- Regra pratica para seu caso: LS1 = I e LS2 = E retorna todas as situacoes, exceto I.

## Variaveis para cadastrar em Var - F7

### LT1
- Tipo: Literal
- Descricao: Loja (codigos separados por virgula)
- Valor padrao: 0
- Instrucao p/ o usuario: Use 0 para todas ou informe codigos (ex.: 1,2,5)

### DT1
- Tipo: Data
- Descricao: Data inicial emissao
- Valor padrao: data atual - 7
- Instrucao p/ o usuario: Informe a data inicial

### DT2
- Tipo: Data
- Descricao: Data final emissao
- Valor padrao: data atual
- Instrucao p/ o usuario: Informe a data final

### LT2
- Tipo: Literal
- Descricao: Fornecedor (codigo)
- Valor padrao: 0
- Instrucao p/ o usuario: Use 0 para todos ou informe o codigo do fornecedor

### LT3
- Tipo: Literal
- Descricao: Numero da NF
- Valor padrao: 0
- Instrucao p/ o usuario: Use 0 para todas ou informe o numero da NF

### LT4
- Tipo: Literal
- Descricao: Codigo geral operacao (aceita multiplos codigos)
- Valor padrao: 0
- Instrucao p/ o usuario: Use 0 para todos ou informe um ou mais codigos separados por virgula (ex.: 100,102)

### LS1
- Tipo: Lista
- Descricao: Situacao (filtro direto)
- Valor padrao: T
- Instrucao p/ o usuario: Selecione T para todos ou uma situacao especifica

### LS2
- Tipo: Lista
- Descricao: Modo de filtro de situacao
- Valor padrao: N
- Instrucao p/ o usuario: N aplica filtro normal da LS1; E aplica exclusao da LS1

## SQL das listas LSx

### SQL da LS1 (situacao)
SELECT 'T' AS ITEM FROM DUAL
UNION ALL SELECT 'I' FROM DUAL
UNION ALL SELECT 'R' FROM DUAL
UNION ALL SELECT 'L' FROM DUAL
UNION ALL SELECT 'C' FROM DUAL
UNION ALL SELECT 'X' FROM DUAL

### SQL da LS2 (modo)
SELECT 'N' AS ITEM FROM DUAL
UNION ALL SELECT 'E' FROM DUAL

## Como funciona a combinacao LS1 x LS2
- LS2 = N: filtro normal (igual ao comportamento antigo).
- LS2 = E: filtro inverso (exclui a situacao da LS1).
- Regra de seguranca: se LS2 = E e LS1 = T, a consulta exclui I por padrao.

## Exemplo do seu caso (Exclusao de I)
- LS1 = I
- LS2 = E
Resultado: retorna todas as situacoes, menos I.

## Passo a passo operacional
1. Abra a Consulta Criacao da consulta consulta_xmls_pendentes_completo.
2. Clique em Var - F7.
3. Cadastre as variaveis LT1, DT1, DT2, LT2, LT3, LT4, LS1 e LS2 com os tipos acima.
4. Dentro da LS1, cole a SQL da lista LS1.
5. Dentro da LS2, cole a SQL da lista LS2.
6. Salve as variaveis.
7. No LT4, voce pode informar um unico CGO ou varios separados por virgula, como 100,102.
8. Execute a consulta informando os filtros.

## Observacao importante
Os filtros visuais antes do Run dependem do cadastro em Var - F7; nao sao criados automaticamente apenas pelo SQL.
