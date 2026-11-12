# Aprendizado Técnico: Auditoria de Acordos Comerciais, Títulos Centralizados na Matriz e Cancelamentos Indevidos no ERP Totvs Consinco

Este documento consolida a investigação técnica e as regras de negócio definitivas para a conciliação entre o módulo Comercial (`MSUV_ACORDOPROMOC`, `MSU_ACORDOPROMOC`, `MSU_ACORDOPROMOCPARCELA`) e o módulo Financeiro (`FI_TITULO`, `FI_TITOPERACAO`) no ERP Totvs Consinco / Oracle.

---

## 1. Contexto do Problema e Sintomas Visuais

No relatório analítico de Acordos e Verbas (`consulta_acordos_verbas_data_mov_filtro.sql`):
* Linhas de acordos aprovados/concluídos apareciam com fundo destacado sem movimentação financeira.
* As colunas exibiam:
  * `DIREITO_OBRIGACAO`: `'Sem Título'`
  * `ESPECIE_TITULO`: `'ACORDO'` (fallback)
  * `ABERTO_QUITADO`: `'Sem Título'`
  * `ULTIMO_RECEBIMENTO`: Vazio (`NULL`)
  * `USUARIO_DATA_HORA_ALTERACAO`: Vazio (`NULL`)
  * `SITUACAO_ACORDO`: `'Financeiro'` (mesmo sem duplicatas aparentes)

---

## 2. Causa Raiz 1: Títulos Faturados Centralizados na Loja 3 (Matriz/Centralizadora)

### O Fluxo Operacional no Totvs Consinco
Quando o setor Comercial cadastra uma verba com rateio por filial (ex: Processos `12066` e `12229` da MARQUESPAN):
1. O Comercial gera um registro de acordo em cada filial (`MSUV_ACORDOPROMOC` nas Lojas 2, 4, 5, 6, 7, 8, 12, 13, 14, 17, 18).
2. O setor Financeiro, por padrão fiscal/contábil da rede, **não gera títulos individuais dentro de cada filial**, mas emite todas as duplicatas a receber centralizadas na **Loja 3 (Matriz/Centralizadora)**.
3. No Contas a Receber (`FI_TITULO`):
   * O campo `T.NROEMPRESA` é gravado como `3`.
   * O campo `T.NROTITULO` e `T.NRODOCUMENTO` recebem o número do acordo de cada filial (`A.NROACORDO`).
   * O valor do título `T.VLRORIGINAL` corresponde ao valor exato do rateio daquela filial (`A.VLRACORDO`).

### O Descarte Silencioso na Query Original
A amarração histórica na `CTE_TITULOS_ACORDO` exigia estritamente:
```sql
AND (
    T.NROEMPRESA = A.NROEMPRESA
    OR (
        A.NROEMPRESA IN (1, 15, 50, 900)
        AND NOT EXISTS (...)
    )
)
```
Como a filial do acordo era a Loja 4, 5, 6, etc. (que não são 1, 15, 50, 900) e o título estava na **Loja 3**, a condição falhava e o título era descartado, fazendo as CTEs financeiras (`CTE_TITULOS_GLOBAL` e `CTE_ACORDO_RESUMO_GLOBAL`) retornarem `NULL`.

---

## 3. A Solução Arquitetural Homologada: Vinculação Centralizada com Blindagem Matemática por Valor

### O Risco da Amarração Solta por Número de Acordo
Se fizéssemos apenas `T.NROTITULO = A.NROACORDO` na Loja 3, ocorreria **multiplicação indevida de linhas**.  
*Exemplo real*: o Acordo nº 36 existia tanto na Loja 5 (R$ 25,36) quanto na Loja 8 (R$ 24,65). Na Loja 3 haviam dois títulos com número 36. Ligar apenas pelo número faria a Loja 5 casar com os dois títulos e a Loja 8 também casar com os dois.

### A Regra Homologada: Correlação pelo Valor Exato do Acordo / Parcela
Para permitir títulos centralizados na Matriz (`T.NROEMPRESA IN (1, 3, 15, 50, 900)`) sem ambiguidade, valida-se o valor nominal com margem de arredondamento de centavos (`< 0.05`):

```sql
AND (
    T.NROEMPRESA = A.NROEMPRESA
    OR (
        T.NROEMPRESA IN (1, 3, 15, 50, 900)
        AND (
            ABS(NVL(T.VLRORIGINAL, 0) - NVL(A.VLRACORDO, 0)) < 0.05
            OR EXISTS (
                SELECT 1
                FROM MSU_ACORDOPROMOCPARCELA P
                WHERE P.NROACORDO = A.NROACORDO
                  AND P.NROEMPRESA = A.NROEMPRESA
                  AND ABS(NVL(T.VLRORIGINAL, 0) - NVL(P.VALORPARCELA, 0)) < 0.05
            )
        )
    )
    OR (
        A.NROEMPRESA IN (1, 15, 50, 900)
        AND NOT EXISTS (
            SELECT 1
            FROM MSU_ACORDOPROMOC A_LOCAL
            WHERE A_LOCAL.NROEMPRESA = T.NROEMPRESA
              AND A_LOCAL.NROACORDO = T.NROTITULO
        )
    )
)
```

Com essa amarração:
* O título da Loja 3 casa unicamente com a filial que possui o valor exato do rateio.
* A coluna `USUARIO_DATA_HORA_ALTERACAO` projeta a tag oficial de auditoria: `[Lj 3] OPERADOR - DATA HORA (Parc. 1/1)`.

---

## 4. Causa Raiz 2: Títulos Cancelados no Financeiro (`T.SITUACAO = 'C'`) e Auditoria Ativa

### A Investigação dos Casos Pendentes (Loja 17 / Acordo 41 e Loja 6 / Acordos 43 e 44)
Após a liberação da Loja 3, 3 linhas permaneceram acusando `'Sem Título'`:
* Loja 17 / Acordo 41 (R$ 19,68)
* Loja 6 / Acordo 43 (R$ 55,29)
* Loja 6 / Acordo 44 (R$ 49,30)

A query de investigação direta comprovou que na tela de **Manutenção/Consulta de Títulos do Consinco**:
* O título nº 41 de R$ 19,68 na Loja 3 existiu, mas foi cancelado pelo usuário `THROCHA` com a justificativa: *"VALOR SAIU ERRADO DO CONTRATO"*.
* Sua situação no banco foi alterada para `SITUACAO = 'C'`.

### O Princípio de Integridade Contábil da Query
A cláusula mandatória em todas as CTEs de títulos é:
```sql
WHERE T.SITUACAO != 'C'
```
Se a query ignorasse o cancelamento, ela exibiria um título cancelado como se fosse um valor a receber válido, gerando **falso faturamento e divergência contábil**.

### O Relatório como Ferramenta Ativa de Auditoria
A exibição de `'Sem Título'` para acordos comerciais concluídos cumpre um papel vital de controle interno:
1. **Sinaliza Inconsistência:** Alerta o setor Financeiro e a Controladoria de que o Comercial concluiu a negociação com o fornecedor, mas o Financeiro cancelou o título (ou não o gerou).
2. **Evita Perda de Receita:** Permite que o operador financeiro reemita o título de verba antes que o prazo de cobrança prescreva, garantindo que o dinheiro entre no caixa da empresa.

---

## 5. Explicação do Fallback da Coluna `SITUACAO_ACORDO = 'Financeiro'`

Por que um acordo sem título exibiu a situação `'Financeiro'`?
* Na `CTE_VALORES_BRUTOS`, o total de parcelas é computado como:
  ```sql
  GREATEST(NVL((SELECT COUNT(*) FROM MSU_ACORDOPROMOCPARCELA ...), 0), NVL(RG.TOTAL_TITULOS, NVL(TG.QTDPARCELA, 1)))
  ```
  O fallback `NVL(TG.QTDPARCELA, 1)` faz com que `TOTAL_PARCELAS` assuma o valor mínimo `1`.
* Na `CTE_CLASSIFICADA_PRE`, a regra classifica:
  ```sql
  WHEN NVL(X.TOTAL_PARCELAS, 0) > 0 THEN 'Financeiro'
  ```
  Logo, qualquer acordo com pelo menos 1 parcela prevista é considerado comercialmente integrado ao fluxo financeiro, cabendo à coluna `DIREITO_OBRIGACAO` e `ABERTO_QUITADO` apontar se os títulos físicos realmente existem no Contas a Receber (`FI_TITULO`).

---

## 6. Hierarquia de Registro de Usuário (`PRIORIDADE_OP`) e Rastreio de Cancelamentos (`CTE_AUDIT_CANC`)

### O Problema do Campo de Usuário em Branco ou Omissão de Cancelamento
Quando o setor Financeiro cancelava uma operação de baixa (`FI_TITOPERACAO.OPCANCELADA = 'S'` ou `USUCANCELOU IS NOT NULL`) ou cancelava o próprio título (`FI_TITULO.SITUACAO = 'C'`):
1. **Em Títulos Ativos com Baixa Cancelada:** O filtro anterior (`WHERE TRIM(O.USUCANCELOU) IS NULL`) descartava a operação cancelada, fazendo o relatório ocultar quem realizou o cancelamento ou perder o vínculo no período quando o acordo havia sido emitido em mês anterior.
2. **Em Acordos com Título Cancelado (`Sem Título`):** Como `CTE_TITULOS_ACORDO` filtra `T.SITUACAO != 'C'` para proteger os valores financeiros (mantendo `VLR_JA_QUITADO = R$ 0,00` e `VALOR_PAG_REGISTRADO = R$ 0,00`), a coluna `USUARIO_DATA_HORA_ALTERACAO` ficava completamente vazia (`NULL`).
3. **Em Acordos de Sell-In por Pedido (ex: `ACORDO REF. PEDIDO: 16/136299/L`):** Acordos concluídos diretamente pela entrada das Notas Fiscais em `MSU_ACORDOTITULORECEB` sem geração de duplicata avulsa de Direito em `FI_TITULO` também ficavam sem informação de usuário.

### A Solução Homologada em 3 Camadas (Sem Alterar o Financeiro)
1. **Hierarquia `PRIORIDADE_OP` em `CTE_OPERACOES_RAW` / `CTE_OPERACOES_TITULO`:**
   * **`PRIORIDADE_OP = 3` (Manutenção Ativa):** Operações `CODOPERACAO NOT IN (16, 18)` não canceladas. São as **únicas** que somam em `VLROPERACAO` (`VALOR_PAG_REGISTRADO`).
   * **`PRIORIDADE_OP = 2` (Operação Cancelada):** Soma `0` no financeiro e projeta `NVL(TRIM(O.USUCANCELOU), TRIM(O.USUALTERACAO)) || ' (CANC)'` com `GREATEST(NVL(O.DTAHORAALTERACAO, O.DTAALTERACAO), NVL(O.DTACANCELOU, ...))` quando não há outra manutenção ativa.
   * **`PRIORIDADE_OP = 1` (Inclusão do Título):** Operações `16` e `18` ativas; exibe o usuário criador do título apenas quando não houve manutenção nem cancelamento posterior.
2. **CTE Dedicada `CTE_AUDIT_CANC` para Linhas `Sem Título`:**
   * Busca títulos/operações cancelados via número do acordo/processo, via `FI_TITOPERACAO.NROPROCESSO = A.SEQPROCESSO` e via `MSU_ACORDOTITULORECEB.LINKERP`, preenchendo `[Lj X] USUARIO (CANC) - DD/MM/YYYY HH24.MI.SS (Parc. 1/1)` exclusivamente na coluna `USUARIO_DATA_HORA_ALTERACAO`.
3. **Fallback para a Tabela `MSU_ACORDOPROMOC` e Prevenção de `ORA-00979`:**
   * Caso o acordo nunca tenha gerado registro em `FI_TITULO` (como em Sell-In liquidado em NF), faz fallback para `COALESCE(AC.USUALTERACAO, AC.USUEXPFINANCEIRO, AC.USUAPROVREPROV, AC.USUINCLUSAO)` e respectiva data.
   * No `GROUP BY` da `CTE_VALORES_BRUTOS`, as colunas `TG.USU_ULTIMA_ALTERACAO`, `CA.USU_CANC`, `TG.DTA_ULTIMA_ALTERACAO`, `CA.DTA_CANC`, `TG.NROEMPRESA_TITULO` e `CA.NROEMPRESA_CANC` devem ser declaradas individualmente para evitar `ORA-00979: not a GROUP BY expression` ao combiná-las com `MAX(AC....)` dentro do `COALESCE`.


