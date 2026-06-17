# Aprendizado: Filtros de Categoria e Erros de Conversão (SQL Consinco)

Este documento registra as lições aprendidas durante a criação de consultas de Bazar e Livraria no ERP Totvs Consinco, focando em evitar resultados vazios e erros de execução.

## 1. Problemas de Resultados Vazios (Hierarquia)
*   **Sintoma:** A consulta não retorna nenhuma linha mesmo com o Mix ativo.
*   **Causa:** Restrição excessiva no nível de hierarquia (`NIVELHIERARQUIA = 1`).
*   **Solução:** 
    *   Remover a trava de nível 1 se não for estritamente necessário.
    *   Usar `LIKE '%TERMO%'` em vez de `= 'TERMO'`.
    *   Verificar se o departamento é **singular ou plural** (ex: `NAO ALIMENTO` vs `NAO ALIMENTOS`).
*   **Exemplo:** Bazar e Livraria na base Baklizi estão no **Nível 2**, enquanto "Não Alimento" está no Nível 1.

## 2. Erro ORA-01722 (Invalid Number)
*   **Sintoma:** Ocorre erro ao tentar concatenar campos ou no processamento dos JOINs.
*   **Causa:** Conversao implicita do Oracle entre `NUMBER` e `VARCHAR2` que falha em ambientes Client do Consinco ao processar valores NULL ou tabelas com tipos mistos.
*   **Solução:**
    *   Evitar concatenações complexas como `TABELA.DSC || ' ' || TABELA.QTD`.
    *   Se necessário, usar `TO_CHAR(CAMPO_NUMERICO)` explicitamente.
    *   Simplificar a consulta removendo JOINS de embalagem (`MAP_FAMEMBALAGEM`) se a informação já existir textualmente na `MAP_FAMDIVISAO`.

## 3. Padrões Encontrados na Rede
*   **NRODIVISAO:** O padrão para comercial é `1`.
*   **FINALIDADEFAMILIA:** Usar sempre `'R'` (Revenda) para filtrar itens comerciais.
*   **Categorias Chave:**
    *   `LIVRARIA`: Contém material escolar.
    *   `NAO ALIMENTO`: Departamento Master (Nível 1).
    *   `BAZAR`: Subcategoria (Nível 2).

## 4. Estrutura de Consulta Segura (Exemplo Final)
```sql
SELECT 
    C.CATEGORIA, 
    A.DESCCOMPLETA, 
    Y.ESTQLOJA
FROM MAP_PRODUTO A
INNER JOIN MRL_PRODUTOEMPRESA Y ON A.SEQPRODUTO = Y.SEQPRODUTO
INNER JOIN MAP_FAMDIVCATEG FDC ON FDC.SEQFAMILIA = A.SEQFAMILIA AND FDC.NRODIVISAO = 1
INNER JOIN MAP_CATEGORIA C ON C.SEQCATEGORIA = FDC.SEQCATEGORIA AND C.NRODIVISAO = 1
WHERE Y.STATUSCOMPRA = 'A'
  AND Y.NROEMPRESA IN (3, 15, 50)
  AND UPPER(C.CATEGORIA) LIKE '%LIVRARIA%'
```

## 5. Ligações de Categorias Duplicadas (Árvores Hierárquicas)
*   **Sintoma:** Um produto (como Coca-Cola ou Água) retorna múltiplas linhas no mesmo nível (ex: mostrando `A CLASSIFICAR` no Nível 1 junto com `BEBIDAS`).
*   **Causa:** O ERP Consinco mantém múltiplas árvores hierárquicas ativas simultaneamente na tabela `MAP_FAMDIVCATEG` (comercial/mercadológica, logística, fiscal, etc.). Se não for filtrado o tipo de categoria, a consulta trará todas as árvores (e as árvores não configuradas retornam para o padrão do sistema `A CLASSIFICAR`).
*   **Solução:**
    *   Filtrar sempre por tipo de categoria comercial (Mercadológica) usando `MAP_CATEGORIA.TIPCATEGORIA = 'M'`.
    *   Filtrar por associação ativa usando `MAP_FAMDIVCATEG.STATUS = 'A'`.
    *   Para expurgar o departamento de `ALMOXARIFADO` sem excluir produtos duplo-categorizados (comerciais que também possuem ligação com o almoxarifado), a cláusula `NOT EXISTS` deve garantir que o produto seja excluído apenas se a sua única associação de nível 1 for o `ALMOXARIFADO`.
*   **Exemplo de Exclusão Robusta de Almoxarifado:**
    ```sql
    AND NOT EXISTS (
          SELECT 1
            FROM MAP_FAMDIVCATEG XF
            JOIN MAP_CATEGORIA YF ON XF.SEQCATEGORIA = YF.SEQCATEGORIA
           WHERE XF.SEQFAMILIA = A.SEQFAMILIA
             AND YF.NIVELHIERARQUIA = 1
             AND UPPER(YF.CATEGORIA) = 'ALMOXARIFADO'
             AND NOT EXISTS (
                   SELECT 1
                     FROM MAP_FAMDIVCATEG XF2
                     JOIN MAP_CATEGORIA YF2 ON XF2.SEQCATEGORIA = YF2.SEQCATEGORIA
                    WHERE XF2.SEQFAMILIA = A.SEQFAMILIA
                      AND YF2.NIVELHIERARQUIA = 1
                      AND UPPER(YF2.CATEGORIA) <> 'ALMOXARIFADO'
               )
      )
    ```
