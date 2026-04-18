# Desenho do QRP - ABC Comprador

## Objetivo
Criar um novo QRP derivado de RelProdlojaComp.QRP para imprimir o relatorio ABC por comprador, mantendo a estrutura de Quick Report que ja funciona no Consinco e trocando apenas o necessario para casar com a query atual.

## Arquivo base recomendado
- Base de layout: C:/Users/Alessandro.soares.BAKLIZI/Downloads/RelProdlojaComp.QRP
- Novo nome sugerido: RelABCCompradorUltCompraCD.QRP

## Motivo da escolha da base
- O RelProdlojaComp.QRP ja contem tratamento de comprador no cabecalho.
- Ele ja contem variavel de comprador no layout.
- Ele ja contem blocos de impressao proximos do relatorio que estamos montando.
- Ele e melhor ponto de partida do que RelProdloja.QRP, que nao contem a camada de comprador.

## O que reaproveitar do RelProdlojaComp.QRP
- Estrutura geral do Quick Report.
- Configuracao de pagina e impressora.
- Blocos de cabecalho, rodape e numeracao de pagina.
- Campo de comprador no cabecalho.
- Campo de periodo no cabecalho.
- Campo de emissao no cabecalho.

## O que precisa mudar no novo QRP

### 1. Titulo
- Trocar o titulo atual por algo aderente a consulta.
- Titulo sugerido: RELATORIO ABC VENDAS POR COMPRADOR

### 2. Remover campos que nao fazem sentido no ABC atual
- Nro Loja
- EAN, se nao for usado na query final
- EmbVda, se nao for usada na query final
- EmbCompra separada, se a query ficar apenas com EMBALAGEM
- Campos antigos de fornecedor e categoria que existiam so para o modelo original por loja

### 3. Incluir os campos da query atual
O novo QRP deve ser desenhado para consumir exatamente estes aliases da query:

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

### 4. Ordem visual sugerida no detalhe
Para imprimir melhor, a linha de detalhe deve seguir esta ordem:

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

### 5. Cabecalho recomendado
O cabecalho do QRP deve mostrar:

- Empresa(s)
- Periodo de vendas
- Comprador
- Emissao
- Opcionalmente fornecedor, se o filtro LT2 estiver preenchido

## Mapeamento funcional do layout

### Variaveis de cabecalho que ja apareceram no QRP base
- vsComprador
- vddtainicialvda
- vddtafinalvda
- vsEmpresas

### Regra para o novo QRP
- O novo QRP deve continuar exibindo comprador no cabecalho.
- O filtro de comprador homologado continua sendo lista no formato codigo - apelido.
- No cabecalho, o valor exibido pode permanecer como texto integral escolhido na LS3.

## Regras visuais recomendadas
- Usar orientacao paisagem.
- Reduzir largura de DESCRICAO_PRODUTO se o detalhe nao couber.
- Formatar DATA_ULTIMA_COMPRA_CD em dd/MM/yyyy.
- Colunas de margem com duas casas decimais.
- Quantidades com mascara numerica simples.
- Manter SUBGRUPO como primeiro agrupador visual.

## Estrategia de implementacao

### Caminho seguro
1. Duplicar RelProdlojaComp.QRP.
2. Renomear para RelABCCompradorUltCompraCD.QRP.
3. Abrir no editor de Quick Report usado no Consinco.
4. Trocar titulo, labels e campos antigos.
5. Vincular os novos campos do detalhe aos aliases da query ABC.
6. Testar com a query atual no Consinco.

### Caminho de menor risco
- Nao tentar reaproveitar campos antigos que nao existem na query atual.
- Nao tentar resolver o layout apenas por SQL se o objetivo for impressao final.
- Nao partir do RelProdloja.QRP simples, porque o modelo por comprador ja esta pronto no RelProdlojaComp.QRP.

## Decisao consolidada
- Para relatorio ABC com comprador, o QRP base oficial passa a ser RelProdlojaComp.QRP.
- A query deve ser adaptada ao layout final, ou o layout deve ser adaptado aos aliases da query.
- A camada de impressao deve ser tratada no QRP, nao apenas na consulta SQL.