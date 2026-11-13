# Configuração Var - F7: Levantamento e Ranking de Troco Solidário por Operadora

## 1. Objetivo
- **Query (`levantamento_troco_solidario.sql`):** Rankear as Operadoras de Caixa que mais arrecadaram doações de **Troco Solidário** no PDV (`CONSINCOMONITOR.TB_DOCTOTROCOSOLIDARIO` + `TB_DOCTO` + `TB_DOCTOPAGTO`, expurgando estornos em `TB_DOCTOESTORNO`), exibindo Loja, Operadora (ID, Login e Nome), Instituição de Caridade Beneficiada (`GE_PESSOA`), Quantidade de Doações, Valor Total Arrecadado, Doação Média, Maior Doação e linha de fechamento `TOTAL GERAL ->`.

---

## 2. Variáveis para Cadastrar em `Var - F7`

| Variável | Tipo | Descrição / Título na Tela | Valor Padrão Sugerido | Instrução ao Usuário |
| :--- | :--- | :--- | :--- | :--- |
| **`DT1`** | Data | `Data Inicial` | Primeiro dia do mês | Informe a data inicial da campanha/período. |
| **`DT2`** | Data | `Data Final` | Data de hoje | Informe a data final da campanha/período. |
| **`LT1`** | Literal | `Lojas (0=Todas ou 1,8,14)` | `0` | Digite `0` (ou deixe em branco) para todas as lojas ou códigos separados por vírgula (ex: `2, 7, 11, 12, 13, 18`). |

