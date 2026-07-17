# Aprendizado e Regras Imutáveis - SQL ABC de Vendas

Este documento registra as descobertas técnicas que garantiram a performance e a exatidão da query ABC de Vendas no Consinco. **Estas regras NÃO devem ser alteradas.**

## 1. Regras de Sintaxe (Performance e Estabilidade)
- **Proibição de Comentários**: NUNCA usar `--` ou `/* */` dentro dos arquivos `.sql`. O parser do Consinco remove as quebras de linha e os comentários "matam" o restante da query.
- **Formatação de Valores Financeiros**: Quando a saída precisar exibir valor monetário formatado em reais, usar como padrão `'R$ ' || TO_CHAR(ROUND(NVL(M.PRECONORMAL, 0), 2), 'FM999G999D00') AS PRECO`, preservando prefixo, arredondamento em 2 casas e centavos fixos.
- **NOT EXISTS para Exclusão**: Para remover departamentos como 'ALMOXARIFADO' ou 'INATIVAR', usar sempre `NOT EXISTS` cruzando `MAP_FAMDIVCATEG` e `MAP_CATEGORIA` Nível 1. É a única forma de garantir exclusão total sem duplicar linhas.
- **Prevenção de Duplicação por Data e Fonte de Vendas**: Ao cruzar tabelas de histórico (`MRL_CUSTODIA`) com tabelas de saldo fixo (`MRL_PRODUTOEMPRESA`), SEMPRE agrupar a tabela de histórico em uma subquery primeiro. Caso contrário, o saldo de estoque será multiplicado pelo número de dias do período. ATENÇÃO: NUNCA usar `MRL_PRODVENDADIA` para totalizar vendas da empresa/rede (ela subestima quantidades); a fonte oficial é `MRL_CUSTODIA` por `DTAENTRADASAIDA`.
- **Case Insensitivity e Acentos**: Sempre usar `UPPER()` nas comparações de texto e `LIKE 'SERVIC%'` para o departamento de Serviços, evitando falhas por acentuação.
- **Performance de Filtros Massivos (Evitar OR EXISTS)**: O banco Oracle 11g perde performance crítica ao rodar `OR EXISTS` dentro de CTEs (como `WITH FILTRADOS AS`) que filtram tabelas transacionais gigantes (`MRL_CUSTODIA`, `NOTAFISCAL`). Para manter consultas rápidas, deve-se usar uma arquitetura baseada em conjuntos: separar as lógicas usando `UNION` (ex: `SELECT vendas UNION SELECT compras`) ao invés de buscar a tabela de cadastro com `OR EXISTS(vendas) OR EXISTS(compras)`.
- **Bypass do Parser e Proibição de Fallback sem CTE**: A ferramenta de validação do Totvs SGI/Consinco exige que a primeira palavra do script seja `SELECT` (erro *"A instrução SQL informada, não é uma consulta"*). É ESTRITAMENTE PROIBIDO criar versões alternativas sem CTE (ex: scripts `_fallback`) para contornar o validador. A solução única e obrigatória é "envelopar" toda a consulta CTE com um `SELECT * FROM ( WITH ... SELECT ... )`. Além disso, ao usar variáveis de lista dentro de funções de texto como `SUBSTR` e `INSTR`, utilize sempre variáveis bind com dois-pontos (ex: `:LS1`) em vez de macros com hash (`#LS1`) para evitar o erro `ORA-00907` por substituição literal sem aspas no Oracle. Para detalhes arquiteturais, ler `aprendizado_otimizacao_ctes_materialize.md`.
## 2. Estrutura de Rede (Consolidada)
- **Agrupamento**: A query deve sempre usar `GROUP BY A.SEQPRODUTO, A.DESCCOMPLETA` (ou incluir as quebras de hierarquia no GROUP BY).
- **Soma de Lojas**: Indicadores como Venda, Estoque Mínimo e Máximo devem ser agregados via `SUM()` para refletir o total da rede (14 lojas selecionadas).
- **Estoque Físico Total**: Para bater o valor real da coluna "Loja" da consulta de produtos, NÃO filtrar por `STATUSCOMPRA = 'A'`, pois itens inativos com saldo físico devem ser contabilizados.

## 3. Query Base Validada (Núcleo V2)
A estrutura de `FROM` e `WHERE` da Versão 2 está validada como rápida e correta. Novas colunas devem ser adicionadas mantendo este bloco intacto.
