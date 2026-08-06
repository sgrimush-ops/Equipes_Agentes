# Aprendizado: Auditoria de Digitação de Pedidos e Expurgo de Múltiplos Usuários via Filtro LTx

Este documento consolida o aprendizado gerado durante a criação de relatórios de auditoria focados na digitação de pedidos (usuários logados no momento do pedido) e no filtro de CDs.

## 1. A Falácia da Tabela `MAD_PEDIDO`
Em ambientes Totvs Consinco, quando se fala em **"Digitação de Pedidos"** solicitada pelo sistema de Abastecimento ("Supply"), muitas vezes o foco não é no módulo de Vendas (MAD), mas no **Gerenciador de Compras e Suprimentos (MSU)**.

A tabela que armazena pedidos de compras a fornecedores externos e os pedidos de **Transferência Interna (CD para Lojas)** é a **`MSU_PEDIDOSUPRIM`** (Capa) e **`MSU_PSITEMRECEBER`** (Itens aguardando faturamento/recebimento).

*   **Dica:** Sempre busque a coluna de log `USUINCLUSAO` e a `DTAHORINCLUSAO` na tabela `MSU_PEDIDOSUPRIM` para saber exatamente o login e o momento em que a necessidade de suprimento nasceu, seja ela gerada manualmente na loja ou pelo robô automático da Supply.

## 2. Expurgo Flexível de Múltiplos Usuários (`Var - F7`)
Frequentemente o usuário precisa ignorar pedidos gerados automaticamente pelo sistema (ex: `AUTOMATICO`, `SUPPLY`). Quando solicitam a capacidade de colocar **vários** nomes num único campo sem se preocupar com maiúsculas/minúsculas e espaços, a abordagem ideal é o `NOT IN` acoplado ao extrator `REGEXP_SUBSTR`:

```sql
AND (:LT2 = '0' OR UPPER(A.USUINCLUSAO) NOT IN (
    SELECT UPPER(TRIM(REGEXP_SUBSTR(:LT2, '[^,]+', 1, LEVEL)))
    FROM DUAL
    CONNECT BY REGEXP_SUBSTR(:LT2, '[^,]+', 1, LEVEL) IS NOT NULL
))
```
**Vantagens dessa abordagem:**
1. O usuário pode digitar `joao, Maria, AUTOMATICO` na caixa da Consulta Criação.
2. O Oracle ignora espaços desnecessários com o `TRIM`.
3. O `UPPER` de ambos os lados neutraliza a case-sensitivity.
4. Quando o campo está zerado (`:LT2 = '0'`), a regra se anula não interferindo na performance.

## 3. O Duplo Papel do Filtro de CD (`:NR2`)
Numa dinâmica de Transferência, a Loja é a Empresa que pede o produto (`A.NROEMPRESA`), e o CD é o fornecedor logístico. No Consinco, o `SEQFORNECEDOR` interno frequentemente aponta direto para o Número da Empresa do CD.

Além de filtrar os documentos (`A.SEQFORNECEDOR = :NR2`), esse mesmo parâmetro pode ser injetado para apontar o estoque físico da tabela geral (`MRL_PRODUTOEMPRESA`) exatamente para o local que está faturando o pedido:

```sql
LEFT JOIN MRL_PRODUTOEMPRESA D ON B.SEQPRODUTO = D.SEQPRODUTO AND D.NROEMPRESA = :NR2
```

Se `:NR2 = 0` (todos os CDs), o estoque na view falha intencionalmente e fica zerado, o que é conceitualmente correto num relatório granular onde o usuário escolheu misturar a origem, não querendo acumular de todos os lados cegamente sem filtro.
