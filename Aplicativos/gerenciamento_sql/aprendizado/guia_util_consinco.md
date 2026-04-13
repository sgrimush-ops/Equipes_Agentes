# Guia Util do Consinco no Projeto

## Objetivo
Este arquivo concentra o que vale manter como referencia permanente sobre o ambiente Totvs Consinco deste repositorio.

## Fontes Estruturais que Devem Ser Mantidas
- catalogo_tabelas_uteis_consinco.md: consolidacao das categorias e do inventario util das tabelas do schema.
- regras_imutaveis_sql.md: regras de seguranca e desempenho para SQL no Consinco.
- arquitetura_monitor_consico_totvs.md: arquitetura real das consultas MBI e uso de SEQCONSULTA.
- referencia_abc_vendas_consico.sql: exemplo real de query ABC com margem e estoque.
- modelo_calculos_custos_consinco.sql: catalogo pratico de campos de custo e metricas de estoque.
- modelo_calculos_vendas_varejo_consinco.sql: referencia de metricas da MBI_TABCVAREJO.
- modelo_calculos_cliente_distrib_consinco.sql: referencia de metricas da MBI_TABCDISTRIB.
- regras_consolidadas_abc_vendas_subgrupo.md: regras finais da query ABC por subgrupo.
- aprendizado_erro_sql.md: licoes de validacao de dicionario e tipos.
- aprendizado_filtros_categorias_embalagem.md: regras praticas de categorias, divisao e embalagem.
- aprendizado_curva_abc_lucratividade.md: visao de lucratividade e funcoes nativas.
- As antigas listas brutas em txt de categorias e tabelas foram consolidadas no catalogo markdown.

## Verdades Operacionais do Ambiente
- Banco alvo: Oracle no ecossistema Totvs Consinco.
- Ambiente cliente: Consinco, sensivel a comentarios em SQL e a aliases problematicos.
- Dicionario local manda mais que conhecimento externo.
- Tabelas MBI e MBIX sao centrais para reproduzir relatorios do sistema.
- Custos e margens complexas do Consinco normalmente passam por tabelas MBI ou funcoes nativas.
- Para evitar explosao de estoque com historico de venda, agregue vendas antes do join.

## Regras Tecnicas Recorrentes
- Usar NVL, DECODE, TRUNC(SYSDATE) e sintaxe Oracle.
- Nao chutar colunas ou joins fora do dicionario local.
- Estoque principal sai de MRL_PRODUTOEMPRESA.
- Embalagem deve respeitar a estrutura validada do ambiente.
- Para relatorios ABC, validar primeiro se existe base pronta em MBI_TABCESTOQUE, MBI_TABCVAREJO ou MBI_TABCDISTRIB.

## Aprendizados Ja Consolidados
- A coluna VLRVDA nao existe em MRL_PRODVENDADIA neste ambiente.
- Para abc_vendas_subgrupo, custo confiavel veio de CMULTCUSLIQUIDOEMP na loja 3.
- Margens pesadas via funcoes FC5 servem para investigacao, nao para consulta final em massa.
- Na versao 40 dias da ABC por subgrupo, o periodo e dinamico, so entra item com venda e existe coluna final de pendente a expedir do CD.

## Artefatos Temporarios
Resultados pontuais de investigacao em txt podem ser descartados desde que as conclusoes estejam refletidas nas regras consolidadas ou na memoria do repositorio.
