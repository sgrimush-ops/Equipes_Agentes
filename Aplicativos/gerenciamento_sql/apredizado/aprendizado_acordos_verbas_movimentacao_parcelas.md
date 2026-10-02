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
   - `VALOR_ACORDO` e `VLR_JA_QUITADO`: exibem os totais acumulados reais do acordo (R$ 3.000,00 e R$ 2.500,00).

3. **Linha de TOTAL GERAL:**
   - `VALOR_ACORDO`: R$ 3.000,00
   - `VLR_JA_QUITADO`: R$ 2.500,00
   - `VALOR_ULTIMO_PAGAMENTO`: soma das parcelas movimentadas no período (R$ 2.500,00 se forem 5 parcelas de R$ 500).

---

## 3. Checklist de Validação Pré-Entrega SQL Consinco

Antes de entregar qualquer query SQL para o ERP Totvs Consinco:
- [x] O código começa com `SELECT * FROM (` para bypass do validador.
- [x] Todas as CTEs possuem o hint `/*+ MATERIALIZE */`.
- [x] **ZERO comentários** (`--` ou `/* */`) no código.
- [x] Não existem expressões aritméticas fora de blocos `CASE` (ex: `(CASE) - X`).
- [x] As variáveis `:DT1, :DT2, :LS1, :LS2, :LS3, :LT3, :NR1, #LT1, #LT2` estão alinhadas com o cadastro da tela.
- [x] Todas as colunas do `UNION ALL` estão alinhadas 1-para-1 em quantidade, ordem e tipo.
- [x] Todos os parênteses estão balanceados.
