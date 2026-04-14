---
description: "Use when the user mentions FILTRO, Var-F7, LT1, LS1, NR1, DT1, lista de selecao, Consulta Criacao, ou pedir query Consinco com campos antes do Run. Obriga entregar SQL principal mais configuracao completa de variaveis e listas."
---

# Consulta Criacao com Filtros

- Quando o usuario mencionar FILTRO em contexto SQL Consinco, assuma que ele quer a query preparada para a tela Consulta Criacao.
- Nao entregue apenas a query. Entregue obrigatoriamente:
  1. SQL principal.
  2. Variaveis para cadastrar em Var - F7.
  3. SQL das listas `LSx`, quando houver.
  4. Passo a passo curto de cadastro.
- Ao criar ou ajustar qualquer query SQL do workspace em `Aplicativos/gerenciamento_sql/querys/`, registre tambem um arquivo de procedimento em `Aplicativos/gerenciamento_sql/Var-F7/`, preferencialmente com o mesmo nome-base da query SQL.
- Explique explicitamente que os filtros visuais antes do Run nao nascem apenas do SQL; eles dependem do cadastro das variaveis em Var - F7.
- Use prefixos coerentes do Consinco: `LTx`, `DTx`, `LSx`, `NRx`.
- Para filtros textuais simples, prefira o caminho mais estavel a concatenacoes complexas.
- Se houver `LSx`, informe sempre o tipo de retorno esperado e a SQL exata da lista.
- Se `#LSx` for usado em comparacao textual direta no `WHERE`, a SQL da lista deve devolver o valor ja entre aspas simples.
- Em lista textual, escapar aspas internas antes de encapsular o valor final.
- Para filtros opcionais, prefira sentinelas explicitas como `0` e `TODOS` em vez de depender de campo vazio.
- Se uma lista `LSx` mostrar comportamento instavel, priorize `LTx` digitado pelo usuario.
- Para consultas com volume alto, aplique filtros seletivos cedo para evitar travamento com `TODOS`.
- Em queries finais para Consinco, evite comentarios dentro do bloco SQL.
- Reaproveite o aprendizado em `Aplicativos/gerenciamento_sql/aprendizado/aprendizado_filtros_consulta_criacao.md`.