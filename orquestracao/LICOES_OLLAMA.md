# 🧠 Memória de Aprendizado Contínuo — IA Local (Ollama)

- **Total de Tarefas Executadas pelo Ollama**: `1`
- **Total de Lições Ensinadas pela IA Online**: `6`
- **Última Atualização**: `17/11/2026 18:14:54`

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

### 📌 Lição #5 — Categoria: `SQL` (2026-11-17 17:49:20)
- **Erro Identificado na Revisão**: Lentidao de minutos em MFLV_BASEDFITEM por segundo scan em CTE materializada e divergencia entre valor bruto de itens da NF de devolucao e valor liquido do boleto
- **Regra Definitiva Aprendida**: **Em devolucoes (MLFV_BASENFE + MFLV_BASEDFITEM, CGO 802/860), faca um unico scan em MFLV_BASEDFITEM com TIPNOTAFISCAL = S, CODGERALOPER e DTAEMISSAO explicitos no WHERE, incluindo o LISTAGG com MAP_PRODUTO no mesmo bloco e isolando GE_REDEPESSOA em CTE pre-agrupada. Concilie o valor bruto com descontos de contrato (VLRDESCCONTRATODEV/VLROPCONTRATODESC), valor liquido (N.VLRTOTAL), boleto (MRL_TITULOFIN.VLRORIGINAL) e status A/Q (FI_TITULO.ABERTOQUITADO).**
- ❌ **Como NÃO fazer**: `CTE PRODUTOS_NF separada lendo MFLV_BASEDFITEM sem WHERE e somando apenas I.VLRITEM sem descontos/boleto`
- ✅ **Como FAZER**: `Scan unico em DADOS_NF com I.TIPNOTAFISCAL = S + CTEs BOLETOS_NF (MRL_TITULOFIN) e FINANCEIRO_NF (FI_TITULO)`

### 📌 Lição #6 — Categoria: `SQL` (2026-11-17 18:14:54)
- **Erro Identificado na Revisão**: ORA-01489: result of string concatenation is too long no LISTAGG de produtos e falso desconto informativo em VLRDESCCONTRATODEV/VLRTOTICMSDESONERADO quando NF e boleto nao tem abatimento
- **Regra Definitiva Aprendida**: **1) Para blindar LISTAGG contra ORA-01489 (limite de 4000 bytes do VARCHAR2 no Oracle) em NFs com muitos itens, numere os itens com ROW_NUMBER() OVER (PARTITION BY NROEMPRESA, SEQNF, TIPNOTAFISCAL ORDER BY SEQPRODUTO) AS RN_ITEM em ITENS_BASE e limite o LISTAGG (CASE WHEN RN_ITEM <= 45 THEN SUBSTR(DESCCOMPLETA, 1, 55) END), mantendo SUM(VLRITEM) sobre 100% dos itens. 2) Apure VALOR_DESCONTO_ACORDO_NF apenas quando houver reducao real entre VALOR_TOTAL_COM_IMPOSTOS e VALOR_DO_BOLETO ou VALOR_LIQUIDO_NF (N.VLRTOTAL), ignorando valores meramente informativos em VLRDESCCONTRATODEV quando VALOR_TOTAL_COM_IMPOSTOS = VALOR_LIQUIDO_NF = VALOR_DO_BOLETO.**
- ❌ **Como NÃO fazer**: `LISTAGG(P.DESCCOMPLETA, ' / ') sem limite de itens e soma cega de VLRDESCCONTRATODEV`
- ✅ **Como FAZER**: `LISTAGG(CASE WHEN B.RN_ITEM <= 45 THEN SUBSTR(B.DESCCOMPLETA, 1, 55) END, ' / ') e desconto apurado pela diferenca real (VALOR_TOTAL_COM_IMPOSTOS_NUM - VALOR_BOLETO_NUM / VALOR_LIQUIDO_NF_NUM)`
