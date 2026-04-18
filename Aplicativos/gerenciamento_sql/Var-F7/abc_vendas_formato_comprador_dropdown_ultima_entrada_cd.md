# Var-F7 - abc_vendas_formato_comprador_dropdown_ultima_entrada_cd

## Query vinculada
- Arquivo SQL: Aplicativos/gerenciamento_sql/querys/abc_vendas_formato_comprador_dropdown_ultima_entrada_cd.sql

## Objetivo
Consulta ABC de vendas no formato comprador com dropdown de comprador e colunas adicionais de data e quantidade da ultima compra do produto no CD.

## Origem da nova coluna
- A data foi extraida do padrao observado no SQL de referencia em aprendizado/referencia_abc_vendas_consico.sql.
- A quantidade foi extraida do mesmo padrao, usando MRL_PRODUTOEMPRESA.QTDULTCOMPRA.
- Nesta clone, data e quantidade foram agregadas no mesmo bloco do CD para as empresas 15, 16 e 50 com MAX(DTAULTCOMPRA) e MAX(QTDULTCOMPRA).
- Regra de negocio desta versao: considerar somente compra. Nao usar outros tipos de entrada ou movimento.

## Variaveis para cadastrar em Var - F7

### DT1
- Tipo: Data
- Descricao: Data Inicial Venda

### DT2
- Tipo: Data
- Descricao: Data Final Venda

### LT2
- Tipo: Literal
- Descricao: Codigo Fornecedor
- Valor padrao: 0

### LS2
- Tipo: Lista
- Descricao: Comprador
- Tipo de retorno: Texto unico
- Valor padrao: TODOS

### NR1
- Tipo: Numerico
- Descricao: Qtd Vendida Maior Que
- Valor padrao: 0

## SQL da lista LS2
```sql
SELECT '''TODOS''' AS COMPRADOR
FROM DUAL
UNION
SELECT DISTINCT '''' || REPLACE(COMPRADOR, '''', '''''') || '''' AS COMPRADOR
FROM MAX_COMPRADOR
WHERE COMPRADOR IS NOT NULL
```

## Observacoes
- A query original nao foi alterada; esta versao e uma clone.
- A nova coluna se chama DATA_ULTIMA_COMPRA_CD.
- A nova coluna de quantidade se chama QTD_ULTIMA_COMPRA_CD.
- Esta versao ficou intencionalmente restrita a compra, usando DTAULTCOMPRA e QTDULTCOMPRA.
- DATA_ULTIMA_COMPRA_CD e exibida formatada como DD/MM/YYYY para nao mostrar hora zerada no grid.