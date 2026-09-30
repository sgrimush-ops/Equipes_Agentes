# Var-F7 - Ranking de Vendas, Compras, Devoluções e Custos por Fornecedor e Rede

## Objetivo
Apresentar o ranking consolidado e/ou detalhado por comprador com totalizadores de Vendas (`MRL_CUSTODIA`), Compras líquidas de devolução/troca (`MLF_NFITEM` / `MLFV_BASENFE`), Bonificações, Devoluções, Trocas, Custos de Estoque em CDs e Lojas (`MRL_PRODUTOEMPRESA`) e Incinerações por fornecedor principal e rede, com filtros antes do Run por Fornecedor (`NR1`), Comprador (`LS1`), Rede (`LS2`), Período (`DT1` e `DT2`) e Visão Consolidada/Detalhada (`LT2`).

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/b.ranking_vendas_subgrupo_fornecedor_rede.sql`

## Variáveis para cadastrar em Var - F7

| Variável | Tipo | Descrição | Valor Padrão | Instrução ao Usuário |
|---|---|---|---|---|
| `DT1` | Data | Data Inicial do Período | - | Informe a data inicial |
| `DT2` | Data | Data Final do Período | - | Informe a data final |
| `NR1` | Numérico | Código do Fornecedor | `0` | Digite o código do fornecedor ou `0` para todos |
| `LS1` | Lista | Comprador / Gestor | `0 - TODOS` | Selecione o Comprador ou mantenha `0 - TODOS` |
| `LS2` | Lista | Rede do Fornecedor | ` TODAS AS REDES` | Selecione a Rede (`GE_REDE`) ou mantenha ` TODAS AS REDES` |
| `LT2` | Literal | Visão (D=Detalhado / C=Consolidado) | `D` | Digite `D` para detalhado por comprador ou `C` para consolidado |

---

## SQL das Listas LSx

### 1. SQL da Lista LS1 (Comprador)
```sql
SELECT '0 - TODOS' FROM DUAL UNION ALL SELECT SEQCOMPRADOR || ' - ' || COMPRADOR FROM MAX_COMPRADOR
```

### 2. SQL da Lista LS2 (Rede)
```sql
SELECT ' TODAS AS REDES' FROM DUAL UNION ALL SELECT DESCRICAO FROM GE_REDE
```

---

## Configuração e Passo a Passo

1. Abra a tela **Consulta Criação** no Totvs Consinco.
2. Pressione **Var - F7** no teclado.
3. Cadastre as variáveis `DT1`, `DT2`, `NR1`, `LS1`, `LS2` e `LT2` conforme a tabela acima.
4. Para as variáveis `LS1` e `LS2`, selecione o tipo **Lista** e cole seus respectivos comandos SQL.
5. Salve e execute a consulta.
