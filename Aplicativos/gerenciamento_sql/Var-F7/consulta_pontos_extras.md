# Var-F7 — consulta_pontos_extras

## Query vinculada
- Arquivo SQL: [Aplicativos/gerenciamento_sql/querys/consulta_pontos_extras.sql](../querys/consulta_pontos_extras.sql)

## Objetivo
Consultar os estoques mínimos e máximos definidos por campanha de exposição de Ponto Extra no ERP Consinco, permitindo filtrar por loja, produto, campanha, comprador e pela situação da vigência (`TODOS`, `VIGENTE`, `ENCERRADO` ou `FUTURO`).

## Colunas Retornadas
- `COD_PONTO_EXTRA`: ID da campanha de exposição extra.
- `NOME_PONTO_EXTRA`: Descrição da campanha.
- `LOJA` / `NOME_LOJA`: Número e nome fantasia da empresa/loja.
- `COMPRADOR`: Apelido do comprador responsável pela família do produto.
- `COD_PRODUTO` / `DESCRICAO_PRODUTO`: Código e descrição completa do item.
- `MINIMO_PONTO_EXTRA`: Estoque mínimo configurado no ponto extra (`ESTQMINIMO`).
- `MAXIMO_PONTO_EXTRA`: Estoque máximo configurado no ponto extra (`ESTQMAXIMO`).
- `INICIO_VIGENCIA` / `FIM_VIGENCIA`: Datas de vigência da exposição no formato DD/MM/YYYY.
- `STATUS_ITEM_EMP`: Status do item na empresa/campanha.
- `SITUACAO_VIGENCIA`: Cálculo da situação da vigência em relação à data atual (`VIGENTE`, `FUTURO` ou `ENCERRADO`).

## Variáveis para cadastrar em Var - F7

| Variável | Tipo no Consinco | Descrição da Variável | Valor Padrão | Instrução / Uso |
| :--- | :--- | :--- | :--- | :--- |
| **`NR1`** | **Numérico** | Loja (0 = todas) | **`0`** | Filtre por uma loja específica ou mantenha 0 |
| **`NR2`** | **Numérico** | Código do Produto (0 = todos) | **`0`** | Filtre por um item ou mantenha 0 |
| **`NR3`** | **Numérico** | ID do Ponto Extra (0 = todos) | **`0`** | Filtre por uma campanha específica ou mantenha 0 |
| **`LS1`** | **Lista** | Comprador | **`0 - TODOS`** | Selecione o comprador responsável ou mantenha todos |
| **`LS2`** | **Lista** | Situação da Vigência | **`TODOS`** | Selecione a situação da vigência para filtrar (`TODOS`, `VIGENTE`, `ENCERRADO` ou `FUTURO`) |

## SQL da lista LS1 (Compradores)
Colar dentro do cadastro da variável `LS1` (sem aspas literais na consulta para blindar contra erro `ORA-01722`):
```sql
SELECT '0 - TODOS' AS COMPRADOR
FROM DUAL
UNION
SELECT DISTINCT TO_CHAR(SEQCOMPRADOR) || ' - ' || NVL(APELIDO, COMPRADOR)
FROM MAX_COMPRADOR
WHERE STATUS = 'A'
ORDER BY 1
```

## SQL da lista LS2 (Situação da Vigência)
Colar dentro do cadastro da variável `LS2`:
```sql
SELECT 'TODOS' AS SITUACAO FROM DUAL
UNION
SELECT 'VIGENTE' FROM DUAL
UNION
SELECT 'ENCERRADO' FROM DUAL
UNION
SELECT 'FUTURO' FROM DUAL
```

## Passo a passo operacional
1. Abra a tela **Consulta Criação** no módulo Consinco e cole o SQL atualizado de `consulta_pontos_extras.sql`.
2. Clique no botão **Var - F7**.
3. Cadastre as variáveis numéricas **`NR1`**, **`NR2`** e **`NR3`** na aba de Numéricos com valor padrão **`0`**.
4. Na aba de Listas, cadastre a lista **`LS1`** (Comprador) com valor padrão `0 - TODOS` e cole o respectivo SQL da lista acima.
5. Cadastre a lista **`LS2`** (Situação da Vigência) com valor padrão `TODOS` e cole o SQL da lista correspondente.
6. Salve o cadastro das variáveis em **Var - F7** e execute a consulta.
