# Indice Mestre de Aprendizado Consinco

## Objetivo
Este indice organiza os arquivos uteis da pasta `aprendizado` por assunto, para consulta rapida por agentes e manutentores.

## Comece Por Aqui
- `guia_util_consinco.md`: visao geral do que deve ser mantido e do que e estrutural no projeto.
- `catalogo_tabelas_uteis_consinco.md`: catalogo consolidado das tabelas, categorias e regras-base do ambiente.
- `roteiro_investigacao_consinco.md`: caminho rapido por tipo de problema (margem, custo, estoque, venda, categoria, fornecedor e performance).

## Regras Operacionais de SQL
- `regras_imutaveis_sql.md`: regras que nao devem ser quebradas em queries do Consinco.
- `aprendizado_otimizacao_ctes_materialize.md`: guia obrigatorio de performance sobre CTEs com hint /*+ MATERIALIZE */, funcoes analiticas e bypass de validacao (SELECT Fantasma), proibindo fallbacks sem CTE.
- `aprendizado_erro_sql.md`: licoes de validacao de dicionario, tipos e joins.
- `aprendizado_filtros_categorias_embalagem.md`: filtros seguros de categoria, divisao e embalagem.
- `aprendizado_filtros_formatacao_faturamento.md`: boas práticas de filtro único (LS sem NR redundante), ordenação correta com formatação monetária (TO_CHAR) e filtros de lista de texto (LT via INSTR).
- `aprendizado_ordenacao_texto_vs_numero_e_filtros_hierarquia.md`: guia sobre a armadilha de ordenação alfabética em aliases formatados com `TO_CHAR`, ordenação por agregação numérica, extração/exibição de Nível 5 (`SUBGRUPO`) e listas `LSx` com `0 - TODOS` (e validador `ORDER BY 1`).
- `aprendizado_compras_transferencias_segregadas.md`: separacao e segregacao tecnica de compras de fornecedores (recebimento) e transferencias internas (CD e expedicao).
- `aprendizado_pendencias_transferencia_recebimento_fantasma.md`: logica de performance, joins (SEQNF vs SEQNOTAFISCAL) e tratamento de notas de transferencia pendentes ("Ped Receber") antigas.
- `aprendizado_pedidos_suprimento_transferencia_status.md`: arquitetura de pedidos de transferencia (MSU_PEDIDOSUPRIM vs MSU_PSITEMRECEBER), soberania do status do item sobre a capa, tratamento de data de expedicao nula e contorno do corte de caracteres em listas LS1 no Delphi (Constantes da Lista e CAST SYS.ODCIVARCHAR2LIST).
- `aprendizado_auditoria_compras_devolucoes_trocas.md`: tratamento de trocas/devolucoes como deducoes, capturas unificadas (Entrada vs Saida) e filtros globais em rankings.
- `aprendizado_estoque_em_transito.md`: desmistificacao da coluna QTDTRANSITO enganosa e a rota correta via MSU_PSITEMRECEBER para encontrar estoques rodando no caminhao.
- `aprendizado_filtros_consulta_criacao.md`: guia sobre criacao de filtros antes do Run no Totvs Consinco (Var-F7, LT1, LS1, NR1, DT1).
- `aprendizado_abc_vendas_formato_comprador_filtros.md`: regras praticas de filtros e corte por quantidade (`NR1`) em subqueries previas antes de joins pesados.
- `aprendizado_auditoria_precos_promocoes.md`: como espelhar a tela nativa de histórico via `MAD_PRODLOGPRECO`, a mecânica do registro automático zero para fim de promoção e o efeito cascata de defasagem de preço base.

## Arquitetura do Consinco e do BI
- `arquitetura_monitor_consico_totvs.md`: fluxo real das telas Consinco e uso de `SEQCONSULTA`.
- `aprendizado_curva_abc_lucratividade.md`: como o Consinco calcula ABC, lucratividade e margem com funcoes nativas e tabelas BI.
- `aprendizado_configuracoes_comerciais_fornecedor.md`: estrutura das regras de negocio, prazos de pagamento, forma de pagamento e restricoes sintaticas (Inline View vs CTE) em consultas do modulo de fornecedores.
- `aprendizado_vendas_mrl_custodia.md`: descoberta critica provando que `MRL_CUSTODIA` (e nao `MRL_PRODVENDADIA`) e a fonte oficial consolidada de vendas no Consinco.

## Modelos de Consulta e Calculo
- `referencia_abc_vendas_consico.sql`: exemplo de query ABC de vendas.
- `modelo_calculos_custos_consinco.sql`: referencia de campos de custo, estoque e metricas relacionadas.
- `modelo_calculos_vendas_varejo_consinco.sql`: referencia das metricas de `MBI_TABCVAREJO`.
- `modelo_calculos_cliente_distrib_consinco.sql`: referencia das metricas de `MBI_TABCDISTRIB`.
- `aprendizado_grade_pedido_lojas_pivoteamento.md`: arquitetura para consultas de grade horizontal por loja (Venda, Estoque e Linha de Compra) com pivoteamento em CTEs independentes.
- `aprendizado_relatorios_grade_pedidos_pivoteados.md`: padrao ouro para relatorios em grade pivoteada com linha 0 de cabecalho (`UNION ALL`) para exibir o numero dos pedidos sem misturar strings no grid numérico.
- `aprendizado_simulador_precificacao_otimizacao_plsql.md`: guia de arquitetura para simuladores de precificação/margem condensados por produto, regras para expurgar transferências em custos brutos (`MAX`), e otimização extrema de performance chamando funções PL/SQL após a agregação SQL.
- `regra_homologada_max0147_preco_sugerido_margem_realizada.md`: regra homologada com formulas obrigatorias e caso validado para o simulador de precificacao MAX0147 (Margem Objetiva, Preco Sugerido e Margem Realizada).
- `aprendizado_precos_dia_e_comprador.md`: regras e query canônica para consulta de preços vigentes (normal, promocional e praticado via NVL/NULLIF em MRL_PRODEMPSEG) com filtro LS1 por Comprador.

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
