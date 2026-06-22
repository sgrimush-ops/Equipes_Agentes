# Aprendizado: Auditoria de Compras, Devoluções e Trocas

Este documento registra o conhecimento adquirido ao construir a query de auditoria "Ranking de Vendas por Subgrupo de Fornecedor" (`a.ranking_vendas_subgrupo_fornecedor_v9.sql`), focado em alinhar os resultados da query com os relatórios nativos do Consinco (ex: Análise ABC de Entradas).

## 1. Dedução de Devoluções e Trocas em "Total Compras"
Nos relatórios de Entradas do Consinco, eventos de Devolução a Fornecedor e Troca de Fornecedor (normalmente CGO 802 e 860) são apresentados na mesma aba que as compras (CGO 1, 28, etc), porém com valores **negativos**. 
Isso significa que o "Total Compras" do Consinco já é um valor líquido. Para a nossa query bater no centavo, a coluna consolidada de Compra deve ser:
`VLR_COMPRA_LIQUIDA = VLR_COMPRADO - VLR_DEVOLUCAO - VLR_TROCA`
*(Assumindo que os VLRs de devolução e troca estão somados em valores absolutos/positivos na subquery)*.

## 2. Captura de CGOs 802 e 860: Entradas vs Saídas
No fluxo fiscal, uma troca ou devolução pode acontecer de duas formas dentro do ERP:
- **Emissão Própria (Saída)**: O próprio mercado emite a nota de devolução/troca. Fica registrado na `MLFV_BASENFE`.
- **Emissão de Terceiro (Entrada)**: O fornecedor emite uma NF de entrada (Retorno de Mercadoria / Reposição) e o operador a lança no sistema. Fica registrado na `MLF_NOTAFISCAL`.

Para garantir que não haja "cegueira" (perder uma NF emitida pela loja ou perder uma enviada pelo fornecedor) e nem duplicidade (visto que a operação fiscal correta gera apenas **um** documento do tipo Devolução/Troca por evento físico), deve-se mapear os CGOs (802, 860) em **ambas** as tabelas. O valor total da Troca é a soma do que ocorreu na Saída com o que ocorreu na Entrada.

## 3. Classificação de Bonificação vs Troca (`TIPPEDCOMPRAITEM`)
Quando o Consinco gera uma NF de compra (`TIPPEDIDOCOMPRA = 'C'`), é comum o parâmetro `CGO_ENTR_BONIF_NFCOMPRA` sobrepor o CGO original caso o item seja bonificado (`TIPPEDCOMPRAITEM = 'B'`).
- **Erro comum**: Avaliar `TIPPEDCOMPRAITEM IN ('B', 'E')`. A letra `'E'` pode representar uma embalagem ou outro evento que não é bonificação. Ao fazer isso, se um fornecedor enviar uma NF com CGO 860 (Troca) e o sistema marcar como `'E'`, o CGO 860 será perdido e forçado como Bonificação (ex: 101), gerando divergência.
- **Solução**: Restringir a regra estritamente para `'B'`: `CASE WHEN N.TIPPEDCOMPRAITEM = 'B' AND ... THEN TO_NUMBER(MP.VALOR)`.

## 4. Filtro de Inclusão Global para Queries de Ranking
Ao fazer um ranking ou painel consolidado de fornecedores/produtos, não se pode assumir que apenas fornecedores "com venda" devem aparecer. Se um fornecedor teve apenas devolução ou troca naquele mês, ele **deve** constar no relatório (pois o valor total de compras dele será negativo ou haverá saldo na devolução).
Para garantir isso:
1. O `LEFT JOIN` ou `WHERE` do esqueleto principal (que cruza produtos com vendas e compras) deve possuir a condição `OR DEV.SEQPRODUTO IS NOT NULL` (ou sua respectiva subquery de devolução).
2. O `HAVING` final de agrupamento deve verificar `OR SUM(VLR_DEVOLUCAO_COMPRA) > 0 OR SUM(VLR_TROCA_COMPRA) > 0`.

## 5. Inclusão da Empresa Atacado (21) nas Compras
Ao mapear as regras de *Compras ao Fornecedor*, é necessário incluir a empresa `21` (que representa operações por Atacado). Garanta que ela esteja listada nos filtros `IN (..., 21, ...)` tanto para as notas de Entrada (Compras) quanto para as de Devolução/Trocas. Não se esqueça de validar se a regra também deve ou não ser aplicada a Vendas ou Estoque, dependendo da necessidade de negócio.
