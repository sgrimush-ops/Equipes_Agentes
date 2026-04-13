# Roteiro de Investigacao Consinco

## Objetivo
Este roteiro orienta a investigacao por tipo de problema no ambiente Totvs Consinco deste projeto.

## Se o problema for Margem
- Ler `regras_consolidadas_abc_vendas_subgrupo.md` se a demanda envolver a ABC por subgrupo.
- Validar se a necessidade e de investigacao pontual ou uso em producao.
- Para investigacao pontual, considerar funcoes nativas como `FC5MARGEMPRECO` apenas em item unico.
- Para producao, preferir margens leves ou bases `MBI_` ja prontas.
- Consultar `aprendizado_curva_abc_lucratividade.md` para entender o papel das funcoes e da `MBI_TABCDISTRIB`.

## Se o problema for Custo
- Comecar por `modelo_calculos_custos_consinco.sql`.
- Validar no dicionario local se a coluna de custo existe na `MRL_PRODUTOEMPRESA`.
- Para a ABC por subgrupo, usar como referencia `CMULTCUSLIQUIDOEMP` na loja 3.
- So recorrer a `MRL_CUSTODIA` quando o problema depender do custo por data.

## Se o problema for Estoque
- Considerar `MRL_PRODUTOEMPRESA` como fonte principal.
- Usar a formula de estoque disponivel com abatimento de `QTDRESERVADAVDA`, `QTDRESERVADARECEB` e `QTDRESERVADAFIXA`.
- Se for estoque logistico de CD, revisar tambem `MRL_PRODEMPRESAWM` e `MAD_PRODESPENDERECO`.
- Se houver divergencia com historico de venda, confirmar se as vendas foram agregadas antes do join.

## Se o problema for Venda ou Periodo
- Comecar por `MRL_PRODVENDADIA` quando a necessidade for quantidade vendida por intervalo.
- Nunca usar `VLRVDA` nesta base local; a coluna valida e `QTDVDA`.
- Para periodos dinamicos, usar `TRUNC(SYSDATE)` e agregar por `SEQPRODUTO` e `NROEMPRESA`.
- Se precisar bater com a curva ABC nativa do Consinco, avaliar `MBIX_TABCDISTRIB`.

## Se o problema for Categoria, Departamento ou Embalagem
- Ler `aprendizado_filtros_categorias_embalagem.md`.
- Confirmar nivel de hierarquia correto em `MAP_CATEGORIA` antes de filtrar.
- Para departamento, usar `NIVELHIERARQUIA = 1` quando a regra pedir o nivel master.
- Para embalagem, preferir `MAP_FAMEMBALAGEM` ou a configuracao ja validada em `MAP_FAMDIVISAO` conforme o caso.

## Se o problema for Fornecedor ou Comprador
- Comprador: validar relacao `MAP_FAMDIVISAO.SEQCOMPRADOR -> MAX_COMPRADOR`.
- Fornecedor principal: validar `MAP_FAMFORNEC` com `PRINCIPAL = 'S'` e `GE_PESSOA`.
- Se precisar codigo e descricao, trazer `SEQFORNECEDOR` e `NOMERAZAO` juntos.

## Se o problema for Tabela ou Coluna Inexistente
- Nao chutar nomes.
- Ler primeiro `catalogo_tabelas_uteis_consinco.md` e `dicionario_consinco.json`.
- Se ainda houver duvida, montar varredura em `ALL_TAB_COLUMNS` por palavra-chave.
- Registrar o resultado consolidado se a descoberta for recorrente.

## Se o problema for Relatorio Nativo do Consinco
- Ler `arquitetura_monitor_consico_totvs.md`.
- Verificar se a tela usa `MBI_` ou `MBIX_` com `SEQCONSULTA`.
- Priorizar o reaproveitamento da base materializada em vez de reconstruir toda a logica transacional.

## Se o problema for Performance
- Evitar funcoes linha a linha em massa.
- Evitar joins diretos entre saldo fixo e historico diario sem agregacao previa.
- Reutilizar tabelas BI materializadas quando existirem.
- Validar se o filtro de lojas e o filtro de revenda estao aplicados corretamente.

## Ordem Padrao de Investigacao
1. Ler `guia_util_consinco.md`.
2. Ler `catalogo_tabelas_uteis_consinco.md`.
3. Ler `regras_imutaveis_sql.md`.
4. Escolher o bloco deste roteiro conforme o tipo de problema.
5. So depois montar a query ou script de investigacao.

## Regra Final
Se a duvida for estrutural e nao estiver documentada, investigar antes de implementar. Se a descoberta for reutilizavel, consolidar no aprendizado do projeto.