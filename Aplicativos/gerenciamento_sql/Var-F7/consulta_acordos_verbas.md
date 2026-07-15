# Var-F7 - consulta_acordos_verbas

## Query vinculada
- Arquivo SQL: [Aplicativos/gerenciamento_sql/querys/consulta_acordos_verbas.sql](../querys/consulta_acordos_verbas.sql)

## Objetivo
Unificar em uma única consulta performática para a Consulta Criação todas as informações do monitor de Acordos e Verbas (`MSUV_ACORDOPROMOC`), incluindo o número de processo (`SEQPROCESSO`), detalhamentos de itens/parcelas financeiras e os totais gerais consolidados do acordo (`TOTAL_GERAL_VLR_ACORDO` e `TOTAL_GERAL_SALDO_ACORDO`), sem duplicar valores por produto.

## Arquitetura e Performance
- **CTE Materializada (`CTE_BASE`)**: Isola com `SELECT DISTINCT` os filtros e joins principais (`MSUV_ACORDOPROMOC`, `GE_PESSOA`, `MAX_COMPRADOR` e `LEFT JOIN` com a tabela física `MSU_ACORDOPROMOC` para obter o `SEQPROCESSO`) e consolida a massa em memória (`/*+ MATERIALIZE */`) eliminando linhas duplicadas oriundas de eventos internos da view.
- **CTEs de Totais (`CTE_TOTAL_ACORDO`, `CTE_TOTAL_SALDO` e `CTE_TOTAIS`)**: Replicam com exatidão os blocos de totais do monitor SQL, somando cada um dos 5 campos financeiros (`VLRFINVENCIDO`, `VLRFINAVENCER`, `VLRACORDO`, `VLRSALDOACORDO` e `VLRUTILPROD`) sem distorção por multiplicidade de produtos.
- **Linha de Total Geral no Rodapé**: Em vez de repetir totais em colunas paralelas em cada linha, a consulta utiliza um `UNION ALL` no final (`ORDEM_LINHA = 2`) para adicionar uma última linha de sumário (`TOTAL GERAL ->`) com a soma exata das colunas monetárias.
- **Bypass do Validador Consinco**: Toda a estrutura `WITH` é envelopada por um `SELECT * FROM (...)` externo, garantindo aprovação no validador sintático do ERP ("A instrução SQL informada, não é uma consulta").
- **Ausência de Comentários**: O código SQL principal não possui comentários lineares (`--`) ou de bloco (`/* */`) além dos hints, evitando falhas de interpretação na engine SGI.

## Colunas retornadas
- `CODIGO_EMPRESA`: código da empresa/loja do acordo (`A.NROEMPRESA`).
- `NUMERO_ACORDO`: número único do acordo promocional (`A.NROACORDO`).
- `NUMERO_PROCESSO`: sequencial do processo que gerou o acordo (`AC.SEQPROCESSO`, obtido via `LEFT JOIN` com a tabela física `MSU_ACORDOPROMOC`).
- `CODIGO_FORNECEDOR`: código do fornecedor do acordo (`B.SEQPESSOA`).
- `FORNECEDOR`: razão social ou nome do fornecedor (`B.NOMERAZAO`, ou `'TOTAL GERAL ->'` na linha de sumário).
- `DESCRICAO_ACORDO`: descrição do acordo (`A.DESCACORDO`).
- `DATA_EMISSAO`: data de emissão do acordo formatada (`TO_CHAR(..., 'DD/MM/YYYY')`).
- `COMPRADOR`: apelido ou nome do gestor/comprador (`C.APELIDO`).
- `STATUS_ACORDO`: descrição do status ('EM ANDAMENTO', 'CANCELADO', 'CONCLUIDO', 'INTERROMPIDA').
- `TIPO_ACORDO`: descrição do tipo do acordo ('VERBA EXTRA', 'SELL-OUT', 'SELL-IN').
- `CODIGO_PRODUTO`: código do produto vinculado, se houver (`A.SEQPRODUTO`).
- `QTD_UTILIZADA_VERBA`: quantidade consumida/utilizada da verba (`A.QTDUTILIZADAVERBA`).
- `DATA_FINAL_VERBA`: data de término/vigência da verba formatada (`TO_CHAR(..., 'DD/MM/YYYY')`).
- `NUMERO_NF`: número da nota fiscal tratada (`SUBSTR(A.NUMERONF, 1, 250)`).
- `NUMERO_PEDIDO_SUPRIMENTO`: número do pedido de compra/suprimento (`A.NROPEDIDOSUPRIM`).
- `VLR_FIN_VENCIDO`: valor financeiro vencido, formatado em reais (`R$ 0.000,00` via `TO_CHAR(..., 'FM999G999G990D00')`).
- `VLR_FIN_A_VENCER`: valor financeiro a vencer, formatado em reais (`R$ 0.000,00`).
- `VALOR_ACORDO`: valor total do acordo, formatado em reais (`R$ 0.000,00`).
- `VALOR_SALDO_ACORDO`: saldo disponível do acordo, formatado em reais (`R$ 0.000,00`).
- `VALOR_UTILIZADO_PRODUTO`: valor utilizado no produto, formatado em reais (`R$ 0.000,00`).

## Variáveis para cadastrar em Var - F7
Os filtros antes do Run na Consulta Criação dependem do cadastro manual em **Var - F7**:

### LT1
- **Tipo:** Literal
- **Descrição:** Lojas
- **Valor padrão:** `1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 17, 18, 900`
- **Instrução p/ o usuário:** Mantenha os números das empresas/lojas separadas por vírgula no campo, incluindo a loja 900, ou informe as lojas desejadas.

### LS1
- **Tipo:** Lista
- **Descrição:** Comprador
- **Valor padrão:** `0 - TODOS`
- **Instrução p/ o usuário:** Selecione o comprador específico para filtro ou mantenha `0 - TODOS` caso não queira filtrar nada.

### LS2
- **Tipo:** Lista
- **Descrição:** Fornecedor
- **Valor padrão:** `0 - TODOS`
- **Instrução p/ o usuário:** Selecione o fornecedor específico para filtro ou mantenha `0 - TODOS` caso não queira filtrar nada.

### LS3
- **Tipo:** Lista
- **Descrição:** Status Acordo
- **Valor padrão:** `0 - TODOS`
- **Instrução p/ o usuário:** Selecione o status (`1 - EM ANDAMENTO`, `2 - CANCELADO`, `3 - CONCLUIDO`, `4 - INTERROMPIDA`) ou mantenha `0 - TODOS` para todos os status.

### NR1
- **Tipo:** Numérico
- **Descrição:** Número Acordo
- **Valor padrão:** `0`
- **Instrução p/ o usuário:** Informe o número exato do acordo. Se deixar `0`, a consulta trará todos os acordos no período e lojas selecionados sem filtrar por número.

### DT1
- **Tipo:** Data
- **Descrição:** Data Emissão Inicial
- **Valor padrão:** Primeiro dia do mês atual ou conforme rotina
- **Instrução p/ o usuário:** Informe a data inicial de emissão dos acordos.

### DT2
- **Tipo:** Data
- **Descrição:** Data Emissão Final
- **Valor padrão:** Data de hoje
- **Instrução p/ o usuário:** Informe a data final de emissão dos acordos.

## SQL da lista LS1 (Comprador)
Cole esta SQL dentro do cadastro da variável `LS1` na tela Var - F7:
```sql
SELECT '0 - TODOS' AS COMPRADOR
FROM DUAL
UNION
SELECT DISTINCT TO_CHAR(SEQCOMPRADOR) || ' - ' || NVL(APELIDO, COMPRADOR)
FROM MAX_COMPRADOR
WHERE STATUS = 'A'
ORDER BY 1
```

## SQL da lista LS2 (Fornecedor)
Cole esta SQL dentro do cadastro da variável `LS2` na tela Var - F7 (trazendo fornecedores ativos para seleção limpa ou sentinela TODOS):
```sql
SELECT '0 - TODOS' AS ITEM
FROM DUAL
UNION ALL
SELECT DISTINCT TO_CHAR(SEQPESSOA) || ' - ' || SUBSTR(REPLACE(NOMERAZAO, '''', ''), 1, 80) AS ITEM
FROM GE_PESSOA
WHERE STATUS = 'A'
```

## SQL da lista LS3 (Status Acordo)
Cole esta SQL dentro do cadastro da variável `LS3` na tela Var - F7:
```sql
SELECT '0 - TODOS' AS ITEM FROM DUAL
UNION ALL
SELECT '1 - EM ANDAMENTO' FROM DUAL
UNION ALL
SELECT '2 - CANCELADO' FROM DUAL
UNION ALL
SELECT '3 - CONCLUIDO' FROM DUAL
UNION ALL
SELECT '4 - INTERROMPIDA' FROM DUAL
```

## Passo a passo operacional
1. Abrir a consulta na tela **Consulta Criação** do Consinco e colar o código SQL de `consulta_acordos_verbas.sql`.
2. Clicar no botão **Var - F7**.
3. Cadastrar `LT1` na aba **Literal** com descrição **Lojas** e valor padrão com as empresas (ex: `1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 17, 18, 900`).
4. Cadastrar `LS1` na aba **Lista** com descrição **Comprador** e colar a SQL da lista `LS1` em seu campo.
5. Cadastrar `LS2` na aba **Lista** com descrição **Fornecedor** e colar a SQL da lista `LS2` em seu campo.
6. Cadastrar `LS3` na aba **Lista** com descrição **Status Acordo** e colar a SQL da lista `LS3` em seu campo.
7. Cadastrar `NR1` na aba **Numérico** com descrição **Número Acordo** e definir valor padrão `0`.
8. Cadastrar `DT1` e `DT2` na aba **Data** com descrições **Data Emissão Inicial** e **Data Emissão Final**.
9. Salvar as configurações de variáveis no painel `Var - F7`.
10. Clicar em **Run** para executar a consulta performática unificada.
