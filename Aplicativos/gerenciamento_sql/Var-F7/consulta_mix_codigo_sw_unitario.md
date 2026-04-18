# Var-F7 - consulta_mix_codigo_sw_unitario

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/consulta_mix_codigo_sw_unitario.sql`

## Objetivo
Consulta para localizar um produto especifico pelo codigo interno do Consinco, trazendo:
- departamento
- codigo do produto
- descricao do produto
- status de compra
- codigo de transicao

O retorno fica restrito ao item informado em `NR1`, mantendo o filtro de loja em `LT1`. A consulta nao filtra mais por `STATUSCOMPRA = 'A'`, entao o item pode aparecer mesmo quando estiver inativo na loja consultada. O codigo de transicao continua priorizando `MAP_PRODCODIGO.CODACESSO` com `TIPCODIGO = 'I'` e embalagem `1`, usando `MAP_PRODUTO.SEQPRODUTOBASEANTIGO` apenas como fallback.

## Variaveis para cadastrar em Var - F7

### LT1
- Tipo: Literal
- Descricao: Loja
- Valor padrao: 1
- Instrucao p/ o usuario: Informe uma ou mais lojas separadas por virgula, por exemplo 1 ou 1,3,15

### NR1
- Tipo: Numerico
- Descricao: Codigo do produto
- Valor padrao: 0
- Instrucao p/ o usuario: Informe o codigo interno do produto no Consinco

## Passo a passo operacional
1. Abrir a consulta na tela Consulta Criacao.
2. Clicar em Var - F7.
3. Cadastrar LT1 na aba Literal.
4. Definir a descricao como Loja.
5. Definir o valor padrao como 1.
6. Cadastrar NR1 na aba Numerica.
7. Definir a descricao como Codigo do produto.
8. Definir o valor padrao como 0.
9. Salvar as variaveis.
10. Fechar e reabrir a consulta.
11. Informar a loja e o codigo do produto.
12. Executar a consulta.

## Observacoes
- Os filtros visuais antes do Run dependem do cadastro manual das variaveis em Var - F7.
- A consulta retorna apenas o item informado em `NR1`.
- O status do item continua sendo exibido na coluna `STATUS_COMPRA`, mas deixou de ser criterio de exclusao no `WHERE`.
- Os departamentos fantasmas excluidos continuam sendo `A CLASSIFICAR`, `ALMOXARIFADO`, `INATIVAR` e `SERVICOS`.
- Se o produto nao tiver codigo de transicao elegivel em `MAP_PRODCODIGO`, a consulta tenta usar `SEQPRODUTOBASEANTIGO` como fallback.