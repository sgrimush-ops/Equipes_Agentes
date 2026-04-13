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
