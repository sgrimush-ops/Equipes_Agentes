# Var-F7 - ranking_de_vendas_periodo

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/ranking_de_vendas_periodo.sql`

## Objetivo
Apurar de forma ultrarrápida via **`MRL_CUSTODIA`** (`VLRTOTALVDA` por `DTAENTRADASAIDA`) as vendas financeiras no período retroativo em dias (`:NR2`) e apresentar o **Ranking ABC separado por Departamento** (`PARTITION BY DEPARTAMENTO`):
- **A**: produtos que representam os primeiros **50%** do faturamento daquele departamento.
- **B**: produtos que representam os próximos **40%** do faturamento daquele departamento (de 50% até 90% do acumulado do departamento).
- **C**: restante dos itens vendidos no departamento (últimos **10%** do acumulado).

### Otimização de Performance (Pirâmide de Afunilamento)
1. **Expurgo no Topo da Pirâmide (`CTE_CATEGORIAS` e `CTE_PRODUTOS_VALIDOS`)**: Antes de ler a tabela de vendas, a query filtra apenas itens de revenda (`FINALIDADEFAMILIA = 'R'`) e exclui automaticamente os departamentos de **Não Venda** (`ALMOXARIFADO`, `SERVICOS`, `INATIVAR`, `A CLASSIFICAR`, `IMOBILIZADO`, `USO E CONSUMO`) e o departamento de **Perecíveis** (`PERECIVEIS`).
2. **Fonte Analítica Oficial (`MRL_CUSTODIA`)**: Substitui a varredura pesada de notas fiscais item a item (`MLFV_BASENFE` + `MFLV_BASEDFITEM`) pela tabela consolidada `MRL_CUSTODIA`, reduzindo drasticamente o tempo de execução.

## Colunas Retornadas
- `COMPRADOR`: nome do comprador/gestor associado à família do produto.
- `DEPARTAMENTO`: descrição do departamento (Nível 1).
- `SUBGRUPO`: descrição do subgrupo (Nível 4/3/5/2).
- `SEQCODIGO`: código interno do produto (`SEQPRODUTO`).
- `DESCRICAO`: descrição completa do produto.
- `STATUS_COMPRA`: status global de compra na rede (`A` = Ativo em pelo menos uma loja do escopo, `I` = Inativo).
- `VALOR_VENDIDO`: valor financeiro vendido no período (`MRL_CUSTODIA.VLRTOTALVDA`).
- `PERC_PARTICIPACAO`: % de participação do item dentro do seu respectivo departamento.
- `PERC_ACUMULADO`: % acumulado contínuo dentro do seu respectivo departamento.
- `RANK`: classificação `A` (até 50%), `B` (de 50% a 90%) ou `C` (> 90%) dentro do departamento.

## Variáveis para Cadastrar em Var - F7

### NR1
- **Tipo**: Numérico
- **Descrição**: Código Fornecedor
- **Valor padrão**: `0`
- **Instrução**: informe o código do fornecedor (ex: `6560`) ou mantenha `0` para considerar todos os fornecedores.

### NR2
- **Tipo**: Numérico
- **Descrição**: Período Consulta (Dias)
- **Valor padrão**: `30`
- **Instrução**: informe a quantidade de dias retroativos para apuração das vendas (ex: `30`, `60`, `90`). Se deixado `0`, assume `30` dias automaticamente.

### LS1
- **Tipo**: Lista
- **Descrição**: Departamento
- **Valor padrão**: `0 - TODOS`
- **Instrução**: selecione o departamento desejado ou mantenha `0 - TODOS` para rankear todos os departamentos comerciais separadamente.

## SQL da Lista LS1 (Departamento - 141 caracteres, respeitando limite <= 145)
```sql
SELECT '0 - TODOS' FROM DUAL UNION ALL SELECT SEQCATEGORIA||' - '||CATEGORIA FROM MAP_CATEGORIA WHERE NIVELHIERARQUIA=1 AND TIPCATEGORIA='M'
```
