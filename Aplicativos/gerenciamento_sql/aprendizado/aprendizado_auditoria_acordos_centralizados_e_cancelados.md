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

