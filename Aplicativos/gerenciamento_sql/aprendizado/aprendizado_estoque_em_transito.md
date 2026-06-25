# Aprendizado: Estoque em Trânsito (Expedição CD para Lojas)

## O Problema do Trânsito Físico vs Lógico
No ERP Totvs Consinco, rastrear o saldo de mercadorias "Em Trânsito" (faturadas/separadas no Centro de Distribuição mas que ainda não deram entrada na loja de destino) é contra-intuitivo, pois:
1. **O CD não emite Notas Fiscais do Tipo 'S' (Saída) diretas para as lojas na `MLF_NOTAFISCAL`**.
2. **A tabela consolidadora `MRL_PRODEMPCOMPRA` não alimenta a coluna `QTDPEDRECTRANSITO` na maioria das configurações**, resultando em saldo zero para trânsito nessa visão gerencial.

## O Erro Comum: Usar a Tabela de Expedição
A tabela de itens expedidos (`MSU_PSITEMEXPEDIDO`) possui uma coluna chamada **`QTDTRANSITO`**.
- **Cuidado**: O nome é enganoso! No Consinco, `MSU_PSITEMEXPEDIDO.QTDTRANSITO` significa **Quantidade Pendente de Expedição/Separação** (o que o CD ainda *precisa* mandar). Ela não representa o que já saiu.
- Na tela de Consulta de Produtos (F7), esse valor aparece na coluna **Ped Expedir** (para a empresa emissora/CD).

## A Solução Correta: Tabela de Recebimento da Loja Destino
O trânsito verdadeiro ("O que já saiu do CD e está rodando no caminhão") fica gravado do lado de quem vai *receber*.
A tabela correta é a **`MSU_PSITEMRECEBER`** na coluna **`QTDTOTTRANSITO`**.

### Regras Práticas
1. Na tela de Consulta de Produtos do Consinco, ao clicar em "Pedidos a Receber" de uma Loja, a coluna **Trânsito** da interface UI é exatamente a soma de `QTDTOTTRANSITO` da `MSU_PSITEMRECEBER`.
2. O valor de "Ped Receber" global de uma loja = (Saldo Pendente de Expedição do CD) + (Quantidade em Trânsito).
3. Para diferenciar mercadorias em trânsito vindas do CD de compras vindas de Fornecedores Externos, é necessário fazer JOIN com o cabeçalho do pedido (`MSU_PEDIDOSUPRIM`).

### Query Padrão para Capturar o Trânsito de CDs
Para encontrar mercadorias em trânsito do CD para as lojas, utilize a query base abaixo:

```sql
SELECT 
    R.NROEMPRESA AS LOJA_DESTINO,
    R.SEQPRODUTO AS CODIGO_PRODUTO,
    PS.SEQFORNECEDOR AS CODIGO_ORIGEM,
    SUM(NVL(R.QTDTOTTRANSITO, 0)) AS QTD_EM_TRANSITO
FROM MSU_PSITEMRECEBER R
JOIN MSU_PEDIDOSUPRIM PS 
  ON PS.NROPEDIDOSUPRIM = R.NROPEDIDOSUPRIM 
 AND PS.NROEMPRESA = R.NROEMPRESA
WHERE R.NROEMPRESA IN (1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 17, 18) -- Filtro das Lojas
  AND NVL(R.QTDTOTTRANSITO, 0) > 0
  AND PS.SEQFORNECEDOR IN (15, 16, 50) -- Filtro dos CDs / Origens Internas
GROUP BY 
    R.NROEMPRESA, 
    R.SEQPRODUTO, 
    PS.SEQFORNECEDOR
```
