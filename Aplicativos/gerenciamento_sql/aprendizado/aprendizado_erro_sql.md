# Aprendizado: Prevenção de Erros SQL no ERP Consinco (ORA-01722, ORA-00942 e ORA-00904)

Este documento registra as lições aprendidas durante o desenvolvimento de queries SQL para o ERP TOTVS Consinco neste ambiente.

## Contexto do Erro 1: Embalagens (ORA-01722 e ORA-00904)
Ao atualizar a query `consulta_emb_PBU.sql`, foram cometidos dois erros técnicos sucessivos:
1. **ORA-01722 (Invalid Number):** Tentativa de comparar a coluna `PADRAOEMBTRANSF` (que é numérica) com a string `'UN'`.
2. **ORA-00904 (Invalid Identifier):** Tentativa de utilizar a coluna `SEQFAMEMBALAGEM` como chave de join na tabela `MAP_FAMEMBALAGEM`, sendo que esta coluna não consta no schema local.

### Causa Raiz
O agente confiou em conhecimentos externos de outros schemas ERP, negligenciando a consulta ao dicionário de dados local disponibilizado no projeto.

---

## Contexto do Erro 2: Compradores em Títulos Financeiros (ORA-00942 e ORA-00904)
Ao construir a query `levantamento_compras.sql` para extrair títulos financeiros (verbas e devoluções a receber) vinculados ao comprador responsável:
1. **ORA-00942 (Table or View does not exist):** Tentativa de usar a tabela `MAP_FORNECEDOR`, que é inválida no dicionário local.
2. **ORA-00904 (Invalid Identifier):** Tentativa de usar a coluna `SEQCOMPRADOR` na tabela `MAF_FORNECEDOR` (onde a coluna não existe).
3. **ORA-00942 (Table or View does not exist):** Tentativa de utilizar as tabelas complementares `MAF_FORNCLI` ou `MAP_FORNCLI`, que não estavam ativas ou acessíveis na base de dados do usuário.

### Causa Raiz e Solução Nativa
Títulos do módulo financeiro (`FI_TITULO`) não carregam o comprador diretamente em tabelas comerciais. O relacionamento correto e nativo estabelecido pelo Totvs SGI é feito de forma independente através da tabela **`FI_TITCOMPRADOR`**, que liga o título ao comprador via chave **`SEQTITULO`**.

---

## Lição Aprendida (Protocolo de Segurança)
Sempre que for criar ou modificar uma query SQL para o ERP Consinco neste repositório:
1. **Consultar o Dicionário:** Verifique obrigatoriamente o arquivo `Aplicativos/gerenciamento_sql/dicionario_consinco.json` para validar nomes de colunas e chaves de join.
2. **Validar Tipos de Dados:** Lembre-se que colunas que representam "Embalagem Padrão" (`PADRAOEMBCOMPRA`, `PADRAOEMBTRANSF`) armazenam a **quantidade** (QTDEMBALAGEM) ou um **ID numérico**, nunca a string textual (ex: 'UN').
3. **Joins de Embalagem:** A chave primária composta da tabela `MAP_FAMEMBALAGEM` neste ambiente é `(SEQFAMILIA, QTDEMBALAGEM)`. Não utilize `SEQFAMEMBALAGEM` a menos que sua existência seja confirmada no dicionário.
4. **Joins de Comprador no Financeiro (FI):** Para associar o comprador responsável a um título financeiro (`FI_TITULO`), utilize obrigatoriamente a tabela intermediária **`FI_TITCOMPRADOR`** (vinculando por `SEQTITULO`) e em seguida ligue a `MAX_COMPRADOR` (via `SEQCOMPRADOR`). Evite o uso de tabelas de parametrização comercial (como `MAP_FORNCLI` ou `MAF_FORNECEDOR`), pois estas podem resultar em erros de tabela inexistente ou identificador inválido dependendo do banco de dados do cliente.

## Regra de Ouro
> "Na dúvida entre a experiência externa e o dicionário local, o dicionário local é a verdade absoluta."
