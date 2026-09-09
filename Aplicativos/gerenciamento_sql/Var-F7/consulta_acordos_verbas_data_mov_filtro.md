# Var-F7 - consulta_acordos_verbas_data_mov_filtro

## Query vinculada
- Arquivo SQL: [Aplicativos/gerenciamento_sql/querys/consulta_acordos_verbas_data_mov_filtro.sql](../querys/consulta_acordos_verbas_data_mov_filtro.sql)

## Objetivo
Listar acordos comerciais e verbas (`MSUV_ACORDOPROMOC` / `MSU_ACORDOPROMOC`) que tiveram **movimentação ou atualização de quitação no período de :DT1 a :DT2**, com filtros por **Lojas (`:LT1`)**, **Usuários da Manutenção (`:LT2`)**, **Códigos fornecedores (`:LT3`)**, **Expurgo de Cancelados (`:NR1`)**, **Comprador (`:LS1`)**, **Situação Financeira (`:LS2`)** e **Rede de Fornecedores (`:LS3`)**, unificando títulos financeiros vinculados (`FI_TITULO` / `FI_TITOPERACAO`), exibindo a **Espécie do Título (`ESPECIE_TITULO` - ex: DEVREC, VERBA, ACORDO)**, rateio por item sem dízimas, totais gerais consolidados e auditoria com usuário e data/hora da última movimentação financeira.

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
- `ESPECIE_TITULO`: sigla da espécie do título financeiro vinculado (ex: `DEVREC`, `VERBA`, `ACORDO`, `ACRPRE`, etc.).
- `ABERTO_QUITADO`: status financeiro atual ('Quitado', 'Aberto', 'Sem Título').
- `TIPO_ACORDO`: modalidade do acordo ('VERBA EXTRA', 'SELL-OUT', 'SELL-IN').
- `CODIGO_PRODUTO`: código do item vinculado (`A.SEQPRODUTO`).
- `QTD_UTILIZADA_VERBA`: quantidade utilizada/abatida da verba.
- `DATA_FINAL_VERBA`: data de vigência final da verba formatada (`DD/MM/YYYY`).
- `VENCIMENTO_EM_ABERTO`: menor data de vencimento com saldo pendente (`DD/MM/YYYY`).
- `ULTIMO_RECEBIMENTO`: data da quitação ou última alteração (`DD/MM/YYYY`).
- `NUMERO_NF`: número do documento fiscal.
- `NUMERO_PEDIDO_SUPRIMENTO`: número do pedido de compra/suprimento.
- `VALOR_ACORDO`: valor total bruto do acordo (`R$ 0.000,00`).
- `VLR_FIN_VENCIDO`: valor vencido em aberto (`R$ 0.000,00`).
- `VLR_JA_QUITADO`: valor financeiro acumulado quitado (`R$ 0.000,00`).
- `VALOR_UTILIZADO_PRODUTO`: valor abatido em produtos (`R$ 0.000,00`).
- `TOTAL_PARCELAS`: total de parcelas geradas/programadas.
- `PARCELAS_PAGAS`: total de parcelas liquidadas.
- `PARCELAS_PENDENTES`: total de parcelas pendentes.
- `VALOR_PAG_REGISTRADO`: valor monetário da última operação financeira vinculada ao operador.
- `USUARIO_DATA_HORA_ALTERACAO`: usuário e data/hora da última movimentação registrada (`USUARIO - DD/MM/YYYY HH24.MI.SS`).

## Variáveis para cadastrar em Var - F7 (9 Variáveis)

| Variável | Tipo | Descrição na Tela | Valor Padrão | Instrução p/ o Usuário |
| :--- | :--- | :--- | :--- | :--- |
| **`LT1`** | Literal | Lojas | `1,2,3,4,5,6,7,8,11,12,13,14,15,16,17,18,21,50,900` | `0` para todas ou lojas separadas por vírgula |
| **`LT2`** | Literal | Usuarios da Manutenção | `0` | `0` para todos ou logins separados por vírgula |
| **`LT3`** | Literal | Código Fornecedor | `0` | `0` para todos ou códigos de fornecedores separados por vírgula |
| **`NR1`** | Numérico | Expurgar CANCELADO | `2` | `2` para expurgar cancelados ou `0` para todos |
| **`DT1`** | Data | Data Inicial Lançamento | `01/01/2026` | Início do período |
| **`DT2`** | Data | Data Final Lançamento | `09/09/2026` | Fim do período |
| **`LS1`** | Lista | Comprador | `0 - TODOS` | Seleção de Comprador |
| **`LS2`** | Lista | Situação Financeira | `0 - TODOS` | `1 - QUITADO`, `2 - ABERTO`, etc. |
| **`LS3`** | Lista | Rede Fornecedores | ` TODAS AS REDES` | Selecione a Rede (`GE_REDE`) desejada ou mantenha ` TODAS AS REDES` |

---

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

### SQL da lista LS2 (Situação Financeira / Aberto / Quitado)
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

### SQL da lista LS3 (Rede Fornecedores)
```sql
SELECT ' TODAS AS REDES' FROM DUAL
UNION ALL
SELECT DESCRICAO FROM GE_REDE
```
