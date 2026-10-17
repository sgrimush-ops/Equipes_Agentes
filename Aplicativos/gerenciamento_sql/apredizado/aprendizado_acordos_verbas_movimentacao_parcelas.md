# Aprendizado Definitivo: Resolução de Erros de SQL no Consinco e Movimentação Financeira de Acordos

Este documento consolida as regras de ouro, as causas raízes de erros do Oracle/Delphi no Totvs Consinco e o padrão arquitetural homologado para consultas financeiras detalhadas por parcela.

---

## 1. Guia Anti-Erros Oracle SQL no Totvs Consinco

### ❌ Erro 1: `ORA-00936: missing expression` em Expressões CASE
- **Causa Raiz:** Escrever operadores aritméticos envolvendo blocos `CASE` com parênteses externos:
  ```sql
  -- NUNCA FAÇA ISSO (Gera ORA-00936):
  ( CASE WHEN F.ACORDO_SUM_PESO > 0 THEN ROUND(...) ELSE F.VLR_TOTAL_ACORDO END ) - NVL(B.VLRUTILPROD, 0)
  ```
  O parser Delphi do Totvs Consinco remove quebras de linha e compacta o SQL em uma string contínua. O `)` após o `END` faz o analisador léxico interpretar que o CASE externo foi encerrado, deixando o operador `-` solto antes da palavra reservada `ELSE`.
- **✅ Solução Obrigatória:** Aplicar a aritmética diretamente dentro de cada cláusula `THEN` e `ELSE`:
  ```sql
  -- FORMA CORRETA E BLINDADA:
  CASE
      WHEN F.ACORDO_SUM_PESO > 0
      THEN ROUND(F.VLR_TOTAL_ACORDO * (B.PROD_PESO / F.ACORDO_SUM_PESO), 2) - NVL(B.VLRUTILPROD, 0)
      ELSE F.VLR_TOTAL_ACORDO - NVL(B.VLRUTILPROD, 0)
  END
  ```

---

### ❌ Erro 2: `ORA-00936: missing expression` por Macros Não Cadastradas (`#LTx`)
- **Causa Raiz:** O código SQL contém `#LT1` (Lojas) ou `#LT2` (Status), mas na tela **Consulta Criação - Comandos da Consulta** do usuário essas variáveis não foram cadastradas em `Var - F7`.
  O Consinco substitui `#LT1` por texto vazio `""`, gerando:
  ```sql
  WHERE A.NROEMPRESA IN () AND A.STATUS NOT IN () -- Falha fatal ORA-00936!
  ```
- **✅ Solução Obrigatória:** Alinhar sempre o SQL com as variáveis cadastradas no formulário. Se as macros de loja/status não forem cadastradas na tela, fixar os valores seguros no código (`A.NROEMPRESA IN (1,2,3,4,5,6,7,8,11,12,13,14,15,16,17,18,50,900)` e `A.STATUS NOT IN (2)`).

---

### ❌ Erro 3: `ORA-01790: expression must have same datatype as corresponding expression`
- **Causa Raiz:** Desalinhamento na ordem, na quantidade ou nos tipos de dados das colunas entre o `SELECT` de dados e o `SELECT` de `TOTAL GERAL ->` no `UNION ALL`.
- **✅ Solução Obrigatória:**
  - Manter exatamente as mesmas colunas na mesma ordem posicional em ambos os lados do `UNION ALL`.
  - Usar sempre `TO_CHAR(...)` nas colunas formatadas e manter os aliases 1-para-1 rigorosamente idênticos.

---

### ❌ Erro 4: Falha no Bind Delphi com `CONNECT BY` em CTEs Materializadas
- **Causa Raiz:** Usar `CONNECT BY REGEXP_SUBSTR(:LT3, '[^,]+', 1, LEVEL)` dentro de CTE com `/*+ MATERIALIZE */` causa erro no driver Delphi ao associar parâmetros com vírgulas.
- **✅ Solução Obrigatória:** Utilizar sempre busca nativa por delimitadores:
  ```sql
  AND (
      NVL(TRIM(:LT3), '0') IN ('0', 'TODOS', '')
      OR INSTR(',' || UPPER(REPLACE(:LT3, ' ', '')) || ',', ',' || UPPER(TRIM(COLUNA_USUARIO)) || ',') > 0
  )
  ```

---

## 2. Arquitetura de Granularidade por Parcela vs Totais Globais

Quando o usuário solicita um relatório de movimentação financeira no período (`:DT1` a `:DT2`):

1. **Separação de CTEs:**
   - **`CTE_TITULOS_GLOBAL`**: Lê todos os títulos do acordo e calcula de forma analítica o número real da parcela (`DENSE_RANK() OVER (...)`) e o total de parcelas (`COUNT(*) OVER (...)`).
   - **`CTE_ACORDO_RESUMO_GLOBAL`**: Agrupa por `(NROEMPRESA, NROACORDO)` para calcular os totais reais do acordo:
     - `VALOR_ACORDO` (R$ 3.000,00)
     - `VLR_JA_QUITADO` (R$ 2.500,00 - acumulado total de todas as parcelas pagas)
     - `TOTAL_PARCELAS` (6)
     - `PARCELAS_PAGAS` (5)
     - `PARCELAS_PENDENTES` (1)
   - **`CTE_VALORES_BRUTOS`**: Faz join com `CTE_TITULOS_GLOBAL` filtrando apenas as parcelas com movimentação no período (`TEVE_MOV_QUITACAO_PERIODO = 1`).

2. **Exibição nas Linhas:**
   - Cada linha representa uma **baixa de parcela realizada no período**.
   - `VALOR_ULTIMO_PAGAMENTO`: exibe o valor da quitação daquela parcela específica (`R$ 500,00`).
   - `USUARIO_DATA_HORA_ALTERACAO`: exibe `OPERADOR - DATA HORA (Parc. X/Y)`.
   - `VALOR_ACORDO`, `VLR_FIN_VENCIDO` e `VLR_JA_QUITADO`: exibem os totais acumulados reais do acordo (R$ 3.000,00 e R$ 2.500,00), **preenchidos apenas na parcela 1** (veja regra 3).

3. **Exibição Única de Valores Totais em Acordos Multiparcelados (`RN_ACORDO = 1`):**
   - **Problema:** Quando um acordo possui múltiplas parcelas (ex: 6 parcelas de R$ 500,00 em um acordo de R$ 3.000,00), as colunas de valor global do acordo (`VALOR_ACORDO`, `VLR_FIN_VENCIDO`, `VLR_JA_QUITADO`) repetiam o valor em todas as 6 linhas. Ao somar a coluna no Excel ou selecionar os dados no grid do Consinco, o valor era multiplicado (ex: R$ 3.000 virava R$ 18.000), não fechando com a linha de total geral do rodapé.
   - **Solução Homologada:** Na `CTE_CLASSIFICADA`, calcula-se o numerador analítico:
     ```sql
     ROW_NUMBER() OVER (
         PARTITION BY C.NROEMPRESA, C.NROACORDO
         ORDER BY NVL(C.NROPARCELA, 1), NVL(C.SEQTITULO, 0)
     ) AS RN_ACORDO
     ```
   - No SELECT final, preenche-se as colunas de totais apenas na primeira linha:
     ```sql
     CASE WHEN X.RN_ACORDO = 1 THEN 'R$ ' || TO_CHAR(NVL(X.VLRACORDO, 0), ...) ELSE NULL END AS VALOR_ACORDO,
     CASE WHEN X.RN_ACORDO = 1 THEN 'R$ ' || TO_CHAR(NVL(X.VLRFINVENCIDO, 0), ...) ELSE NULL END AS VLR_FIN_VENCIDO,
     CASE WHEN X.RN_ACORDO = 1 THEN 'R$ ' || TO_CHAR(NVL(X.VLR_JA_QUITADO, 0), ...) ELSE NULL END AS VLR_JA_QUITADO
     ```
   - As demais parcelas ficam como `NULL` (em branco). A soma manual fecha perfeitamente ao centavo com a linha de `TOTAL GERAL ->`.

---

## 3. Desduplicação de Operações em `FI_TITOPERACAO` (Operação 16 - Inclusão de Títulos)

### ❌ O Problema da Duplicação por Usuário
A tabela `FI_TITOPERACAO` do Totvs Consinco grava a **Operação 16 (`Incl Títulos`)** com o valor nominal do título no momento da criação do contas a pagar/receber. Posteriormente, liquidações e baixas geram novas operações na mesma tabela.

Inicialmente, para evitar a soma de `Inclusão + Baixa`, filtrava-se apenas usuárias da quitação (ex: `VERIDI`, `DEBCO`). Porém, essa abordagem falhou criticamente quando:
1. Um mesmo operador (ativo ou inativo) realizou a inclusão E a quitação do título.
2. Ao filtrar por esse usuário, ambas as operações passavam, somando a Inclusão (R$ 3.571,43) + a Quitação (R$ 3.571,43) = R$ 7.142,86 (duplicado).
3. Títulos quitados por outros operadores ficavam de fora.

### ✅ A Solução Definitiva em 2 CTEs

1. **`CTE_OPERACOES_RAW`**: Conta analiticamente quantas operações **diferentes de 16 e não canceladas** existem para cada título:
   ```sql
   CTE_OPERACOES_RAW AS (
       SELECT /*+ MATERIALIZE */
           O.SEQTITULO,
           O.SEQTITOPERACAO,
           O.CODOPERACAO,
           O.DTAOPERACAO,
           NVL(O.DTAHORAALTERACAO, O.DTAALTERACAO) AS DTAALTERACAO_EFETIVA,
           O.USUALTERACAO,
           NVL(O.VLROPERACAO, 0) AS VLROPERACAO,
           COUNT(
               CASE 
                   WHEN O.CODOPERACAO != 16 
                   THEN 1 
               END
           ) OVER (PARTITION BY O.SEQTITULO) AS QTD_OUTRAS_OPS
       FROM FI_TITOPERACAO O
       INNER JOIN CTE_TITULOS_ACORDO TA
           ON TA.SEQTITULO = O.SEQTITULO
       WHERE (O.OPCANCELADA IS NULL OR TRIM(O.OPCANCELADA) = 'N')
         AND TRIM(O.USUCANCELOU) IS NULL
   )
   ```

2. **`CTE_OPERACOES_TITULO`**: Filtra e agrega os valores com as seguintes regras de negócio:
   - **Se já existem outras operações (`QTD_OUTRAS_OPS > 0`)**: a Operação 16 é **completamente expurgada**. Sobram apenas as baixas/quentações.
   - **Se NÃO existem outras operações (`QTD_OUTRAS_OPS = 0`)**: a Operação 16 é **mantida** para trazer a auditoria de quem lançou (`MAGE`, `ROLIVA`) e quando foi lançado.
   - **Regra de Ouro do Pagamento Registrado:** a Operação 16 NUNCA é um pagamento! Portanto, o `SUM` só soma quando `CODOPERACAO != 16`. Um título em aberto que só tem lançamento exibe `R$ 0,00` em `VALOR_PAG_REGISTRADO`, nunca o valor nominal do título!

   ```sql
   CTE_OPERACOES_TITULO AS (
       SELECT /*+ MATERIALIZE */
           R.SEQTITULO,
           MAX(R.DTAOPERACAO) AS MAX_DTAOPERACAO,
           MAX(R.DTAALTERACAO_EFETIVA) AS MAX_DTAHORAALTERACAO,
           MAX(R.USUALTERACAO) KEEP (
               DENSE_RANK LAST 
               ORDER BY R.DTAALTERACAO_EFETIVA NULLS FIRST, R.SEQTITOPERACAO
           ) AS USUALTERACAO,
           SUM(
               CASE 
                   WHEN R.CODOPERACAO != 16 
                   THEN R.VLROPERACAO 
                   ELSE 0 
               END
           ) AS VLROPERACAO
       FROM CTE_OPERACOES_RAW R
       WHERE (R.QTD_OUTRAS_OPS = 0 OR R.CODOPERACAO != 16)
       GROUP BY
           R.SEQTITULO
   )
   ```

---

## 4. Checklist de Validação Pré-Entrega SQL Consinco

Antes de entregar qualquer query SQL para o ERP Totvs Consinco:
- [x] O código começa com `SELECT * FROM (` para bypass do validador.
- [x] Todas as CTEs possuem o hint `/*+ MATERIALIZE */`.
- [x] **ZERO comentários** (`--` ou `/* */`) no código final.
- [x] Não existem expressões aritméticas fora de blocos `CASE` (ex: `(CASE) - X`).
- [x] As variáveis `:DT1, :DT2, :LS1, :LS2, :LS3, :LT3, :NR1, #LT1, #LT2` estão alinhadas com o cadastro da tela.
- [x] Todas as colunas do `UNION ALL` estão alinhadas 1-para-1 em quantidade, ordem e tipo.
- [x] Todos os parênteses estão balanceados.
- [x] Colunas globais de acordo preenchidas exclusivamente na primeira parcela (`RN_ACORDO = 1`) para fechar soma de Excel.
- [x] Operação 16 de `FI_TITOPERACAO` expurgada quando houver baixas, e com valor financeiro zerado para pagamentos registrados em títulos abertos.
