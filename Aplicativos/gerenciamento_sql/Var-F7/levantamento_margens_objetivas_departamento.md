# Var-F7 — levantamento_margens_objetivas_departamento

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/levantamento_margens_objetivas_departamento.sql`

## Objetivo
Levantar a margem objetiva por produto/hierarquia de departamento, com código e descrição do produto, para identificar margens incorretas. Retorna exclusivamente produtos **Ativos para Compra** (`STATUSCOMPRA = 'A'`). Permite filtrar por produto e comprador.

---

## Variáveis para cadastrar em Var-F7

### NR1 — Código do Produto (opcional)
| Campo        | Valor                              |
|--------------|------------------------------------|
| Nome         | NR1                                |
| Tipo         | Numérico                           |
| Descrição    | Código do produto (0 = todos)      |
| Valor Padrão | 0                                  |

### LS1 — Comprador (opcional, lista dropdown)
| Campo        | Valor                                           |
|--------------|-------------------------------------------------|
| Nome         | LS1                                             |
| Tipo         | Lista                                           |
| Descrição    | Comprador (selecione ou deixe 0 - TODOS)        |
| Valor Padrão | `0 - TODOS`                                     |

**SQL da Lista LS1:**
```sql
SELECT '0 - TODOS' AS ITEM FROM DUAL
UNION ALL
SELECT TO_CHAR(SEQCOMPRADOR) || ' - ' || COMPRADOR AS ITEM
FROM MAX_COMPRADOR
ORDER BY ITEM
```
> O item `0 - TODOS` ja e retornado pela SQL da lista.

---

## Passo a Passo — Cadastro em Var-F7

1. Abra a Consulta Criação e localize ou crie a consulta `levantamento_margens_objetivas_departamento`.
2. Acesse **Var-F7** (botão ou tecla F7).
3. Cadastre **NR1**:
   - Aba: Numérico
   - Descrição: `Código do produto (0 = todos)`
   - Valor padrão: `0`
4. Cadastre **LS1**:
   - Aba: Lista
   - Descrição: `Comprador`
   - Valor padrão: `0 - TODOS`
   - SQL da lista: `SELECT '0 - TODOS' AS ITEM FROM DUAL UNION ALL SELECT TO_CHAR(SEQCOMPRADOR) || ' - ' || COMPRADOR AS ITEM FROM MAX_COMPRADOR ORDER BY ITEM`
5. Salve as variáveis.
6. Execute a consulta.

---

## Observações

- **Apenas Produtos Ativos:** A consulta possui filtro obrigatório por `PE.STATUSCOMPRA = 'A'`, expurgando produtos inativos ou fora de linha.
- **Filtro de Loja Removido:** O filtro por loja (`NR1=empresa`) foi removido conforme solicitação; a verificação abrange todas as lojas comerciais fixas da rede.
- O filtro de comprador usa o padrão `codigo - comprador` e extrai o código para comparar com `MAP_FAMDIVISAO.SEQCOMPRADOR`.
- Selecionar `0 - TODOS` retorna todos os compradores.
- O comprador aparece como coluna `COMPRADOR` no grid, entre a hierarquia e o código do produto.
- Empresas não comerciais já são expurgadas via lista fixa: `IN (1,2,3,4,5,6,7,8,11,12,13,14,15,17,18)`.
