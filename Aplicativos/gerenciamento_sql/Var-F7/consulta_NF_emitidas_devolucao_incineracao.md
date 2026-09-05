# Var-F7 - Consulta 1: Analítico de NFs Emitidas (Devolução / Incineração / Troca)

## Query Vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/consulta_NF_emitidas_devolucao_incineracao.sql`

## Objetivo
Auditar cada Nota Fiscal de Saída emitida pelos CDs/Empresas parametrizadas (`:LT3`) nos CGOs de devolução, troca e incineração (`#LT1`), trazendo o detalhe de produto por produto, comprador, rede, quantidade e valor, com subtotais por comprador e total geral.

---

## Variáveis para Cadastrar em Var - F7

| Variável | Tipo | Tipo de Retorno | Descrição | Valor Padrão | Instrução ao Usuário |
|---|---|---|---|---|---|
| **`#LT1`** | Macro / Literal | - | CGOs das Notas | `802,860,831,821` | Informe os CGOs separados por vírgula (ex: `802, 860`) |
| **`DT1`** | Data | - | Data Inicial Emissão | - | Informe a data inicial de emissão das notas / período |
| **`DT2`** | Data | - | Data Final Emissão | - | Informe a data final de emissão das notas / período |
| **`NR1`** | Numérico | - | Número da NF | `0` | Informe o número da NF ou deixe `0` para todas |
| **`LT2`** | Literal | Literal | Código Fornecedor | `0` | Informe o código do fornecedor ou deixe `0` para todos |
| **`LT3`** | Literal | Literal | CDs Emissores da NF | `15,16,50` | Digite os códigos dos CDs emissores da NF separados por vírgula ou `TODOS` |
| **`LS1`** | Lista | Literal | Seleção de Rede | ` TODAS AS REDES` | Selecione a Rede (`GE_REDE`) desejada ou mantenha ` TODAS AS REDES` |

---

## SQL da Lista LS1 (Rede)
Cole o script SQL abaixo no cadastro da variável `LS1` dentro de **Var - F7** (limite de 145 caracteres):

```sql
SELECT ' TODAS AS REDES' FROM DUAL UNION ALL SELECT DESCRICAO FROM GE_REDE
```
