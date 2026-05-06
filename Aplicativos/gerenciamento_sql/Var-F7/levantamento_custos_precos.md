# Var-F7 — levantamento_custos_precos

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/levantamento_custos_precos.sql`

## Objetivo
Custo bruto, custo líquido, margem objetiva, preço sugerido, preço de venda e margem realizada por produto e loja. Fórmulas validadas contra o simulador MAX0147.

---

## Variáveis para cadastrar em Var-F7

### NR1 — Loja (opcional)
| Campo         | Valor                                    |
|---------------|------------------------------------------|
| Nome          | NR1                                      |
| Tipo          | Numérico                                 |
| Descrição     | Loja (0 = todas as lojas de venda)       |
| Valor Padrão  | 0                                        |

> Informe `0` para retornar todas as lojas. As lojas não comerciais (CD, Matriz) já são expurgadas via lista fixa no SQL.

### NR2 — Código do Item (opcional)
| Campo         | Valor                                 |
|---------------|---------------------------------------|
| Nome          | NR2                                   |
| Tipo          | Numérico                              |
| Descrição     | Código do item (0 = todos)            |
| Valor Padrão  | 0                                     |

---

## Passo a Passo — Cadastro em Var-F7

1. Abra a Consulta Criação e localize ou crie a consulta `levantamento_custos_precos`.
2. Acesse **Var-F7** (botão ou tecla F7).
3. Cadastre **NR1**:
   - Aba: Numérico
   - Descrição: `Loja (0 = todas as lojas de venda)`
   - Valor padrão: `0`
4. Cadastre **NR2**:
   - Aba: Numérico
   - Descrição: `Código do item (0 = todos)`
   - Valor padrão: `0`
5. Salve as variáveis.
6. Execute a consulta.

---

## Observações

- **Expurgo de empresas não comerciais:** fixo no SQL via `IN (1,2,3,4,5,6,7,8,11,12,13,14,15,17,18)` — mesmo padrão dos demais SQLs do workspace.
- `NR1 = 0` → todas as lojas; `NR1 = 15` → apenas loja 15.
- `NR2 = 0` → todos os produtos; `NR2 = 860` → apenas produto 860.
- Fórmulas validadas contra simulador MAX0147 (produto 860, empresa 15).
