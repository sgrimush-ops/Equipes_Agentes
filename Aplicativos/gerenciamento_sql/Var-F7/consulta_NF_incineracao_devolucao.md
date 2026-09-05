# Var-F7 - Consulta NF Incineração e Devolução com Compras de Fornecedor

## Query Vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/consulta_NF_incineracao_devolucao.sql`

## Objetivo
Consultar notas fiscais de devolução e incineração emitidas pelos CDs/Empresas parametrizadas no `:LT3`, confrontando para cada produto o total de **compras reais de fornecedores** nas lojas/empresas discriminadas no `:LT4` dentro do período pesquisado (`:DT1` a `:DT2`).

---

## Variáveis para Cadastrar em Var - F7

| Variável | Tipo | Tipo de Retorno | Descrição | Valor Padrão | Instrução ao Usuário |
|---|---|---|---|---|---|
| **`#LT1`** | Macro / Literal | - | CGOs das Notas | `802, 860, 821, 831` | Informe os CGOs separados por vírgula (ex: `802, 860`) |
| **`DT1`** | Data | - | Data Inicial Emissão | - | Informe a data inicial de emissão das notas / período |
| **`DT2`** | Data | - | Data Final Emissão | - | Informe a data final de emissão das notas / período |
| **`NR1`** | Numérico | - | Número da NF | `0` | Informe o número da NF ou deixe `0` para todas |
| **`LT2`** | Literal | Literal | Código Fornecedor | `0` | Informe o código do fornecedor ou deixe `0` para todos |
| **`LT3`** | Literal | Literal | CDs Emissores da NF | `15, 16, 50` | Digite os códigos dos CDs emissores da NF separados por vírgula ou `TODOS` |
| **`LT4`** | Literal | Literal | Lojas Pesquisa Compra | `1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18, 50` | Digite os códigos das lojas para pesquisa de compra discriminados por vírgula ou `TODOS` |
| **`LS1`** | Lista | Literal | Seleção de Rede | ` TODAS AS REDES` | Selecione a Rede (`GE_REDE`) desejada ou mantenha ` TODAS AS REDES` |

---

## SQL da Lista LS1 (Rede)
Cole o script SQL abaixo no cadastro da variável `LS1` dentro de **Var - F7** (limite de 145 caracteres):

```sql
SELECT ' TODAS AS REDES' FROM DUAL UNION ALL SELECT DESCRICAO FROM GE_REDE
```

---

## Diferenciação dos Filtros de Empresa:
- **`LT3` (Emissão de NFs):** Filtra onde as notas fiscais de devolução/incineração foram geradas (padrão: `15, 16, 50` ou deixe vazio / `TODOS` para todas as empresas).
- **`LT4` (Entrada de Compras):** Filtra em quais lojas/CDs serão totalizadas as compras reais de fornecedor para revenda no período (exclui transferências CGO 50, padrão com todas as lojas discriminadas: `1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18, 50` ou vazio / `TODOS`).
- **Linha de Total Geral:** Totaliza exclusivamente os valores financeiros (`VALOR_PRODUTO_NF` e `VALOR_COMPRAS_FORNECEDOR`), exibindo `--` nos campos de quantidade.
