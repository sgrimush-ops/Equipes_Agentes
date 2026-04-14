---
name: aprendizado-query-sql
description: 'Ensine e construa queries SQL de forma guiada, com foco em Oracle e Consinco, leitura de tabelas, joins, filtros, depuracao de erro e evolucao passo a passo. Use quando o usuario quiser aprender query SQL, entender uma consulta, corrigir erros ORA-*, montar consultas com explicacao didatica ou estudar os materiais internos de SQL deste workspace.'
argument-hint: 'Tema, regra de negocio, query atual ou objetivo da consulta'
---

# Aprendizado de Query em SQL

## Objetivo
Use esta skill para transformar pedidos sobre SQL em uma experiencia de aprendizado pratico. O foco nao e apenas entregar uma query pronta, mas explicar o raciocinio, mostrar como investigar tabelas e colunas e deixar claro como evoluir a consulta com seguranca.

Esta skill foi desenhada para uso neste workspace e prioriza o contexto Oracle e ERP Consinco. Preserve as restricoes tecnicas ja conhecidas do ambiente local e reutilize os materiais internos antes de propor uma solucao nova.

## Quando Usar
- O usuario quer aprender SQL do zero ou consolidar fundamentos.
- O usuario trouxe uma query e quer entender o que ela faz.
- O usuario quer montar uma consulta nova com explicacao passo a passo.
- O usuario recebeu erro Oracle, como ORA-00904, ORA-00942 ou ORA-00923, e quer corrigir aprendendo.
- O usuario quer descobrir em quais tabelas ou colunas uma informacao existe antes de escrever a query final.
- O usuario quer comparar abordagens, por exemplo subquery, CTE, agregacao antes do join ou filtros parametrizados.
- O usuario mencionar a palavra FILTRO ao pedir uma query Consinco, especialmente quando quiser campos preenchidos antes do Run na Consulta Criacao.

## Fluxo de Trabalho
1. Identifique o objetivo real do usuario.
   Classifique o pedido em uma destas trilhas: conceito, explicacao de query existente, construcao de query nova, depuracao de erro, otimizacao ou investigacao de tabela/coluna.
2. Descubra o nivel de detalhe necessario.
   Se o usuario for iniciante, explique cada bloco. Se ele ja estiver avancado, foque na modelagem, nas regras de negocio e nos riscos tecnicos.
3. Consulte primeiro os materiais locais do workspace.
   Leia o mapa em [trilha-aprendizado](./references/trilha-aprendizado.md) para decidir quais arquivos do projeto inspecionar antes de responder.
4. Monte a resposta na ordem correta.
   Comece pelo objetivo da consulta, depois detalhe a granularidade, as tabelas-base, os joins, os filtros, as agregacoes e por fim a query completa ou a correcao proposta.
5. Ensine junto com a entrega.
   Sempre que fizer sentido, explique por que cada join existe, por que uma agregacao foi feita antes do join e qual erro seria causado por uma abordagem incorreta.
6. Feche com o proximo passo de aprendizado.
   Sugira uma pequena variacao da query, um filtro extra, um campo novo ou uma verificacao para o usuario praticar em seguida.

## Decisoes e Ramificacoes

### Se o pedido for conceitual
- Explique os conceitos com um exemplo pequeno.
- Depois conecte o conceito ao contexto real do workspace.
- So entregue query longa se o usuario pedir ou se ela for necessaria para fixar a explicacao.

### Se o pedido for explicar uma query existente
- Reescreva a logica em linguagem simples.
- Quebre a consulta em blocos: SELECT, FROM, JOIN, WHERE, GROUP BY e ORDER BY.
- Aponte onde estao a granularidade, os filtros criticos e os riscos de duplicidade.

### Se o pedido for construir uma query nova
- Confirme mentalmente o grao da analise: produto, loja, dia, fornecedor, familia ou outro.
- Escolha a tabela mais confiavel como base.
- So depois acrescente joins e agregacoes.

### Se o pedido mencionar FILTRO
- Considere que o usuario quer uma query preparada para a tela Consulta Criacao do Consinco.
- Entregue sempre o pacote completo: SQL principal, variaveis a cadastrar em `Var - F7` e SQL da lista para cada `LSx`.
- Explique explicitamente que os campos antes do Run nao nascem so da query; eles dependem do cadastro manual das variaveis na tela.
- Se um filtro puder ser feito por texto direto com mais estabilidade, prefira isso a concatenacoes complexas ou `SELECT ... INTO` desnecessario.

### Se o pedido for depurar erro
- Identifique primeiro se o problema parece ser coluna inexistente, tabela inexistente, alias malformado, variavel invalida ou explosao de linhas por join incorreto.
- Se faltar certeza sobre a estrutura do banco, prefira orientar uma consulta ao dicionario antes de inventar nomes.

### Se o pedido for otimizar ou validar resultado
- Verifique se ha agregacao previa antes de juntar historico com saldo fixo.
- Verifique se filtros de negocio e de escopo foram aplicados cedo o suficiente.
- Verifique se a query preserva a granularidade esperada.

## Criterios de Qualidade
- A resposta precisa ensinar, nao apenas entregar codigo.
- A query final precisa estar coerente com a regra de negocio descrita.
- Nao chute tabelas ou colunas quando houver incerteza; investigue primeiro.
- Em Consinco/Oracle, privilegie tabelas, colunas e restricoes confirmadas nos materiais locais.
- Se a query for para uso final em telas do Consinco, evite comentarios dentro do bloco SQL e respeite as regras locais de alias e parametrizacao.
- Sempre deixe claro o que foi assumido e o que foi validado.
- Se houver FILTRO, nao entregue so o SQL. Inclua obrigatoriamente o cadastro de `Var - F7` e, quando aplicavel, a SQL do gerador da lista.

## Formato Preferido de Resposta
Use esta estrutura sempre que ela couber no pedido:
1. Objetivo da consulta
2. Estrategia da modelagem
3. Query ou ajuste proposto
4. Explicacao didatica dos blocos
5. Proximo exercicio ou validacao sugerida

## Exemplos de Ativacao
- Aprenda comigo a montar uma query de vendas por loja no Consinco.
- Explique esta consulta Oracle passo a passo e mostre onde posso errar.
- Estou com ORA-00904 nesta query. Corrija e me ensine a investigar.
- Quero descobrir em qual tabela fica o campo de embalagem antes de montar a consulta.

## Recursos Locais
- Consulte [trilha-aprendizado](./references/trilha-aprendizado.md) para escolher os arquivos do projeto mais uteis.
- Quando o pedido for especificamente sobre Consinco, reaproveite os aprendizados e regras locais antes de criar uma query do zero.
- Quando o pedido envolver filtros antes da execucao, leia o aprendizado em `Aplicativos/gerenciamento_sql/aprendizado/aprendizado_filtros_consulta_criacao.md` e replique o padrao descoberto.
