# Checklist de Adaptacao do QRP - ABC Comprador

## Objetivo
Checklist pratico para adaptar o arquivo RelProdlojaComp.QRP ao novo relatorio ABC por comprador, usando a query pronta para QRP.

## Regra principal do layout
- O formato de impressao deve ficar igual ao formato da grid.
- O QRP nao deve mais usar desenho em blocos por fornecedor, categoria ou produto em duas linhas.
- O detalhe deve ser uma linha tabular unica por produto, com colunas na mesma ordem logica da grid.
- O cabecalho da impressao pode continuar com titulo, comprador, periodo, emissao e empresas, mas o corpo deve espelhar a grid.

## Arquivos de referencia
- QRP base: C:/Users/Alessandro.soares.BAKLIZI/Downloads/RelProdlojaComp.QRP
- Novo QRP sugerido: RelABCCompradorUltCompraCD.QRP
- Query pronta para o layout: Aplicativos/gerenciamento_sql/querys/abc_vendas_formato_comprador_dropdown_ultima_entrada_cd_qrp_final.sql
- Procedimento Var-F7: Aplicativos/gerenciamento_sql/Var-F7/abc_vendas_formato_comprador_dropdown_ultima_entrada_cd_qrp_final.md
- Mapeamento de campos: Aplicativos/gerenciamento_sql/aprendizado/mapeamento_query_para_qrp_abc_comprador.md

## Checklist

### 1. Preparar a base
1. Fazer uma copia do arquivo RelProdlojaComp.QRP.
2. Renomear a copia para RelABCCompradorUltCompraCD.QRP.
3. Preservar o arquivo original sem alteracao.

### 2. Abrir no editor correto
1. Abrir o novo QRP no editor de Quick Report usado pelo Consinco.
2. Confirmar que o arquivo abre com os objetos de cabecalho, detalhe e rodape.
3. Confirmar que o layout esta em paisagem ou ajustar para paisagem se necessario.

### 3. Ajustar o cabecalho
1. Trocar o titulo para RELATORIO ABC VENDAS POR COMPRADOR.
2. Manter campo de emissao.
3. Manter campo de periodo de vendas.
4. Manter campo de comprador.
5. Manter empresa(s) no cabecalho, se o layout base ja trouxer isso.
6. Opcional: manter fornecedor no cabecalho somente se fizer sentido visualmente.

### 4. Remover elementos herdados do modelo antigo
1. Remover Nro Loja do detalhe.
2. Remover EAN do detalhe, se nao for necessario.
3. Remover EmbVda separado.
4. Remover EmbCompra separado.
5. Remover campos antigos que nao existem na query qrp_final.
6. Remover qualquer referencia visual a fornecedor principal no detalhe.
7. Remover agrupamentos visuais por fornecedor.
8. Remover linha de categoria herdada do modelo antigo.
9. Remover o desenho em bloco quebrado por produto.

### 5. Vincular os campos do detalhe aos aliases da query final
Usar exatamente estes aliases da query:

1. SUBGRUPO
2. COD_PROD
3. PRODUTO
4. EMB
5. PERC_ACM
6. PRC_CST
7. PRC_VDA
8. MARG_ATU
9. MARG_OBJ
10. QTD_VDA
11. EST_MIN
12. EST_MAX
13. EST_LOJA
14. EST_CD
15. PEND_CD
16. DT_ULT_COMP
17. QTD_ULT_COMP

### 6. Ordem visual recomendada no detalhe
1. SUBGRUPO
2. COD_PROD
3. PRODUTO
4. EMB
5. QTD_VDA
6. PERC_ACM
7. PRC_CST
8. PRC_VDA
9. MARG_ATU
10. MARG_OBJ
11. EST_MIN
12. EST_MAX
13. EST_LOJA
14. EST_CD
15. PEND_CD
16. DT_ULT_COMP
17. QTD_ULT_COMP

### 6.1 Estrutura visual obrigatoria
1. Uma linha de cabecalho com os titulos das colunas.
2. Uma linha de detalhe por produto.
3. Sem quebra do mesmo produto em duas linhas.
4. Sem cabecalhos intermediarios de fornecedor.
5. Sem cabecalhos intermediarios de categoria.
6. Sem blocos visuais diferentes da ordem da grid.

### 7. Padronizar textos curtos no layout
1. COD_PROD
2. PRODUTO
3. EMB
4. PERC_ACM
5. PRC_CST
6. PRC_VDA
7. MARG_ATU
8. MARG_OBJ
9. QTD_VDA
10. EST_MIN
11. EST_MAX
12. EST_LOJA
13. EST_CD
14. PEND_CD
15. DT_ULT_COMP
16. QTD_ULT_COMP

### 8. Ajustar mascaras e formatos
1. DT_ULT_COMP em dd/MM/yyyy.
2. Margens com duas casas decimais.
3. Precos com duas casas decimais.
4. Quantidades com mascara numerica simples.
5. PERC_ACM com uma casa decimal, se o editor permitir manter esse formato.

### 9. Validar alimentacao da query
1. Confirmar que a consulta usada no Consinco e a abc_vendas_formato_comprador_dropdown_ultima_entrada_cd_qrp_final.sql.
2. Confirmar que o Var-F7 foi cadastrado conforme o procedimento correspondente.
3. Confirmar que LS3 usa a lista codigo - apelido homologada.
4. Confirmar que LT2 continua com 0 para todos.

### 10. Validar impressao
1. Rodar a consulta com um comprador real.
2. Abrir a impressao no Quick Report.
3. Verificar se o cabecalho mostra comprador e periodo corretamente.
4. Verificar se todas as colunas esperadas aparecem.
5. Verificar se a ordem esta por subgrupo crescente e quantidade vendida decrescente.
6. Verificar se a largura cabe em uma pagina utilizavel.
7. Verificar se o corpo da impressao espelha a grid, sem agrupamentos herdados.
8. Verificar se cada produto ocupa apenas uma linha visual no detalhe.

### 11. Ajustes finos se ainda ficar largo
1. Reduzir largura de PRODUTO.
2. Reduzir fonte do detalhe.
3. Levar PERC_ACM e margens para mais a direita.
4. Se necessario, quebrar em duas linhas visuais no detalhe.
5. So remover coluna se o ajuste de layout nao resolver.

## Criterio de pronto
- O QRP abre sem erro.
- O cabecalho mostra comprador, periodo e emissao.
- O detalhe mostra apenas os campos esperados da query final.
- A impressao fica legivel sem depender de cortar colunas na consulta.
- O layout segue o padrao homologado de filtro por comprador em codigo - apelido.
- O corpo da impressao fica com aparencia de grid, e nao com o layout antigo em blocos.