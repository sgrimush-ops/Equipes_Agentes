# 🧠 Memória de Aprendizado Contínuo — IA Local (Ollama)

- **Total de Tarefas Executadas pelo Ollama**: `1`
- **Total de Lições Ensinadas pela IA Online**: `4`
- **Última Atualização**: `13/11/2026 17:53:29`

> Este arquivo é sincronizado automaticamente pelo `executor_ollama.py`. Toda lição registrada aqui é injetada no prompt de sistema do Ollama para evitar que erros corrigidos pela IA Online se repitam.

---

### 📌 Lição #1 — Categoria: `SQL` (2026-11-13 17:50:00)
- **Erro Identificado na Revisão**: Uso de comentários '--' no código SQL que quebram o parser de linha única do Totvs Consinco.
- **Regra Definitiva Aprendida**: **Proibição absoluta de '--' em qualquer ponto do arquivo .sql. O único comentário permitido é o hint /*+ MATERIALIZE */.**
- ❌ **Como NÃO fazer**: `-- Filtro de loja
WHERE NROEMPRESA = 1`
- ✅ **Como FAZER**: `WHERE NROEMPRESA = 1`

### 📌 Lição #2 — Categoria: `SQL` (2026-11-13 17:50:00)
- **Erro Identificado na Revisão**: Query começando diretamente com WITH causa o erro 'A instrução SQL informada, não é uma consulta' no Consinco.
- **Regra Definitiva Aprendida**: **Sempre envelopar queries que usam CTE (WITH) dentro de um SELECT * FROM ( WITH CTE AS (SELECT /*+ MATERIALIZE */ ...) SELECT ... ).**
- ❌ **Como NÃO fazer**: `WITH BASE AS (SELECT SEQPRODUTO FROM MAP_PRODUTO) SELECT * FROM BASE`
- ✅ **Como FAZER**: `SELECT * FROM (
    WITH BASE AS (
        SELECT /*+ MATERIALIZE */ SEQPRODUTO FROM CONSINCO.MAP_PRODUTO
    )
    SELECT * FROM BASE
)`

### 📌 Lição #3 — Categoria: `VAR_F7` (2026-11-13 17:50:00)
- **Erro Identificado na Revisão**: SQL da Lista (LS1/LS2) maior que 145 caracteres ou usando SYS.ODCIVARCHAR2LIST (que trunca em 3 letras no Delphi).
- **Regra Definitiva Aprendida**: **Manter SQL da lista abaixo de 145 caracteres em linha única e usar DECODE(LEVEL,...) FROM DUAL CONNECT BY LEVEL<=N para opções fixas.**
- ❌ **Como NÃO fazer**: `SELECT COLUMN_VALUE FROM TABLE(SYS.ODCIVARCHAR2LIST('TODOS', 'ATIVOS'))`
- ✅ **Como FAZER**: `SELECT DECODE(LEVEL,1,'TODOS',2,'ATIVOS') FROM DUAL CONNECT BY LEVEL<=2`

### 📌 Lição #4 — Categoria: `SQL` (2026-11-13 17:53:29)
- **Erro Identificado na Revisão**: Usou 'AS' para alias de subconsulta/tabela (FROM (...) AS CTE_VENDAS) e ponto-e-vírgula (;) no final, gerando ORA-00933 e ORA-00911 no Oracle/Consinco.
- **Regra Definitiva Aprendida**: **No Oracle nunca use 'AS' antes de alias de tabela ou subconsulta (apenas em colunas) e nunca coloque ';' no final da query da Consulta Criação.**
- ❌ **Como NÃO fazer**: `FROM (...) AS CTE_VENDAS;`
- ✅ **Como FAZER**: `FROM (...) CTE_VENDAS`
