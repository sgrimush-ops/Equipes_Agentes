# Aprendizado e Regras Imutáveis - SQL ABC de Vendas

Este documento registra as descobertas técnicas que garantiram a performance e a exatidão da query ABC de Vendas no Consinco. **Estas regras NÃO devem ser alteradas.**

## 1. Regras de Sintaxe (Performance e Estabilidade)
- **Proibição de Comentários**: NUNCA usar `--` ou `/* */` dentro dos arquivos `.sql`. O parser do SGI SGI remove as quebras de linha e os comentários "matam" o restante da query.
- **NOT EXISTS para Exclusão**: Para remover departamentos como 'ALMOXARIFADO' ou 'INATIVAR', usar sempre `NOT EXISTS` cruzando `MAP_FAMDIVCATEG` e `MAP_CATEGORIA` Nível 1. É a única forma de garantir exclusão total sem duplicar linhas.
- **Prevenção de Duplicação por Data**: Ao cruzar tabelas de histórico (como `MRL_PRODVENDADIA`) com tabelas de saldo fixo (`MRL_PRODUTOEMPRESA`), SEMPRE agrupar a tabela de histórico em uma subquery primeiro. Caso contrário, o saldo de estoque será multiplicado pelo número de dias do período.
- **Case Insensitivity e Acentos**: Sempre usar `UPPER()` nas comparações de texto e `LIKE 'SERVIC%'` para o departamento de Serviços, evitando falhas por acentuação.

## 2. Estrutura de Rede (Consolidada)
- **Agrupamento**: A query deve sempre usar `GROUP BY A.SEQPRODUTO, A.DESCCOMPLETA` (ou incluir as quebras de hierarquia no GROUP BY).
- **Soma de Lojas**: Indicadores como Venda, Estoque Mínimo e Máximo devem ser agregados via `SUM()` para refletir o total da rede (14 lojas selecionadas).
- **Estoque Físico Total**: Para bater o valor real da coluna "Loja" da consulta de produtos, NÃO filtrar por `STATUSCOMPRA = 'A'`, pois itens inativos com saldo físico devem ser contabilizados.

## 3. Query Base Validada (Núcleo V2)
A estrutura de `FROM` e `WHERE` da Versão 2 está validada como rápida e correta. Novas colunas devem ser adicionadas mantendo este bloco intacto.
