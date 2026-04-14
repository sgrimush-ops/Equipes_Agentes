# Aprendizado: ABC Vendas Formato Comprador com Filtros

Este documento consolida as descobertas praticas feitas ao adaptar a query `abc_vendas_formato_comprador.sql` para a tela Consulta Criacao do Consinco.

## Objetivo do caso
Adicionar filtros antes do Run sem alterar as colunas atuais da consulta:
- data inicial
- data final
- codigo do fornecedor
- comprador
- quantidade vendida minima

## O que se provou estavel

### 1. Fornecedor opcional por codigo
- O caminho estavel e usar campo `Literal`, nao `Numerico`, quando o componente visual precisa aceitar um valor especial para "todos".
- O padrao aprovado foi `LT2` com valor padrao `0`.
- Regra: `0 = todos`.

### 2. Comprador opcional
- O caminho com `LS2` e lista de comprador gerou comportamento instavel no parser do Consinco.
- O caminho estavel foi abandonar lista para comprador e usar `LT3` literal com valor padrao `TODOS`.
- Regra: `TODOS = nao restringe comprador`.

### 2.1. Comprador por dropdown validado
- O dropdown de comprador tambem pode funcionar no Consinco, desde que a lista `LS2` devolva o valor textual ja entre aspas simples.
- Exemplo validado: a opcao `TODOS` precisa chegar ao SQL principal como `'TODOS'`, e nao como `TODOS`.
- Regra: quando `#LSx` for comparado diretamente com coluna textual no `WHERE`, a SQL da lista deve devolver o texto ja quoted.

### 3. Filtro de quantidade vendida
- Nao basta filtrar no `HAVING` final quando a consulta tem muitos joins pesados.
- Quando o usuario escolhe fornecedor/comprador amplos, a consulta pode processar produtos demais antes de cortar a massa.
- O padrao estavel e empurrar o corte de `NR1` para uma subquery previa por produto, antes dos joins pesados.

## O que se provou instavel

### 1. Lista `LSx` para comprador
- Lista com `UNION`, `ORDER BY`, subquery derivada ou join ANSI no `Var - F7` pode falhar mesmo que seja SQL Oracle valida.
- Mesmo quando a lista abre, a macro resultante pode ser expandida como texto bruto e quebrar no `WHERE` principal se o retorno nao vier quoted.

### 2. Campo vazio como opcional
- Em varios componentes da Consulta Criacao, deixar vazio nao significa necessariamente `NULL` util.
- Em alguns casos o botao Run nao libera, ou a tela se comporta de forma inconsistente.
- Preferir sempre um valor sentinela explicito:
  - `0` para codigo numerico em campo literal
  - `TODOS` para filtro textual

### 3. SELECT INTO para filtro textual opcional
- So usar `SELECT ... INTO` quando for realmente necessario converter uma escolha visual para chave tecnica.
- Em filtros opcionais do Consinco, isso aumenta a superficie de erro e deve ser evitado se o filtro textual direto resolver.

## Padroes finais aprovados neste caso

### Variaveis Var-F7
- `DT1`: data inicial
- `DT2`: data final
- `LT2`: codigo fornecedor, valor padrao `0`
- `LT3`: comprador, valor padrao `TODOS`
- `NR1`: quantidade vendida minima

### Variante validada com dropdown
- `LS2`: comprador em dropdown, retornando texto ja entre aspas simples

### Regras de interpretacao
- `LT2 = 0` -> todos os fornecedores
- `LT3 = TODOS` -> todos os compradores
- `NR1` deve ser aplicado cedo, em subquery de vendas agregadas por produto
- `#LS2` em comparacao textual direta precisa expandir como `'VALOR'`, nunca como `VALOR` sem aspas

## Regra de performance
- Se houver filtro amplo como `TODOS`, nunca confiar apenas em `HAVING` no fim da query para cortar massa.
- Fazer prefiltragem por produto no periodo, com `HAVING SUM(QTDVDA) > :NR1`, antes dos joins de BI, custo e hierarquia.

## Regra de processo
- Diante de prints e erros do Consinco, parar tentativa exploratoria cedo.
- Priorizar apenas padroes ja validados por modelos funcionais ou evidencias da propria tela.
- Sempre registrar a conclusao em `Var-F7/` e em `aprendizado/`.

## SQL validada da lista textual
```sql
SELECT '''TODOS''' AS COMPRADOR
FROM DUAL
UNION
SELECT DISTINCT '''' || REPLACE(COMPRADOR, '''', '''''') || '''' AS COMPRADOR
FROM MAX_COMPRADOR
WHERE COMPRADOR IS NOT NULL
```

## Regra especifica consolidada
- Se a lista `LSx` alimentar `#LSx` em comparacao textual direta no `WHERE`, a lista deve devolver o valor final com aspas simples.
- Se o valor textual puder conter aspas, escapar com `REPLACE(valor, '''', '''''')` antes de encapsular.