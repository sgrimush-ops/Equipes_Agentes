# Aprendizado: Segregação de Pedidos Pendentes (Compras de Fornecedores vs. Transferências Internas)

Este documento consolida as descobertas práticas feitas ao implementar e refinar as colunas de pedidos pendentes `PEND_CD` e `PEND_FOR` na query `ABC_Vendas_Formato_Comprador.sql` para o ERP Totvs Consinco.

---

## 1. O Cenário de Negócio
No ecossistema de compras e abastecimento, é crítico distinguir duas origens de pedidos pendentes para evitar duplicidade de contagem física e tomar decisões de compra corretas:
* **`PEND_CD` (Transferências Internas / Trânsito):** Representa o que está sendo movimentado de estoque próprio da empresa (do CD para as lojas de varejo). Geralmente atrelado ao **CGO 50**. Esta mercadoria já está no processamento operacional da empresa.
* **`PEND_FOR` (Compras de Fornecedor / Intenções de Compra):** Representa pedidos de compra firmados com fornecedores externos (**CGO 1, 28, 32, 200, 290**). Mercadoria que ainda não está na empresa e constitui real intenção de compra externa.

---

## 2. Limitações Identificadas no ERP

### A. Mistura na Tabela Física (`MRL_PRODUTOEMPRESA`)
* A coluna de estoque `QTDPENDPEDCOMPRA` na `MRL_PRODUTOEMPRESA` armazena as pendências de compra de fornecedores.
* No entanto, nas filiais de varejo (lojas), as transferências internas a receber vindas do CD também são gravadas nesta mesma coluna (`QTDPENDPEDCOMPRA`) dependendo da parametrização do ERP.
* **Impacto:** Realizar o somatório irrestrito de `QTDPENDPEDCOMPRA` na rede inteira causava uma duplicidade crônica no consolidado (somando as compras do CD de 2.300 com as transferências das lojas de 1.240, gerando indevidamente 3.540).

### B. View de Expedição (`MAXV_MSUPEDIDOSUPRIMEXP`)
* A view pública de expedição do módulo de suprimentos (`MAXV_MSUPEDIDOSUPRIMEXP`) monitora apenas o fluxo de remessas e expedições internas do CD.
* **Impacto:** Compras de fornecedores externos são fluxos de recebimento direto e **não passam** por expedição interna. Tentar obter compras por esta view resulta em valores zerados (`0`) no relatório.

---

## 3. A Solução Homologada

### A. View Pública de Recebimentos (`MAXV_MSUPEDIDOSUPRIMREC`)
A view pública correta para listar pedidos de suprimento que entrarão na empresa (compras e recebimento de transferências) é a **`MAXV_MSUPEDIDOSUPRIMREC`**. 

A varredura de colunas no banco de dados revelou as seguintes colunas ativas para cálculo de saldo pendente:
* **`QTDSOLICITADA` (NUMBER):** Quantidade solicitada no pedido.
* **`QTDRECCANC` (NUMBER):** Quantidade recebida ou cancelada do pedido.
* **`TIPPEDIDOSUPRIM` (VARCHAR2):** Tipo do pedido de suprimentos.
  * O valor **`'C'`** indica compras com fornecedores externos.
  * Outros valores indicam transferências de suprimento.

### B. Cálculo Correto (Query de Compras Correlacionada)
Para calcular as compras de fornecedores expurgando 100% das transferências internas (remessas CD -> Loja), deve-se fazer a subquery correlacionada baseada na view de recebimento filtrando pelo tipo de compra:

```sql
(
  SELECT NVL(SUM(CASE WHEN X.QTDSOLICITADA > X.QTDRECCANC THEN X.QTDSOLICITADA - X.QTDRECCANC ELSE 0 END), 0)
    FROM MAXV_MSUPEDIDOSUPRIMREC X
   WHERE X.SEQPRODUTO = A.SEQPRODUTO
     AND X.TIPPEDIDOSUPRIM = 'C'
     AND X.NROEMPRESA IN (1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18, 50)
     AND (:NR1 = '0' OR X.NROEMPRESA = TO_NUMBER(:NR1))
) AS PEND_FOR
```

Esta solução garante que:
* Se `:NR1 = 0` (consolidado), a consulta somará as compras de fornecedor do CD + eventuais compras diretas locais que as lojas tenham feito a fornecedores, sem misturar com as transferências internas a receber.
* Se `:NR1` for uma filial individual, trará apenas a pendência de compras de fornecedores daquela filial específica.
* O desempenho seja excelente (a view é otimizada pelo otimizador do Oracle quando o `SEQPRODUTO` é passado de forma correlacionada).
