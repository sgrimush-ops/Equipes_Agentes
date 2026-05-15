# Var-F7 - ranking_vendas_subgrupo_fornecedor_v3

## Query vinculada
- Arquivo SQL: Aplicativos/gerenciamento_sql/querys/a.ranckng_vendas_subgrupo_fornecedor_v3.sql

## Objetivo
Ranking de fornecedores por valor de venda, compra, bonificacao e custo de estoque bruto (CD + Lojas), com filtro opcional por comprador e modo consolidado/detalhado. Inclui linha de TOTAL GERAL via UNION ALL.

## Variaveis para cadastrar em Var - F7

### DT1
- Tipo: Data
- Descricao: Data Inicial do Periodo

### DT2
- Tipo: Data
- Descricao: Data Final do Periodo

### LS1
- Tipo: Lista
- Descricao: Comprador
- Valor padrao: 0 - TODOS
- Regra: selecionar pela lista no formato codigo - apelido

### LT2
- Tipo: Literal
- Descricao: Modo de Exibicao
- Valor padrao: D
- Regra: D = Detalhado (mostra comprador individual), C = Consolidado

### NR1
- Tipo: Numerico
- Descricao: Limite de Linhas (Top N)
- Valor padrao: 50
- Regra: quantidade maxima de fornecedores retornados no ranking

## SQL da lista LS1

A variavel LS1 deve ser cadastrada como Lista. Cole a SQL abaixo dentro da variavel:

```sql
SELECT '0 - TODOS' AS COMPRADOR
FROM DUAL
UNION
SELECT DISTINCT
    TO_CHAR(C.SEQCOMPRADOR) || ' - ' || NVL(C.APELIDO, C.COMPRADOR) AS COMPRADOR
FROM MAX_COMPRADOR C
WHERE C.SEQCOMPRADOR IS NOT NULL
```

IMPORTANTE: como a query usa `#LS1` (macro de texto), a SQL da lista DEVE retornar valores ja entre aspas simples para evitar ORA-00904. Se o Var-F7 ja esta configurado e funcionando, nao altere.

## CGOs de Compra
A query classifica notas fiscais de entrada usando CGO_EFETIVA:
- CGOs 1, 28, 70 = Compra normal (VLR_COMPRADO_TOTAL)
- CGOs 100, 101 = Bonificacao (VLR_BONIFICADO_TOTAL)

## Passo a passo curto
1. Cadastre a query na Consulta Criacao.
2. Abra Var - F7 e cadastre DT1, DT2, LS1, LT2 e NR1 com os tipos acima.
3. Dentro da variavel LS1, cadastre a SQL da lista exatamente como informado.
4. LT2 controla se os resultados vem agrupados por comprador (D) ou consolidados (C).
5. NR1 limita quantos fornecedores aparecem no ranking (padrao 50).

## Observacoes
- A variavel LS1 usa macro `#LS1` no SQL principal. A SQL da lista no Var-F7 deve retornar valores ja entre aspas simples para evitar ORA-00904.
- A segunda parte da query (UNION ALL com TOTAL GERAL) repete os mesmos joins e filtros para garantir que o totalizador reflita exatamente o mesmo universo de dados.
