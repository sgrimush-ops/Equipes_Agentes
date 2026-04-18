# Var-F7 - abc_vendas_formato_comprador_dropdown_ultima_entrada_cd_relatorio_impressao

## Query vinculada
- Arquivo SQL: Aplicativos/gerenciamento_sql/querys/abc_vendas_formato_comprador_dropdown_ultima_entrada_cd_relatorio_impressao.sql

## Objetivo
Versao preparada para sair mais pronta no Quick Report do Consinco, com os mesmos dados principais, mas titulos curtos e descricao reduzida para caber melhor na impressao.

## Quando usar esta versao
- Use quando a consulta de impressao ainda ficar larga demais no Quick Report.
- Esta versao preserva os dados relevantes, mas encurta os titulos e a descricao do produto para ajudar a caber na pagina.
- O filtro de comprador segue a regra de ouro homologada: lista no formato codigo - apelido, filtrando por SEQCOMPRADOR.

## Colunas desta versao
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

## Passo a passo curto
1. Abrir a tela Consulta Criacao.
2. Cadastrar a SQL desta consulta de relatorio para impressao.
3. Abrir Var - F7 e cadastrar DT1, DT2, LT2, LS3 e NR1.
4. Dentro da variavel LS3, cadastrar a SQL da lista informada acima.
5. Deixar LS3 com valor padrao 0 - TODOS para considerar todos os compradores.
6. Executar a consulta com Run.
7. Na grade de resultado, clicar no icone de impressora para abrir o Quick Report.

## Observacoes
- Esta versao existe especificamente para impressao mais compacta.
- As colunas de comprador e fornecedor principal continuam fora da grade.
- PRODUTO foi reduzido com SUBSTR(..., 1, 55) para caber melhor no Quick Report.
- A ordenacao ficou por SUBGRUPO crescente e QTD_VDA decrescente.