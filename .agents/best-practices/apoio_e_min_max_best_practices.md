# 🛡️ Guia de Boas Práticas e Aprendizados: Painel de Apoio & Mínimo e Máximo

Este documento registra as lições aprendidas, padrões arquiteturais e correções de robustez desenvolvidas no ecossistema do **Painel de Apoio** (`Aplicativos/Apoio`) e do módulo de **Estoque Mínimo e Máximo** (`Aplicativos/min_e_max`).

---

## 📅 Data de Atualização: 17/10/2026

---

## 🎛️ 1. Padrão Arquitetural: Painel de Apoio (GUI Tkinter Assíncrona)

O aplicativo `app_apoio.py` centraliza a execução de scripts críticos da cadeia de suprimentos e inteligência de estoque:
- `1-data_query.py` (Importação, sanitização e sincronização de dados).
- `1-min_max.py` (Cálculo volumoso de mínimo e máximo).
- `capacidade.xlsx` (Abertura de planilha de parametrização).
- `gam.py` (Handover para o robô de automação).

### Lições Aprendidas:
1. **Execução Assíncrona sem Congelamento**:
   - Subprocessos pesados (`1-data_query.py` e `1-min_max.py`) **nunca** devem rodar na thread principal da interface gráfica.
   - Use sempre `threading.Thread(target=..., daemon=True)` em conjunto com `queue.Queue()` e o loop de verificação periódica `root.after(100, process_queue)` do Tkinter.
2. **Buffer de Saída em Tempo Real**:
   - No Windows, scripts chamados via `subprocess.Popen` retêm buffers de `print()` a menos que o parâmetro `-u` ou a variável de ambiente `PYTHONUNBUFFERED=1` seja explicitamente injetada.
   - O `app_apoio.py` utiliza `PYTHONUNBUFFERED="1"` e `bufsize=1` para exibir cada linha de log imediatamente no console da GUI.
3. **Decodificação Flexível de Console**:
   - Saídas de scripts legados no Windows podem emitir caracteres em `cp1252`, `latin1` ou `utf-8`.
   - O pipeline de leitura tenta `utf-8`, recai para `latin1` e por fim utiliza `errors='replace'`, impedindo travamentos por `UnicodeDecodeError`.
4. **Comunicação Bidirecional via Terminal Virtual**:
   - Foi disponibilizada uma barra de entrada interativa ("Entrada Terminal") no rodapé do console com captura de tecla `<Return>`.
   - As respostas digitadas pelo usuário são despachadas via `self.current_process.stdin.write(...)` e `flush()`.

---

## 🔢 2. Resolução do Erro de Lojas no `1-min_max.py` (Múltiplas Lojas e Zeros à Esquerda)

### O Problema:
- Ao informar múltiplas lojas (ex: `01, 02, 03`) ou formatos com pontuação (`01; 02; 03`), o script abortava imediatamente com a mensagem `x Número de loja inválido`.
- O código antigo utilizava `loja_input.isdigit()` (que retorna `False` na presença de vírgulas e espaços) e aplicava filtragem por igualdade estrita: `df[df['CODIGO_EMPRESA_INT'] == loja_especifica]`.

### Solução e Padrão Obrigatório:
1. **Extração com Expressão Regular**:
   - Utilizar `re.findall(r'\d+', input_str)` para extrair todos os blocos numéricos da entrada.
2. **Sanitização de Inteiros (Eliminação de Zeros à Esquerda)**:
   - Converter cada número para `int(x)`. O número `01` vira `1`, `02` vira `2`, etc.
   - Deduplicar preservando a ordem: `list(dict.fromkeys(lojas_encontradas))`.
3. **Filtragem com Pertinência Múltipla (`.isin()`)**:
   ```python
   df['CODIGO_EMPRESA_INT'] = pd.to_numeric(df['CODIGO_EMPRESA'], errors='coerce').fillna(-1).astype(int)
   df = df[df['CODIGO_EMPRESA_INT'].isin(lojas_selecionadas)].copy()
   ```
4. **Interface Modal Integrada**:
   - A tela modal do `app_apoio.py` valida e formata a lista de lojas, enviando-a diretamente para o `stdin` do `1-min_max.py`.

---

## 📊 3. Ordem de Prioridade e Padrão do Relatório de Mín/Máx

- No diálogo de parâmetros, a opção padrão selecionada é:
  **`[1] APENAS sugestões para AUMENTAR (Recomendado)`**
- Motivação Operacional: No abastecimento diário, focar em aumentos de estoque mínimo protege as lojas contra rupturas de gôndola. As opções `[2] TOTAL`, `[3] DIMINUIR` e `[4] AMBOS` permanecem disponíveis para manutenções amplas de estoque.

---

## 📑 4. Fluxo Pós-Execução: Planilha de Digitar (`digitar.xlsx`) e Ajuste (`ajustepp.xlsx`)

### Arquitetura de Arquivos no Ecossistema GAM:
- **`Aplicativos/GAM/bd_saida/digitar.xlsx`**: É a planilha oficial de saída contendo os pedidos gerados para serem digitados pelo robô no ERP Consinco.
- **`Aplicativos/GAM/bd_entrada/ajustepp.xlsx`**: É a planilha de resultado do cálculo de mínimos e máximos utilizada na ação de ajuste de min/max.

### Abertura Automática Inteligente:
Ao término bem-sucedido do `1-min_max.py`, o método `abrir_planilhas_pos_min_max` no `app_apoio.py`:
1. Localiza e abre a planilha de digitar (`digitar.xlsx` ou `digitar.csv`).
2. Aplica um intervalo breve (`time.sleep(0.5)`) para estabilização de instâncias do Excel no Windows.
3. Localiza e abre a planilha de resultado de ajuste (`ajustepp.xlsx`), priorizando a versão mais recente caso o arquivo tenha sido mantido na pasta local ou movido para `bd_entrada`.

---

## 🚀 5. Handover e Transição Desacoplada de Processos (`Apoio` ➔ `GAM`)

Ao acionar a transição para o GAM ("4º Botão: Abrir GAM e Fechar Painel de Apoio"):
1. **Processo Desanexado no Windows**:
   - O novo processo deve ser gerado com flags `subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS` e `close_fds=True`.
   - Isso garante que quando o `app_apoio.py` invocar `self.root.destroy()`, o processo do `gam.py` continue executando de forma independente na máquina do usuário sem ser terminado junto com o processo pai.
2. **Segurança de Execução Ativa**:
   - Antes de fechar, o sistema verifica se há rotinas de dados em andamento (`self.is_running`) e solicita confirmação explícita do usuário para evitar perda de processamento em andamento.
