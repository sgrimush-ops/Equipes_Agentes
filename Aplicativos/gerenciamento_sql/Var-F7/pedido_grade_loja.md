# Consulta Criação: Pedido Grade Loja (Venda x Estoque x Compra por Loja)

## Objetivo
Apresentar uma grade linha a linha por produto com colunas sucessivas para cada loja de compra da rede (`1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 17, 18`), exibindo para cada filial:
- **Venda do Período** (`LX_VENDA`)
- **Estoque Disponível Atual** (`LX_ESTQ`)
- **Linha de Preenchimento para Pedido de Compra** (`LX_COMPR`, preenchida com `________`)

Além disso, traz as colunas iniciais com **DIAS** (período retroativo dinâmico a partir de ontem via `LS2`), **Comprador**, **Código do Produto**, **Descrição**, **EMB** e finaliza com **Total Venda** e **Total Estoque** somando todas as lojas.

---

## 1. Variáveis para Var - F7

| Variável | Tipo | Retorno | Padrão | Descrição |
| :--- | :--- | :--- | :--- | :--- |
| **`DT1`** | Data | Data | *Data Inicial* | Data inicial para apuração das vendas por loja |
| **`DT2`** | Data | Data | *Data Final* | Data final para apuração das vendas por loja |
| **`LT1`** | Literal | Literal | `TODOS` ou `1,2,...` | Lojas para exibição de colunas na grade (`TODOS` ou lista de números das lojas ex: `1,2,3`) |
| **`NR1`** | Numérico | Numérico | `0` | Código do Produto (`SEQPRODUTO`) ou `0` para listar todos |
| **`LS1`** | Lista | Literal | `0 - TODOS` | Filtro por Fornecedor Principal / Selecionado |
| **`LS2`** | Lista | Literal | `0 - TODOS` | Filtro por Comprador (`0 - TODOS` ou Código/Nome do Comprador) |
| **`LS3`** | Lista | Literal | `0 - TODOS` | Filtro por Subcategoria / Nível 5 (`0 - TODOS` ou Nome da Categoria Nível 5) |

---

## 2. SQL da Lista LS3 (Subcategoria - Nível 5)

Cole a query abaixo na configuração da Lista **LS3** em `Var - F7`:
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

---

## 3. Passo a Passo Operacional de Configuração

1. Abra o módulo **Consulta Criação** do Totvs Consinco.
2. Cole o script SQL principal (disponível em [`querys/pedido_grade_loja.sql`](file:///c:/Users/usr/Downloads/Equipes_Agentes/Aplicativos/gerenciamento_sql/querys/pedido_grade_loja.sql)) na janela principal da consulta.
3. Clique no botão **Var - F7** para cadastrar e configurar as variáveis:
   - **`DT1` e `DT2`**: Tipo **Data** (Período das vendas).
   - **`LT1`**: Tipo **Literal**, valor padrão `TODOS` (ou digite os números de loja ex: `1,2,3,4,5`).
   - **`NR1`**: Tipo **Numérico**, valor padrão `0`.
   - **`LS1`**: Tipo **Lista**, retorno **Literal** (Selecione a lista de Fornecedores da base).
   - **`LS2`**: Tipo **Lista**, retorno **Literal** (Selecione a lista de Compradores da base).
   - **`LS3`**: Tipo **Lista**, retorno **Literal** (Cole a SQL de Subcategoria/Nível 5 acima).
4. Salve a consulta como `Pedido_Grade_Loja`.

---

## 4. Conformidade com Regras de Performance Consinco

- **Materialização de CTEs**: Todas as subconsultas (`FORN_PRINCIPAL`, `PRODUTOS`, `VENDAS_LOJA`, `VENDAS_PIVOT`, `ESTOQUE_LOJA`, `ESTOQUE_PIVOT`, `GRADE_RESULTADO`) utilizam o hint `/*+ MATERIALIZE */`.
- **Prevenção contra Cartesianos**: Vendas e Estoque são agregados por produto em CTEs de pivô independentes antes do `JOIN` com o produto, evitando multiplicação de linhas.
- **Bypass do Validador de CTE**: A instrução está envelopada em `SELECT * FROM ( WITH ... )` para passar na validação "A instrução SQL informada, não é uma consulta".
- **Sem Comentários Internos**: O SQL não possui comentários `--` ou `/* */` que possam corromper a execução no SGI Client.
