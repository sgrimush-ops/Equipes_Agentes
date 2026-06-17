# Aprendizado: Prevenção de Erros SQL no ERP Consinco (ORA-01722, ORA-00942, ORA-00904 e ORA-00923)

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

## Contexto do Erro 3: Aliases Acentuados e Aspas Duplas (ORA-00923)
Ao criar a query `a.ranking_vendas_investiacao_v7.sql`, a execução no Totvs SGI resultou no erro:
- **ORA-00923: FROM keyword not found where expected:** Causado pela tentativa de usar aspas duplas com espaços e caracteres acentuados no alias da coluna (ex: `AS "Código Produto"` e `AS "Valor Liquido"`).

### Causa Raiz e Solução
Alguns clientes Oracle e drivers do Totvs SGI têm restrições de codificação e problemas de parser quando interpretam caracteres especiais em aspas duplas.
A solução é utilizar aliases de colunas em formato padrão: em letras maiúsculas, sem aspas, sem espaços e ASCII simples sem acentos (ex: `AS CODIGO_PRODUTO`, `AS VALOR_LIQUIDO`).

---

## Contexto da Regra de Negócio: Exclusão de Categoria Almoxarifado
Identificamos que alguns produtos comerciais (como cortes JBS) possuem múltiplos vínculos de categoria no ERP (ex: vinculados ao mesmo tempo a `PERECIVEIS` e `ALMOXARIFADO`).
- **Problema**: O uso de `EXISTS (SELECT 1 ... NOT IN ('ALMOXARIFADO'))` inclui esses produtos nas vendas da query porque o banco encontra o vínculo alternativo comercial. Porém, os relatórios oficiais do sistema expurgam de forma restrita **qualquer item** associado a `ALMOXARIFADO`. Isso gerou a inflação das vendas de maio em R$ 95.038,67.
- **Solução**: Utilizar a cláusula de expurgo estrito com **`NOT EXISTS (SELECT 1 ... IN ('ALMOXARIFADO'))`**. Isso garante que itens com dupla categorização sejam totalmente expurgados, fazendo com que as queries batam centavo por centavo com o relatório oficial do ERP.

---

## Contexto de Visualização: Pivot de Operações em Linha Única
Em consultas de títulos financeiros (`FI_TITULO` e `FI_TITOPERACAO`), um título pode conter múltiplas baixas parciais por CGO/Operação (compensações, pagamentos em conta corrente ou descontos obtidos), gerando linhas repetidas na grade.
- **Solução**: Consolidar o faturamento agrupando por chave de título (`SEQTITULO`) e pivotando os tipos de baixas em colunas distintas através de soma condicional:
  ```sql
  SUM(CASE WHEN CODOPERACAO = 19 THEN VLROPERACAO ELSE 0 END) AS VLR_COMPENSADO,
  SUM(CASE WHEN CODOPERACAO = 29 THEN VLROPERACAO ELSE 0 END) AS VLR_DESCONTO,
  SUM(CASE WHEN CODOPERACAO = 6 THEN VLROPERACAO ELSE 0 END) AS VLR_PAGO_BANCO
  ```
  Isso remove a duplicidade e distribui os detalhes de pagamento lado a lado de forma clara e limpa.

---

## Lição Aprendida (Protocolo de Segurança)
Sempre que for criar ou modificar uma query SQL para o ERP Consinco neste repositório:
1. **Consultar o Dicionário:** Verifique obrigatoriamente o arquivo `Aplicativos/gerenciamento_sql/dicionario_consinco.json` para validar nomes de colunas e chaves de join.
2. **Validar Tipos de Dados:** Lembre-se que colunas que representam "Embalagem Padrão" (`PADRAOEMBCOMPRA`, `PADRAOEMBTRANSF`) armazenam a **quantidade** (QTDEMBALAGEM) ou um **ID numérico**, nunca a string textual (ex: 'UN').
3. **Joins de Embalagem:** A chave primária composta da tabela `MAP_FAMEMBALAGEM` neste ambiente é `(SEQFAMILIA, QTDEMBALAGEM)`. Não utilize `SEQFAMEMBALAGEM` a menos que sua existência seja confirmada no dicionário.
4. **Joins de Comprador no Financeiro (FI):** Para associar o comprador responsável a um título financeiro (`FI_TITULO`), utilize obrigatoriamente a tabela intermediária **`FI_TITCOMPRADOR`** (vinculando por `SEQTITULO`) e em seguida ligue a `MAX_COMPRADOR` (via `SEQCOMPRADOR`). Evite o uso de tabelas de parametrização comercial (como `MAP_FORNCLI` ou `MAF_FORNECEDOR`), pois estas podem resultar em erros de tabela inexistente ou identificador inválido dependendo do banco de dados do cliente.
5. **Nomes de Aliases Sem Caracteres Especiais:** Sempre nomeie colunas de saída (`AS`) usando apenas caracteres alfanuméricos ASCII simples, sem espaços e em caixa alta. Nunca use aspas duplas, cedilhas ou acentuação, pois causará erros ORA-00923 no Totvs SGI.
6. **Expurgo de Almoxarifado via NOT EXISTS:** A exclusão de categorias como 'ALMOXARIFADO' deve sempre utilizar `NOT EXISTS` e operador `IN` para que o expurgo seja absoluto sobre qualquer produto associado a essa categoria.

## Regra de Ouro
> "Na dúvida entre a experiência externa e o dicionário local, o dicionário local é a verdade absoluta."
