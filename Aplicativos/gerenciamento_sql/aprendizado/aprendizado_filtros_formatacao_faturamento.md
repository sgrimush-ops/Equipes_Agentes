# Aprendizado — Filtros Únicos (LS vs NR), Formatação Monetária e Listas de Texto (LT)

## 1. Evitar Redundância de Variáveis de Entrada (NR + LS para a Mesma Entidade)

### Problema
Em relatórios da Consulta Criação do Consinco, era comum criar duas variáveis para filtrar uma mesma entidade:
- **`NR1`** (Numérico): Para o usuário digitar o código (ex: `6560`).
- **`LS1`** (Lista de Seleção): Para o usuário escolher no dropdown (ex: `6560 - ANTONIAZZI & CIA LTDA`).

### Padrão Recomendado
- **Mantenha apenas `LS1`**.
- O componente de Combobox da tela Consulta Criação do Consinco possui **busca incremental**: ao digitar números (`6560`) ou texto (`ANTONIA`), o próprio dropdown filtra e seleciona o item na hora.
- Isso simplifica a interface para o usuário e limpa a cláusula `WHERE` da query.

#### Exemplo de Filtro `WHERE` para `LS1` (Fornecedor / Pessoa):
```sql
AND (
    NVL(TRIM(:LS1), 'TODOS') IN ('TODOS', '0 - TODOS', '0', '')
    OR INSTR(TRIM(:LS1), 'TODOS') > 0
    OR TO_CHAR(MLF_NOTAFISCAL.SEQPESSOA) = TRIM(:LS1)
    OR INSTR(TRIM(:LS1), TO_CHAR(MLF_NOTAFISCAL.SEQPESSOA) || ' - ') = 1
    OR INSTR(TRIM(:LS1), TO_CHAR(MLF_NOTAFISCAL.SEQPESSOA) || '-') = 1
)
```

---

## 2. Formatação Monetária (`R$ 0.000,00`) e Ordenação Numérica

### Problema
Quando aplicamos `TO_CHAR` para formatar colunas financeiras (ex: `R$ 1.234,50`), o Oracle converte o resultado em **String (`VARCHAR2`)**.
Se o `ORDER BY` referenciar o alias da coluna formatada (`ORDER BY VALOR_TOTAL_FATURADO DESC`), a ordenação será **alfabética**:
- `'R$ 950,00'` aparecerá antes de `'R$ 1.200,00'`.

### Padrão Recomendado
1. Formate a coluna no `SELECT` com `TO_CHAR(...)` + máscara `FM999G999G990D00`.
2. No `ORDER BY`, ordene **sempre pela expressão numérica não formatada**.

#### Exemplo:
```sql
SELECT 
    MLF_NOTAFISCAL.SEQPESSOA,
    GE_PESSOA.NOMERAZAO,
    'R$ ' || TO_CHAR(SUM(NVL(MLF_NFITEM.VLRTOTALITEM, 0)), 'FM999G999G990D00', 'NLS_NUMERIC_CHARACTERS='',.''') AS VALOR_TOTAL_FATURADO
FROM ...
GROUP BY MLF_NOTAFISCAL.SEQPESSOA, GE_PESSOA.NOMERAZAO
ORDER BY SUM(NVL(MLF_NFITEM.VLRTOTALITEM, 0)) DESC, GE_PESSOA.NOMERAZAO
```

---

## 3. Filtro de Múltiplos Códigos via Lista de Texto (`LT`)

### Problema
Permitir que o usuário digite múltiplos códigos separados por vírgula (ex: `1, 28, 32, 200, 290`) no filtro de texto (`LT1`) sem usar SQL dinâmico.

### Padrão Recomendado (Envelopamento com Vírgulas via `INSTR`)
Remova espaços, envolva a string de entrada e o campo com vírgulas `,` nas extremidades. Isso garante que buscar `,28,` não case por engano com `,280,` ou `,128,`.

#### Exemplo (`WHERE` seguro para `:LT1`):
```sql
AND (
    NVL(TRIM(:LT1), '0') IN ('0', 'TODOS', '')
    OR INSTR(',' || REPLACE(TRIM(:LT1), ' ', '') || ',', ',' || MLF_NOTAFISCAL.CODGERALOPER || ',') > 0
)
```
- **Se `:LT1 = '1, 28, 32, 200, 290'`**: Filtrará exatamente os CGOs contidos na lista.
- **Se `:LT1 = '0'` ou `'TODOS'`**: Ignorará o filtro e trará todos os CGOs.
