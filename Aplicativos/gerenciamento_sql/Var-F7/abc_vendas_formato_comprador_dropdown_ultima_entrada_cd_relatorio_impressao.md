# Var-F7 - abc_vendas_formato_comprador_dropdown_ultima_entrada_cd_relatorio_impressao

## Query vinculada
- Arquivo SQL: [Aplicativos/gerenciamento_sql/querys/abc_vendas_formato_comprador_dropdown_ultima_entrada_cd_relatorio_impressao.sql](Aplicativos/gerenciamento_sql/querys/abc_vendas_formato_comprador_dropdown_ultima_entrada_cd_relatorio_impressao.sql)

## Objetivo
Consulta de ABC por fornecedor, subgrupo e produto, com custo bruto/Custo NF parametrizado pela loja de origem do custo. O filtro novo afeta apenas o custo; o restante da consulta permanece no desenho atual.

## Variáveis para cadastrar em Var-F7

### DT1
- Tipo: Data
- Descrição: Data Inicial Venda

### DT2
- Tipo: Data
- Descrição: Data Final Venda

### LT2
- Tipo: Literal
- Descrição: Código Fornecedor
- Valor padrão: 0
- Regra: informar apenas números; 0 = todos

### LS3
- Tipo: Lista
- Descrição: Comprador
- Tipo de retorno: Texto único
- Valor padrão: 0 - TODOS
- Regra: selecionar pela lista no formato código - apelido

### NR1
- Tipo: Numérico
- Descrição: Qtd Vendida Maior Que
- Valor padrão: 0

### NR2
- Tipo: Numérico
- Descrição: Loja de origem do custo
- Valor padrão: 3
- Regra: informe a loja que deve ser usada para calcular o custo bruto/Custo NF

## Passo a passo curto
1. Abrir a tela Consulta Criacao.
2. Cadastrar a SQL desta consulta.
3. Abrir Var - F7 e cadastrar DT1, DT2, LT2, LS3, NR1 e NR2.
4. Deixar NR2 com valor 3 para manter o comportamento atual, ou trocar para a loja desejada.
5. Salvar as variáveis.
6. Informar as datas, o fornecedor, o comprador, a quantidade mínima e a loja de custo.
7. Executar a consulta.

## Observações
- O filtro de NR2 altera apenas a origem do custo bruto em MRL_PRODUTOEMPRESA.CMULTVLRNF.
- O preço de venda continua vindo da loja 3, como já estava homologado.
- O filtro de comprador continua no formato codigo - apelido.

## Query vinculada
- Arquivo SQL: Aplicativos/gerenciamento_sql/querys/abc_vendas_formato_comprador_dropdown_ultima_entrada_cd_relatorio_impressao.sql

## Objetivo
Versao preparada para sair mais pronta no Quick Report do Consinco, com os mesmos dados principais, mas titulos curtos e descricao reduzida para caber melhor na impressao.

## Quando usar esta versao
- Use quando a consulta de impressao ainda ficar larga demais no Quick Report.
- Esta versao preserva os dados relevantes, mas encurta os titulos e a descricao do produto para ajudar a caber na pagina.
- O filtro de comprador segue a regra de ouro homologada: lista no formato codigo - apelido, filtrando por SEQCOMPRADOR.

## Colunas desta versao
- TITULO_FORNECEDOR
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
- Para usar no cabecalho da impressao, configure o titulo do Quick Report com a coluna TITULO_FORNECEDOR (ex.: 12345 - FORNECEDOR XYZ).
- PRODUTO foi reduzido com SUBSTR(..., 1, 55) para caber melhor no Quick Report.
- A ordenacao ficou por SUBGRUPO crescente e QTD_VDA decrescente.