# Mapeamento Query -> QRP ABC Comprador

## Objetivo
Mapear a query atual do relatorio ABC por comprador para o novo QRP derivado de RelProdlojaComp.QRP, deixando claro o que entra no cabecalho, o que entra no detalhe e o que deve sair do layout antigo.

## Query de referencia
- Arquivo SQL: Aplicativos/gerenciamento_sql/querys/abc_vendas_formato_comprador_dropdown_ultima_entrada_cd_impressao_cod_comprador.sql

## QRP base
- Base de layout: C:/Users/Alessandro.soares.BAKLIZI/Downloads/RelProdlojaComp.QRP
- Novo layout alvo: RelABCCompradorUltCompraCD.QRP

## Blocos do QRP a manter
- Cabecalho com emissao.
- Cabecalho com periodo.
- Cabecalho com comprador.
- Numeracao de pagina.
- Estrutura de detalhe por linha.

## Blocos do QRP a remover ou substituir
- Campo de Nro Loja.
- Campo de EAN, se nao for exigido no layout final.
- Campo de EmbVda separado.
- Campo de EmbCompra separado, porque a query atual entrega EMBALAGEM unica.
- Campos antigos do modelo por loja que nao existem na query atual.

## Cabecalho do relatorio

### Exibir no cabecalho
- Comprador: valor textual escolhido na LS3, no formato codigo - apelido.
- Periodo de vendas: DT1 ate DT2.
- Emissao: data atual.
- Fornecedor: opcional, se LT2 for diferente de 0.

### Variaveis de cabecalho a manter no QRP
- vsComprador
- vddtainicialvda
- vddtafinalvda
- vsEmpresas

## Mapeamento dos campos de detalhe

### Grupo e identificacao
- SUB.SUBGRUPO -> SUBGRUPO
- A.SEQPRODUTO -> CODIGO_PRODUTO
- A.DESCCOMPLETA -> DESCRICAO_PRODUTO
- MAX(FD.PADRAOEMBCOMPRA) -> EMBALAGEM

### Curva e venda
- ROUND(... ) -> PERC_ACM
- MAX(NVL(VF.QTD_VENDIDA_TOTAL, 0)) -> QTD_VENDIDA

### Preco e margem
- MAX(NVL(C3.PRECO_CUSTO, 0)) -> PRECO_CUSTO
- MAX(NVL(PV.PRECO_VENDA, 0)) -> PRECO_VENDA
- ROUND(DECODE(...), 2) -> MARGEM_ATUAL
- ROUND(MAX(NVL(NULLIF(MOBJ.MARGEM_OBJETIVA, 0), ...)), 2) -> MARGEM_OBJETIVA

### Estoque
- SUM(NVL(Y.ESTQMINIMOLOJA, 0)) -> ESTOQUE_MINIMO
- SUM(NVL(Y.ESTQMAXIMOLOJA, 0)) -> ESTOQUE_MAXIMO
- SUM(NVL(Y.ESTQLOJA, 0)) -> ESTOQUE_LOJA
- MAX(NVL(CD.ESTOQUE_CD, 0)) -> ESTOQUE_DEPOSITO
- MAX(NVL(CD.QTD_PENDENTE_EXPEDIR_CD, 0)) -> PENDENTE_EXPEDIR_CD

### Ultima compra CD
- TO_CHAR(MAX(CD.DATA_ULTIMA_COMPRA_CD), 'DD/MM/YYYY') -> DATA_ULTIMA_COMPRA_CD
- MAX(NVL(CD.QTD_ULTIMA_COMPRA_CD, 0)) -> QTD_ULTIMA_COMPRA_CD

## Ordem recomendada do detalhe no QRP
1. SUBGRUPO
2. CODIGO_PRODUTO
3. DESCRICAO_PRODUTO
4. EMBALAGEM
5. QTD_VENDIDA
6. PERC_ACM
7. PRECO_CUSTO
8. PRECO_VENDA
9. MARGEM_ATUAL
10. MARGEM_OBJETIVA
11. ESTOQUE_MINIMO
12. ESTOQUE_MAXIMO
13. ESTOQUE_LOJA
14. ESTOQUE_DEPOSITO
15. PENDENTE_EXPEDIR_CD
16. DATA_ULTIMA_COMPRA_CD
17. QTD_ULTIMA_COMPRA_CD

## Campos que nao devem aparecer no novo QRP
- COMPRADOR no detalhe.
- CODIGO_FORNECEDOR_PRINCIPAL.
- FORNECEDOR_PRINCIPAL.
- NROEMPRESA como coluna do detalhe.
- CODIGO EAN, salvo se o usuario pedir explicitamente.

## Ordem da query e impacto no layout
- A query ja esta ordenada por SUBGRUPO crescente e QTD_VENDIDA decrescente.
- O QRP deve respeitar essa ordem e nao reinventar agrupamento por loja.

## Recomendacao de nomes curtos para um QRP compacto
Se o layout ficar largo demais, usar estes titulos de coluna:
- SUBGRUPO -> SUBGRUPO
- CODIGO_PRODUTO -> COD_PROD
- DESCRICAO_PRODUTO -> PRODUTO
- EMBALAGEM -> EMB
- PRECO_CUSTO -> PRC_CST
- PRECO_VENDA -> PRC_VDA
- MARGEM_ATUAL -> MARG_ATU
- MARGEM_OBJETIVA -> MARG_OBJ
- QTD_VENDIDA -> QTD_VDA
- ESTOQUE_MINIMO -> EST_MIN
- ESTOQUE_MAXIMO -> EST_MAX
- ESTOQUE_LOJA -> EST_LOJA
- ESTOQUE_DEPOSITO -> EST_CD
- PENDENTE_EXPEDIR_CD -> PEND_CD
- DATA_ULTIMA_COMPRA_CD -> DT_ULT_COMP
- QTD_ULTIMA_COMPRA_CD -> QTD_ULT_COMP

## Decisao final
- O novo QRP deve ser alimentado diretamente pelos aliases da query atual.
- Se houver necessidade de encaixe fino no layout, preferir ajustar alias da query a criar transformacoes complexas dentro do QRP.
- O RelProdlojaComp.QRP continua sendo a base oficial para derivacao do relatorio ABC por comprador.