# Aprendizado: Grade de Pedidos e Compras por Loja (Pivoteamento via CTEs)

## 1. Contexto e Objetivo
Em relatórios de apoio a compras e abastecimento no Totvs Consinco (Consulta Criação), frequentemente é necessário montar uma **Grade Horizontal (Pivô)** por produto onde cada loja da rede (`1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 17, 18`) ocupa um bloco de colunas de apoio à decisão:
- **`LX_VENDA`**: Venda consolidada da loja no período retroativo (`30`, `60` ou `90` dias a partir de ontem via variável `LS2`).
- **`LX_ESTQ`**: Estoque físico disponível da loja (`ESTQLOJA + ESTQDEPOSITO - QTDRESERVADAVDA - QTDRESERVADARECEB`).
- **`LX_COMPR`**: Coluna visual de preenchimento (`'________'`) para anotação ou digitação de pedidos.
- **Filtros Dinâmicos**: Suporta filtragem por Fornecedor Principal (`LS1`) e Período Retroativo em Dias (`LS2`).

---

## 2. Padrão Arquitetural Antigargalo (Prevenção de Produto Cartesiano)

### O Risco do Join Direto
Se o produto (`PRODUTOS`) fizer `LEFT JOIN` diretamente com histórico de vendas por loja (`VENDAS_LOJA`) e saldo de estoque por loja (`ESTOQUE_LOJA`), cada produto gerará até $14 \times 14 = 196$ combinações cruzadas, multiplicando indevidamente os valores e explodindo a memória do Oracle.

### A Solução OBRIGATÓRIA: CTEs de Pivô Independentes
Antes de juntar com a tabela de produtos, crie **duas CTEs separadas** de pivoteamento com agregação (`GROUP BY SEQPRODUTO`), garantindo relação estritamente **1 para 1** com o produto:

```sql
VENDAS_PIVOT AS (
    SELECT /*+ MATERIALIZE */
        V.SEQPRODUTO,
        SUM(CASE WHEN V.NROEMPRESA = 1 THEN V.QTD_VENDA ELSE 0 END) AS VDA_1,
        ...
    FROM VENDAS_LOJA V
    GROUP BY V.SEQPRODUTO
),
ESTOQUE_PIVOT AS (
    SELECT /*+ MATERIALIZE */
        E.SEQPRODUTO,
        SUM(CASE WHEN E.NROEMPRESA = 1 THEN E.QTD_ESTOQUE ELSE 0 END) AS ESTQ_1,
        ...
    FROM ESTOQUE_LOJA E
    GROUP BY E.SEQPRODUTO
)
```

Dessa forma, o `SELECT` da grade apenas conecta `PRODUTOS P LEFT JOIN VENDAS_PIVOT V LEFT JOIN ESTOQUE_PIVOT E`, mantendo a precisão exata e performance instantânea.

---

## 3. Apelidos (Aliases) Limpos e Curtos para Exportação / Impressão

Em relatórios com muitas lojas (mais de 40 colunas no grid), apelidos longos poluem a interface da Consulta Criação e alargam planilhas exportadas para Excel.
- Use **`DIAS`** em vez de `DIAS_CONSULTADOS` para o cálculo `(TRUNC(:DT2) - TRUNC(:DT1)) + 1`.
- Use **`EMB`** em vez de `EMBALAGEM_COMPRA` para `FD.PADRAOEMBCOMPRA`.
- Mantenha padrão de coluna de loja **`L<NUMERO>_<METRICA>`** (ex: `L1_VENDA`, `L1_ESTQ`, `L1_COMPR`).
- NUNCA utilize aspas duplas, acentos ou caracteres especiais nos apelidos.

---

## 4. Filtro Dinâmico de Lojas (`LT1`) Integrado às Colunas

Para permitir que o usuário consulte todas as lojas (`TODOS` ou `1,2,3...18`) ou apenas um subconjunto (ex: `1,2`), a condicional de exibição da coluna deve verificar a variável `:LT1`:

```sql
CASE 
    WHEN (NVL(TRIM(:LT1), 'TODOS') IN ('TODOS', '0', '') OR INSTR(',' || REPLACE(TRIM(:LT1), ' ', '') || ',', ',1,') > 0) 
    THEN NVL(V.VDA_1, 0) 
    ELSE 0 
END AS L1_VENDA
```

Isso zera automaticamente colunas de lojas que não foram solicitadas no filtro, mantendo os totais horizontais (`TOTAL_VENDA` e `TOTAL_ESTOQUE`) perfeitamente alinhados à seleção do usuário.

---

## 5. Arquivo de Referência
- **Query completa homologada**: [`Aplicativos/gerenciamento_sql/querys/pedido_grade_loja.sql`](file:///c:/Users/usr/Downloads/Equipes_Agentes/Aplicativos/gerenciamento_sql/querys/pedido_grade_loja.sql)
- **Procedimento Var-F7**: [`Aplicativos/gerenciamento_sql/Var-F7/pedido_grade_loja.md`](file:///c:/Users/usr/Downloads/Equipes_Agentes/Aplicativos/gerenciamento_sql/Var-F7/pedido_grade_loja.md)
