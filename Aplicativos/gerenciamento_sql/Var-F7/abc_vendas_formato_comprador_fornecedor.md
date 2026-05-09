# Var-F7 - abc_vendas_formato_comprador_fornecedor

## Query vinculada
- Arquivo SQL: Aplicativos/gerenciamento_sql/querys/abc_vendas_formato_comprador_fornecedor.sql

## Objetivo
Consulta ABC de vendas com filtro opcional por fornecedor, permitindo filtrar por codigo quando conhecido e por descricao quando o codigo nao for conhecido.

## Regra de uso dos filtros de fornecedor
- Se souber o codigo, preencher LT2 com o codigo numerico e manter LT4 = TODOS.
- Se nao souber o codigo, manter LT2 = 0 e preencher LT4 com parte do nome (exemplo: SPAL).
- Se quiser todos os fornecedores, manter LT2 = 0 e LT4 = TODOS.

## Variaveis para cadastrar em Var - F7

### DT1
- Tipo: Data
- Descricao: Data Inicial Venda

### DT2
- Tipo: Data
- Descricao: Data Final Venda

### LT2
- Tipo: Literal
- Descricao: Codigo Fornecedor
- Valor padrao: 0
- Regra: informar apenas numeros; 0 = todos

### LT4
- Tipo: Literal
- Descricao: Descricao Fornecedor
- Valor padrao: TODOS
- Regra: informar parte do nome do fornecedor; exemplo SPAL
- Observacao tecnica: manter LT4 como Literal (nao Lista), pois a SQL principal usa bind :LT4 para evitar erro de parser em SQL longo.

### LS3
- Tipo: Lista
- Descricao: Comprador
- Tipo de retorno: Texto unico
- Valor padrao: 0 - TODOS
- Regra: selecionar pela lista no formato codigo - apelido

### NR1
- Tipo: Numerico
- Descricao: Qtd Vendida Maior Que
- Valor padrao: 0

## SQL da lista LS3
```sql
SELECT '''0 - TODOS''' AS COMPRADOR
FROM DUAL
UNION
SELECT DISTINCT
    '''' || TO_CHAR(C.SEQCOMPRADOR) || ' - ' || REPLACE(NVL(C.APELIDO, C.COMPRADOR), '''', '''''') || '''' AS COMPRADOR
FROM MAX_COMPRADOR C
WHERE C.SEQCOMPRADOR IS NOT NULL
```

## SQL auxiliar para localizar fornecedores por descricao
```sql
SELECT
    P.SEQPESSOA AS COD_FORNECEDOR,
    P.NOMERAZAO AS FORNECEDOR
FROM GE_PESSOA P
WHERE P.TIPOPESSOA = 'J'
  AND UPPER(P.NOMERAZAO) LIKE '%' || UPPER(:LT4) || '%'
ORDER BY P.NOMERAZAO
```

## Passo a passo curto
1. Cadastre a query na Consulta Criacao.
2. Abra Var - F7 e cadastre DT1, DT2, LT2, LT4, LS3 e NR1 com os tipos acima.
3. Dentro da variavel LS3, cadastre a SQL da lista exatamente como informado.
4. Para pesquisar fornecedor por nome antes do Run, use LT2 = 0 e preencha LT4.
5. Para filtrar por codigo direto, preencha LT2 e deixe LT4 = TODOS.

## Observacoes
- Os filtros visuais antes do Run dependem do cadastro em Var - F7; nao sao criados apenas pelo SQL.
- O filtro de comprador permanece no padrao homologado codigo - apelido, com extracao do codigo para SEQCOMPRADOR.
- Se LT4 nao estiver cadastrado no Var - F7 com valor padrao TODOS, a consulta pode se comportar como sem filtro de fornecedor.
- Se LT4 estiver como Lista, ajuste para Literal antes de executar.
- Quando LT2 = 0 e LT4 vier preenchido (ex.: SPAL), a coluna TITULO_FORNECEDOR passa a mostrar CODIGO - FORNECEDOR.
