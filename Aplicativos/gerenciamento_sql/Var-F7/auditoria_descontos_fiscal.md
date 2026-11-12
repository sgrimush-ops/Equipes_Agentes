# Configuração Var - F7: Auditoria de Descontos (Detalhada e Resumo por Tipo de Operação)

## 1. Objetivo
- **Query 1 (`auditoria_descontos_fiscal_detalhada.sql`):** Auditar item a item todos os **descontos manuais autorizados por senha de Fiscal de Caixa** em vendas válidas no PDV (`CONSINCOMONITOR.TB_LOGSEGURANCAPDV` + `CONSINCO.MFL_CUPOMFISCAL`), exibindo Operador, Fiscal Autorizador, Auto-Liberação, valores em `R$` e `% de Desconto`.
- **Query 2 (`auditoria_descontos_fiscal_ranking.sql`):** Consolidar os valores de desconto de **todos os tipos de operação** (Manuais de Fiscal + Automáticos de Sistema: `21 - Incentivo no item`, `92 - Scanntech`, `09 - Produto Composto`, `06 - Desconto a partir de`, `02 - Desconto no item`, `01 - Desconto no cupom`, etc.), listando quantidade de lojas (`QTD_LOJAS`) e quais lojas (`Q_LOJAS`) aplicaram cada desconto.

---

## 2. Variáveis para Cadastrar em `Var - F7` (Mesmas 3 variáveis para as duas Queries — Sem `LS`)

| Variável | Tipo | Descrição / Título na Tela | Valor Padrão Sugerido | Instrução ao Usuário |
| :--- | :--- | :--- | :--- | :--- |
| **`DT1`** | Data | `Data Inicial` | Primeiro dia do mês | Informe a data inicial do período. |
| **`DT2`** | Data | `Data Final` | Data de hoje | Informe a data final do período. |
| **`LT1`** | Literal | `Lojas (0=Todas ou 1,8,14)` | `0` | Digite `0` para todas as lojas ou códigos separados por vírgula (ex: `1, 3, 8, 14`). |
