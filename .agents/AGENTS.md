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

---

# Regras para Automação de Interface Gráfica (GUI), OCR e PyInstaller no ERP Consinco

Ao criar automações desktop ou protótipos em Python para interagir visualmente com as telas do ERP Consinco:
1. **Consulte a Skill de Automação GUI Consinco:** Sempre leia e aplique os padrões descritos em `c:\Users\usr\Downloads\Equipes_Agentes\.agents\skills\automacao_gui_consinco\SKILL.md`.
2. **PyInstaller com RapidOCR:** É obrigatório usar `collect_submodules('rapidocr_onnxruntime')` além de `collect_data_files` nos arquivos `.spec` para evitar `AttributeError: module 'ch_ppocr_v3_det' has no attribute 'TextDetector'`.
3. **Mecânica de Rolagem no Consinco (Seta para Baixo):** Mapeie as `N` linhas visíveis iniciais (`step 0 até N-1`). A partir da `N`-ésima linha (`step >= N`), fixe a ancoragem de leitura e clique na coordenada `Y` da última linha visível, pois o foco permanece travado e os registros sobem na tabela.
4. **Isolamento de Coluna OCR via Recorte Assimetricamente Estreito:** Em colunas adjacentes a datas (ex: Valor ao lado de Vencimento), recorte caixas estreitas à direita (`[x - 20, y - 10, x + 65, y + 10]`) para impedir a captura acidental de anos (`2026`).

---

# Permissões e Autonomia no Workspace `Equipes_Agentes`

- **Acesso Total e Sem Bloqueio:** O agente possui **acesso total** e **permissão contínua irrestrita** em todos os diretórios e arquivos dentro da pasta `Equipes_Agentes`.
- **Execução Direta Sem Solicitar Confirmação:** Não é necessário solicitar aprovações ou confirmações prévias para ler, criar, editar arquivos, refatorar código ou executar scripts/comandos no terminal dentro de `Equipes_Agentes`. O agente deve agir com total autonomia e proatividade.

