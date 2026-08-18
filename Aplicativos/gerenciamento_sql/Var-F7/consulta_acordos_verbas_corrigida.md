# Var-F7 - consulta_acordos_verbas_corrigida

## Query vinculada
- Arquivo SQL: [Aplicativos/gerenciamento_sql/querys/consulta_acordos_verbas_corrigida.sql](../querys/consulta_acordos_verbas_corrigida.sql)

## Objetivo
Unificar em uma única consulta performática para a Consulta Criação do Totvs Consinco todas as informações do monitor de Acordos e Verbas (`MSUV_ACORDOPROMOC`), incluindo número de processo (`SEQPROCESSO`), detalhamentos de itens/parcelas financeiras, status, situação financeira calculada e totais gerais consolidados do acordo, com expurgo de cancelados por padrão via `#LT2`.

## Arquitetura e Performance
- **CTEs Materializadas (`/*+ MATERIALIZE */`)**:
  - `CTE_TITULOS_ACORDO`: Isola e materializa em RAM a unificação de títulos financeiros vinculados ao acordo via `FI_TITULO`, `MSU_ACORDOTITULORECEB`, `MSU_CCACORDOPROMOC`, `MSU_CCDIVIDA` e `MSU_ACORDOPROMOC`.
  - `CTE_VALORES_BRUTOS`: Agrupa e materializa dados da `MSUV_ACORDOPROMOC` com consumo de verba (`MRLV_VERBACONSUMIDA`) e vencimentos.
  - `CTE_CLASSIFICADA`: Materializa os cálculos analíticos de rateio, situação financeira e vencimentos em aberto.
- **Linha de Total Geral no Rodapé (`CTE_TOTAIS`)**: Adiciona uma última linha de sumário (`TOTAL GERAL ->`, `ORDEM_LINHA = 2`) consolidada em passagem única na `CTE_CLASSIFICADA`.
- **Bypass do Validador Consinco**: Toda a estrutura `WITH` é envelopada por `SELECT * FROM (...)` externo, garantindo aprovação no validador sintático do ERP ("A instrução SQL informada, não é uma consulta").
- **Ausência de Comentários**: O código SQL não possui comentários textuais (`--` ou `/* */`), evitando truncamento ou quebra pelo parser SGI.

## Colunas retornadas
- `CODIGO_EMPRESA`: código da empresa/loja do acordo (`A.NROEMPRESA`).
- `NUMERO_ACORDO`: número único do acordo promocional (`A.NROACORDO`).
- `NUMERO_PROCESSO`: sequencial do processo vinculado (`AC.SEQPROCESSO`).
- `CODIGO_FORNECEDOR`: código do fornecedor (`B.SEQPESSOA`).
- `FORNECEDOR`: razão social do fornecedor (ou `'TOTAL GERAL ->'` na linha de sumário).
- `DESCRICAO_ACORDO`: descrição do acordo (`A.DESCACORDO`).
- `DATA_EMISSAO`: data de emissão formatada (`DD/MM/YYYY`).
- `COMPRADOR`: apelido ou nome do comprador (`C.APELIDO`).
- `STATUS_ACORDO`: status literal exibido no topo da tela do ERP Consinco ('Aprovado', 'Cancelado', 'Concluido', 'Interrompido', 'Pendente').
- `SITUACAO_ACORDO`: situação literal exibida no topo da tela do ERP Consinco ('Financeiro', 'Pendente', 'Cancelado').
- `DIREITO_OBRIGACAO`: tipo de lançamento no financeiro do ERP ('Direito', 'Obrigação', 'Sem Título').
- `ABERTO_QUITADO`: status do título no financeiro do ERP ('Quitado', 'Aberto', 'Sem Título').
- `TIPO_ACORDO`: tipo do acordo ('VERBA EXTRA', 'SELL-OUT', 'SELL-IN').
- `CODIGO_PRODUTO`: código do produto vinculado, se houver (`A.SEQPRODUTO`).
- `QTD_UTILIZADA_VERBA`: quantidade consumida/utilizada da verba.
- `DATA_FINAL_VERBA`: data de vigência da verba formatada (`DD/MM/YYYY`).
- `VENCIMENTO_EM_ABERTO`: menor data de vencimento pendente formatada (`DD/MM/YYYY`).
- `ULTIMO_RECEBIMENTO`: data da última liquidação registrada formatada (`DD/MM/YYYY`).
- `NUMERO_NF`: número da nota fiscal tratada (`SUBSTR(A.NUMERONF, 1, 250)`).
- `NUMERO_PEDIDO_SUPRIMENTO`: número do pedido de compra/suprimento (`A.NROPEDIDOSUPRIM`).
- `VALOR_ACORDO`: valor total do acordo (`R$ 0.000,00`).
- `VLR_EM_ABERTO`: valor monetário pendente/em aberto (`R$ 0.000,00`).
- `VLR_FIN_VENCIDO`: valor financeiro vencido (`R$ 0.000,00`).
- `VLR_JA_QUITADO`: valor financeiro já quitado (`R$ 0.000,00`).
- `VALOR_SALDO_ACORDO`: saldo disponível do acordo (`R$ 0.000,00`).
- `VALOR_UTILIZADO_PRODUTO`: valor utilizado no produto (`R$ 0.000,00`).
- `TOTAL_PARCELAS`: quantidade total de parcelas programadas.
- `PARCELAS_PAGAS`: quantidade de parcelas já quitadas (`ABERTOQUITADO = 'Q'`).
- `PARCELAS_PENDENTES`: quantidade de parcelas pendentes.

## Variáveis para cadastrar em Var - F7

### LT1
- **Tipo:** Literal
- **Descrição:** Lojas
- **Valor padrão:** `1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 17, 18, 900`
- **Instrução p/ o usuário:** Mantenha os números das lojas separadas por vírgula no campo ou altere para as lojas desejadas.

### LT2
- **Tipo:** Literal
- **Descrição:** Expurgo Status (Cancelados)
- **Valor padrão:** `2`
- **Instrução p/ o usuário:** Define os códigos de status a serem ignorados/expurgados da consulta. O padrão `2` expurga os acordos **CANCELADOS**. Para trazer todos sem expurgo, informe `0`.

### LS1
- **Tipo:** Lista
- **Descrição:** Comprador
- **Valor padrão:** `0 - TODOS`
- **Instrução p/ o usuário:** Selecione o comprador específico para filtro ou mantenha `0 - TODOS`.

### LS2
- **Tipo:** Lista
- **Descrição:** Fornecedor
- **Valor padrão:** `0 - TODOS`
- **Instrução p/ o usuário:** Selecione o fornecedor específico para filtro ou mantenha `0 - TODOS`.

### LS3
- **Tipo:** Lista
- **Descrição:** Aberto/Quitado (Financeiro)
- **Valor padrão:** `0 - TODOS`
- **Instrução p/ o usuário:** Selecione a situação do título desejada (`1 - QUITADO`, `2 - ABERTO`, `3 - SEM TITULO`, `4 - CANCELADO`) ou mantenha `0 - TODOS`.

### NR1
- **Tipo:** Numérico
- **Descrição:** Número Acordo
- **Valor padrão:** `0`
- **Instrução p/ o usuário:** Informe o número exato do acordo ou mantenha `0` para trazer todos.

### DT1
- **Tipo:** Data
- **Descrição:** Data Emissão Inicial
- **Valor padrão:** Primeiro dia do mês atual ou conforme rotina
- **Instrução p/ o usuário:** Informe a data inicial de emissão dos acordos.

### DT2
- **Tipo:** Data
- **Descrição:** Data Emissão Final
- **Valor padrão:** Data de hoje (`SYSDATE`)
- **Instrução p/ o usuário:** Informe a data final de emissão dos acordos.

## SQL das Listas de Seleção

### SQL da lista LS1 (Comprador)
```sql
SELECT '0 - TODOS' AS COMPRADOR
FROM DUAL
UNION
SELECT DISTINCT TO_CHAR(SEQCOMPRADOR) || ' - ' || NVL(APELIDO, COMPRADOR)
FROM MAX_COMPRADOR
WHERE STATUS = 'A'
ORDER BY 1
```

### SQL da lista LS2 (Fornecedor)
```sql
SELECT '0 - TODOS' AS ITEM
FROM DUAL
UNION ALL
SELECT DISTINCT TO_CHAR(SEQPESSOA) || ' - ' || SUBSTR(REPLACE(NOMERAZAO, '''', ''), 1, 80) AS ITEM
FROM GE_PESSOA
WHERE STATUS = 'A'
```

### SQL da lista LS3 (Aberto / Quitado)

Cole o comando SQL abaixo na caixa de instrução da lista `LS3` no **Var - F7**:

```sql
SELECT '0 - TODOS' AS ITEM FROM DUAL
UNION ALL
SELECT '1 - QUITADO' FROM DUAL
UNION ALL
SELECT '2 - ABERTO' FROM DUAL
UNION ALL
SELECT '3 - SEM TITULO' FROM DUAL
UNION ALL
SELECT '4 - CANCELADO' FROM DUAL
```

## Passo a passo operacional na Consulta Criação
1. Abrir a tela **Consulta Criação** no Totvs Consinco e colar o conteúdo de [`consulta_acordos_verbas_corrigida.sql`](../querys/consulta_acordos_verbas_corrigida.sql).
2. Pressionar o botão **Var - F7**.
3. Cadastrar `LT1` na aba **Literal** com valor padrão `1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 17, 18, 900`.
4. Cadastrar `LT2` na aba **Literal** com valor padrão `2` (para expurgar acordos cancelados por padrão).
5. Cadastrar `LS1` na aba **Lista** com descrição **Comprador** e colar a SQL correspondente.
6. Cadastrar `LS2` na aba **Lista** com descrição **Fornecedor** e colar a SQL correspondente.
7. Cadastrar `LS3` na aba **Lista** com descrição **Status Acordo** e colar a SQL correspondente.
8. Cadastrar `NR1` na aba **Numérico** com valor padrão `0`.
9. Cadastrar `DT1` e `DT2` na aba **Data**.
10. Gravar as variáveis e clicar em **Run**.
