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

5. **Proibição de Operadores Aritméticos Externos a Blocos `CASE` (Prevenção de `ORA-00936`):**
   Nunca envolva uma expressão `CASE` com parênteses para aplicar operações matemáticas fora dela (ex: `( CASE WHEN ... END ) - NVL(...)`). O parser do Consinco interpreta o `)` após o `END` como encerramento do `CASE` e acusa erro de sintaxe no `-` antes do `ELSE`. **Aplique sempre a aritmética internamente em cada ramo `THEN` e `ELSE`.**

6. **Alinhamento Rigoroso 1-para-1 em `UNION` e `UNION ALL` (Prevenção de `ORA-01790`):**
   Todos os blocos de um `UNION` ou `UNION ALL` (como dados principais vs `TOTAL GERAL ->`) devem possuir a **exata mesma quantidade de colunas**, a **mesma ordem posicional** e os **mesmos tipos de dados**. Colunas de ordenação interna devem ser espelhadas em todos os blocos do `UNION`.

7. **Filtros Multi-Valores em Binds (`:LT3`) via `INSTR` (Evitar Falhas de Bind Delphi):**
   Nunca utilize subconsultas com `CONNECT BY` em CTEs materializadas para separar strings com vírgula. Utilize sempre a busca nativa por delimitadores:
   `INSTR(',' || UPPER(REPLACE(:LT3, ' ', '')) || ',', ',' || UPPER(TRIM(COLUNA)) || ',') > 0`.

8. **Compatibilidade Estrita com as Variáveis da Tela (`Var - F7`):**
   O SQL não deve depender de macros `#LTx` que não estejam cadastradas no formulário da tela atual. Se as macros de loja ou status não existirem no `Var - F7`, use os valores fixos no código (`IN (1,2...18,50,900)` e `NOT IN (2)`) para evitar que a substituição vazia resulte em `IN ()` e `ORA-00936`.

9. **Limite Rígido de 145 Caracteres para SQL da Lista (`Var - F7` / `LSx`):**
   O campo de cadastro da instrução SQL da lista de seleção (`LS1`, `LS2`, etc.) na tela `Var - F7` do Consinco possui limite físico restrito. O script da lista **nunca pode ultrapassar 145 caracteres (incluindo espaços e quebras)**. Construa queries de listas extremamente enxutas e em uma única linha.

10. **Padrão Obrigatório de Vendas Rápidas via `MRL_CUSTODIA`:**
    Para apuração de vendas consolidadas e faturamento por período e loja (Rankings, Giro, Curva ABC), **nunca varra documentos fiscais item a item** (`MLFV_BASENFE` + `MFLV_BASEDFITEM` ou `MFL_DFITEM`). Use obrigatoriamente a tabela analítica oficial **`MRL_CUSTODIA`** (`VLRTOTALVDA` para valor financeiro e `QTDVDA` para quantidade) filtrando por `DTAENTRADASAIDA`. Ao consultar saídas complementares (Devolução `802`, Troca `860`, Incineração `821, 831`), unifique todas as verificações fiscais em **um único scan** com `CASE WHEN CODGERALOPER IN (...)`.

11. **Comparativo de Estoque WMS vs. ERP (Bypass do Bloqueio `LOG0085`):**
    Para inventários e conciliações em tempo real sem travar a tela `LOG0085`, cruze `MRL_PRODUTOEMPRESA` (`ESTQDEPOSITO`) com `MLO_ENDERECO` (`ESPECIEENDERECO = 'A'` apanha, `'P'` pulmão), apurando pendências em trânsito com `MLO_CARGARECPROD` (recebimento não armazenado) e `MLO_CARGAEXPPROD` (separação liberada). Use `FULL OUTER JOIN` em CTE materializada para garantir que produtos com saldo apenas no WMS ou apenas no ERP não sejam omitidos. **`ESTQGERENCIAL` não existe em `MRL_PRODUTOEMPRESA`**; as reservas comerciais são obtidas pela soma `(NVL(QTDRESERVADAVDA,0) + NVL(QTDRESERVADARECEB,0) + NVL(QTDRESERVADAFIXA,0) + NVL(QTDRESERVADAFISC,0))`.

12. **Expurgo Dinâmico Multi-Termos (`LT2`) com Imunidade a Acentos e Espaços:**
    Ao implementar filtros de exclusão/expurgo de categorias ou departamentos onde o usuário digita múltiplos termos separados por vírgula em um bind literal (`LT2`), utilize `REGEXP_LIKE` combinado com `TRANSLATE` para remover acentuação gráfica e `REPLACE` para eliminar espaços:
    `NOT REGEXP_LIKE(REPLACE(TRANSLATE(UPPER(COLUNA), 'ÁÉÍÓÚÀÈÌÒÙÃÕÂÊÎÔÛÇ', 'AEIOUAEIOUAOAEIOUC'), ' ', ''), REPLACE(REPLACE(TRANSLATE(UPPER(TRIM(:LT2)), 'ÁÉÍÓÚÀÈÌÒÙÃÕÂÊÎÔÛÇ', 'AEIOUAEIOUAOAEIOUC'), ' ', ''), ',', '|'), 'i')`.
    Sempre preveja o sentinela `0` / `'NENHUM'` para desativar o expurgo (`NVL(TRIM(:LT2), '0') IN ('0', 'NENHUM', '')`).

---

# Regras para Automação de Interface Gráfica (GUI), OCR e PyInstaller no ERP Consinco

Ao criar automações desktop ou protótipos em Python para interagir visualmente com as telas do ERP Consinco:
1. **Consulte a Skill de Automação GUI Consinco:** Sempre leia e aplique os padrões descritos em `c:\Users\usr\Downloads\Equipes_Agentes\.agents\skills\automacao_gui_consinco\SKILL.md`.
2. **PyInstaller com RapidOCR:** É obrigatório usar `collect_submodules('rapidocr_onnxruntime')` além de `collect_data_files` nos arquivos `.spec` para evitar `AttributeError: module 'ch_ppocr_v3_det' has no attribute 'TextDetector'`.
3. **Mecânica de Rolagem no Consinco (Seta para Baixo):** Mapeie as `N` linhas visíveis iniciais (`step 0 até N-1`). A partir da `N`-ésima linha (`step >= N`), fixe a ancoragem de leitura e clique na coordenada `Y` da última linha visível, pois o foco permanece travado e os registros sobem na tabela.
4. **Isolamento de Coluna OCR via Recorte Assimetricamente Estreito:** Em colunas adjacentes a datas (ex: Valor ao lado de Vencimento), recorte caixas estreitas à direita (`[x - 20, y - 10, x + 65, y + 10]`) para impedir a captura acidental de anos (`2026`).
5. **Ativação Obrigatória com Setas (`Down` -> `Up`) em ComboBox Delphi:** No Consinco, ao abrir um ComboBox embutido no grid (`Alt + Down`), é obrigatório enviar `Down` para que o Delphi registre a alteração de índice (`OnChange`). Se a opção desejada for a primeira (ex: `DP 60`), envie `Up` em seguida para fixar a primeira opção. Nunca saia com `Tab` sem antes ter movimentado as setas, pois o Consinco deixará a célula vazia.
6. **Proibição de `Enter` no Grid / Confirmação via `Tab`:** Para avançar entre as células do grid (`Embalagem` -> `Lastro` -> `Altura` -> `Est. Min.`), utilize estritamente a tecla `Tab`. Nunca envie `Enter`, pois o Delphi pode fechar o grid ou mover para outra linha indesejada.
7. **Limpeza Prévia Obrigatória com Backspace e Delete (Prevenção de `60100`):** Ao dar `Tab` saindo da Embalagem, o Consinco frequentemente preenche o Lastro com o multiplicador da embalagem (`60`). Antes de digitar qualquer número nos campos numéricos, envie `Backspace` (x4) e `Delete` (x4) para limpar o campo antes do `pyautogui.write()`.
8. **Fechamento de Popups Modais em Sequência (`Alt + O`):** Feche popups modais de confirmação com `Alt + O` e sempre verifique com `win32gui` se há uma segunda janela modal de Atenção antes de prosseguir com a navegação de abas.
9. **Varredura Dinâmica e Total do Grid para Identificação de Embalagem:** Em tabelas logísticas do Consinco (*Espécie de Endereço*), a embalagem pode estar explícita na linha `APANHA` e omitida na linha `PULMAO`. Nunca use valores padrão fixos (`DP 60`). Realize uma varredura OCR na faixa do grid com regex `(CX|DP|UN|FD|PCT|PC|CJ|KG|LT)\s*\.?\s*\d+` para garantir que o robô selecione no ComboBox a embalagem real do produto (ex: `CX 120`).

# Regras de Dicionário, Nomes Oficiais e Governança de Dados Consinco

1. **Proibição Absoluta de Nomes Inventados / Informais:**
   Nunca crie tabelas ou estruturas no banco com nomes informais (como `A_PAGAR`, `EAN_DUN`, `PED_PENDENTE`, `RANKING_ABC_PRODUTOS`, `NIVEL_ATENDIMENTO_CDS`). Use sempre as tabelas canônicas oficiais do Totvs Consinco:
   - Títulos / Contas a Pagar: `FI_TITULO`, `FI_TITCOMPRADOR`, `FI_TITOPERACAO`.
   - Códigos de Barras: `MAP_PRODCODIGO`.
   - Pedidos de Suprimento e Transferência: `MSU_PEDIDOSUPRIM`, `MSU_PSITEMRECEBER`, `MSU_PSITEMEXPEDIDO`.
   - Curva ABC e Distribuição: `MBI_TABCDISTRIB`.
   - Estoque e Custos por Loja: `MRL_PRODUTOEMPRESA`, `MRL_CUSTODIA`.
   - Vendas Diárias: `MRL_PRODVENDADIA`.
   - Preços de Venda: `MRL_PRODEMPSEG`.
   - Pontas de Gôndola / Ilhas: `MRL_PONTOEXTRA`, `MRL_PONTOEXTRAPRODUTO`, `MRL_PONTOEXTRAPRODUTOEMPRESA`.
2. **Visualização no Simulador Zona SQL:**
   - Na aba **`📚 Dicionário`**: manter as 7.111 tabelas e 126.636 colunas oficiais para busca e consulta de arquitetura.
   - Na aba **`📁 Tabelas`**: exibir estritamente as tabelas oficiais que possuem dados reais populados (`row_count > 0`), ocultando tabelas vazias e internas.

---

# Regras de Carga e Atualização de Pontas de Gôndola (Mínimo, Máximo e Vigência)

Ao atualizar estoques de pontas de gôndola via planilha:
1. **Chaves Primárias Obrigatórias:** O registro na tabela `MRL_PONTOEXTRAPRODUTOEMPRESA` é unívoco por `(SEQPONTOEXTRA, SEQPRODUTO, NROEMPRESA, SEQVIGENCIA)`.
2. **Garantia de Capa:** Antes de inserir na tabela de empresa, garanta que o vínculo produto x ponta exista na tabela `MRL_PONTOEXTRAPRODUTO` (`STATUS = 'A'`).
3. **Scripts de Carga:** Gerar script `MERGE INTO` ou blocos transacionais `UPDATE / INSERT` finalizando com `COMMIT;`.

---

# Padrões da Integração com o Mentor IA Local (Ollama)

Na Zona SQL e ferramentas de apoio com IA:
1. **Conexão Local:** Utilizar endpoint `http://127.0.0.1:11434` com modelos locais (`hermes3:latest`, `gemma4:latest`).
2. **Parâmetros de Inferência Ágil:** Configurar `num_ctx: 2048`, `num_predict: 400`, `temperature: 0.2` e `timeout: 120` para evitar estouro de tempo em respostas complexas.
3. **Depuração de Erros 1-Clique:** Quando o banco retornar erros `ORA-*` (ex: `ORA-00904`, `ORA-00936`, `ORA-00979`, `ORA-01790`), enviar o SQL e a mensagem para o método `explain_and_fix_error` gerando a explicação didática e o código corrigido sem comentários `--`.

---

# Permissões e Autonomia no Workspace `Equipes_Agentes`

- **Acesso Total e Sem Bloqueio:** O agente possui **acesso total** e **permissão contínua irrestrita** em todos os diretórios e arquivos dentro da pasta `Equipes_Agentes`.
- **Execução Direta Sem Solicitar Confirmação:** Não é necessário solicitar aprovações ou confirmações prévias para ler, criar, editar arquivos, refatorar código ou executar scripts/comandos no terminal dentro de `Equipes_Agentes`. O agente deve agir com total autonomia e proatividade.

