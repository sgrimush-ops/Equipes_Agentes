# Var-F7 — levantamento_margens_objetivas_departamento_venda

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/levantamento_margens_objetivas_departamento_venda.sql`

## Objetivo
Levantar a margem objetiva por produto/hierarquia de departamento, incorporando o volume financeiro total vendido (`VENDA_VALOR`) e o valor vendido em promoção (`VENDA_PROMOCAO`) no período dos últimos 60 dias (de ontem para 60 dias atrás).

> [!NOTE]
> Esta consulta foi parametrizada para **uso único e direto** (sem variáveis de tela), retornando exclusivamente os produtos **Ativos para Compra** (`STATUSCOMPRA = 'A'`) em todas as lojas comerciais da rede.

---

## Variáveis em Var-F7
* **Nenhuma variável necessária:** Todos os filtros (`VAR`) foram removidos para execução direta e rápida.

---

## Passo a Passo Operacional
1. Abra a Consulta Criação no Totvs Consinco e cole o SQL do arquivo vinculado (`levantamento_margens_objetivas_departamento_venda.sql`).
2. Execute diretamente no botão **Run / Executar** (não é necessário configurar Var-F7).

---

## Regras e Especificações da Query
- **Apenas Produtos Ativos:** Filtro rigoroso por `PE.STATUSCOMPRA = 'A'`.
- **Período Fixo:** Vendas apuradas de `TRUNC(SYSDATE) - 60` até `< TRUNC(SYSDATE)` (últimos 60 dias fechados até ontem).
- **Fonte Homologada de Faturamento:** Utiliza as notas fiscais de saída (`MLFV_BASENFE` + `MFLV_BASEDFITEM` com operação comercial `800`).
- **Ofertas e Promoções:** Cruzamento via `MRLV_BASEPRODPROMOC` isolado em CTE com hint de memória RAM (`/*+ MATERIALIZE */`).
- **Bypass de Validador Consinco:** Envelopada em `SELECT * FROM ( WITH ... )` para evitar erro de CTE sem o comando `SELECT` inicial.
- **Zero Comentários:** Nenhum comentário (`--` ou `/* */`) foi mantido no SQL para prevenir falhas de quebra de linha no parser do ERP.
