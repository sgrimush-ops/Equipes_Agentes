# Var-F7 - consulta_promocao_v4

## Query vinculada
- Arquivo SQL: [Aplicativos/gerenciamento_sql/querys/consulta_promocao_v4.sql](../querys/consulta_promocao_v4.sql)

## Objetivo
Listar produtos em promocao com preco normal, preco promocional, quantidade vendida no periodo atual, quantidade vendida no periodo anterior e uma coluna calculada de valor total vendido.

## Colunas retornadas
- `PROMOCAO`: identificador da promocao.
- `DTAINICIO`: data inicial da promocao.
- `DTAFIM`: data final da promocao.
- `LOJA`: mantida como 0 no modelo atual.
- `NOME`: sequencia da promocao.
- `COD`: codigo do produto.
- `DESCRICAO`: descricao completa do produto.
- `PRECO`: preco normal.
- `MGNORMAL`: margem normal formatada.
- `PROMO`: preco promocional.
- `MGPROMOC`: margem promocional formatada.
- `QTD_ATUAL`: quantidade vendida no periodo atual.
- `QTD_ANTERIOR`: quantidade vendida no periodo anterior.
- `VALOR_TOTAL_VENDIDO`: preco promocional multiplicado pela quantidade vendida atual.

## Variaveis para cadastrar em Var - F7
Essa consulta usa as variaveis ja existentes na tela de Consulta Criacao:

### LS1
- Tipo: Lista
- Descricao: Promocao
- Instrucao: selecione a promocao para filtrar a base principal e as subconsultas de vendas.

### DT1
- Tipo: Data
- Descricao: Data Inicial Periodo Anterior
- Instrucao: informe o inicio do periodo comparativo anterior.

### DT2
- Tipo: Data
- Descricao: Data Final Periodo Anterior
- Instrucao: informe o fim do periodo comparativo anterior.

### DT3
- Tipo: Data
- Descricao: Data Inicial Periodo Atual
- Instrucao: informe o inicio do periodo atual.

### DT4
- Tipo: Data
- Descricao: Data Final Periodo Atual
- Instrucao: informe o fim do periodo atual.

## SQL da lista LS1
Nao ha SQL de lista nesta alteracao, porque a consulta ja consome `#LS1` como lista cadastrada na tela.

## Passo a passo operacional
1. Abrir a consulta na tela Consulta Criacao.
2. Clicar em Var - F7.
3. Conferir o cadastro de LS1 como lista de promocao.
4. Conferir os cadastros de DT1, DT2, DT3 e DT4 como datas.
5. Salvar as variaveis.
6. Executar a consulta.

## Observacoes
- A nova coluna `VALOR_TOTAL_VENDIDO` nao exige outras pesquisas no SQL; ela usa o preco promocional ja retornado e a quantidade agregada da subconsulta `Q1`.
- Se a intencao for usar preco normal em vez de preco promocional, basta trocar `MIN(M.PRECOPROMOCIONAL)` por `MIN(M.PRECONORMAL)` na expressao da nova coluna.