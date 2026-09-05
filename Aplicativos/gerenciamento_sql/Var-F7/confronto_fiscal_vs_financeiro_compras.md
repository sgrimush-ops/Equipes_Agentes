# Var-F7 - Confronto Fiscal vs Financeiro de Compras (MLF_NOTAFISCAL x FI_TITULO)

## Query Vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/confronto_fiscal_vs_financeiro_compras.sql`

## Objetivo
Realizar a **auditoria e conciliação completa** entre as **Notas Fiscais de Entrada de Compra (`MLF_NOTAFISCAL`)** e os **Títulos Gerados no Contas a Pagar / Pagos (`FI_TITULO`)**, confrontando linha a linha o **Valor dos Produtos**, o **Valor Total da NF (com ICMS-ST, IPI, Frete e Despesas)** contra o **Valor Nominal dos Títulos Gerados**, além de demonstrar o Valor Pago, Saldo em Aberto, Diferença e Status da Conciliação.

---

## Estrutura das Colunas de Valores

1. **`VALOR_PRODUTOS_NF`**: Soma líquida do valor dos produtos (`MLF_NFITEM.VLRITEM`).
2. **`VALOR_TOTAL_NF`**: Valor total oficial da nota fiscal (DANFE) incluindo ICMS ST, IPI, Despesas Acessórias e Descontos (`MLF_NOTAFISCAL.VLRTOTFORNEC` ou itens calculados).
3. **`VALOR_FINANCEIRO_TITULOS`**: Valor nominal total das duplicatas/boletos gerados no Contas a Pagar (`FI_TITULO.VLRNOMINAL`).
4. **`VALOR_PAGO`**: Valor efetivamente quitado ao fornecedor/banco (`FI_TITULO.VLRPAGO`).
5. **`SALDO_ABERTO`**: Saldo que ainda resta pagar da nota (`VLRNOMINAL - VLRPAGO`).
6. **`DIFERENCA_TOTAL_NF_FIN`**: `VALOR_TOTAL_NF - VALOR_FINANCEIRO_TITULOS`.
7. **`STATUS_CONCILIACAO`**: Identifica se a NF está `CONCILIADO 100%`, com `DIVERGENCIA` ou `APENAS NO FISCAL`.

---

## Variáveis para Cadastrar em Var - F7

| Variável | Tipo | Tipo de Retorno | Descrição | Valor Padrão | Instrução ao Usuário |
|---|---|---|---|---|---|
| **`#LT1`** | Macro | - | CGOs de Compra/Entrada | `1,2,3,4,6,7,8,28,100,101,290` | Informe os CGOs separados por vírgula (ex: `1, 28, 100`) |
| **`DT1`** | Data | - | Data Inicial Entrada | - | Informe a data inicial de entrada das notas / período |
| **`DT2`** | Data | - | Data Final Entrada | - | Informe a data final de entrada das notas / período |
| **`NR1`** | Numérico | - | Número da NF | `0` | Informe o número da NF ou deixe `0` para todas |
| **`LT2`** | Literal | Literal | Código Fornecedor | `0` | Informe o código do fornecedor ou deixe `0` para todos |
| **`LT3`** | Literal | Literal | Lojas de Entrada | `1,2,3,4,5,6,7,8,11,12,13,14,15,16,17,18,50` | Digite os códigos das lojas separados por vírgula ou `TODOS` |
| **`LS1`** | Lista | Literal | Seleção de Rede | ` TODAS AS REDES` | Selecione a Rede (`GE_REDE`) desejada ou mantenha ` TODAS AS REDES` |

---

## SQL da Lista LS1 (Rede)
Cole o script SQL abaixo no cadastro da variável `LS1` dentro de **Var - F7** (limite de 145 caracteres):

```sql
SELECT ' TODAS AS REDES' FROM DUAL UNION ALL SELECT DESCRICAO FROM GE_REDE
```
