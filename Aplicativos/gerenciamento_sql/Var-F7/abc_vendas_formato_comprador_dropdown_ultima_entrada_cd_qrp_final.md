# Var-F7 - abc_vendas_formato_comprador_dropdown_ultima_entrada_cd_qrp_final

## Query vinculada
- Arquivo SQL: Aplicativos/gerenciamento_sql/querys/abc_vendas_formato_comprador_dropdown_ultima_entrada_cd_qrp_final.sql

## Objetivo
Versao da consulta preparada para alimentar diretamente o QRP final do relatorio ABC por comprador, com aliases padronizados para o layout derivado de RelProdlojaComp.QRP.

## Quando usar esta versao
- Use quando a meta for casar a query diretamente com o QRP final.
- Esta versao preserva os dados da consulta completa sem as tres colunas removidas do detalhe.
- O filtro de comprador segue a regra de ouro homologada: lista no formato codigo - apelido, filtrando por SEQCOMPRADOR.

## Aliases do detalhe entregues ao QRP
- SUBGRUPO
- COD_PROD
- PRODUTO
- EMB
- PERC_ACM
- PRC_CST
- PRC_VDA
- MARG_ATU
- MARG_OBJ
- QTD_VDA
- EST_MIN
- EST_MAX
- EST_LOJA
- EST_CD
- PEND_CD
- DT_ULT_COMP
- QTD_ULT_COMP

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
- Regra: informar apenas numeros; 0 = todos

### LS3
- Tipo: Lista
- Descricao: Comprador
- Tipo de retorno: Texto unico
- Valor padrao: 0 - TODOS
- Regra: selecionar pela lista no formato codigo - apelido

### NR1
- Tipo: Numerico
- Descricao: Qtd Vendida Maior Que
- Valor padrao: 0

## SQL da lista LS3
```sql
SELECT '''0 - TODOS''' AS COMPRADOR
FROM DUAL
UNION
SELECT DISTINCT
	'''' || TO_CHAR(C.SEQCOMPRADOR) || ' - ' || REPLACE(NVL(C.APELIDO, C.COMPRADOR), '''', '''''') || '''' AS COMPRADOR
FROM MAX_COMPRADOR C
WHERE C.SEQCOMPRADOR IS NOT NULL
```

## Cabecalho esperado no QRP
- Comprador
- Periodo de vendas
- Emissao
- Empresa(s)
- Fornecedor, se LT2 vier preenchido

## Observacoes
- Esta versao e a base de dados para o QRP derivado de RelProdlojaComp.QRP.
- As colunas COMPRADOR, CODIGO_FORNECEDOR_PRINCIPAL e FORNECEDOR_PRINCIPAL permanecem fora do detalhe.
- A ordenacao sai por SUBGRUPO crescente e QTD_VDA decrescente.
- DT_ULT_COMP sai formatada como DD/MM/YYYY.