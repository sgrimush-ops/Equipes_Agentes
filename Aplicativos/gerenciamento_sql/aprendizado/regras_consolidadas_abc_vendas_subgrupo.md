# Regras Consolidadas - ABC Vendas Subgrupo

## Escopo
Este documento consolida as regras finais e validas para manutencao da consulta abc_vendas_subgrupo.

## Fonte Oficial da Query
- Arquivo alvo: Aplicativos/gerenciamento_sql/querys/abc_vendas_subgrupo.sql
- Variante operacional: Aplicativos/gerenciamento_sql/querys/abc_vendas_subgrupo_40dias.sql

## Regras Funcionais Estaveis
- Loja de referencia para preco e custo: 3.
- Custo de referencia: MRL_PRODUTOEMPRESA.CMULTCUSLIQUIDOEMP (NROEMPRESA = 3).
- Quantidade vendida: SUM(QTDVDA) em MRL_PRODVENDADIA agregada por SEQPRODUTO e NROEMPRESA no periodo.
- PERC_ACM: manter arredondamento em 1 casa decimal.
- Ordenacao final: SUBGRUPO ascendente e PERC_ACM descendente.
- Coluna VALOR_VENDIDO: removida por decisao funcional; nao reintroduzir sem solicitacao explicita.

## Regras da Versao 40 Dias
- Periodo dinamico: DTAVDA BETWEEN TRUNC(SYSDATE) - 40 AND TRUNC(SYSDATE).
- Filtrar apenas itens com venda no periodo: HAVING SUM(NVL(VND.QTD_VENDIDA, 0)) > 0.
- Ordenacao da versao 40 dias: SUB.SUBGRUPO ascendente e QTD_VENDIDA descendente.
- Antes do nome do fornecedor principal, manter CODIGO_FORNECEDOR_PRINCIPAL.
- CODIGO_FORNECEDOR_PRINCIPAL vem de MAP_FAMFORNEC.SEQFORNECEDOR com F.PRINCIPAL = 'S'.
- No final da query, manter PENDENTE_EXPEDIR_CD vindo da agregacao de QTDPENDPEDEXPED nas empresas 15, 16 e 50.

## Regras de Margem (Consolidadas)
- MARGEM_ATUAL e MARGEM_OBJETIVA devem permanecer apos PRECO_VENDA.
- Nao usar funcoes FC5MARGEMPRECO e FC5MARGEMPRECOCADDESPOPER na consulta principal (trava/performance).
- MARGEM_ATUAL em producao: ((PRECO_VENDA - PRECO_CUSTO) / PRECO_VENDA) * 100 com protecao para PRECO_VENDA = 0.
- MARGEM_OBJETIVA em producao: priorizar margem de BI e aplicar fallback via MGMCADASTRO (FC5MARGEMPRECOCADDESPOPER) quando BI vier zerada.
- Arredondamento das margens: 2 casas decimais.

## Regras de Integridade
- Manter filtro de lojas: 1,2,3,4,5,6,7,8,11,12,13,14,17,18.
- Manter exclusao de departamentos: A CLASSIFICAR, ALMOXARIFADO, INATIVAR, SERVIC%.
- Manter padrao de evitar multiplicacao indevida de estoque com vendas: agregacao de vendas em subquery antes do join.

## Regras de Investigacao (Quando Necessario)
- Para validar estruturas de margem/custo sem chute, usar ALL_TAB_COLUMNS.
- Para validacao pontual de margem nativa, usar item unico (ex: 12278) e comparar com resultado de producao.
- Se houver regressao de performance, priorizar estrategia com tabela BI e remover chamadas funcionais linha a linha.

## Checklist Rapido Antes de Publicar Alteracao
- Colunas do relatorio permanecem na ordem validada pelo usuario.
- MARGEM_ATUAL e MARGEM_OBJETIVA continuam presentes e leves.
- Query executa sem ORA-00904 e sem duplicidade de ORDER BY.
- Nao houve reintroducao de VALOR_VENDIDO sem aprovacao.
