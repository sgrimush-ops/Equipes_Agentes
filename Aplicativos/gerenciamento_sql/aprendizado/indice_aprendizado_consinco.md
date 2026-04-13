# Indice Mestre de Aprendizado Consinco

## Objetivo
Este indice organiza os arquivos uteis da pasta `aprendizado` por assunto, para consulta rapida por agentes e manutentores.

## Comece Por Aqui
- `guia_util_consinco.md`: visao geral do que deve ser mantido e do que e estrutural no projeto.
- `catalogo_tabelas_uteis_consinco.md`: catalogo consolidado das tabelas, categorias e regras-base do ambiente.
- `roteiro_investigacao_consinco.md`: caminho rapido por tipo de problema (margem, custo, estoque, venda, categoria, fornecedor e performance).

## Regras Operacionais de SQL
- `regras_imutaveis_sql.md`: regras que nao devem ser quebradas em queries do Consinco.
- `aprendizado_erro_sql.md`: licoes de validacao de dicionario, tipos e joins.
- `aprendizado_filtros_categorias_embalagem.md`: filtros seguros de categoria, divisao e embalagem.

## Arquitetura do Consinco e do BI
- `arquitetura_monitor_consico_totvs.md`: fluxo real das telas Consinco e uso de `SEQCONSULTA`.
- `aprendizado_curva_abc_lucratividade.md`: como o Consinco calcula ABC, lucratividade e margem com funcoes nativas e tabelas BI.

## Modelos de Consulta e Calculo
- `referencia_abc_vendas_consico.sql`: exemplo de query ABC de vendas.
- `modelo_calculos_custos_consinco.sql`: referencia de campos de custo, estoque e metricas relacionadas.
- `modelo_calculos_vendas_varejo_consinco.sql`: referencia das metricas de `MBI_TABCVAREJO`.
- `modelo_calculos_cliente_distrib_consinco.sql`: referencia das metricas de `MBI_TABCDISTRIB`.

## Regras Especificas do Projeto
- `regras_consolidadas_abc_vendas_subgrupo.md`: regras finais da query `abc_vendas_subgrupo` e da variante de 40 dias.

## Ordem Recomendada de Consulta
1. Ler `guia_util_consinco.md` para contexto geral.
2. Ler `catalogo_tabelas_uteis_consinco.md` para identificar tabelas e regras do ambiente.
3. Ler `roteiro_investigacao_consinco.md` para escolher o fluxo por tipo de problema.
4. Ler `regras_imutaveis_sql.md` antes de editar qualquer SQL.
5. Ler o arquivo especifico do tema: arquitetura, custo, varejo, distribuicao ou regra do relatorio alvo.

## Convencao de Uso
- Antes de criar ou alterar query, validar primeiro se a tabela/coluna ja esta documentada.
- Para relatorios Consinco, preferir bases `MBI_` e `MBIX_` quando o calculo nativo ja existir.
- Para manutencao da ABC por subgrupo, usar primeiro `regras_consolidadas_abc_vendas_subgrupo.md`.
