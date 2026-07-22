# Var-F7 - consulta_precos_dia_comprador

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/consulta_precos_dia_comprador.sql`

## Objetivo
Consulta de preços do dia (Preço Normal, Promocional e Praticado) por Produto (trazendo o EAN principal ao lado do código do produto), Empresa e Segmento na embalagem padrão de venda, com filtro pré-execução para escolher o Comprador (`LS1` ou todos), além de filtros opcionais para Loja (`NR1`) e Produto (`NR2`).

## Variáveis para cadastrar em Var - F7

### LS1
- **Tipo**: Lista
- **Descrição**: Comprador
- **Tipo de retorno**: Literal
- **Valor padrão**: 0 - TODOS
- **Instrução p/ o usuário**: Selecione o comprador no formato `Código - Apelido` ou `0 - TODOS`. Preencha o campo Valor Padrão com "0 - TODOS".

### NR1
- **Tipo**: Numérico
- **Descrição**: Empresa / Loja
- **Valor padrão**: 0
- **Instrução p/ o usuário**: Informe o número da empresa para filtrar apenas uma loja específica, ou `0` para considerar todas as filiais ativas da rede.

### NR2
- **Tipo**: Numérico
- **Descrição**: Código do Produto (`SEQPRODUTO`)
- **Valor padrão**: 0
- **Instrução p/ o usuário**: Informe o código de um produto específico para consultar apenas ele, ou `0` para listar todos os itens com mix ativo.

## SQL da lista LS1 (Comprador)
Cole esta SQL dentro do quadro da variável `LS1` na tela **Var - F7**:

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
2. Colar ou carregar o SQL principal (`consulta_precos_dia_comprador.sql`).
3. Clicar em **Var - F7** para cadastrar as variáveis do relatório.
4. Na aba **Lista**, cadastrar `LS1` com retorno **Literal**, colando a SQL de Comprador acima e definindo Valor Padrão como `0 - TODOS`.
5. Na aba **Numérico**, cadastrar `NR1` (Empresa) com valor padrão `0`.
6. Na aba **Numérico**, cadastrar `NR2` (Produto) com valor padrão `0`.
7. Salvar as configurações e executar com **Run (F8)**.
