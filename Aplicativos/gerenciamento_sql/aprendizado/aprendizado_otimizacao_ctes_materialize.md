# Aprendizado Técnico: Otimização com CTEs, Hint /*+ MATERIALIZE */ e Bypass de Validação no Totvs Consinco (Oracle)

## 1. O Problema Histórico e o Erro do "Fallback sem CTE"
Durante a evolução de scripts SQL complexos no ERP Totvs Consinco (em especial relatórios que cruzam Contas a Pagar, Projeção de Pedidos de Compra e Fornecedores), foi identificada a prática nociva de criar scripts de **"Fallback" sem o uso de CTEs (`WITH ... AS`)** (ex: `_fallback.sql`).

### Por que isso acontecia?
O módulo **Consulta Criação / SGI Client** do Totvs Consinco possui um validador de interface arcaico que exige estritamente que a **primeira palavra** do script executado seja `SELECT`. 
Quando um desenvolvedor ou uma IA tentava estruturar a consulta utilizando CTEs iniciando o script com a palavra `WITH`, a tela rejeitava a execução com o erro:
> *"A instrução SQL informada, não é uma consulta"*

Como alternativa incorreta (Anti-Pattern), abandonavam o uso de `WITH` e reescreviam o SQL com subconsultas inline repetitivas.

---

## 2. O Impacto Catastrófico na Performance (Por que NÃO fazer Fallback sem CTE)
Ao remover as CTEs para tentar agradar o validador da tela, o script incorria em três problemas graves no Oracle:

1. **Leitura Múltipla de Views Pesadas sem Cache de RAM:**
   No Consinco, objetos que iniciam com `MACV_`, `MAXV_`, `MRLV_` ou `FIV_` não são tabelas simples, mas sim **VIEWS transacionais complexas** (que realizam dezenas de joins internos). 
   Sem uma CTE materializada, se você fizer referência à view `MACV_PSITEMRECEBER` 3 vezes na consulta (ex: no `UNION ALL`, num `LEFT JOIN` de contagem e numa subquery correlacionada), o Oracle executará toda a lógica da view **3 vezes do zero**, multiplicando exponencialmente o tempo de processamento e causando *Timeout*.

2. **Loops em Subconsultas Correlacionadas na Cláusula WHERE:**
   Para buscar o "item mais frequente" (como o Comprador Principal ou Moda de Compras de um Fornecedor), é um erro grave fazer loops correlacionados como:
   ```sql
   -- PROIBIDO: Subconsulta em loop que varre a tabela repetidamente para cada linha
   WHERE Z.QTD = (
       SELECT MAX(W.QTD)
       FROM (
           SELECT B2.SEQCOMPRADOR, COUNT(1) AS QTD
           FROM MACV_PSITEMRECEBER B2
           WHERE B2.SEQFORNECEDOR = Z.SEQFORNECEDOR -- Correlação que destrói a performance
           GROUP BY B2.SEQCOMPRADOR
       ) W
   )
   ```

---

## 3. Padrão Ouro Operacional (A Solução Obrigatória para IAs e Desenvolvedores)

Para garantir **máxima velocidade no Oracle** e, ao mesmo tempo, **passar 100% pelo validador do Consinco sem erros**, toda IA ou desenvolvedor deve seguir estritamente a arquitetura abaixo em consultas complexas:

### Regra 1: O Bypass do Validador (SELECT Fantasma) e Variáveis Bind
O validador do Consinco bloqueia qualquer consulta que não comece com a palavra `SELECT` (erro *"A instrução SQL informada, não é uma consulta"*). Nunca abandone o uso de `WITH`. Para contornar esse erro, **envelope toda a consulta CTE dentro de um SELECT externo simples**:
```sql
SELECT * FROM (
    WITH ...
    SELECT ...
)
```
**Importante sobre Variáveis:** Ao utilizar variáveis de lista de seleção em funções de manipulação de texto (como `SUBSTR` e `INSTR`), utilize **sempre variáveis bind iniciadas com dois-pontos** (ex: `:LS1`) em vez de macros iniciadas com hash (`#LS1`). Macros com hash são substituídas literalmente no texto antes da execução; se o valor for inserido sem aspas, o Oracle dispara o erro fatal **`ORA-00907: missing right parenthesis`**.

### Regra 2: Obrigatoriedade do Hint `/*+ MATERIALIZE */`
Em todas as CTEs que lerem Views do Consinco (`MACV_`, `MAXV_`, `MRLV_`, etc.) ou tabelas de alto volume (`MRL_PRODUTOEMPRESA`, `FI_TITULO`, `MAC_PSITEMRECEBER`), insira obrigatoriamente a instrução `/*+ MATERIALIZE */` logo após o `SELECT` da CTE.
Isso força o otimizador do Oracle a criar uma tabela temporária em memória RAM (Temporary Tablespace) na primeira leitura, respondendo aos joins seguintes em frações de segundo.
```sql
WITH MINHA_CTE_OTIMIZADA AS (
    SELECT /*+ MATERIALIZE */
        A.SEQFORNECEDOR,
        SUM(A.VLRTOTAL) AS TOTAL
    FROM MACV_PSITEMRECEBER A
    WHERE ...
    GROUP BY A.SEQFORNECEDOR
)
```

### Regra 3: Substituir Subqueries Correlacionadas por Funções Analíticas
Para encontrar o maior valor, o primeiro registro ou a moda de um grupo sem fazer subconsultas correlacionadas em loop, utilize a função analítica `ROW_NUMBER() OVER` ou `RANK() OVER` dentro da CTE materializada:
```sql
WITH COMPRADOR_SUGERIDO AS (
    SELECT /*+ MATERIALIZE */
        SEQFORNECEDOR,
        SEQCOMPRADOR AS SEQCOMPRADOR_SUGERIDO
    FROM (
        SELECT
            B.SEQFORNECEDOR,
            B.SEQCOMPRADOR,
            ROW_NUMBER() OVER (PARTITION BY B.SEQFORNECEDOR ORDER BY COUNT(1) DESC) AS RN
        FROM MACV_PSITEMRECEBER B
        WHERE B.TIPPEDIDOSUPRIM = 'C'
          AND NVL(B.STATUSITEM, 'A') != 'C'
          AND NVL(B.SEQCOMPRADOR, 0) <> 1
        GROUP BY B.SEQFORNECEDOR, B.SEQCOMPRADOR
    )
    WHERE RN = 1
)
```

---

## 4. Comparativo Arquitetural: Antes vs. Depois

| Critério | Anti-Pattern (Versão Fallback sem CTE) | Padrão Ouro Otimizado (Com CTE e Bypass) |
| :--- | :--- | :--- |
| **Aceitação no Consinco** | Passa (começa com SELECT) | **Passa perfeitamente** (SELECT Fantasma externo) |
| **Leitura de Views Pesadas** | 3 ou mais varreduras completas no disco | **1 única varredura**, gravada em RAM via `/*+ MATERIALIZE */` |
| **Subqueries de Agrupamento** | Executadas em loop para cada registro (Nested Loop) | **Resolvidas em conjunto único** (Hash Join / Window Function) |
| **Tempo de Resposta** | Risco alto de lentidão severa ou Timeout (ORA-01013) | **Execução ultra-rápida (milissegundos a poucos segundos)** |
| **Comentários no SQL** | Zero comentários | **Zero comentários** (obrigatório para evitar quebra no SGI) |
| **Variáveis Bind em Funções/Tipos** | Erro `ORA-00907` ou `ORA-00932` por tipo incompatível | **Sem erros**, usando bind `:LS1` e `TO_NUMBER(:NR1)` |

## 5. Diretriz Imutável para Agentes de IA
Quando solicitado a criar, otimizar ou corrigir consultas SQL no ERP Consinco:
1. **NUNCA** sugira ou crie arquivos com sufixo `_fallback` que abram mão do uso de CTEs.
2. **SEMPRE** analise se a consulta acessa views ou repete a leitura da mesma tabela em múltiplos `JOIN` ou `UNION ALL`. Se repetir, isole em CTE com `/*+ MATERIALIZE */`.
3. **SEMPRE** aplique o envelope `SELECT * FROM ( WITH ... SELECT ... )` quando houver CTEs para passar no validador *"não é uma consulta"*.
4. **SEMPRE** prefira variáveis bind com dois-pontos (`:LS1`, `:NR1`) a macros com hash (`#LS1`), principalmente dentro de funções como `SUBSTR` e `INSTR`, para evitar erros de sintaxe `ORA-00907` na substituição literal do Consinco.
5. **SEMPRE** aplique conversão explícita `TO_NUMBER(:NR1)` ao comparar variáveis bind com colunas numéricas do Oracle (ex: `SEQPESSOA = TO_NUMBER(:NR1)`) ou em blocos `CASE WHEN`, evitando o erro **`ORA-00932: inconsistent datatypes: expected CHAR got NUMBER`**.
