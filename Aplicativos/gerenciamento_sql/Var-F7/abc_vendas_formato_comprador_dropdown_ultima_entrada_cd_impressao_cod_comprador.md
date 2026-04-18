# Var-F7 - abc_vendas_formato_comprador_dropdown_ultima_entrada_cd_impressao_cod_comprador

## Query vinculada
- Arquivo SQL: Aplicativos/gerenciamento_sql/querys/abc_vendas_formato_comprador_dropdown_ultima_entrada_cd_impressao_cod_comprador.sql

## Objetivo
Versao de impressao da consulta ABC preparada para Quick Report, com filtro de comprador por dropdown exibindo codigo e apelido, sem precisar digitar nome completo.

## Quando usar esta versao
- Use quando quiser selecionar o comprador em lista sem digitar o nome completo.
- A lista mostra codigo e apelido do comprador.
- O filtro continua usando o codigo do comprador ligado em MAP_FAMDIVISAO.SEQCOMPRADOR, mas a selecao fica mais amigavel.

## Colunas desta versao
- SUBGRUPO
- CODIGO_PRODUTO
- DESCRICAO_PRODUTO
- EMBALAGEM
- PERC_ACM
- PRECO_CUSTO
- PRECO_VENDA
- MARGEM_ATUAL
- MARGEM_OBJETIVA
- QTD_VENDIDA
- ESTOQUE_MINIMO
- ESTOQUE_MAXIMO
- ESTOQUE_LOJA
- ESTOQUE_DEPOSITO
- PENDENTE_EXPEDIR_CD
- DATA_ULTIMA_COMPRA_CD
- QTD_ULTIMA_COMPRA_CD

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

## Passo a passo curto
1. Abrir a tela Consulta Criacao.
2. Cadastrar a SQL desta consulta de impressao.
3. Abrir Var - F7 e cadastrar DT1, DT2, LT2, LS3 e NR1.
4. Dentro da variavel LS3, cadastrar a SQL da lista informada acima.
5. Deixar LS3 com valor padrao 0 - TODOS para considerar todos os compradores.
6. Executar a consulta com Run.
7. Na grade de resultado, clicar no icone de impressora para abrir o Quick Report.

## Observacoes
- Esta versao nao substitui a consulta principal; ela existe como alternativa mais estavel para impressao.
- Esta versao preserva as colunas da versao completa e remove apenas os equivalentes de COMPRADOR, CODIGO_FORNECEDOR_PRINCIPAL e FORNECEDOR_PRINCIPAL.
- DATA_ULTIMA_COMPRA_CD e exibida como DD/MM/YYYY.
- A lista LS3 mostra codigo e apelido, mas a query extrai apenas o codigo para filtrar o comprador.