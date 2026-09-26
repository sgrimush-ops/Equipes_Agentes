# Var-F7 - Consulta de Devolucao de Compra

## Objetivo
Listar uma linha por nota fiscal de devolucao de compra com loja, numero da NF, codigo e razao social do fornecedor, valores, observacao/motivo da devolucao e as listas de codigos e descricoes dos produtos.

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/consulta_devolucao_compra.sql`

## Variaveis para cadastrar em Var - F7

| Variavel | Tipo | Descricao | Valor padrao |
|---|---|---|---|
| `NR1` | Numerico | Codigo do fornecedor (`SEQPESSOA`) ou `0` para todos | `0` |
| `DT1` | Data | Data inicial de emissao | - |
| `DT2` | Data | Data final de emissao | - |

## Configuracao

Cadastre as variaveis acima em **Var - F7** com os mesmos nomes usados no SQL. Os campos de filtro antes do Run nao nascem apenas do texto da consulta; eles dependem desse cadastro manual.

O campo `OBSERVACAO` usa a observacao do item (`I.OBSERVACAO`) e, quando estiver vazia, utiliza a observacao da nota (`N.OBSERVACAOLF`). Os campos `CODIGOS_PRODUTOS` e `DESCRICOES_PRODUTOS` ficam nas duas ultimas colunas e reune os itens da NF separados por ` / `.

Os dados da NF e as listas de produtos sao agregados separadamente e relacionados por `SEQNF`, `NROEMPRESA` e `TIPNOTAFISCAL`.

A consulta usa o bypass `SELECT * FROM (WITH ...)` porque a Consulta Criacao exige que o primeiro comando seja `SELECT`.