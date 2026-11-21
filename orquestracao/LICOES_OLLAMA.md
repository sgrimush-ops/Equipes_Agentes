# 🧠 Memória de Aprendizado Contínuo — IA Local (Ollama)

- **Total de Tarefas Executadas pelo Ollama**: `8`
- **Total de Lições Ensinadas pela IA Online**: `12`
- **Última Atualização**: `21/11/2026 12:14:32`

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

### 📌 Lição #7 — Categoria: `PYTHON` (2026-11-19 08:25:56)
- **Erro Identificado na Revisão**: Execucao de cmdlets PowerShell diretamente no subprocess.run sem invocar powershell.exe e importacao de win32com.client quando pedido apenas biblioteca padrao
- **Regra Definitiva Aprendida**: **Para rodar cmdlets PowerShell via Python usando apenas biblioteca padrao, invocar sempre ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', script] e parsear JSON via ConvertTo-Json -Compress.**
- ❌ **Como NÃO fazer**: `subprocess.run('Get-CimInstance Win32_PnPSignedDriver')`
- ✅ **Como FAZER**: `subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', 'Get-CimInstance Win32_PnPSignedDriver | ConvertTo-Json -Compress'])`

### 📌 Lição #8 — Categoria: `SQL` (2026-11-19 14:51:38)
- **Erro Identificado na Revisão**: Loop infinito repetindo SELECT ... FROM ( sem construir as CTEs da MRL_CUSTODIA
- **Regra Definitiva Aprendida**: **Sempre escrever o bloco WITH completo com todas as CTEs materializadas e finalizar com o SELECT agrupado, nunca repetir SELECT ... FROM ( em cascata**
- ❌ **Como NÃO fazer**: `SELECT ... FROM ( SELECT ... FROM ( ...`
- ✅ **Como FAZER**: `SELECT * FROM ( WITH CTE_PRODUTOS AS (...), CTE_MESES AS (...) SELECT ... FROM CTE_SERIE_COMPLETA GROUP BY ... )`

### 📌 Lição #9 — Categoria: `PYTHON` (2026-11-19 15:31:20)
- **Erro Identificado na Revisão**: Loop infinito repetindo imports selenium no inicio de consolidar.py
- **Regra Definitiva Aprendida**: **Gerar apenas imports necessarios (pandas, numpy, plotly, pathlib, calendar) e escrever todas as funcoes completas sem repetir imports**
- ❌ **Como NÃO fazer**: `from selenium.webdriver.common.by import By (repetido 50x)`
- ✅ **Como FAZER**: `import calendar, pandas as pd, plotly.graph_objects as go ... def compilar_visao(...):`

### 📌 Lição #10 — Categoria: `PYTHON` (2026-11-21 12:09:43)
- **Erro Identificado na Revisão**: Gerou cercas markdown `python no arquivo .py e entrou em loop infinito de elif content_type repetido sem fechar a funcao
- **Regra Definitiva Aprendida**: **Nunca incluir cercas markdown `python em arquivos .py; usar tuplas/conjuntos para verificar extensoes ou MIME types em vez de repetir elif**
- ❌ **Como NÃO fazer**: ``python ... elif content_type == '...': ... elif content_type == '...':`
- ✅ **Como FAZER**: `EXTENSOES = ('.xls', '.xlsx', '.ods'); if fname.lower().endswith(EXTENSOES): ...`

### 📌 Lição #11 — Categoria: `PYTHON` (2026-11-21 12:12:22)
- **Erro Identificado na Revisão**: Repetiu indefinidamente blocos elif 'E' in segmento / elif 'O' in segmento sem implementar o parser
- **Regra Definitiva Aprendida**: **Usar expressoes regulares (re.search / re.findall) para extrair datas e valores de strings em vez de dividir manualmente com if/elif**
- ❌ **Como NÃO fazer**: `if 'E' in segmento: ... elif 'O' in segmento:`
- ✅ **Como FAZER**: `re.findall(r'(\\d{1,2})[./](\\d{1,2})[./](\\d{2,4})', texto)`

### 📌 Lição #12 — Categoria: `PYTHON` (2026-11-21 12:14:32)
- **Erro Identificado na Revisão**: Usou DataFrame.append() que foi removido no pandas 2.x e referenciou scripts/CSS externos inexistentes no HTML
- **Regra Definitiva Aprendida**: **No pandas 2.x acumular dicionarios em lista e construir pd.DataFrame(lista) no final; em relatorios HTML estaticos embutir CSS e JS inline no proprio arquivo**
- ❌ **Como NÃO fazer**: `df = df.append({...}, ignore_index=True)`
- ✅ **Como FAZER**: `registros.append({...}); df = pd.DataFrame(registros)`
