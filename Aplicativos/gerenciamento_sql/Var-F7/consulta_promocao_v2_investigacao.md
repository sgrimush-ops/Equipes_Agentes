# Var-F7 - consulta_promocao_v2_investigacao

## Query vinculada
- Arquivo SQL: [Aplicativos/gerenciamento_sql/querys/consulta_promocao_v2_investigacao.sql](../querys/consulta_promocao_v2_investigacao.sql)

## Objetivo
Investigar por que a consulta promocional pode voltar vazia, expondo a base por loja e os componentes usados no calculo do total vendido.

Esta versao ficou fixa para a promocao `VERDINHA`, com periodo anterior de `01/04/2026` a `30/04/2026` e periodo atual de `01/05/2026` a `30/05/2026`.
Ela foi reduzida para evitar erro de parser e nao depende mais de cadastro de empresas.

## Colunas retornadas
- `PROMOCAO`: identificador da promocao.
- `DTAINICIO`: data inicial da promocao.
- `DTAFIM`: data final da promocao.
- `LOJA`: empresa da linha.
- `NOME`: sequencia da promocao.
- `COD`: codigo do produto.
- `DESCRICAO`: descricao completa do produto.
- `PRECO_NORMAL`: preco normal sem agregacao.
- `PRECO_PROMOCIONAL`: preco promocional sem agregacao.
- `MGNORMAL`: margem normal formatada.
- `MGPROMOC`: margem promocional formatada.
- `QTD_ANTERIOR`: quantidade vendida no periodo anterior.
- `QTD_ATUAL`: quantidade vendida no periodo atual.
- `VALOR_TOTAL_VENDIDO`: preco promocional multiplicado pela quantidade atual.

## Variaveis para cadastrar em Var - F7
Essa consulta nao depende de cadastro de variaveis.

## SQL da lista
Nao se aplica.

## Passo a passo operacional
1. Abrir a consulta na tela Consulta Criacao.
2. Clicar em Var - F7.
3. Executar a consulta de investigacao.

## Observacoes
- Esta consulta nao consolida lojas e mantem o mesmo filtro base da v2.
- O valor total e retornado como numero com `ROUND(..., 2)`.