# Var-F7 - abc_venda_formato_comprador_liquido

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/abc_venda_formato_comprador_liquido.sql`

## Objetivo
Consulta de Curva ABC por Fornecedor, Subcategoria/Subgrupo e Produto com custos e margens líquidas, permitindo filtragem pré-execução por Loja (`NR1`), Produto (`NR2`), Fornecedor (`LT2`), Loja de Custo CD (`LT1`), Comprador (`LS3`), Período (`DT1` e `DT2`) e Subcategoria (`LS1`).

## Variáveis para cadastrar em Var - F7

### DT1
- Tipo: Data
- Descrição: Data Inicial de Análise
- Instrução p/ o usuário: Informe a data inicial para considerar vendas, entradas e emissões.

### DT2
- Tipo: Data
- Descrição: Data Final de Análise
- Instrução p/ o usuário: Informe a data final do período analisado.

### LT1
- Tipo: Literal
- Descrição: Empresa/Loja Origem Custo CD
- Valor padrão: 15
- Instrução p/ o usuário: Informe o número da empresa (ex.: 15) para referência de cálculo do custo CD.

### LT2
- Tipo: Literal
- Descrição: Código do Fornecedor
- Valor padrão: 0
- Instrução p/ o usuário: Digite o código do fornecedor desejado ou 0 para considerar todos.

### LS1
- Tipo: Lista
- Descrição: Subcategoria (Nível 5)
- Tipo de retorno: Literal
- Valor padrão: 0 - TODOS
- Instrução p/ o usuário: Selecione a subcategoria (Nível 5) ou 0 - TODOS para todas as subcategorias. Preencha o campo Valor Padrão com "0 - TODOS".

### LS3
- Tipo: Lista
- Descrição: Comprador
- Tipo de retorno: Literal
- Valor padrão: 0 - TODOS
- Instrução p/ o usuário: Selecione o comprador no formato Código - Apelido ou 0 - TODOS.

### NR1
- Tipo: Numérico
- Descrição: Empresa/Loja (Vendas/Estoque)
- Valor padrão: 0
- Instrução p/ o usuário: Informe o número da loja para filtrar ou 0 para considerar todas as lojas da consulta.

### NR2
- Tipo: Numérico
- Descrição: Código do Produto
- Valor padrão: 0
- Instrução p/ o usuário: Informe o código do produto específico ou 0 para considerar todos.

## SQL da lista LS1 (Subcategoria / Nível 5)
Cole esta SQL dentro do quadro da variável `LS1` na tela Var - F7:

```sql
SELECT '0 - TODOS' AS SUBCATEGORIA
FROM DUAL
UNION
SELECT DISTINCT A.CATEGORIA AS SUBCATEGORIA
FROM MAP_CATEGORIA A
WHERE A.STATUSCATEGOR = 'A'
  AND A.TIPCATEGORIA = 'M'
  AND A.NIVELHIERARQUIA = 5
```

## SQL da lista LS3 (Comprador)
Cole esta SQL dentro do quadro da variável `LS3` na tela Var - F7:

```sql
SELECT '0 - TODOS' AS COMPRADOR
FROM DUAL
UNION
SELECT DISTINCT
    TO_CHAR(C.SEQCOMPRADOR) || ' - ' || REPLACE(NVL(C.APELIDO, C.COMPRADOR), '''', '') AS COMPRADOR
FROM MAX_COMPRADOR C
WHERE C.SEQCOMPRADOR IS NOT NULL
```

## Passo a passo operacional
1. Abrir a tela **Consulta Criação** no Totvs Consinco.
2. Colar ou carregar o SQL de `abc_venda_formato_comprador_liquido.sql`.
3. Clicar em **Var - F7** para cadastrar as variáveis.
4. Cadastrar `DT1` e `DT2` na aba **Data**.
5. Cadastrar `LT1` e `LT2` na aba **Literal** com os valores padrões acima.
6. Cadastrar `NR1` e `NR2` na aba **Numérico** com valor padrão `0`.
7. Cadastrar `LS1` na aba **Lista** com retorno **Literal**, colando a SQL de Subcategoria acima.
8. Cadastrar `LS3` na aba **Lista** com retorno **Literal**, colando a SQL de Comprador acima.
9. Salvar as configurações das variáveis e executar com **Run (F8)**.
