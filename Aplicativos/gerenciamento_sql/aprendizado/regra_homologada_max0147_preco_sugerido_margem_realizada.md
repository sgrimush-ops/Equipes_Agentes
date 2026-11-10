# Regra homologada - Simulador MAX0147 (Preco Sugerido e Margem Realizada)

## Status
- Homologado com evidencia de tela do simulador para produto 860 na empresa 15.
- Este documento passa a ser referencia obrigatoria para consultas que precisem reproduzir o simulador de precificacao MAX0147.

## Objetivo
- Reproduzir no SQL os campos:
  - MARGEM_OBJETIVA
  - PRECO_SUGERIDO
  - MARGEM_REALIZADA
- Evitar formulas simplificadas que divergem da tela do simulador.

## Regras de Calculo (obrigatorias)
1. Empresa base deve ser parametrizada por :NR1 (nunca hardcode fixo da empresa).
2. MARGEM_OBJETIVA deve vir de FC5MARGEMPRECOCADDESPOPER com contexto de empresa/segmento/embalagem.
3. CUSTO_LIQUIDO deve ser calculado com a composicao da MRL_PRODUTOEMPRESA:
   - CMULTVLRNF + CMULTIPI - CMULTCREDICMS + CMULTICMSST + CMULTDESPNF + CMULTDESPFORANF - CMULTDCTOFORANF - CMULTCREDPIS - CMULTCREDCOFINS - CMULTVLRVERBA
4. Carga fiscal de venda deve vir de Pkg_Carregaimposto.fc_BuscaTributacao no contexto da empresa/segmento/divisao:
   - PERALIQUOTAICMS
   - PERALIQUOTAPIS
   - PERALIQUOTACOFINS
5. PRECO_SUGERIDO deve usar custo liquido e margem com carga fiscal:
   - PRECO_SUGERIDO = CUSTO_LIQUIDO / (1 - (MARGEM_OBJETIVA + ICMS + PIS + COFINS)/100)
6. MARGEM_REALIZADA deve ser liquida (igual simulador), com denominador no PRECO_VENDA:
   - MARGEM_REALIZADA = ((PRECO_VENDA * (1 - (ICMS + PIS + COFINS)/100)) - CUSTO_LIQUIDO) / PRECO_VENDA * 100
7. PRECO_VENDA deve considerar promocional quando houver:
   - NVL(NULLIF(PRECOVALIDPROMOC, 0), PRECOVALIDNORMAL)
8. Embalagem do preco de venda deve seguir PADRAOEMBVENDA por familia/segmento (nao fixar QTDEMBALAGEM = 1 para todos os itens).

## Caso de Validacao Homologado
- Produto: 860
- Empresa: 15
- Simulador MAX0147 exibiu:
  - Custo liquido: 12,203597
  - Margem objetivo cadastro: 18,0000
  - Preco sugerido: 21,889860 (21,89)
  - Preco praticado: 17,900000
  - Margem praticada liquida: 5,5735
  - Carga fiscal total usada na simulacao: 26,2500 (ICMS 17,0000 + PIS 1,6500 + COFINS 7,6000)

## Resultado esperado no SQL
- Para o produto 860 / empresa 15:
  - PRECO_SUGERIDO = 21,89
  - MARGEM_REALIZADA = 5,57

## Anti-padroes proibidos
- Calcular PRECO_SUGERIDO apenas com custo/(1-margem) sem carga fiscal.
- Calcular MARGEM_REALIZADA como (PRECO_VENDA - CUSTO_BRUTO)/PRECO_VENDA.
- Fixar empresa 15 no SQL quando o contexto exige consulta parametrica.
- Iniciar SQL da Consulta Criacao com WITH (pode ser rejeitado pela tela).

## Arquivo de referencia implementado
- Aplicativos/gerenciamento_sql/querys/levantamento_custos_precos.sql
