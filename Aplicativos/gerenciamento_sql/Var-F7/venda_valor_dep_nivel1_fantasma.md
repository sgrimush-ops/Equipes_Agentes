# Var-F7 - venda_valor_dep_nivel1_por_loja_tipo_registro

## Query vinculada
- Arquivo SQL: Aplicativos/gerenciamento_sql/querys/venda_valor_dep_nivel1_por_loja_tipo_registro.sql

## Objetivo
Consolidar itens de cupom por dia, tipo de registro, departamento, comprador, produto e loja no periodo informado.

## Colunas retornadas
- DIA_VENDA: data da venda.
- TIPO_REGISTRO: tipo de venda derivado de CODGERALOPER.
- DEPARTAMENTO: categoria nivel 1 da familia do produto.
- COMPRADOR: apelido do comprador responsavel pela familia.
- CODIGO_PRODUTO: codigo interno do produto.
- DESCRICAO_PRODUTO: descricao completa do produto.
- NUMERO_CUPOM: numero do documento fiscal.
- LOJA: numero da empresa.
- VLR_ITEM: valor do item no cupom.

## Variaveis para cadastrar em Var - F7

### DT1
- Tipo: Data
- Descricao: Data Inicial Venda
- Instrucao: informe a data inicial do periodo

### DT2
- Tipo: Data
- Descricao: Data Final Venda
- Instrucao: informe a data final do periodo

### NR1
- Tipo: Numerico
- Descricao: Codigo Operacao
- Valor padrao: 800
- Instrucao: informe o codigo da operacao; use 800 como padrao

### NR2
- Tipo: Numerico
- Descricao: Loja
- Valor padrao: 0
- Instrucao: informe o numero da loja para filtrar; use 0 para trazer todas as lojas da lista branca

### LT1
- Tipo: Literal
- Descricao: Departamento
- Valor padrao: TODOS
- Instrucao: informe o nome exato do departamento ou TODOS para nao filtrar

### LT2
- Tipo: Literal
- Descricao: Tipo Departamento
- Valor padrao: TODOS
- Instrucao: informe FANTASMA para A CLASSIFICAR/ALMOXARIFADO/INATIVAR, VENDA para excluir fantasmas, ou TODOS

## Passo a passo operacional
1. Abrir a consulta e colar o SQL do arquivo vinculado.
2. Clicar em Var - F7.
3. Cadastrar DT1 na aba Data com a descricao Data Inicial Venda.
4. Cadastrar DT2 na aba Data com a descricao Data Final Venda.
5. Cadastrar NR1 na aba Numerico com a descricao Codigo Operacao e valor padrao 800.
6. Cadastrar NR2 na aba Numerico com a descricao Loja e valor padrao 0.
7. Cadastrar LT1 na aba Literal com a descricao Departamento e valor padrao TODOS.
8. Cadastrar LT2 na aba Literal com a descricao Tipo Departamento e valor padrao TODOS.
9. Salvar as variaveis.
10. Executar a consulta; os filtros visuais aparecerao antes do Run.

## Observacoes
- Os filtros visuais nao nascem apenas do SQL; dependem do cadastro manual em Var - F7.
- O filtro de loja segue a regra: 0 = todas as lojas da lista branca; valor diferente de 0 = somente a loja informada.
- O filtro LT2 segue a regra: FANTASMA retorna A CLASSIFICAR/ALMOXARIFADO/INATIVAR (e variacoes INATIVO/INATIVOS), VENDA exclui esses departamentos, TODOS nao aplica esse corte.
- A query continua restrita a TIPNOTAFISCAL = 'S'.
