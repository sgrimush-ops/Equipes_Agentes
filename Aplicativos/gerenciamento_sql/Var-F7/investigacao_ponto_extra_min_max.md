# Var-F7 — investigacao_ponto_extra_min_max

## Query vinculada
- Arquivo SQL: [Aplicativos/gerenciamento_sql/querys/investigacao_ponto_extra_min_max.sql](../querys/investigacao_ponto_extra_min_max.sql)

## Objetivo
Investigar e listar os novos estoques mínimos e máximos definidos por campanha de exposição de Ponto Extra, detalhando por loja, produto, vigência e comprador. A estrutura foi revelada via rastreamento de SQL Monitor do ERP Consinco.

## Tabelas Reveladas (O Mapa do Ponto Extra)
- `MRL_PONTOEXTRA`: Cabeçalho da campanha/evento do Ponto Extra (`SEQPONTOEXTRA`, `DESCRICAO`, `STATUS`).
- `MRL_PONTOEXTRAPRODUTO`: Relação de produtos associados ao Ponto Extra.
- `MRL_PONTOEXTRAPRODUTOEMPRESA`: **Tabela Principal!** Armazena por Loja/Empresa os valores de `ESTQMINIMO`, `ESTQMAXIMO` e as datas de vigência (`DTAVIGENCIAINICIO`, `DTAVIGENCIAFIM`).

## Colunas Retornadas
- `COD_PONTO_EXTRA`: ID da campanha.
- `NOME_PONTO_EXTRA`: Nome/descrição da campanha.
- `LOJA` / `NOME_LOJA`: Empresa onde a exposição extra está aplicada.
- `COMPRADOR`: Comprador responsável pela família do produto.
- `COD_PRODUTO` / `DESCRICAO_PRODUTO`: Dados do item.
- `MINIMO_PONTO_EXTRA`: Novo estoque mínimo da exposição extra (`ESTQMINIMO`).
- `MAXIMO_PONTO_EXTRA`: Novo estoque máximo da exposição extra (`ESTQMAXIMO`).
- `INICIO_VIGENCIA` / `FIM_VIGENCIA`: Período em que o novo mínimo/máximo sobrepõe o padrão.
- `STATUS_ITEM_EMP`: Status do vínculo na loja.
- `SITUACAO_VIGENCIA`: Calculado automaticamente (`VIGENTE`, `FUTURO` ou `ENCERRADO`).

## Variáveis para cadastrar em Var - F7

| Variável | Tipo no Consinco | Descrição da Variável | Valor Padrão | Instrução / Uso |
| :--- | :--- | :--- | :--- | :--- |
| **`NR1`** | **Numérico** | Loja (0 = todas) | **`0`** | Filtre por uma loja específica ou mantenha 0 |
| **`NR2`** | **Numérico** | Código do Produto (0 = todos) | **`0`** | Filtre por um item ou mantenha 0 |
| **`NR3`** | **Numérico** | ID do Ponto Extra (0 = todos) | **`0`** | Filtre por uma campanha ou mantenha 0 |
| **`LS1`** | **Lista** | Comprador | **`0 - TODOS`** | Selecione o comprador responsável |

## SQL da lista LS1 (Compradores)
Colar dentro da variável LS1 (sem aspas literais para blindar contra ORA-01722):
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
1. Abra a Consulta Criação e cole o SQL de `investigacao_ponto_extra_min_max.sql`.
2. Acesse a tela Var - F7.
3. Cadastre as variáveis numéricas `NR1`, `NR2` e `NR3` com valor padrão `0`.
4. Cadastre a lista `LS1` com valor padrão `0 - TODOS` e o SQL da lista acima.
5. Salve e execute a consulta.
