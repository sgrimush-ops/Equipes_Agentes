# Var-F7 - consulta_promocao_v4_fornecedor

## Query vinculada
- Arquivo SQL: [Aplicativos/gerenciamento_sql/querys/consulta_promocao_v4_fornecedor.sql](../querys/consulta_promocao_v4_fornecedor.sql)

## Objetivo
Versao derivada da V4 para consulta por fornecedor, sem filtro por oferta/promocao. Retorna todos os itens do fornecedor informado em NR1, com comparativo de venda entre periodo anterior e periodo atual.

## Colunas retornadas
- `CODIGO_FORNECEDOR`: codigo do fornecedor principal da familia.
- `FORNECEDOR`: nome/razao do fornecedor principal.
- `COMPRADOR`: apelido (ou nome) do comprador da familia.
- `COD`: codigo do produto.
- `DESCRICAO`: descricao completa do produto.
- `QTD_ATUAL`: quantidade vendida no periodo atual (DT3 a DT4).
- `QTD_ANTERIOR`: quantidade vendida no periodo anterior (DT1 a DT2).
- `DIFERENCA_QTD`: diferenca entre periodo atual e anterior.

## Variaveis para cadastrar em Var - F7
Os filtros antes do Run dependem do cadastro manual destas variaveis em Var - F7.

### DT1
- Tipo: Data
- Descricao: Data Inicial Anterior
- Instrucao: inicio do periodo comparativo anterior.

### DT2
- Tipo: Data
- Descricao: Data Final Anterior
- Instrucao: fim do periodo comparativo anterior.

### DT3
- Tipo: Data
- Descricao: Data Comparada Atual
- Instrucao: inicio do periodo comparativo atual.

### DT4
- Tipo: Data
- Descricao: Data Comparada Atual
- Instrucao: fim do periodo comparativo atual.

### NR1
- Tipo: Numerico
- Descricao: Codigo do Fornecedor
- Valor padrao: 0
- Instrucao: informar o codigo do fornecedor. Valor 0 nao retorna dados.

### LS1
- Tipo: Lista
- Descricao: Comprador
- Valor padrao: 0 - TODOS
- Instrucao: selecione o comprador para filtrar ou mantenha 0 - TODOS para trazer todos os compradores do fornecedor.

## SQL da lista LS1
Cole esta SQL dentro da propria variavel LS1 na tela Var - F7:

```sql
SELECT'''0 - TODOS'''FROM DUAL UNION ALL SELECT''''||SEQCOMPRADOR||' - '||REPLACE(COMPRADOR,'''','''''')||''''FROM MAX_COMPRADOR
```

Essa versao e propositalmente compacta para caber no limite do campo da lista.

## Passo a passo operacional
1. Abrir a consulta na tela Consulta Criacao e colar o SQL do arquivo vinculado.
2. Clicar em Var - F7.
3. Cadastrar DT1, DT2, DT3 e DT4 como Data.
4. Cadastrar NR1 como Numerico com descricao Codigo do Fornecedor.
5. Cadastrar LS1 como Lista com retorno Literal.
6. Colar a SQL da lista LS1 no campo da propria variavel.
7. Salvar as variaveis.
8. Executar a consulta.

## Observacoes
- Esta versao remove totalmente o filtro por oferta/promocao.
- O filtro de comprador segue o padrao homologado `codigo - comprador`, convertendo o codigo para comparar com `MAP_FAMDIVISAO.SEQCOMPRADOR`.
- Se houver variavel LS1 antiga de oferta cadastrada nesta consulta, exclua e recrie LS1 com a configuracao acima.