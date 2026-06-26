# Regras de Performance e Padrões para SQL Consinco / Oracle

Ao criar ou refatorar scripts SQL focados no ERP Totvs Consinco (Banco Oracle), os agentes devem obrigatoriamente seguir estas regras de performance para evitar timeout no processamento e travas do validador interno do SGI/Consinco:

1. **Evitar Loops com `OR EXISTS` ou `NOT EXISTS` em blocos de repetição:** 
   Se uma lógica de busca ou filtro (como encontrar o Fornecedor Principal de um produto) se repete em múltiplas subconsultas (ex: em blocos de `UNION ALL`), **nunca** deixe o banco recalcular isso múltiplas vezes. Isole a lógica em uma CTE (`WITH ... AS`).

2. **Obrigatoriedade do Hint `/*+ MATERIALIZE */`:** 
   Sempre que isolar blocos pesados ou tabelas transacionais em uma CTE (`WITH`), insira a instrução `/*+ MATERIALIZE */` logo após o `SELECT`. Isso força o banco Oracle a salvar o resultado na memória RAM (Temporary Tablespace) antes de realizar os joins principais, evitando lentidão catastrófica.
   - *Exemplo*: `WITH PRODUTOS AS (SELECT /*+ MATERIALIZE */ A.SEQPRODUTO ... )`

3. **Bypass do Validador "Não é uma consulta" (Erro de CTE):** 
   O módulo de Consulta Criação do Totvs Consinco possui um validador arcaico que exige que a mesmíssima primeira palavra do código seja `SELECT`. Se a query começar com `WITH`, ele emitirá o erro *"A instrução SQL informada, não é uma consulta"*. 
   - **Solução Obrigatória:** Para usar CTEs e ao mesmo tempo passar pelo validador, você deve envelopar a query inteira com um `SELECT` fantasma externo.
   - *Estrutura Correta*:
     ```sql
     SELECT * FROM (
         WITH CTE_EXEMPLO AS (
             SELECT /*+ MATERIALIZE */ ...
         )
         SELECT ...
         FROM ...
     )
     ```

4. **Proibição Absoluta de Comentários no Código SQL:**
   O parser/validador do Totvs Consinco remove quebras de linha em alguns cenários e tenta executar a query em uma única string de texto. Se houver qualquer comentário no estilo `-- comentário` ou `/* comentário */` inserido no meio do script, o Consinco transformará o restante do código válido em um comentário gigantesco, resultando em erro fatal (`missing expression`, etc). **NUNCA comente dentro dos arquivos SQL!**
