# Var-F7: ABC Vendas por Fornecedor e Comprador

**Query Principal**: `abc_vendas_subgrupo_fornecedor_primeira_coluna.sql`  
**Validação**: `INV05_modelo_simplificado_sem_filtros.sql` (sem parâmetros, apenas TOP 30)

---

## 📋 Definição de Variáveis

| Variável | Tipo | Rótulo | Descrição | Padrão | Obrigatória |
|----------|------|--------|-----------|--------|-------------|
| **LT1** | Literal | Data Inicial | *(não usado, deixe em branco)* | — | Não |
| **LT2** | Literal | Visualização | Modo `D` (detalhado por comprador) ou `C` (consolidado) | D | Não |
| **LT3** | Literal | Campo auxiliar | *(não usado, deixe em branco)* | — | Não |
| **LT4** | Literal | Comprador | *(não usado, deixe em branco)* | — | Não |

**Obs**: Use **DT1** e **DT2** (abas "Data") para as datas. O filtro de comprador deve ser feito em **LS1** (lista).

---

## 🔄 SQL para LS1 (Lista de Compradores)

Use este SQL **EM VAR-F7** na coluna **SQL da Lista** para popular o dropdown de compradores:

```sql
SELECT '0 - TODOS' COMPRADOR_DISPLAY FROM DUAL
UNION ALL
SELECT TO_CHAR(C.SEQCOMPRADOR) || ' - ' || NVL(C.COMPRADOR, 'SEM NOME') COMPRADOR_DISPLAY
FROM MAX_COMPRADOR C
```

---

## 📝 Passo a Passo de Cadastro em Var-F7

### 1. Criar **DT1** (Data Inicial)

- **Aba**: Data
- **Nome**: `DT1`
- **Rótulo**: `Data Inicial`
- **Descrição**: `Início do período de vendas`
- **Valor Padrão**: *(deixar vazio)*
- **Obrigatória**: Sim
- **Máscara**: `DD/MM/YYYY`

---

### 2. Criar **DT2** (Data Final)

- **Aba**: Data
- **Nome**: `DT2`
- **Rótulo**: `Data Final`
- **Descrição**: `Fim do período de vendas`
- **Valor Padrão**: *(deixar vazio)*
- **Obrigatória**: Sim
- **Máscara**: `DD/MM/YYYY`

---

### 3. Criar **LS1** (Lista de Compradores)

- **Aba**: Lista
- **Nome**: `LS1`
- **Rótulo**: `Comprador`
- **Descrição**: `Selecione o comprador responsável pela família`
- **Valor Padrão**: `0 - TODOS`
- **Obrigatória**: Não
- **SQL da Lista**: Use o SQL acima (seção anterior)

---

### 4. Criar **LT2** (Visualização)

- **Aba**: Literal
- **Nome**: `LT2`
- **Rótulo**: `Visualização`
- **Descrição**: `Digite 'D' para Detalhado (por comprador) ou 'C' para Consolidado (só fornecedor)`
- **Valor Padrão**: `D`
- **Obrigatória**: Não
- **Máscara**: *(sem máscara)*
- **Tamanho**: 1

---

## 🎯 Modo de Uso

### Cenário 1: Relatório Completo (Modo Detalhado)

1. **DT1**: `01/05/2026`
2. **DT2**: `31/05/2026`
3. **LS1**: `0 - TODOS`
4. **LT2**: `D` ou (deixar padrão)

**Resultado**: Todos os fornecedores do período, separados por comprador.

---

### Cenário 2: Análise de Fornecedor (Consolidado)

1. **DT1**: `01/05/2026`
2. **DT2**: `31/05/2026`
3. **LS1**: `0 - TODOS`
4. **LT2**: `C`

**Resultado**: Todos os fornecedores somados sem separação por comprador.

---

### Cenário 3: Comprador Específico

1. **DT1**: `01/04/2026`
2. **DT2**: `30/04/2026`
3. **LS1**: `123 - NOME DO COMPRADOR`
4. **LT2**: `D`

**Resultado**: Apenas fornecedores sob responsabilidade de João Silva, modo detalhado.

---

## ✅ Checklist de Validação

- [ ] **DT1** criada (Data, Obrigatória)
- [ ] **DT2** criada (Data, Obrigatória)
- [ ] **LS1** criada (Lista, com SQL correto)
- [ ] **LT2** criada (Literal, valores D ou C)
- [ ] LS1 retorna pelo menos `0 - TODOS` como padrão
- [ ] LT2 valor padrão = `D`
- [ ] Query é executável com DT1 e DT2 preenchidas
- [ ] Query retorna resultados diferentes quando LT2 = 'D' vs 'C'

---

## 🐛 Troubleshooting

**"ORA-00936: expressão ausente"**  
→ Verifique se o filtro de comprador usa `#LS1` e se o SQL da lista retorna o valor já entre aspas simples no formato `'codigo - apelido'`, incluindo `'0 - TODOS'`.

**"Nenhum resultado mesmo com data válida"**  
→ Verificar se período tem vendas em MRL_PRODVENDADIA e compras em MLFV_BASENFE (CODGERALOPER 200/202).

**LS1 mostra branco ou vazio**  
→ SQL da lista pode estar com erro. Testar manualmente: `SELECT DISTINCT SEQCOMPRADOR, COMPRADOR FROM MAX_COMPRADOR`.

**LT2 não está funcionando**  
→ Verificar se o valor digitado é exatamente `D` ou `C` (maiúsculas). Espaços em branco causam falha.

**"ORA-00979: not a GROUP BY expression"**
→ Nesta consulta, usar o modelo com dois blocos (`UNION ALL`) para os modos `D` e `C`. Evitar `CASE` com `:LT2` no `SELECT/GROUP BY`.

---

## 📚 Referência Rápida

| Se o usuário quer... | Configure assim |
|----------------------|-----------------|
| Ver TOP fornecedores do mês | DT1/DT2 do mês, LT2=D, LS1=`0 - TODOS` |
| Análise sem detalhes | LT2=C, LS1=`0 - TODOS` |
| Foco em comprador específico | LS1=`código - nome`, LT2=D |
| Exportar histórico 6 meses | DT1=6 meses atrás, DT2=hoje, LT2=C, LS1=`0 - TODOS` |

