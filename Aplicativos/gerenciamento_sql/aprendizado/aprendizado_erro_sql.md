# Aprendizado: Prevenção de Erros SQL no ERP Consinco (ORA-01722 e ORA-00904)

Este documento registra uma lição aprendida durante o desenvolvimento de queries SQL para o ERP TOTVS Consinco neste ambiente.

## Contexto do Erro
Ao atualizar a query `consulta_emb_PBU.sql`, foram cometidos dois erros técnicos sucessivos:
1. **ORA-01722 (Invalid Number):** Tentativa de comparar a coluna `PADRAOEMBTRANSF` (que é numérica) com a string `'UN'`.
2. **ORA-00904 (Invalid Identifier):** Tentativa de utilizar a coluna `SEQFAMEMBALAGEM` como chave de join na tabela `MAP_FAMEMBALAGEM`, sendo que esta coluna não consta no schema local.

## Causa Raiz
O agente confiou em conhecimentos externos de outros schemas ERP, negligenciando a consulta ao dicionário de dados local disponibilizado no projeto.

## Lição Aprendida (Protocolo de Segurança)
Sempre que for criar ou modificar uma query SQL para o ERP Consinco neste repositório:
1. **Consultar o Dicionário:** Verifique obrigatoriamente o arquivo `Aplicativos/gerenciamento_sql/dicionario_consinco.json` para validar nomes de colunas e chaves de join.
2. **Validar Tipos de Dados:** Lembre-se que colunas que representam "Embalagem Padrão" (`PADRAOEMBCOMPRA`, `PADRAOEMBTRANSF`) armazenam a **quantidade** (QTDEMBALAGEM) ou um **ID numérico**, nunca a string textual (ex: 'UN').
3. **Joins de Embalagem:** A chave primária composta da tabela `MAP_FAMEMBALAGEM` neste ambiente é `(SEQFAMILIA, QTDEMBALAGEM)`. Não utilize `SEQFAMEMBALAGEM` a menos que sua existência seja confirmada no dicionário.

## Regra de Ouro
> "Na dúvida entre a experiência externa e o dicionário local, o dicionário local é a verdade absoluta."
