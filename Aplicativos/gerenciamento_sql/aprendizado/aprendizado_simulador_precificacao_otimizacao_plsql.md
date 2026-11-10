# Aprendizado: Simulador de Precificação Condensado por Produto & Otimização de Performance com Funções PL/SQL

Este documento consolida as melhores práticas, regras de negócio e técnicas de otimização extrema de performance validadas ao criar a consulta do **Simulador de Custo, Preço de Venda e Margem por Produto (`simulador_custo_preco_venda.sql`)** compatível com a regra homologada **MAX0147** do TOTVS Consinco.

---

## 1. Condensação por Produto e Cálculo de Custo Médio (Expurgo do Custo Zero)

Em consultas que visam simular preços e margens em nível de produto (1 linha por item) a partir da tabela de estoques e custos filiais (`MRL_PRODUTOEMPRESA`):

### A. Custo Líquido Médio (Desconsiderando Custo Zero)
* Lojas que nunca compraram o item ou possuem cadastro inativo sem saldo/custo têm `CMULTVLRNF = 0` / `CUSTO_LIQUIDO = 0`.
* Incluir custos zerados na média aritmética puxa o custo unitário artificialmente para baixo.
* **Regra Homologada:** A média deve ser calculada estritamente sobre lojas que possuem custo ativo:
  ```sql
  ROUND(
      NVL(AVG(CASE WHEN (SOMA_CUSTO_LIQUIDO) > 0 THEN (SOMA_CUSTO_LIQUIDO) END), 0),
      4
  ) AS CUSTO_LIQUIDO
  ```

### B. Visualização do Custo Bruto (`CUSTO_NF_BRUTO`) vs. Notas de Transferência
* **O Problema das Transferências:** Quando mercadorias entram via Centros de Distribuição (ex: **Empresa 15 e CD 16**) e são transferidas para as lojas de varejo, a nota fiscal de entrada na loja adota o valor já transferido/líquido sem destacar os créditos de ICMS/PIS/COFINS originais da indústria.
* **A Solução (`MAX` no Custo Bruto e Créditos):** Para que a visualização do **Custo Bruto NF (`CUSTO_NF_BRUTO`)** refleta a nota fiscal original emitida pela indústria sem distorcer o custo líquido da rede, utiliza-se a função agregação `MAX(...)` nos componentes de entrada bruto e créditos:
  ```sql
  ROUND(NVL(MAX(PE.CMULTVLRNF), 0), 4)       AS CUSTO_NF_BRUTO,
  ROUND(NVL(MAX(PE.CMULTCREDICMS), 0), 4)    AS CREDITO_ICMS,
  ROUND(NVL(MAX(PE.CMULTCREDPIS), 0), 4)     AS CREDITO_PIS,
  ROUND(NVL(MAX(PE.CMULTCREDCOFINS), 0), 4)  AS CREDITO_COFINS
  ```
  Isso resgata perfeitamente a "fotografia" da compra original no CD centralizador sem alterar o cálculo de margem (que se baseia no `CUSTO_LIQUIDO`).

---

## 2. Otimização Extrema de Performance: Agregações SQL Antes de Chamadas PL/SQL

### A. Causa de Travamento / Timeout na Consulta Criação
Quando uma query chama funções PL/SQL ou Table Functions do Oracle por linha em subconsultas não agregadas, o custo computacional explode:
* Exemplo anti-padrão: Chamar `Pkg_Carregaimposto.fc_BuscaTributacao(...)` e `FC5MARGEMPRECOCADDESPOPER(...)` dentro do scan de `MRL_PRODUTOEMPRESA`.
* Para 25.000 produtos ativos × 16 empresas = **400.000 linhas**, executar 3 chamadas de tributação por linha gera **1.200.000 chamadas PL/SQL**, causando travamento ou timeout no validador do Consinco SGI.

### B. Padrão Arquitetural de Alta Performance (Agregação Prévia)
Para garantir execução em poucos segundos:
1. **Etapa 1 (`CTE_CUSTOS_PRODUTO` e `CTE_PRECOS_PRODUTO`):** Agrupar primeiro os dados de custo e preço por produto (`GROUP BY SEQPRODUTO`) usando puramente operações de conjunto SQL (Hash Group By nativo).
2. **Etapa 2 (`CTE_BASE_CONDENSADA`):** Fazer o `JOIN` do produto condensado (apenas 1 linha por `SEQPRODUTO`) e somente nesta etapa invocar as funções PL/SQL:
   ```sql
   SELECT /*+ MATERIALIZE */
       A.SEQPRODUTO,
       C.CUSTO_LIQUIDO,
       ROUND(NVL(FC5MARGEMPRECOCADDESPOPER(A.SEQPRODUTO, 1, 1, 1, 'M'), 0), 2) AS MARGEM_OBJETIVA,
       NVL((
           SELECT MAX(NVL(T.PERALIQUOTAICMS, 0))
           FROM TABLE(Pkg_Carregaimposto.fc_BuscaTributacao(
               A.SEQPRODUTO, 'S', NVL(FD.NROTRIBUTACAO, 1), 'SN',
               0, 'RS', 'RS', 1, 3, TRUNC(SYSDATE)
           )) T
       ), 0) AS ALIQ_ICMS_VENDA
   FROM MAP_PRODUTO A
   INNER JOIN CTE_CUSTOS_PRODUTO C ON C.SEQPRODUTO = A.SEQPRODUTO
   ```
* **Resultado:** O número de execuções PL/SQL cai de **1.200.000** para **~25.000** (apenas 1 vez por item), reduzindo o tempo de processamento de minutos para menos de 3 segundos.

---

## 3. Matemática do Simulador no Excel (Alíquota % vs Valor R$)

Para garantir que o simulador no Excel recalcule corretamente ao alterar o **Preço Praticado** ou a **Margem Desejada**:
* **Sempre usar a Alíquota Percentual (`ALIQ_IMPOSTOS_TOTAL` em %) na fórmula**, nunca o valor fixo em R$ (`VALOR_IMPOSTOS_VENDA`).
* Como os impostos de venda (ICMS, PIS, COFINS) incidem percentualmente sobre o preço de prateleira, usar a alíquota % garante que o imposto em R$ se reajuste proporcionalmente ao novo preço simulado:
  $$\text{Margem Realizada Simulada (\%)} = \frac{\text{Novo\_Preco} \times \left(1 - \frac{\text{Alíquota\%}}{100}\right) - \text{Custo\_Líquido}}{\text{Novo\_Preco}}$$
