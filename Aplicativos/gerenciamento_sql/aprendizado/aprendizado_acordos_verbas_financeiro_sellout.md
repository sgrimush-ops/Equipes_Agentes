# Aprendizado Técnico e Regras de Negócio: Consulta de Acordos e Verbas Comerciais (Totvs Consinco / Oracle)

## 1. Contexto e Objetivos de Negócio

No ERP Totvs Consinco, o módulo de Acordos Comerciais e Verbas Promocionais (`MSUV_ACORDOPROMOC`, `MSU_ACORDOPROMOC`, `FI_TITULO`, `MRLV_VERBACONSUMIDA`) gerencia compromissos financeiros entre a rede varejista e os fornecedores (Verba Extra, Sell-Out e Sell-In).

A conciliação desses acordos com o setor Financeiro exige **fechamento contábil rigoroso (diferença de R$ 0,00 entre o valor contratado e a soma de aberto + quitado)**, além de fidelidade total aos status literais exibidos nas telas do ERP.

---

## 2. Padrão Ouro: Fidelidade Literal aos Status das Telas do ERP Consinco

Para evitar divergências de entendimento entre os setores de Compras, Comercial e Financeiro, a query **não deve inventar nem interpretar status**, devendo refletir exatamente o que o operador visualiza nas telas do sistema:

### 2.1. Módulo Comercial (Tela: *Manutenção de Acordos Promocionais*)
* **`STATUS_ACORDO` (Campo "Status" no topo da tela do ERP):**
  * `Aprovado`: Acordo ativo e aprovado no comercial (`STATUS = 1`).
  * `Cancelado`: Acordo formalmente cancelado (`STATUS = 2`).
  * `Concluido`: Acordo encerrado administrativamente (`STATUS = 3`).
  * `Interrompido`: Acordo interrompido (`STATUS = 4`).
  * `Pendente`: Acordo em elaboração ou aguardando aprovação (`STATUS = 0` / outros).
* **`SITUACAO_ACORDO` (Campo "Situação" no topo da tela do ERP):**
  * `Financeiro`: O acordo gerou processo/títulos integrados com o Contas a Receber (`TOTAL_PARCELAS > 0` ou títulos em `FI_TITULO`).
  * `Pendente`: O acordo não gerou duplicatas/parcelas no financeiro.
  * `Cancelado`: Acordo cancelado (`STATUS = 2`).

### 2.2. Módulo Financeiro (Tela: *Consulta de Títulos / FiConsTitulo*)
* **`DIREITO_OBRIGACAO` (Campo `FI_TITULO.OBRIGDIREITO`):**
  * `Direito`: Título a receber do fornecedor / crédito da empresa (`OBRIGDIREITO = 'D'`).
  * `Obrigação`: Título a pagar ao fornecedor (`OBRIGDIREITO = 'O'`).
  * `Sem Título`: Acordo sem títulos emitidos no Contas a Receber.
* **`ABERTO_QUITADO` (Campo `FI_TITULO.ABERTOQUITADO`):**
  * `Quitado`: Todos os títulos do acordo foram efetivamente baixados/pagos pelo Financeiro (`ABERTOQUITADO = 'Q'`).
  * `Aberto`: Possui títulos com saldo em aberto a receber (`ABERTOQUITADO = 'A'`).
  * `Sem Título`: Acordo sem títulos emitidos no Contas a Receber.

---

## 3. Regra Contábil Imutável de Quitação Financeira

* **Entrada de NF / Pedido de Sell-In NÃO é Quitação:**  
  A Nota Fiscal de compra vinculada a um acordo de Sell-In (`VERBA NEGOCIADA POR PRODUTO`) serve como comprovação da negociação e gera o direito de recebimento da verba. Ela **não constitui o pagamento em si**. O recebimento real pode ocorrer via desconto em duplicata, abatimento em borderô, depósito bancário ou bonificação.
* **Critério Estrito de Quitação (`VLR_JA_QUITADO`):**  
  Um valor só é classificado como quitado se houver **baixa financeira real** registrada no Contas a Receber (`FI_TITULO.ABERTOQUITADO = 'Q'`). Caso não haja baixa financeira, o valor permanece integralmente em `VLR_EM_ABERTO` e `VALOR_SALDO_ACORDO`.

---

## 4. Isolamento Estrito entre Filiais e Matriz (`FI_TITULO` vs `MSU_ACORDOPROMOC`)

* **O Problema de Contaminação entre Lojas:**  
  Em redes com matriz e filiais, amarrações com `OR T.NROEMPRESAMAE = A.NROEMPRESA` faziam títulos de uma filial (ex: Loja 16) serem somados indevidamente em acordos de outra loja (ex: Loja 3) caso houvesse o mesmo número de processo ou documento.
* **A Solução Mandatória:**  
  Toda amarração na `CTE_TITULOS_ACORDO` deve ser **estritamente por filial**, garantindo que `T.NROEMPRESA = A.NROEMPRESA` em todos os blocos de junção.

---

## 5. A Causa Raiz da Inconsistência de Rateio e a Solução em 2 Níveis

### O Problema Histórico
Ao tentar ratear títulos financeiros de processos (`RAW_VLRFINVENCIDO` / `fValorTitAcordo`) em acordos com múltiplos produtos através de fórmulas artificiais de produto (`VLRSALDOACORDO + VLRUTILPROD`), gerava-se descasamento na soma total de valores.

### O Padrão Ouro: Consolidação em 2 Níveis (Acordo ➔ Produto)

1. **Nível 1 — Cabeçalho do Acordo (`CTE_ACORDO_HEADER` e `CTE_ACORDO_FINANCEIRO`):**
   Calcula-se o financeiro consolidado por chave de contrato (`NROEMPRESA + NROACORDO`):
   ```sql
   /* Nível 1: Garante 100% que Aberto + Quitado = Total do Acordo */
   VLR_TOTAL_ACORDO = GREATEST(SUM(PROD_PESO), QUITADO + VENCIDO + AVENCER)
   ACORDO_VLR_QUITADO = LEAST(VLR_TOTAL_ACORDO, RAW_QUITADO)
   ACORDO_VLR_ABERTO = VLR_TOTAL_ACORDO - ACORDO_VLR_QUITADO
   ACORDO_VLR_VENCIDO = LEAST(ACORDO_VLR_ABERTO, RAW_VENCIDO)
   ```

2. **Nível 2 — Rateio Proporcional Blindado por Produto (`CTE_VALORES_PRE`):**
   Para acordos com múltiplos produtos, cada linha recebe a fração exata do peso do item:
   ```sql
   /* Nível 2: Rateio que fecha rigorosamente na vírgula sem centavos soltos */
   LINE_VLRACORDO = ROUND(VLR_TOTAL_ACORDO * (PESO / SUM_PESO), 2)
   LINE_VLR_QUITADO = ROUND(ACORDO_VLR_QUITADO * (PESO / SUM_PESO), 2)
   LINE_VLR_ABERTO = LINE_VLRACORDO - LINE_VLR_QUITADO
   LINE_VLR_VENCIDO = LEAST(LINE_VLR_ABERTO, ROUND(ACORDO_VLR_VENCIDO * (PESO / SUM_PESO), 2))
   ```

**Propriedades Matemáticas Garantidas:**
- $\text{VLR\_JA\_QUITADO} + \text{VLR\_EM\_ABERTO} = \text{VALOR\_ACORDO}$ em 100% das linhas.
- $\text{VLR\_FIN\_VENCIDO} \le \text{VLR\_EM\_ABERTO} \le \text{VALOR\_ACORDO}$ em 100% das linhas.
- $\text{Diferença no Total Geral} = \mathbf{R\$\ 0,00}$.

---

## 6. Guia de Resolução de Erros ORA-* no Oracle / Consinco

| Código de Erro | Causa no Consinco | Solução Aplicada |
| :--- | :--- | :--- |
| **`ORA-00979: not a GROUP BY expression`** | Referência a coluna não agregada dentro de um `CASE` em CTE com `GROUP BY` (ex: `A.NUMERONF` solto no `CASE`). | Usar apenas colunas presentes no `GROUP BY` ou aplicar função de agregação (`MAX(A.NUMERONF)`). |
| **`ORA-00904: "VC"."VLRUTILIZADAVERBA": invalid identifier`** | Grafia incorreta da coluna na view `MRLV_VERBACONSUMIDA`. | O nome nativo é **`VLRUTILIZADOVERBA`** (com *"O"* no final). |
| **`ORA-00937: not a single-group group function`** | Mistura de `SUM(coluna)` agregada direta com subconsultas escalares `(SELECT ...)` no mesmo `SELECT` sem `GROUP BY` na `CTE_TOTAIS`. | Desacoplar em **`CTE_TOTAIS_VALORES`** (agregação única) e **`CTE_TOTAIS_PARCELAS`** unidas via **`CROSS JOIN`**. |
| **`ORA-00936 / ORA-00907: missing expression / parenthesis`** | Macro literal `#LT2` sem preenchimento na interface (`AND A.STATUS NOT IN ()`). | Cadastrar a variável **`LT2`** na aba Literal do `Var - F7` com valor padrão `2` (expurga cancelados) ou `0` (auditoria total). |
| **`ORA-00932: inconsistent datatypes: expected CHAR got NUMBER`** | Variável bind `:NR1` comparada diretamente sem conversão de tipos de dados. | Usar sempre conversão explícita **`TO_NUMBER(:NR1)`**. |
| **`ORA-01013: user requested cancel / Timeout`** | Recálculo repetido de 6 `UNION`s em `FI_TITULO` e views transacionais. | Inserir obrigatoriamente o hint **`/*+ MATERIALIZE */`** nas CTEs pesadas (`CTE_TITULOS_ACORDO`, `CTE_VALORES_BRUTOS`, `CTE_CLASSIFICADA`). |
| **`Erro "Não é uma consulta"`** | Validador arcaico da tela Consulta Criação que exige `SELECT` como primeira palavra. | Envelopar toda a consulta com **`SELECT * FROM ( WITH ... SELECT ... )`**. |

---

## 7. Padrão de Configuração de Variáveis de Lista `LS*` (Var - F7)

Para que as listas de seleção no `Var - F7` gerem menus dropdown limpos com cada opção em sua própria linha:

* **Instrução SQL Obrigatória para `LS3` (Aberto / Quitado):**
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
