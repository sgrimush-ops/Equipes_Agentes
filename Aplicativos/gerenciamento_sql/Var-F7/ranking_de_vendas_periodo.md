# Var-F7 - ranking_de_vendas_periodo

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/ranking_de_vendas_periodo.sql`

## Objetivo
Vasculhar as vendas financeiras no período retroativo em dias informado na lista (`Periodo Consulta`, variável `LS2`) e apresentar o ranking decrescente por valor vendido com a classificação ABC automática baseada no percentual acumulado sobre o total da venda:
- **A**: produtos que representam os primeiros **50%** da soma total vendida.
- **B**: produtos que representam os próximos **40%** da soma total vendida (de 50% até 90% do acumulado).
- **C**: restante dos itens vendidos (últimos **10%** do acumulado).

A consulta expurga automaticamente o departamento **ALMOXARIFADO** e traz exclusivamente itens que tiveram venda no período (`VALOR_VENDIDO > 0`), independente do seu status de compra (`'A'` ou `'I'`).

## Colunas Retornadas
- `COMPRADOR`: nome do comprador/gestor associado à família do produto.
- `DEPARTAMENTO`: descrição do departamento (Nível 1).
- `SUBGRUPO`: descrição do subgrupo (Nível 4/3/5).
- `SEQCODIGO`: código interno do produto (`SEQPRODUTO`).
- `DESCRICAO`: descrição completa do produto.
- `STATUS_COMPRA`: status global de compra na rede (`A` = Ativo em pelo menos uma loja do escopo, `I` = Inativo).
- `VALOR_VENDIDO`: valor financeiro bruto vendido no período.
- `PERC_PARTICIPACAO`: % de participação do item no total geral vendido.
- `PERC_ACUMULADO`: % acumulado contínuo na curva decrescente de vendas.
- `RANK`: classificação `A` (até 50%), `B` (de 50% a 90%) ou `C` (> 90%).

## Variáveis para Cadastrar em Var - F7

### NR1
- **Tipo**: Numérico
- **Descrição**: Código Fornecedor
- **Valor padrão**: `0`
- **Instrução**: informe o código do fornecedor para teste (ex: `6560`) ou mantenha `0` para trazer todos os fornecedores.

### LS1
- **Tipo**: Lista
- **Descrição**: Departamento
- **Valor padrão**: `0 - TODOS`
- **Instrução**: selecione o departamento desejado ou mantenha `0 - TODOS`.

### LS2
- **Tipo**: Lista
- **Descrição**: Periodo Consulta
- **Valor padrão**: `30`
- **Instrução**: selecione a quantidade de dias retroativos da pesquisa (ex: 30, 60, 90 dias).

## SQL da Lista LS1 (Departamento)
```sql
SELECT '0 - TODOS' AS DEPARTAMENTO FROM DUAL
UNION ALL
SELECT TO_CHAR(SEQCATEGORIA) || ' - ' || CATEGORIA AS DEPARTAMENTO
FROM MAP_CATEGORIA
WHERE NIVELHIERARQUIA = 1
  AND TIPCATEGORIA = 'M'
  AND STATUSCATEGOR = 'A'
ORDER BY 1
```

## SQL da Lista LS2 (Periodo Consulta em Dias)
```sql
SELECT '30' AS PERIODO FROM DUAL
UNION ALL
SELECT '60' FROM DUAL
UNION ALL
SELECT '90' FROM DUAL
UNION ALL
SELECT '180' FROM DUAL
```
