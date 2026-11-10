# Aprendizado: Ordenação de Texto vs. Número e Filtros por Hierarquia (Nível 5)

Este documento consolida as lições aprendidas e padrões arquiteturais sobre a ordenação de dados no Oracle (evitando armadilhas lexicográficas em colunas formatadas para exibição) e a parametrização robusta de filtros por hierarquia de categorias (Nível 5) no ERP Totvs Consinco.

---

## 1. Armadilha: Ordenação Alfabética (Lexicográfica) em Aliases com `TO_CHAR`

### O Problema
Ao construir relatórios no módulo *Consulta Criação* do Consinco, é uma prática comum formatar colunas numéricas no `SELECT` final com espaços ou funções de formatação para melhor alinhamento no grid:
```sql
SELECT
  '  ' || TO_CHAR(MAX(NVL(VF.QTD_VENDIDA_TOTAL, 0))) AS QTD_VDA
FROM ...
```

Se a cláusula `ORDER BY` referenciar diretamente o alias dessa coluna (`ORDER BY QTD_VDA DESC`), o banco de dados Oracle tratará a expressão como uma comparação de caracteres (`VARCHAR2`) e não como um número.

### Por que isso é perigoso?
Na ordenação alfabética decrescente, o caractere `'9'` é avaliado como maior (superior) ao caractere `'1'`. Portanto:
- O texto `'  9'` é colocado **acima** de `'  100'`, `'  20'` ou `'  150'`.
- Um produto que vendeu 9 unidades aparecerá no topo do relatório de curva ABC ou ranking, passando a falsa impressão de ser o item mais vendido, enquanto um item com 100 unidades aparecerá muito mais abaixo na lista.

### A Solução Obrigatória
Sempre que a coluna de exibição (`SELECT`) for convertida para texto com `TO_CHAR` ou concatenada com espaços, a cláusula `ORDER BY` **nunca deve usar o alias de texto**. A ordenação deve ser feita diretamente pela **agregação numérica matemática pura**:

```sql
ORDER BY
  SUB.SUBGRUPO ASC,
  MAX(NVL(VF.QTD_VENDIDA_TOTAL, 0)) DESC,
  A.DESCCOMPLETA ASC,
  A.SEQPRODUTO ASC
```
*(Caso não seja possível repetir a função agregadora no `ORDER BY`, deve-se forçar a conversão explícita com `TO_NUMBER(TRIM(alias_da_coluna)) DESC`)*.

---

## 2. Padrão para Extração e Ordenação por Subcategoria (Nível 5)

Em relatórios de grade de compras, reposição e curva ABC, o agrupamento principal por **Nível 5** (geralmente equivalente a *Subcategoria* ou *Subgrupo*) deve seguir regras estritas de modelagem para evitar duplicação de árvores hierárquicas e garantir clareza visual.

### A. Extração Oficial via CTE / Subquery
A busca do Nível 5 deve cruzar a `MAP_FAMDIVCATEG` com a `MAP_CATEGORIA` restringindo pela finalidade comercial (`TIPCATEGORIA = 'M'`), status ativo e nível 5:
```sql
CATEGORIAS AS (
    SELECT /*+ MATERIALIZE */
        X.SEQFAMILIA,
        MAX(Y.CATEGORIA) AS NIVEL_5
    FROM MAP_FAMDIVCATEG X
    INNER JOIN MAP_CATEGORIA Y ON Y.SEQCATEGORIA = X.SEQCATEGORIA AND Y.NRODIVISAO = X.NRODIVISAO
    WHERE Y.TIPCATEGORIA = 'M'
      AND Y.NIVELHIERARQUIA = 5
      AND X.STATUS = 'A'
      AND X.NRODIVISAO = 1
    GROUP BY X.SEQFAMILIA
)
```

### B. Exposição da Coluna no Grid (Clareza Visual)
Quando o `ORDER BY` agrupa os dados por Nível 5 (`ORDER BY G.NIVEL_5 ASC, TOTAL_VENDA DESC`), é **obrigatório que a coluna `NIVEL_5` (ou `SUBGRUPO`) também seja selecionada e exibida no grid do relatório**.
- Se a coluna não for exposta, o usuário verá blocos sucessivos de itens ordenados por venda decrescente, mas não saberá onde começa e onde termina cada subcategoria ao rolar a tela.
- Utilize sempre `NVL(CAT.NIVEL_5, 'SEM NIVEL 5')` na montagem da coluna para evitar células vazias caso algum produto não possua a árvore completa cadastrada.

---

## 3. Padrão de Filtro de Lista (`LSx`) para Subcategoria (Nível 5)

Para permitir que o usuário filtre o relatório por uma Subcategoria específica ou visualize todas, o filtro na variável `LSx` (ex: `:LS3`) deve ser construído combinando a tabela virtual `DUAL` e o cadastro ativo da `MAP_CATEGORIA`.

### A. SQL da Lista em `Var - F7`
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
> [!IMPORTANT]
> **Regra do `ORDER BY 1` invisível do Consinco:** A interface da *Consulta Criação* injeta automaticamente o trecho `ORDER BY 1` no final das queries de variável do tipo Lista (`LS`). Nunca deixe a palavra `UNION` ou um `ORDER BY` manual no final do script da lista, caso contrário o sistema gerará o erro `ORA-00928: missing SELECT keyword`. Ao deixar a query sem ordenação explícita, o Consinco aplica `ORDER BY 1`, colocando `0 - TODOS` perfeitamente no topo da combobox.

### B. Consumo do Filtro na Query Principal
Na cláusula `WHERE` da CTE de produtos ou da query base, o filtro deve aceitar tanto a sentinela `'0 - TODOS'` quanto a seleção individual de forma insensível a maiúsculas/minúsculas e espaços:
```sql
AND (
    NVL(TRIM(:LS3), 'TODOS') IN ('TODOS', '0 - TODOS', '0', '')
    OR INSTR(TRIM(:LS3), 'TODOS') > 0
    OR UPPER(TRIM(CAT.NIVEL_5)) = UPPER(TRIM(:LS3))
)
```

---

## 4. Padrão de Condensação de Cabeçalho (Economia de Colunas via `UNION ALL`)

Quando um relatório possui parâmetros gerais ou variáveis de contexto que se repetiriam em **todas as linhas** da consulta (ex: Número da Loja, Dias de Período, Fornecedor Principal ou Período), a exibição em colunas separadas desperdiça espaço visual valioso no grid da *Consulta Criação*.

Adotamos a abordagem padronizada de **Condensação na 1ª Linha** (originada em `impressao_pedidos_grade_loja.sql` e estendida para relatórios ABC/Rankings), que converte colunas de contexto em um **banner/cabeçalho único** na linha inicial (`ORDEM = 0`).

### Estrutura da Arquitetura

1. **CTE dos Itens (`LINHAS_ITENS`):**
   Contém os dados reais do relatório. Recebe uma coluna interna `1 AS ORDEM` e agrega/seleciona as colunas repetitivas internamente.
   > [!IMPORTANT]
   > **Compatibilidade de Tipos no `UNION ALL`:** Como as colunas de ID (ex: `A.SEQPRODUTO`) receberão strings informativas (ex: `'DIAS: 4'`) na linha inicial do cabeçalho, converta a coluna de código em string na CTE `LINHAS_ITENS` usando `TO_CHAR(A.SEQPRODUTO) AS COD_PROD`.
2. **CTE da Linha de Cabeçalho (`LINHA_CABECALHO`):**
   Lê diretamente de `LINHAS_ITENS`, constrói uma linha sentinela com `0 AS ORDEM`, e **distribui inteligentemente** os valores de contexto nas 3 primeiras colunas visíveis do grid (`SUBGRUPO`, `COD_PROD` e `PRODUTO`), evitando que o texto fique encavalado em apenas uma célula:
   - Em `SUBGRUPO` (1ª coluna visível): `'LOJA: ' || NVL(TO_CHAR(MAX(LOJA)), '0')`
   - Em `COD_PROD` (2ª coluna visível): `'DIAS: ' || NVL(TO_CHAR(MAX(DIAS)), '0')`
   - Em `PRODUTO` (3ª coluna visível): `'> FORN: ' || NVL(MAX(TITULO_FORNECEDOR), 'VÁRIOS / TODOS') || ' >'`
   
   As demais colunas numéricas/textuais de exibição recebem espaços em branco (`' '`) ou identificadores de separação (`'___________'`).
3. **`SELECT` Final (Eliminação das Colunas Repetitivas):**
   O `SELECT` externo une as duas CTEs via `UNION ALL`, selecionando **apenas** as colunas finais de dados e omitindo as colunas repetitivas brutas.

```sql
WITH LINHAS_ITENS AS (
    SELECT /*+ MATERIALIZE */
        1 AS ORDEM,
        MAX(NVL(VF.QTD_VENDIDA_TOTAL, 0)) AS QTD_VDA_NUM,
        TO_NUMBER(:NR1) AS LOJA,
        DIAS,
        TITULO_FORNECEDOR,
        SUB.SUBGRUPO AS SUBGRUPO,
        TO_CHAR(A.SEQPRODUTO) AS COD_PROD, -- Convertido para VARCHAR2 para compatibilidade com o cabeçalho
        SUBSTR(A.DESCCOMPLETA, 1, 55) AS PRODUTO,
        '  ' || TO_CHAR(MAX(FD.PADRAOEMBCOMPRA)) AS EMB
        ...
),
LINHA_CABECALHO AS (
    SELECT /*+ MATERIALIZE */
        0 AS ORDEM,
        999999999 AS QTD_VDA_NUM, -- Garante topo em qualquer ordenação por quantidade
        0 AS LOJA,
        0 AS DIAS,
        ' ' AS TITULO_FORNECEDOR,
        'LOJA: ' || NVL(TO_CHAR(MAX(LOJA)), '0') AS SUBGRUPO,
        'DIAS: ' || NVL(TO_CHAR(MAX(DIAS)), '0') AS COD_PROD,
        '> FORN: ' || NVL(MAX(TITULO_FORNECEDOR), 'VÁRIOS / TODOS') || ' >' AS PRODUTO,
        ' ' AS EMB
        ...
    FROM LINHAS_ITENS
)
SELECT
    SUBGRUPO, COD_PROD, PRODUTO, EMB ... -- Colunas brutas LOJA, DIAS e TITULO_FORNECEDOR omitidas do grid!
FROM (
    SELECT * FROM LINHA_CABECALHO
    UNION ALL
    SELECT * FROM LINHAS_ITENS
)
ORDER BY
    ORDEM ASC,
    SUBGRUPO ASC,
    QTD_VDA_NUM DESC,
    PRODUTO ASC,
    COD_PROD ASC
```

---

## 5. Checklist de Aplicação em Consultas Consinco
- [ ] Colunas formatadas com `TO_CHAR` ou espaços **não** foram usadas como critério em `ORDER BY ... DESC` sem conversão ou agregação numérica pura.
- [ ] Em empates de venda ou estoque, foram incluídos critérios determinísticos auxiliares no `ORDER BY` (ex: `DESCCOMPLETA ASC, SEQPRODUTO ASC`).
- [ ] Subconsultas de agregação de categoria possuem o hint `/*+ MATERIALIZE */` e estão livres de comentários (`--` ou `/* */`).
- [ ] A coluna de Nível 5 está visível no grid (`SELECT`) sempre que utilizada como primeiro critério de ordenação (`ORDER BY 1º`).
- [ ] Colunas repetitivas globais (Loja, Dias, Fornecedor de filtro) foram condensadas em linha de cabeçalho (`ORDEM = 0`) para economizar colunas no grid final.
- [ ] O filtro de variável `:LSx` foi documentado e possui registro correspondente na pasta `Aplicativos/gerenciamento_sql/Var-F7/`.
