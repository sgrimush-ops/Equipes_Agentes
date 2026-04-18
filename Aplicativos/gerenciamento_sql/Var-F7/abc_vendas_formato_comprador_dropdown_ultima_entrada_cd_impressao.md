# Var-F7 - abc_vendas_formato_comprador_dropdown_ultima_entrada_cd_impressao

## Query vinculada
- Arquivo SQL: Aplicativos/gerenciamento_sql/querys/abc_vendas_formato_comprador_dropdown_ultima_entrada_cd_impressao.sql

## Objetivo
Versao enxuta da consulta ABC de vendas por comprador, preparada para imprimir melhor no Quick Report da Consulta Criacao do Consinco.

## Quando usar esta versao
- Use esta consulta quando a versao completa ficar larga demais no Quick Report.
- Esta versao reduz a quantidade de colunas para aumentar a chance de a tela de impressao abrir de forma utilizavel.
- Mantem os mesmos filtros da versao principal, mas prioriza leitura em papel.

## Colunas desta versao
- SUBGRUPO
- CODIGO_PRODUTO
- DESCRICAO_PRODUTO
- EMBALAGEM
- QTD_VENDIDA
- ESTOQUE_LOJA
- ESTOQUE_CD
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

### LT3
- Tipo: Literal
- Descricao: Comprador
- Valor padrao: TODOS
- Regra: TODOS = nao restringe comprador
- Instrucao p/ o usuario: informar preferencialmente o apelido do comprador; o nome completo tambem funciona

### NR1
- Tipo: Numerico
- Descricao: Qtd Vendida Maior Que
- Valor padrao: 0

## Passo a passo curto
1. Abrir a tela Consulta Criacao.
2. Cadastrar a SQL da consulta de impressao.
3. Abrir Var - F7 e cadastrar DT1, DT2, LT2, LT3 e NR1.
4. Em LT3, digitar TODOS para nao filtrar ou informar o apelido do comprador. Se necessario, o nome completo tambem funciona.
5. Executar a consulta com Run.
6. Na grade de resultado, clicar no icone de impressora para abrir o Quick Report.

## Observacoes
- Esta versao nao substitui a consulta completa; ela existe apenas para impressao.
- As colunas removidas da grade nesta versao foram exatamente os equivalentes da versao completa: COMPRADOR, CODIGO_FORNECEDOR_PRINCIPAL e FORNECEDOR_PRINCIPAL. Nesta consulta de impressao elas estavam nomeadas como COMPRADOR, CODIGO_FORNECEDOR e FORNECEDOR.
- O filtro de comprador desta versao usa LT3 literal, nao LS2, porque a expansao de lista estava quebrando o parser da Consulta Criacao com ORA-00907.
- DATA_ULTIMA_COMPRA_CD e exibida como DD/MM/YYYY.
- Se o Quick Report ainda ficar largo, o proximo ajuste e cortar mais colunas, normalmente FORNECEDOR ou SUBGRUPO.