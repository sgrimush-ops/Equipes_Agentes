# Trilha Local de Aprendizado SQL

Use este mapa para decidir quais arquivos do workspace devem ser lidos antes de responder.

## Arquivos-base do workspace
- Aplicativos/gerenciamento_sql/aprendizado/indice_aprendizado_consinco.md
  Use como porta de entrada para localizar o assunto mais proximo do pedido.
- Aplicativos/gerenciamento_sql/aprendizado/catalogo_tabelas_uteis_consinco.md
  Use para descobrir tabelas e colunas mais confiaveis antes de montar joins.
- Aplicativos/gerenciamento_sql/aprendizado/regras_imutaveis_sql.md
  Use para validar restricoes tecnicas e evitar erros repetidos.
- Aplicativos/gerenciamento_sql/aprendizado/roteiro_investigacao_consinco.md
  Use quando o usuario ainda nao souber em qual tabela a informacao mora.
- Aplicativos/gerenciamento_sql/aprendizado/aprendizado_erro_sql.md
  Use quando houver erro Oracle ou comportamento inesperado.
- Aplicativos/gerenciamento_sql/aprendizado/aprendizado_filtros_consulta_criacao.md
  Use quando a query precisar abrir filtros antes do Run na Consulta Criacao do Consinco.

## Arquivos por tipo de problema
- Curva ABC e lucratividade:
  Aplicativos/gerenciamento_sql/aprendizado/aprendizado_curva_abc_lucratividade.md
  Aplicativos/gerenciamento_sql/aprendizado/referencia_abc_vendas_consico.sql
  Aplicativos/gerenciamento_sql/aprendizado/regras_consolidadas_abc_vendas_subgrupo.md
- Categorias, filtros e embalagem:
  Aplicativos/gerenciamento_sql/aprendizado/aprendizado_filtros_categorias_embalagem.md
- Modelos prontos de calculo:
  Aplicativos/gerenciamento_sql/aprendizado/modelo_calculos_cliente_distrib_consinco.sql
  Aplicativos/gerenciamento_sql/aprendizado/modelo_calculos_custos_consinco.sql
  Aplicativos/gerenciamento_sql/aprendizado/modelo_calculos_vendas_varejo_consinco.sql
- Contexto arquitetural:
  Aplicativos/gerenciamento_sql/aprendizado/arquitetura_monitor_consico_totvs.md

## Procedimento recomendado
1. Comece pelo indice ou pelo catalogo de tabelas.
2. Se houver erro, leia tambem o material de erros.
3. Se a duvida envolver uma regra de negocio recorrente, busque o arquivo tematico correspondente.
4. So depois escreva ou corrija a query final.
5. Feche a resposta explicando o raciocinio e propondo o proximo passo de estudo.

## Alertas
- Nao invente nomes de tabela ou coluna se o material local nao der suporte.
- Em consultas Consinco para uso final, evite comentarios dentro do SQL.
- Ao misturar historico de venda e saldo de estoque, agregue o historico antes do join quando isso for necessario para evitar multiplicacao indevida de linhas.
