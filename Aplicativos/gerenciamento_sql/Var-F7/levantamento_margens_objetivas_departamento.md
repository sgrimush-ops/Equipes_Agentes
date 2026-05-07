# Var-F7 — levantamento_margens_objetivas_departamento

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/levantamento_margens_objetivas_departamento.sql`

## Objetivo
Levantar a margem objetiva por produto/hierarquia de departamento, com código e descrição do produto, para identificar margens incorretas. Permite filtrar por loja, produto e comprador.

---

## Variáveis para cadastrar em Var-F7

### NR1 — Loja (opcional)
| Campo        | Valor                              |
|--------------|------------------------------------|
| Nome         | NR1                                |
| Tipo         | Numérico                           |
| Descrição    | Loja (0 = todas)                   |
| Valor Padrão | 0                                  |

### NR2 — Código do Produto (opcional)
| Campo        | Valor                              |
|--------------|------------------------------------|
| Nome         | NR2                                |
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
SELECT TO_CHAR(SEQCOMPRADOR) || ' - ' || APELIDO AS ITEM
FROM MAX_COMPRADOR
ORDER BY APELIDO
```
> Adicionar manualmente o item `0 - TODOS` como primeira opção ou definir como valor padrão no cadastro da lista.

---

## Passo a Passo — Cadastro em Var-F7

1. Abra a Consulta Criação e localize ou crie a consulta `levantamento_margens_objetivas_departamento`.
2. Acesse **Var-F7** (botão ou tecla F7).
3. Cadastre **NR1**:
   - Aba: Numérico
   - Descrição: `Loja (0 = todas)`
   - Valor padrão: `0`
4. Cadastre **NR2**:
   - Aba: Numérico
   - Descrição: `Código do produto (0 = todos)`
   - Valor padrão: `0`
5. Cadastre **LS1**:
   - Aba: Lista
   - Descrição: `Comprador`
   - Valor padrão: `0 - TODOS`
   - SQL da lista: `SELECT TO_CHAR(SEQCOMPRADOR) || ' - ' || APELIDO AS ITEM FROM MAX_COMPRADOR ORDER BY APELIDO`
6. Salve as variáveis.
7. Execute a consulta.

---

## Observações

- O filtro de comprador usa o padrão `codigo - apelido` e extrai o código para comparar com `MAP_FAMDIVISAO.SEQCOMPRADOR`.
- Selecionar `0 - TODOS` retorna todos os compradores.
- O comprador aparece como coluna `COMPRADOR` no grid, entre a hierarquia e o código do produto.
- Empresas não comerciais já são expurgadas via lista fixa: `IN (1,2,3,4,5,6,7,8,11,12,13,14,15,17,18)`.
