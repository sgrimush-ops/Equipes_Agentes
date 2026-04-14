# Aprendizado: Filtros na Consulta Criacao do Consinco

Este documento consolida a descoberta pratica sobre como fazer uma query abrir campos de filtro antes do Run na tela Consulta Criacao do Consinco.

## Descoberta principal
- Os filtros visuais nao nascem apenas do texto SQL.
- A query apenas consome variaveis como `#LT1`, `#LS1`, `:DT1` e `:NR1`.
- Quem materializa os campos antes da execucao e o cadastro manual em `Var - F7`.

## Regra operacional
Quando o usuario pedir uma query com a palavra FILTRO, a entrega deve incluir sempre tres partes:

1. SQL principal da consulta.
2. Mapa das variaveis a cadastrar em `Var - F7`.
3. SQL da lista para variaveis do tipo `LSx`, quando houver.

## Prefixos praticos validados
- `LTx`: Literal.
- `DTx`: Data.
- `LSx`: Lista.
- `NRx`: Numerico.

## O que entregar junto da query

### Para variavel Literal
- Descricao.
- Valor padrao.
- Instrucao ao usuario.

### Para variavel Numerica
- Descricao.
- Valor padrao.
- Instrucao ao usuario.

### Para variavel Lista
- Descricao.
- Tipo de retorno.
- Instrucao ao usuario.
- SQL exata da lista.

## Padrao de ensino obrigatorio
- Explicar que a tela de filtro nao e inferida automaticamente.
- Explicar que a SQL da lista deve ser cadastrada dentro da propria variavel `LSx`.
- Explicar que, sem o cadastro em `Var - F7`, o filtro nao aparece mesmo que a query use a variavel.

## Heuristica de estabilidade
- Se um filtro puder ser resolvido por texto direto, prefira isso a concatenacoes complexas com `SELECT ... INTO`.
- Para departamento, um filtro textual simples em `MAP_CATEGORIA` nivel 1 costuma ser mais estavel do que listas concatenadas por codigo e descricao.
- So use `SELECT ... INTO` quando realmente precisar converter uma escolha textual para chave tecnica.
- Para filtros opcionais na Consulta Criacao, prefira sentinelas explicitas como `0` e `TODOS` em vez de depender de campo vazio.
- Se `LSx` comecar a gerar erros de parser ou expansao de macro, substitua por `LTx` textual sempre que o filtro aceitar digitacao direta.
- Se `#LSx` for usado em comparacao textual direta no `WHERE`, a SQL da lista deve devolver o valor ja entre aspas simples.
- Para listas textuais, escapar aspas do conteudo com `REPLACE(campo, '''', '''''')` antes de encapsular o retorno.
- Para consultas pesadas, aplique o filtro de quantidade minima o mais cedo possivel, em subquery agregada, antes dos joins caros.

## Regra concreta validada
Quando a query tiver um trecho como:

```sql
AND UPPER(CAMPO_TEXTO) = UPPER(#LS2)
```

a lista `LS2` deve devolver algo no formato:

```sql
SELECT '''TODOS'''
FROM DUAL
UNION
SELECT DISTINCT '''' || REPLACE(CAMPO_TEXTO, '''', '''''') || ''''
FROM TABELA
WHERE CAMPO_TEXTO IS NOT NULL
```

## Exemplo minimo de consumo no SQL
```sql
SELECT
    A.SEQPRODUTO,
    A.DESCCOMPLETA
FROM MAP_PRODUTO A
INNER JOIN MRL_PRODUTOEMPRESA B ON A.SEQPRODUTO = B.SEQPRODUTO
WHERE B.NROEMPRESA IN (#LT1)
  AND B.ESTQLOJA > :NR1
```

## Checklist final
- A query usa as variaveis corretas.
- As variaveis foram cadastradas em `Var - F7`.
- A lista `LSx` foi testada dentro da tela da propria variavel.
- O usuario recebeu o passo a passo de cadastro, nao apenas o SQL.
- Se houver filtros amplos como `TODOS`, revisar se a query corta massa cedo o suficiente para nao travar.