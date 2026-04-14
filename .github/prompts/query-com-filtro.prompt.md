---
name: "Query Com Filtro"
description: "Crie uma query Consinco para Consulta Criacao com filtros antes do Run e entregue tambem o cadastro completo de Var-F7. Use para pedidos com a palavra FILTRO."
argument-hint: "Objetivo da query, colunas desejadas e filtros antes do Run"
agent: "agent"
---

Crie uma query Oracle para o Totvs Consinco preparada para a tela Consulta Criacao.

Se o pedido mencionar FILTRO, trate isso como obrigacao de entregar o pacote completo para filtros antes do Run.

Use o aprendizado consolidado em [aprendizado_filtros_consulta_criacao.md](../../Aplicativos/gerenciamento_sql/aprendizado/aprendizado_filtros_consulta_criacao.md).

Entregue sempre nestas secoes:

1. Objetivo da consulta.
2. SQL principal final, sem comentarios dentro do bloco SQL.
3. Variaveis para cadastrar em Var - F7:
   - nome da variavel
   - tipo
   - descricao
   - valor padrao, se houver
   - instrucao ao usuario
4. SQL das listas LSx, quando houver.
5. Passo a passo curto para cadastro na tela Var - F7.

Regras obrigatorias:
- Nao entregue apenas a query se houver FILTRO.
- Explique que o filtro visual nao nasce sozinho do SQL.
- Use prefixos SGI coerentes como LTx, DTx, LSx e NRx.
- Para filtros textuais simples, prefira o caminho mais estavel a concatenacoes desnecessarias.
- Em contexto Consinco, preserve as regras locais do workspace para estoque, revenda e categorias.