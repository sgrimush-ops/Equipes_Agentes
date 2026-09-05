# Var-F7 - Consulta 2: Analítico de Entradas (Compras de Fornecedor)

## Query Vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/consulta_entradas_compras_fornecedor.sql`

## Objetivo
Consultar e auditar todas as **Notas Fiscais de Entrada de Compras de Fornecedor** recebidas nas lojas/empresas parametrizadas (`:LT3`) no período (`:DT1` a `:DT2`), trazendo o detalhamento de NF, Série, CGO, Comprador, Rede, Fornecedor e Produto, com subtotais por comprador e total geral consolidado.

---

## Variáveis para Cadastrar em Var - F7

| Variável | Tipo | Tipo de Retorno | Descrição | Valor Padrão | Instrução ao Usuário |
|---|---|---|---|---|---|
| **`#LT1`** | Macro / Literal | - | CGOs de Compra/Entrada | `1,2,3,4,6,7,8,28,100,101,290` | Informe os CGOs de entrada separados por vírgula (ex: `1, 28, 100`) |
| **`DT1`** | Data | - | Data Inicial Entrada | - | Informe a data inicial de entrada das notas / período |
| **`DT2`** | Data | - | Data Final Entrada | - | Informe a data final de entrada das notas / período |
| **`NR1`** | Numérico | - | Número da NF | `0` | Informe o número da NF de compra ou deixe `0` para todas |
| **`LT2`** | Literal | Literal | Código Fornecedor | `0` | Informe o código do fornecedor ou deixe `0` para todos |
| **`LT3`** | Literal | Literal | Lojas de Entrada | `1,2,3,4,5,6,7,8,11,12,13,14,15,16,17,18,50` | Digite os códigos das lojas de entrada separados por vírgula ou `TODOS` |
| **`LS1`** | Lista | Literal | Seleção de Rede | ` TODAS AS REDES` | Selecione a Rede (`GE_REDE`) desejada ou mantenha ` TODAS AS REDES` |

---

## SQL da Lista LS1 (Rede)
Cole o script SQL abaixo no cadastro da variável `LS1` dentro de **Var - F7** (limite de 145 caracteres):

```sql
SELECT ' TODAS AS REDES' FROM DUAL UNION ALL SELECT DESCRICAO FROM GE_REDE
```
