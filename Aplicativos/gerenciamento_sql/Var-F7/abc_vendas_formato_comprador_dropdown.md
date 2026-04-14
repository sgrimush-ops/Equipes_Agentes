# Var-F7 - abc_vendas_formato_comprador_dropdown

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/abc_vendas_formato_comprador_dropdown.sql`

## Objetivo
Consulta ABC de vendas no formato comprador com filtros antes do Run para:
- data inicial de venda
- data final de venda
- codigo do fornecedor
- comprador por dropdown
- quantidade vendida maior que

## Observacao importante
- Esta e a variante com dropdown de comprador.
- Esta versao com `LS2` foi validada quando a lista passou a devolver o valor textual ja entre aspas simples.
- Esta variante existe para atender a necessidade de selecao em lista.
- Se o parser do Consinco voltar a rejeitar a lista, o fallback seguro e a query original `abc_vendas_formato_comprador.sql`.

## Aprendizado homologado
- Regra validada: lista textual usada por `#LS2` em comparacao direta precisa devolver o texto final quoted.
- Exemplo homologado: `TODOS` precisa chegar ao SQL principal como `'TODOS'`.

## Variaveis para cadastrar em Var - F7

### DT1
- Tipo: Data
- Descricao: Data Inicial Venda
- Valor padrao: definir conforme rotina do usuario
- Instrucao p/ o usuario: Informe a data inicial do periodo de venda

### DT2
- Tipo: Data
- Descricao: Data Final Venda
- Valor padrao: Data de hoje
- Instrucao p/ o usuario: Informe a data final do periodo de venda

### LT2
- Tipo: Literal
- Descricao: Codigo Fornecedor
- Valor padrao: 0
- Instrucao p/ o usuario: Informe o codigo do fornecedor. Use 0 para considerar todos

### LS2
- Tipo: Lista
- Descricao: Comprador
- Tipo de retorno: Texto unico
- Valor padrao: TODOS
- Instrucao p/ o usuario: Selecione o comprador diretamente na lista. Nao digite manualmente o valor.

### NR1
- Tipo: Numerico
- Descricao: Qtd Vendida Maior Que
- Valor padrao: 0
- Instrucao p/ o usuario: Informe a quantidade vendida minima para o filtro

## SQL da lista LS2
```sql
SELECT '''TODOS''' AS COMPRADOR
FROM DUAL
UNION
SELECT DISTINCT '''' || REPLACE(COMPRADOR, '''', '''''') || '''' AS COMPRADOR
FROM MAX_COMPRADOR
WHERE COMPRADOR IS NOT NULL
```

## Passo a passo operacional
1. Abrir a consulta na tela Consulta Criacao.
2. Clicar em Var - F7.
3. Cadastrar DT1 na aba Data com descricao Data Inicial Venda.
4. Cadastrar DT2 na aba Data com descricao Data Final Venda.
5. Cadastrar LT2 na aba Literal com descricao Codigo Fornecedor.
6. Definir LT2 com valor padrao 0 para considerar todos os fornecedores.
7. Cadastrar LS2 na aba Lista com descricao Comprador.
8. Definir o valor padrao de LS2 como TODOS.
9. Colar a SQL da lista dentro da configuracao da propria LS2.
10. Validar que o retorno da lista traz os nomes entre aspas simples, por exemplo `'TODOS'` ou `'FULANO'`.
11. Cadastrar NR1 na aba Numerico com descricao Qtd Vendida Maior Que.
12. Salvar as variaveis.
13. Executar a consulta.

## Observacoes
- As colunas originais da consulta foram preservadas.
- O periodo de venda continua controlado por DT1 e DT2.
- O fornecedor continua sendo filtrado por codigo digitado em `LT2`; use `0` para considerar todos.
- O comprador agora e filtrado por dropdown em `LS2`, usando comparacao textual direta no `WHERE`.
- O retorno da lista `LS2` precisa vir entre aspas simples, porque o `#LS2` e expandido diretamente dentro do SQL principal.
- O corte de `NR1` continua sendo aplicado em subquery agregada antes dos joins mais caros.