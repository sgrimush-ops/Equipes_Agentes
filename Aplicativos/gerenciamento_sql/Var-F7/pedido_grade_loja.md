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
| **`LT1`** | Literal | Literal | `1,2,3,4,5,6,7,8,11,12,13,14,17,18` | Lojas consideradas na grade ou `TODOS` |
| **`NR1`** | Numérico | Numérico | `0` | Código do Produto (`SEQPRODUTO`) ou `0` para listar todos |
| **`LS1`** | Lista | Literal | `0 - TODOS` | Fornecedor Principal / Selecionado |
| **`LS2`** | Lista | Literal | `30` | Dias retroativos de venda a partir de ontem (`30`, `60`, `90`) |

---

## 2. SQL da Lista LS2 (Período de Vendas Retroativo - Dias)

Cole a query abaixo na configuração da Lista **LS2**:
```sql
SELECT '30' AS DIAS FROM DUAL
UNION ALL
SELECT '60' AS DIAS FROM DUAL
UNION ALL
SELECT '90' AS DIAS FROM DUAL
```

---

## 3. Passo a Passo Operacional de Configuração

1. Abra o módulo **Consulta Criação** do Totvs Consinco.
2. Cole o script SQL principal (disponível em [`querys/pedido_grade_loja.sql`](file:///c:/Users/usr/Downloads/Equipes_Agentes/Aplicativos/gerenciamento_sql/querys/pedido_grade_loja.sql)) na janela principal da consulta.
3. Clique no botão **Var - F7** para configurar as variáveis:
   - **`LT1`**: Tipo **Literal**, valor padrão `1,2,3,4,5,6,7,8,11,12,13,14,17,18`.
   - **`NR1`**: Tipo **Numérico**, valor padrão `0`.
   - **`LS1`**: Tipo **Lista**, retorno **Literal** (seleção de Fornecedores).
   - **`LS2`**: Tipo **Lista**, retorno **Literal** (seleção de Período `30`, `60` ou `90` dias).
4. Salve a consulta como `Pedido_Grade_Loja`.

---

## 4. Conformidade com Regras de Performance Consinco

- **Materialização de CTEs**: Todas as subconsultas (`FORN_PRINCIPAL`, `PRODUTOS`, `VENDAS_LOJA`, `VENDAS_PIVOT`, `ESTOQUE_LOJA`, `ESTOQUE_PIVOT`, `GRADE_RESULTADO`) utilizam o hint `/*+ MATERIALIZE */`.
- **Prevenção contra Cartesianos**: Vendas e Estoque são agregados por produto em CTEs de pivô independentes antes do `JOIN` com o produto, evitando multiplicação de linhas.
- **Bypass do Validador de CTE**: A instrução está envelopada em `SELECT * FROM ( WITH ... )` para passar na validação "A instrução SQL informada, não é uma consulta".
- **Sem Comentários Internos**: O SQL não possui comentários `--` ou `/* */` que possam corromper a execução no SGI Client.
