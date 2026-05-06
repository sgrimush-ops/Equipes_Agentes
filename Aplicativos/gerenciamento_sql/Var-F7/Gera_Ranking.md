# Gera_Ranking — Procedimento Var-F7

## Objetivo
Ranking de produtos por valor de venda em um período, ordenado do maior para o menor, para conferência por produto e período. Descarta produtos com venda zero no período.

## Regra de Apuração
- A consulta usa `MLFV_BASENFE` + `MFLV_BASEDFITEM` + `MAP_PRODUTO`.
- Quantidade vendida: `SUM(I.QUANTIDADE)`.
- Valor de venda: `SUM(I.VLRITEM)`.
- Filtros fixos homologados: `TIPNOTAFISCAL = 'S'` e `CODGERALOPER = 800`.
- Restricao operacional desta consulta: nao usar bases `DWV`, porque elas sao limitadas nesse ambiente.

## Colunas Retornadas
| Coluna           | Descrição                          |
|------------------|------------------------------------|
| COD_PRODUTO      | Código interno do produto          |
| DESC_PRODUTO     | Descrição do produto               |
| QTD_VENDIDA      | Quantidade total vendida           |
| VLR_FAT_LIQUIDO  | Valor faturado líquido (VLRITEM)   |

---

## Variáveis — Var-F7

### DT1 — Data Inicial
| Campo       | Valor               |
|-------------|---------------------|
| Nome        | DT1                 |
| Tipo        | Data                |
| Descrição   | Data inicial do período |
| Valor Padrão| (data corrente ou início do mês) |

### DT2 — Data Final
| Campo       | Valor               |
|-------------|---------------------|
| Nome        | DT2                 |
| Tipo        | Data                |
| Descrição   | Data final do período |
| Valor Padrão| (data corrente)      |

### NR1 — Código do Produto (opcional)
| Campo       | Valor                                      |
|-------------|--------------------------------------------|
| Nome        | NR1                                        |
| Tipo        | Numérico                                   |
| Descrição   | Código interno do produto (0 = todos)      |
| Valor Padrão| 0                                          |

> Deixe `0` para retornar todos os produtos. Informe o `SEQPRODUTO` para filtrar um produto específico.

---

## Passo a Passo — Cadastro em Var-F7

1. Abra a Consulta Criação, localize ou crie a consulta `Gera_Ranking`.
2. Acesse **Var - F7** (botão ou tecla F7).
3. Cadastre a variável **DT1**:
   - Tipo: **Data**
   - Descrição: `Data inicial do período`
   - Informe um valor padrão se desejar.
4. Cadastre a variável **DT2**:
   - Tipo: **Data**
   - Descrição: `Data final do período`
   - Informe um valor padrão se desejar.
5. Cadastre a variável **NR1**:
   - Tipo: **Numérico**
   - Descrição: `Código interno do produto (0 = todos)`
   - Valor padrão: `0`
6. Salve as variáveis e feche o Var-F7.
7. Antes de executar (Run), preencha DT1 e DT2 com o intervalo desejado. Para conferir um produto específico, informe seu código em NR1; deixe `0` para ver o ranking completo.

---

## Observações
- O filtro `CODGERALOPER = 800` restringe apenas operações de venda; não inclui devoluções (820/850).
- A lista de empresas foi ampliada para `1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,20,21,22,23,50,900,901,902` para aproximar o escopo usado nas análises do monitor.
- O `HAVING SUM > 0` garante que produtos sem nenhuma venda no período não apareçam no resultado.
- Não há SQL de lista (sem LSx nesta consulta).
