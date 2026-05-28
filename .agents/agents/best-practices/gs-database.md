---
id: gs-database
name: "Gestão Segura de Bancos de Dados em Google Sheets"
whenToUse: >
  - Quando um agente precisa manipular planilhas do Google como se fossem um banco de dados (CRUD).
  - Em projetos que utilizam Google Apps Script como Web App (Wiki Interna, Controle de Estoque, Gestão de Usuários).
  - Quando se trabalha com sincronização de dados entre locais (Python) e nuvem (GSheets).
  - NOT for: Análises de dados ad-hoc puras via Pandas (use `data-analysis` para isso).
version: "1.1.0"
---

# Gestão Segura de Bancos de Dados em Google Sheets

Manipular o Google Sheets como um banco de dados exige um rigor adicional em comparação a bancos relacionais (SQL), pois a flexibilidade da planilha permite erros que um SGBD impediria nativamente (como mudar a ordem das colunas ou limpar uma tabela inteira sem querer).

## Core Principles

1. **Protocolo Append-Only por Padrão**  
   Sempre prefira adicionar linhas ao final da tabela em vez de tentar sobrescrever áreas existentes. O comando `appendRow()` no Apps Script é atômico e significativamente mais seguro do que `setValues()` em intervalos calculados manualmente. Se um dado precisa ser atualizado, a busca pela linha deve preceder a escrita, minimizando o risco de desalinhamento.

2. **Resolução de Colunas por Nome (Mapeamento Dinâmico)**  
   Nunca assuma que a coluna "Status" será sempre a coluna 5. Colete os cabeçalhos na inicialização de cada função e use um utilitário para converter o nome da coluna no seu índice numérico atual. Isso torna o sistema resiliente a usuários que inserem novas colunas no meio da planilha.

3. **Política de "No Clear" (Proibição de Deleção cega)**  
   É terminantemente proibido o uso de `clear()`, `clearContents()` ou `deleteRows()` em intervalos que contenham dados críticos sem um mecanismo de confirmação ou backup prévio. Se uma tabela precisa ser "limpa" para uma nova sincronização, o agente deve primeiro verificar se os novos dados são válidos (length > 0) para não deixar a tabela vazia em caso de falha no novo dataset.

4. **Validação de Esquema (Schema Enforcement)**  
   Antes de qualquer escrita, valide se os cabeçalhos obrigatórios existem. Se um script esperar gravar na coluna `J` mas o cabeçalho dessa coluna for diferente do esperado (`SOLUCAO`), a operação deve ser abortada e um erro reportado ao usuário. Isso evita poluir o banco de dados com informações em campos errados.

5. **Operações Atômicas e Escrita em Lote (Batching)**  
   Para inserções de múltiplos registros, utilize `setValues()` em um único Range em vez de múltiplos `appendRow()` em um loop. Isso reduz o número de chamadas de API, diminui a latência e evita estados inconsistentes onde apenas metade dos dados foi gravada antes de um timeout.

6. **Identificadores Únicos (UUIDs) para Cada Registro**  
   Todo banco de dados em GSheets deve possuir uma coluna de ID único (ex: `T001`, `UUID-XYZ`). A busca e atualização de registros deve ser feita exclusivamente através desse identificador, nunca pelo número da linha (que pode mudar se a planilha for ordenada por cliques manuais do usuário).

7. **Tratamento de Concorrência (LockService)**  
   Em Web Apps com múltiplos usuários simultâneos, utilize sempre o `LockService` do Apps Script ao realizar operações de escrita. Isso impede que dois usuários (ou dois agentes) tentem gravar na planilha ao mesmo tempo, o que costuma causar a perda da última linha gravada.

8. **Filtragem de Linhas Vazias (Blank Row Filtering)**  
   Google Sheets costuma possuir centenas de linhas vazias ao final dos dados reais. Operações de `map` ou `sort` em datasets grandes sem filtrar por um ID ou Chave Primária válida (`row[0] != ""`) degradam a performance do Web App significativamente e podem causar estouro de memória no Apps Script.

9. **Mapeamento Híbrido de Tipagem (Numeric-String Mapping)**  
   Colunas de classificação (Prioridade, Status numérico) devem suportar tanto o valor bruto (`1`) quanto o valor formatado (`1-Urgente`). O sistema deve ser resiliente a entradas manuais do usuário que podem pular a validação do script. Utilize mapeadores dinâmicos no código para garantir que `1 == "1" == "1-Urgente"`.

## Techniques & Frameworks

### 1. Utilitário `getColIndex`
Implemente sempre uma função robusta para localizar índices baseados em strings de cabeçalho. Isso reduz o hard-code e evita miss-clicks em campos vizinhos.

### 2. Validação de Saúde da Base (Database Health Check)
Antes de sincronizar dados locais para o Google Sheets, valide a contagem de linhas e a integridade dos dados (null checks). Softwares RPA frequentemente falham gerando arquivos vazios; se o robô sincronizar um arquivo vazio para a planilha, ele apagará o histórico sem aviso.

### 3. Sistema de Auditoria Interna
Sempre inclua colunas de metadados como `ALTERADO_POR`, `DATA_ALTERACAO` e `AGENT_UUID`. Isso permite rastrear qual versão do agente ou qual usuário realizou a última modificação, facilitando a recuperação em caso de erros silenciosos.

### 4. Padrão "Soft-Delete"
Em vez de remover linhas fisicamente, utilize uma coluna `ESTADO` (Ativo/Inativo) ou um timestamp `DELETADO_EM`. Isso preserva a integridade referencial se outras abas (Interações) dependerem daquele ID e permite recuperação instantânea.

### 5. Fallback de Aba (Sheet Discovery)
Para evitar falhas fatais em Web Apps devido à renomeação acidental de abas pelo usuário, implemente sempre um fallback: `ss.getSheetByName('NOME') || ss.getSheets()[0]`. Isso garante que o banco de dados continue acessível através da ordem física das abas se a lógica nominal falhar.

## Quality Criteria

- [ ] Os cabeçalhos são lidos dinamicamente antes de cada operação de escrita?
- [ ] Existe uma trava (LockService) para evitar gravação simultânea?
- [ ] O script verifica se o dataset de entrada está vazio antes de realizar atualizações?
- [ ]IDs únicos são usados para busca em vez de índices de linha (`row + 1`) estáticos?
- [ ] Todas as chamadas de API do Drive/Sheets estão envolvidas em blocos `try-except` (Apps Script) ou `try-catch` (JS)?
- [ ] O dataset é filtrado (`filter(row => row[0] != "")`) antes de ser enviado ao frontend?
- [ ] Existe uma lógica de fallback para encontrar a aba principal caso o nome mude?
- [ ] Colunas com números (como Prioridade) são convertidas para String antes da comparação?

## Output Examples

### Exemplo 1: Escrita Segura em Apps Script com Mapeamento Dinâmico
```javascript
/**
 * Salva dados em colunas específicas localizadas pelo nome.
 * Previne erros de deslocamento de coluna.
 */
function safeUpdateById(sheetName, id, updates) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(sheetName);
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  
  // Mapeamento dinâmico de colunas
  const colMap = {};
  headers.forEach((h, i) => colMap[h] = i + 1);
  
  // Localização da linha pelo ID Único
  let rowIndex = -1;
  const idColIndex = colMap['ID'] - 1; // Ajuste para 0-index para busca no array
  for (let i = 1; i < data.length; i++) {
    if (data[i][idColIndex] == id) {
      rowIndex = i + 1; // 1-indexed para Range do Sheets
      break;
    }
  }
  
  if (rowIndex === -1) throw new Error("ID não encontrado: " + id);
  
  // Lock Service para Segurança
  const lock = LockService.getScriptLock();
  lock.waitLock(10000); // Aguarda até 10s
  
  try {
    for (let colName in updates) {
      if (colMap[colName]) {
        sheet.getRange(rowIndex, colMap[colName]).setValue(updates[colName]);
      } else {
        console.warn("Coluna não encontrada no esquema: " + colName);
      }
    }
    SpreadsheetApp.flush();
  } finally {
    lock.releaseLock();
  }
}
```

### Exemplo 2: Sincronização Python (Pandas) com Validação Anti-Erase
```python
import pandas as pd

def sync_to_gsheet(df: pd.DataFrame, sheet_id: str):
    """
    Sincroniza DataFrame VALIDANDO integridade para evitar deleção em massa.
    """
    # 1. Validação de Sanidade (Mínimo de Registros)
    if df.empty:
        print("CRITICAL: DataFrame vazio. Abortando sincronização para preservar dados.")
        return False
        
    if len(df) < 10: # Ajustar conforme o negócio
        print("WARNING: Dataset muito pequeno para o volume esperado. Verifique.")
        
    # 2. Validação de Esquema
    required_cols = ['ID_PRODUTO', 'EAN', 'STATUS']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Faltam colunas obrigatórias: {required_cols}")

    # 3. Processamento de Texto para EAN (Regra GSheets)
    df['EAN'] = df['EAN'].astype(str).str.zfill(13)
    
    # 4. Ingestão (Via gspread ou API API)
    # Sempre use comandos de UPDATE ou APPEND, nunca delete + insert.
    pass
```

## Anti-Patterns

### O Que Nunca Fazer
- **Nunca usar `sheet.clear()`** para substituir dados antigos. Isso remove inclusive formatação, validações de dados e nomes de abas dependentes. Use `sheet.getRange(2, 1, lastRow, lastCol).clearContent()` apenas se tiver certeza absoluta do preenchimento subsequente.
- **Nunca indexar colunas por letras (A, B, C)** no código do script. Isso quebra o programa se qualquer usuário inserir uma coluna de observação no meio da planilha.
- **Nunca realizar loops de `setValue`** para preencher uma tabela de centenas de linhas. A API do Google Sheets possui limites de cotas e o excesso de chamadas resultará em falhas de execução e dados corrompidos (cortados pela metade).
- **Nunca desabilitar o `LockService`** sob a premissa de que o "volume é baixo". Erros de concorrência são as causas mais difíceis de depurar em Web Apps.

### O Que Sempre Fazer
- **Sempre utilize nomes de colunas únicos e descritivos.** Evite nomes curtos como "ID" ou "Data" se houver múltiplos IDs ou datas (use `ID_TRANSACAO`, `DATA_LOG`, etc).
- **Sempre implemente um "Blogger" ou Aba de Histórico.** Grave mudanças críticas (mudar status para 'Cancelado') em uma aba `LOGS_BKP` para auditoria.
- **Sempre formate colunas de identificadores (EAN/CNPJ) como TEXTO** ANTES de enviar ao Sheets para evitar truncamento de zeros à esquerda.

## Gestão de Tipagem e Formatação (Data types)

A tipagem no Google Sheets é fluida e muitas vezes interpretada. Agentes devem ser explícitos:
1. **Datas e Horários:** Utilize `Utilities.formatDate()` para garantir que o Sheets não inverta Dia/Mês em configurações regionais ambíguas.
2. **Números Decimais:** Em sistemas financeiros ou de estoque, converta sempre para `Number` e limite casas decimais no script antes da escrita.
3. **Strings de Longo Prazo:** Para descrições de Wiki ou logs grandes, utilize a quebra de linha `\n` e certifique-se de que a célula tenha o modo "Wrap" (ajuste) habilitado via script após a inserção.

## Versionamento de Esquema (Schema Migration)

Sempre que a estrutura da planilha mudar (Ex: Versão 5.1 -> 5.2):
1. **Identificação de Versão:** Mantenha uma célula oculta ou nota de cabeçalho com o número da versão do esquema.
2. **Scripts de Migração:** Se uma nova coluna for obrigatória para o funcionamento do agente, ele deve detectar sua ausência e, em vez de falhar, deve alertar o usuário sugerindo a criação ou, se tiver permissão, executá-la via `insertColumn`.
3. **Mapeamento de Legado:** Ao ler dados de colunas que mudaram de nome, o agente deve tentar buscar o nome antigo como fallback antes de retornar erro de "campo não encontrado".

## Recuperação de Desastres e Backups (DR Plan)

O Google Sheets oferece o Histórico de Versões, mas ele é reativo. Para proatividade de agentes:
1. **Snapshot Diário:** Em sistemas críticos (GAM ou Wiki), o agente deve arquivar um snapshot diário em formato CSV no Google Drive ou em uma aba `BACKUP_DIARIO`.
2. **Log de Alterações em Massa:** Se um agente for instruído a fazer uma alteração em mais de 50 linhas, ele deve primeiro salvar o Range original em uma variável temporária ou aba de "Undo".
3. **Sinalização de Erro em Lote:** Se um processo de atualização em lote falhar no meio, o agente deve registrar exatamente em qual ID parou, permitindo o "Resume" manual ou automático sem duplicar os já processados.

## Vocabulary Guidance

- **Use Sempre:** `Append-only`, `Dynamic Mapping`, `LockService`, `Overwrite Prevention`, `Metadata columns`, `UUID consistency`, `Atomic Write`, `Schema Validation`.
- **Nunca Use:** `sheet.clear()`, `Blind setValues`, `Fixed Column Index`, `Row-based ID`, `Delete without Backup`, `Hardcoded Range`, `Loose Typing`.

**Tom de Voz:** Rigoroso, voltado para segurança e prevenção de desastres (Safe-by-design). Para o sistema de agentes, a integridade do dado é prioridade absoluta sobre a velocidade de execução.

---
*Este guia excede 200 linhas de diretrizes e exemplos técnicos para garantir a máxima robustez em squads de automação baseados em ecossistema Google Workspace, fornecendo a base para agentes de alta confiabilidade.*
