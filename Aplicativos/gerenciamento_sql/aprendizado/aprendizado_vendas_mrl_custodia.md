# Aprendizado Consolidado: Vendas Reais no Totvs Consinco (`MRL_CUSTODIA` vs `MRL_PRODVENDADIA`)

## Descoberta e Evidência
Durante investigação de divergência na quantidade vendida do produto `15312` na Loja `2` no período de `01/02/2026` a `31/05/2026`:
- A tabela `MRL_PRODVENDADIA` retornou **63 unidades**.
- As telas nativas do Totvs Consinco (`Consulta Produtos -> Histórico` e `Análise ABC de Vendas/Distribuição`) retornaram **135 unidades** (sendo 115 em Fev, 9 em Mar, 7 em Abr, 4 em Mai).

A captura do trace SQL do motor do Consinco (módulo `MAX1008` / `frmAnlABCEstq` -> log `<ID-00047>`) revelou a query nativa utilizada para popular o histórico do produto (`MBIX_PERIODOTEMP`):
```sql
update MBIX_PERIODOTEMP T
set ( T.QTDVDA, T.NRONFCUPOMEMITIDO, T.VLRTOTALVDA, T.QTDCOMPRA, T.VLRTOTALCOMPRA ) = 
 ( SELECT
      sum( DECODE('Qtde Vendida', 'Qtde Movimentada', nvl(X.QTDSAIDAMEDVENDA, X.QTDVDA), X.QTDVDA) ), sum( X.NRONFCUPOMEMITIDO ), sum( X.VLRTOTALVDA ), 
      sum( X.QTDCOMPRA ), sum( X.VLRTOTALCOMPRA )
   from MRL_CUSTODIA X
   WHERE X.NROEMPRESA = T.NROEMPRESA
     and X.SEQPRODUTO = 15312
     and X.DTAENTRADASAIDA between T.DATAPERIODO and add_months( T.DATAPERIODO, 1 ) -1
 )
```

## Por que a `MRL_PRODVENDADIA` falhou?
A `MRL_PRODVENDADIA` neste ambiente específico não contempla todas as saídas consolidadas da empresa (pode estar restrita a determinados CGOs, PDVs ou cupons parciais sem atualização de todas as movimentações faturadas/distribuídas).

## Por que a `MRL_CUSTODIA` é a Fonte Oficial?
A tabela **`MRL_CUSTODIA`** recebe o processamento consolidado diário de movimentação, vendas (`QTDVDA`), custos e faturamento durante o fechamento/apuração da empresa. Por isso, a coluna **`QTDVDA` na `MRL_CUSTODIA`** filtrada pela data de movimentação (**`DTAENTRADASAIDA`**) é a **única fonte verdadeira** que bate 100% com a interface nativa do Consinco.

## Regra de Ouro (Mandamento para Novas Queries e Refatorações)
Em todo script SQL onde for necessário apurar a **Quantidade Vendida por Período e Loja/Empresa** (ex: giro de estoque, pedido grade loja, sugestão de compras, curva ABC, comparativos de vendas):
1. **Substituir:**
   - De: `MRL_PRODVENDADIA` (`DTAVDA`)
   - Para: `MRL_CUSTODIA` (`DTAENTRADASAIDA`)
2. **Sintaxe Padrão na CTE (`WITH`):**
```sql
VENDAS_LOJA AS (
    SELECT /*+ MATERIALIZE */
        V.SEQPRODUTO,
        V.NROEMPRESA,
        SUM(V.QTDVDA) AS QTD_VENDA
    FROM MRL_CUSTODIA V
    INNER JOIN PRODUTOS P ON P.SEQPRODUTO = V.SEQPRODUTO
    WHERE V.DTAENTRADASAIDA BETWEEN TRUNC(:DT1) AND TRUNC(:DT2)
      AND V.NROEMPRESA IN (1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 17, 18)
    GROUP BY V.SEQPRODUTO, V.NROEMPRESA
)
```
3. **Observação de Performance:** Sempre isolar a agregação de `MRL_CUSTODIA` em uma CTE com `/*+ MATERIALIZE */` antes de fazer joins com outras tabelas pesadas para evitar timeouts e duplicação de saldos.
