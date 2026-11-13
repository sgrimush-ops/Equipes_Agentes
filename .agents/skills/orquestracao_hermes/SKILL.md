---
name: orquestracao_hermes
description: "Orquestração Híbrida (IA Online Antigravity + IA Local Ollama) com Ciclo de Aprendizado Contínuo e fila de tarefas."
---

# Skill: Orquestração Híbrida (Antigravity Online + Ollama Local)

Esta skill define o protocolo obrigatório de **Trabalho Híbrido para Economia de Tokens** e **Ciclo de Aprendizado Contínuo** entre a IA Online (Google Antigravity) e a IA Local (Ollama rodando em `http://127.0.0.1:11434`).

---

## 🔄 Fluxo Híbrido Obrigatório (Planejamento Online -> Execução Local -> Revisão e Ensino)

Sempre que o usuário solicitar a criação de consultas SQL, documentações `Var - F7`, scripts Python repetitivos, resumos ou tratamento de arquivos:

### Passo 1 — Raciocínio e Definição Rápida (IA Online)
- A IA Online analisa o pedido rapidamente, consulta o dicionário/regras essenciais e **define a arquitetura da solução** (quais tabelas usar, quais joins, quais filtros, qual estrutura de código).
- Em vez de gastar milhares de tokens gerando textos extensos ou rascunhos longos diretamente na nuvem, a IA Online monta um **briefing técnico enxuto** para o Ollama.

### Passo 2 — Execução Braçal pela IA Local (`executor_ollama.py`)
- A IA Online invoca o executor local via terminal:
  ```powershell
  python orquestracao/scripts/executor_ollama.py executar `
    --categoria "sql" `
    --prompt "Briefing técnico definido pela IA Online..." `
    --saida "caminho/do/arquivo_gerado.sql"
  ```
- Categorias suportadas (com roteamento automático de modelo local):
  - `sql` -> usa `gemma4:latest` (com sanitização anti-comentários `--`)
  - `var_f7` -> usa `hermes3:latest` (documentação de variáveis de tela Consinco)
  - `python` -> usa `gemma4:latest`
  - `codigo_rapido` -> usa `qwen2.5-coder:1.5b`
  - `dados` / `geral` -> usa `hermes3:latest`

### Passo 3 — Revisão Rigorosa pela IA Online
- A IA Online lê o arquivo gerado pelo Ollama (`read_file`) e valida contra todas as regras do `.agents/AGENTS.md` e `.agents/rules.md`.
- Se estiver perfeito, entrega imediatamente ao usuário.

### Passo 4 — Correção e Ensino Imediato à IA Local (Memória Anti-Reincidência)
- **Se a IA Online encontrar qualquer erro no trabalho do Ollama** (ex.: sintaxe Oracle incorreta, ausência de `/*+ MATERIALIZE */`, uso de comentário `--`, falta de coluna no `GROUP BY`, código fora do padrão):
  1. A IA Online **corrige o arquivo** imediatamente (`edit_file` / `write_file`).
  2. A IA Online **ensina obrigatoriamente a IA Local** executando o comando `ensinar`:
     ```powershell
     python orquestracao/scripts/executor_ollama.py ensinar `
       --categoria "sql" `
       --erro "Descrição exata do erro que o Ollama cometeu" `
       --regra "Regra clara para o Ollama nunca mais repetir esse erro" `
       --errado "Trecho errado gerado" `
       --correto "Trecho corrigido pela IA Online"
     ```
- Essa lição fica gravada permanentemente em `orquestracao/memoria_aprendizado_ollama.json` e documentada em `orquestracao/LICOES_OLLAMA.md`, sendo injetada automaticamente no System Prompt do Ollama em todas as próximas execuções!

---

## 📂 Diretórios e Arquivos da Orquestração

- **Executor e Memória Local**:
  - `orquestracao/scripts/executor_ollama.py` (Motor híbrido + aprendizado contínuo)
  - `orquestracao/memoria_aprendizado_ollama.json` (Banco de lições aprendidas)
  - `orquestracao/LICOES_OLLAMA.md` (Painel legível de evolução do Ollama)
- **Fila de Tarefas (Hermes <-> Antigravity)**:
  - `orquestracao/scripts/despachante_hermes.py`
  - `orquestracao/tarefas/pendentes/`
  - `orquestracao/tarefas/em_execucao/`
  - `orquestracao/tarefas/concluidas/`
  - `orquestracao/tarefas/falhas/`
