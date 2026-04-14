---
name: consulta-criacao-filtros
description: 'Crie queries Oracle para a Consulta Criacao do Totvs Consinco com filtros antes do Run. Use quando o usuario mencionar FILTRO, Var-F7, LT1, LS1, NR1, DT1, lista de selecao, cadastro de variaveis ou quiser SQL principal mais configuracao completa da tela.'
argument-hint: 'Objetivo da query, colunas, filtros desejados e regra de negocio'
---

# Consulta Criacao com Filtros

## Objetivo
Use esta skill quando a query precisar abrir filtros antes da execucao na tela Consulta Criacao do Consinco.

Nesta situacao, a entrega nao termina no SQL. Ela so esta completa quando inclui:
- SQL principal.
- Variaveis para cadastrar em `Var - F7`.
- SQL das listas `LSx`, quando houver.
- Passo a passo operacional curto para o usuario configurar a consulta.
- Registro persistente do procedimento na pasta `Aplicativos/gerenciamento_sql/Var-F7/` com o mesmo nome-base da query quando a consulta for nova ou alterada.

Mesmo fora do caso de filtros, se uma query SQL nova for criada em `Aplicativos/gerenciamento_sql/querys/`, registre tambem um procedimento correspondente em `Aplicativos/gerenciamento_sql/Var-F7/`.

## Quando Usar
- O usuario disser FILTRO.
- O usuario quiser escolher loja, data, fornecedor, departamento, categoria ou estoque antes do Run.
- O usuario mencionar `Var - F7`.
- O usuario quiser uma query para Consulta Criacao e nao apenas um `SELECT` solto.

## Regra Inquebravel
Os filtros visuais nao nascem automaticamente do texto SQL.

A query apenas consome variaveis como `#LT1`, `#LS1`, `:DT1` e `:NR1`.
Quem materializa os campos antes do Run e o cadastro manual em `Var - F7`.

## Entrega Obrigatoria

### 1. SQL principal
- Escreva a query completa.
- Consuma as variaveis corretas do Consinco.
- Evite comentarios dentro do SQL final.

### 2. Variaveis para Var - F7
Para cada filtro, informe:
- Nome da variavel.
- Tipo: Literal, Data, Lista ou Numerico.
- Descricao.
- Valor padrao, quando fizer sentido.
- Instrucao ao usuario.

### 3. SQL da lista
Se houver `LSx`, entregue a SQL exata da lista.
Se `#LSx` for comparado diretamente com coluna textual no `WHERE`, entregue a lista retornando os valores ja entre aspas simples.

### 4. Passo a passo operacional
Explique em formato curto como cadastrar cada variavel em `Var - F7`.

### 5. Registro em pasta
Quando estiver criando ou fechando uma query nova com filtros, salve um arquivo de procedimento em `Aplicativos/gerenciamento_sql/Var-F7/` contendo as variaveis, a SQL das listas e o passo a passo operacional.

Se a query criada nao tiver filtros antes do Run, ainda assim salve um registro minimo em `Aplicativos/gerenciamento_sql/Var-F7/` explicando objetivo, ausencia de filtros e eventuais parametros manuais.

## Prefixos Praticos Validados
- `LTx`: Literal.
- `DTx`: Data.
- `LSx`: Lista.
- `NRx`: Numerico.

## Heuristicas de Estabilidade
- Se um filtro textual direto resolver, prefira isso a concatenacoes complexas.
- So use `SELECT ... INTO` quando a escolha visual precisar virar uma chave tecnica.
- Para departamento, um filtro textual em `MAP_CATEGORIA` nivel 1 costuma ser mais estavel do que uma lista concatenada com codigo.
- Sempre avise que a SQL da lista deve ser cadastrada dentro da propria variavel `LSx`.
- Em filtros opcionais, prefira sentinelas explicitas como `0` e `TODOS` em vez de depender de campo vazio.
- Se `LSx` começar a falhar por parser ou expansao de macro, substitua por `LTx` quando o usuario puder digitar o valor.
- Se `#LSx` aparecer em comparacao textual direta, a lista deve retornar o texto ja quoted, por exemplo `'TODOS'`.
- Em listas textuais, escapar aspas do conteudo antes de encapsular o valor final.
- Em consultas pesadas, empurre filtros seletivos para subqueries agregadas antes dos joins mais caros.

## Formato de Resposta
Ao responder, use sempre esta estrutura:
1. Objetivo da consulta.
2. SQL principal.
3. Variaveis para cadastrar em `Var - F7`.
4. SQL das listas `LSx`, quando houver.
5. Passo a passo curto de configuracao.
6. Registro persistente na pasta `Var-F7`, quando houver criacao ou ajuste de query no workspace.

## Recursos Locais
- Leia `Aplicativos/gerenciamento_sql/aprendizado/aprendizado_filtros_consulta_criacao.md` antes de montar filtros pre-execucao.
- Reaproveite tambem `Aplicativos/gerenciamento_sql/aprendizado/aprendizado_filtros_categorias_embalagem.md` quando houver departamento, categoria ou embalagem.