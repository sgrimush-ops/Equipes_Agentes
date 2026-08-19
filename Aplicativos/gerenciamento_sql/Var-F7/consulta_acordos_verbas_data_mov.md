# Var-F7 - consulta_acordos_verbas_data_mov

## Query vinculada
- Arquivo SQL: [Aplicativos/gerenciamento_sql/querys/consulta_acordos_verbas_data_mov.sql](../querys/consulta_acordos_verbas_data_mov.sql)

## Objetivo
Listar acordos comerciais e verbas (`MSUV_ACORDOPROMOC` / `MSU_ACORDOPROMOC`) que tiveram **movimentação ou atualização de quitação no período de :DT1 a :DT2**, com filtro opcional por **Usuários da Manutenção (`:LT3`)**, unificando todos os títulos financeiros vinculados (`FI_TITULO` / `FI_TITOPERACAO`), valores rateados rigorosamente por produto sem dízimas, totais gerais e auditoria de alteração com usuário e data/hora da última movimentação financeira.

## Arquitetura e Otimização
- **`CTE_TITULOS_ACORDO`**: Unifica via 6 uniões seguras todos os títulos vinculados ao acordo no Contas a Receber (`MSU_ACORDOTITULORECEB`, `MSU_CCACORDOPROMOC`, `MSU_CCDIVIDA`, `FI_TITOPERACAO` via processo e relacionamento direto por documento/espécie).
- **`CTE_OPERACOES_TITULO`**: Coleta e indexa de forma materializada em RAM (`/*+ MATERIALIZE */`) as operações financeiras em `FI_TITOPERACAO` vinculadas estritamente aos títulos do acordo, capturando o usuário (`USUALTERACAO`), a data da operação (`DTAOPERACAO`) e o timestamp da alteração (`DTAHORAALTERACAO`).
- **`CTE_TITULOS_RESUMO`**: Agrega os dados financeiros e de auditoria por acordo (`NROACORDO`, `NROEMPRESA`), identificando a bandeira `TEVE_MOV_QUITACAO_PERIODO = 1` quando houver quitação ou movimentação/operação entre `:DT1` e `:DT2`.
- **`CTE_VALORES_BRUTOS`**: Aplica o filtro de quitação no período (`TR.TEVE_MOV_QUITACAO_PERIODO = 1`), filtros de loja (`#LT1`), expurgo de cancelados (`#LT2`), **usuários da manutenção (`:LT3`)**, comprador (`:LS1`), fornecedor (`:LS2`) e número do acordo (`:NR1`).
- **Rateio e Fechamento em 2 Níveis**: Cabeçalho do acordo (`CTE_ACORDO_HEADER` / `CTE_ACORDO_FINANCEIRO`) com rateio exato por produto (`CTE_VALORES_PRE`), garantindo $\text{VLR\_JA\_QUITADO} + \text{VLR\_EM\_ABERTO} = \text{VALOR\_ACORDO}$ e diferença zero no total.
- **Coluna de Auditoria**: `USUARIO_DATA_HORA_ALTERACAO` trazendo o operador responsável e o instante da alteração no formato `USUARIO - DD/MM/YYYY HH24:MI:SS`.

## Colunas Retornadas
- `CODIGO_EMPRESA`: código da empresa/loja do acordo (`A.NROEMPRESA`).
- `NUMERO_ACORDO`: número único do acordo (`A.NROACORDO`).
- `NUMERO_PROCESSO`: sequencial do processo vinculado (`AC.SEQPROCESSO`).
- `CODIGO_FORNECEDOR`: código do fornecedor (`B.SEQPESSOA`).
- `FORNECEDOR`: razão social do fornecedor (ou `'TOTAL GERAL ->'` no rodapé).
- `DESCRICAO_ACORDO`: descrição textual do acordo (`A.DESCACORDO`).
- `DATA_EMISSAO`: data de emissão formatada (`DD/MM/YYYY`).
- `COMPRADOR`: apelido ou nome do comprador (`C.APELIDO`).
- `STATUS_ACORDO`: status comercial ('Aprovado', 'Cancelado', 'Concluido', 'Interrompido', 'Pendente').
- `SITUACAO_ACORDO`: situação operacional ('Financeiro', 'Pendente', 'Cancelado').
- `DIREITO_OBRIGACAO`: classificação do título ('Direito', 'Obrigação', 'Sem Título').
- `ABERTO_QUITADO`: status financeiro atual ('Quitado', 'Aberto', 'Sem Título').
- `TIPO_ACORDO`: modalidade do acordo ('VERBA EXTRA', 'SELL-OUT', 'SELL-IN').
- `CODIGO_PRODUTO`: código do item vinculado (`A.SEQPRODUTO`).
- `QTD_UTILIZADA_VERBA`: quantidade utilizada/abatida da verba.
- `DATA_FINAL_VERBA`: data de vigência final da verba formatada (`DD/MM/YYYY`).
- `VENCIMENTO_EM_ABERTO`: menor data de vencimento com saldo pendente (`DD/MM/YYYY`).
- `ULTIMO_RECEBIMENTO`: data da quitação/última liquidação formatada (`DD/MM/YYYY`).
- `NUMERO_NF`: número do documento fiscal.
- `NUMERO_PEDIDO_SUPRIMENTO`: número do pedido de compra/suprimento.
- `VALOR_ACORDO`: valor total do acordo (`R$ 0.000,00`).
- `VLR_EM_ABERTO`: valor pendente em aberto (`R$ 0.000,00`).
- `VLR_FIN_VENCIDO`: valor vencido em aberto (`R$ 0.000,00`).
- `VLR_JA_QUITADO`: valor financeiro efetivamente quitado (`R$ 0.000,00`).
- `VALOR_SALDO_ACORDO`: saldo disponível do acordo (`R$ 0.000,00`).
- `VALOR_UTILIZADO_PRODUTO`: valor abatido em produtos (`R$ 0.000,00`).
- `TOTAL_PARCELAS`: total de parcelas geradas/programadas.
- `PARCELAS_PAGAS`: total de parcelas liquidadas.
- `PARCELAS_PENDENTES`: total de parcelas pendentes.
- `USUARIO_DATA_HORA_ALTERACAO`: usuário e data/hora da última movimentação/quitação registrada (`USUARIO - DD/MM/YYYY HH24:MI:SS`).

## Variáveis para cadastrar em Var - F7

### LT1
- **Tipo:** Literal
- **Descrição:** Lojas
- **Valor padrão:** `1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18, 50, 900`
- **Instrução p/ o usuário:** Mantenha os números das lojas separadas por vírgula no campo ou informe as lojas desejadas.

### LT2
- **Tipo:** Literal
- **Descrição:** Expurgar CANCELADO
- **Valor padrão:** `2`
- **Instrução p/ o usuário:** Define os códigos de status a serem ignorados. O padrão `2` expurga acordos cancelados. Para trazer todos sem expurgo, informe `0`.

### LT3
- **Tipo:** Literal
- **Descrição:** Usuarios da Manutenção
- **Valor padrão:** `0` (ou deixe vazio / `TODOS` para não filtrar por usuário, ou digite logins separados por vírgula ex: `veridi,debco`)
- **Instrução p/ o usuário:** Digite um ou mais logins de usuários separados por vírgula (ex: `veridi,debco`). O filtro é insensível a maiúsculas/minúsculas. Para trazer todos os usuários, informe `0` ou `TODOS`.

### NR1
- **Tipo:** Numérico
- **Descrição:** Numero Acordo
- **Valor padrão:** `0`
- **Instrução p/ o usuário:** Informe o número exato do acordo ou mantenha `0` para trazer todos.

### DT1
- **Tipo:** Data
- **Descrição:** Data Inicial Emissão / Quitação
- **Valor padrão:** Primeiro dia do mês atual ou conforme rotina
- **Instrução p/ o usuário:** Informe a data inicial da movimentação de quitação/baixa.

### DT2
- **Tipo:** Data
- **Descrição:** Data Final Emissão / Quitação
- **Valor padrão:** Data de hoje (`SYSDATE`)
- **Instrução p/ o usuário:** Informe a data final da movimentação de quitação/baixa.

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
- **Descrição:** Situação Financeira (Aberto / Quitado)
- **Valor padrão:** `0 - TODOS`
- **Instrução p/ o usuário:** Selecione a situação desejada (`1 - QUITADO`, `2 - ABERTO`, `3 - SEM TITULO`, `4 - CANCELADO`) ou mantenha `0 - TODOS`.

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

### SQL da lista LS3 (Situação Financeira / Aberto / Quitado)
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
1. Abrir a tela **Consulta Criação** no Totvs Consinco e colar o código de [`consulta_acordos_verbas_data_mov.sql`](../querys/consulta_acordos_verbas_data_mov.sql).
2. Clicar no botão **Var - F7**.
3. Cadastrar as variáveis na seguinte ordem:
   - `LT1` (Literal) - Lojas
   - `LT2` (Literal) - Expurgar CANCELADO
   - `LT3` (Literal) - Usuarios da Manutenção
   - `NR1` (Numérico) - Numero Acordo
   - `DT1` (Data) - Data Inicial
   - `DT2` (Data) - Data Final
   - `LS1` (Lista) - Comprador
   - `LS2` (Lista) - Fornecedor
   - `LS3` (Lista) - Situação Financeira
4. Colar as queries correspondentes nas listas `LS1`, `LS2` e `LS3`.
5. Salvar o painel de variáveis e clicar em **Run**.
