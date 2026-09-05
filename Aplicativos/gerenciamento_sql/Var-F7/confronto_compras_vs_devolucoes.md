# Var-F7 - Consulta 2: Balanço Comercial (Compras vs Devoluções / Incinerações)

## Query Vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/confronto_compras_vs_devolucoes.sql`

## Objetivo
Confrontar gerencialmente o volume total de **compras reais de fornecedores** nas lojas parametrizadas (`:LT4`) contra o total de **devoluções, trocas e incinerações** emitidas pelos CDs (`:LT3`), agrupando por **Produto**, calculando o **% de Devolução sobre a Compra** com subtotais por comprador e total geral consolidado, **100% livre de duplicidades**.

---

## Variáveis para Cadastrar em Var - F7

| Variável | Tipo | Tipo de Retorno | Descrição | Valor Padrão | Instrução ao Usuário |
|---|---|---|---|---|---|
| **`#LT1`** | Macro / Literal | - | CGOs Devolução/Perda | `802,860,831,821` | Informe os CGOs de saída separados por vírgula (ex: `802, 860`) |
| **`DT1`** | Data | - | Data Inicial Período | - | Informe a data inicial de compras e devoluções |
| **`DT2`** | Data | - | Data Final Período | - | Informe a data final de compras e devoluções |
| **`LT2`** | Literal | Literal | Código Fornecedor | `0` | Informe o código do fornecedor ou deixe `0` para todos |
| **`LT3`** | Literal | Literal | CDs Emissores Devolução | `15,16,50` | Digite os códigos dos CDs de emissão separados por vírgula ou `TODOS` |
| **`LT4`** | Literal | Literal | Lojas Pesquisa Compra | `1,2,3,4,5,6,7,8,11,12,13,14,15,16,17,18,50` | Digite os códigos das lojas de entrada de compras separados por vírgula ou `TODOS` |
| **`LS1`** | Lista | Literal | Seleção de Rede | ` TODAS AS REDES` | Selecione a Rede (`GE_REDE`) desejada ou mantenha ` TODAS AS REDES` |

---

## SQL da Lista LS1 (Rede)
Cole o script SQL abaixo no cadastro da variável `LS1` dentro de **Var - F7** (limite de 145 caracteres):

```sql
SELECT ' TODAS AS REDES' FROM DUAL UNION ALL SELECT DESCRICAO FROM GE_REDE
```
