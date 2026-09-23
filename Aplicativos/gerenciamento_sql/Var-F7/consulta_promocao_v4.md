# Var-F7 - consulta_promocao_v4

## Query vinculada
- Arquivo SQL: [Aplicativos/gerenciamento_sql/querys/consulta_promocao_v4.sql](../querys/consulta_promocao_v4.sql)

## Objetivo
Listar produtos em promoção com preço normal, preço promocional, quantidade vendida no período atual, quantidade vendida no período anterior, comprador da família e valor total vendido. Permite selecionar uma promoção específica ou trazer **todas as promoções ativas** no período de datas (`:DT3` a `:DT4`).

## Colunas retornadas
- `PROMOCAO`: identificador da promoção.
- `DTAINICIO`: data inicial da promoção.
- `DTAFIM`: data final da promoção.
- `COMPRADOR`: apelido (ou nome) do comprador vinculado à família (`NRODIVISAO = 1`).
- `NOME`: sequência/código da promoção.
- `COD`: código do produto.
- `DESCRICAO`: descrição completa do produto.
- `PRECO`: preço normal formatado (`FM999G990D00`).
- `MGNORMAL`: margem normal formatada (`FM999G990D99`).
- `PROMO`: preço promocional formatado (`FM999G990D00`).
- `MGPROMOC`: margem promocional formatada (`FM999G990D99`).
- `QTD_ATUAL`: quantidade vendida no período atual (`:DT3` a `:DT4`).
- `QTD_ANTERIOR`: quantidade vendida no período anterior (`:DT1` a `:DT2`).
- `VALOR_TOTAL_VENDIDO`: preço promocional multiplicado pela quantidade vendida atual.

## Variáveis para cadastrar em Var - F7

### LS1
- **Tipo**: Lista
- **Descrição**: Promoção
- **Instrução**: Selecione uma promoção específica ou mantenha `0 - TODAS` para trazer todas as promoções ativas no período (`DT3` a `DT4`).

### LS2
- **Tipo**: Lista
- **Descrição**: Comprador
- **Instrução**: Selecione o comprador para filtrar ou mantenha `0 - TODOS` para trazer todos os compradores.

### DT1
- **Tipo**: Data
- **Descrição**: Data Inicial Período Anterior
- **Instrução**: Informe o início do período comparativo anterior.

### DT2
- **Tipo**: Data
- **Descrição**: Data Final Período Anterior
- **Instrução**: Informe o fim do período comparativo anterior.

### DT3
- **Tipo**: Data
- **Descrição**: Data Inicial Período Atual
- **Instrução**: Informe o início do período atual.

### DT4
- **Tipo**: Data
- **Descrição**: Data Final Período Atual
- **Instrução**: Informe o fim do período atual.

## SQL da lista LS1
Colar no cadastro da variável `LS1` (Promoção - com opção `0 - TODAS`):
```sql
SELECT '0 - TODAS' AS ITEM FROM DUAL UNION SELECT DISTINCT PROMOCAO AS ITEM FROM MRLV_BASEPRODPROMOC WHERE CENTRALLOJA = 'C' AND PRINCIPAL = 'S'
```

## SQL da lista LS2
Colar no cadastro da variável `LS2` (Comprador):
```sql
SELECT '0 - TODOS' AS COMPRADOR
FROM DUAL
UNION
SELECT DISTINCT TO_CHAR(SEQCOMPRADOR) || ' - ' || NVL(APELIDO, COMPRADOR)
FROM MAX_COMPRADOR
WHERE STATUS = 'A'
ORDER BY 1
```

## Passo a passo operacional
1. Abrir a tela **Consulta Criação** do Totvs Consinco e colar o SQL principal.
2. Clicar no botão **Var - F7**.
3. Cadastrar/atualizar a variável **LS1** como Lista com a query de seleção contendo `'0 - TODAS'`.
4. Cadastrar **LS2** como Lista de comprador.
5. Cadastrar **DT1**, **DT2**, **DT3** e **DT4** como tipo Data.
6. Salvar as variáveis e executar a consulta.

## Observações
- Ao selecionar `0 - TODAS`, o filtro `DTAINICIO <= :DT4 AND DTAFIM >= :DT3` garante que todas as promoções vigentes/ativas no período atual sejam retornadas.
- As subconsultas de vendas (`MRL_CUSTODIA`) também respondem dinamicamente ao filtro de promoção/lojas ativas.