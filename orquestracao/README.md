# Orquestração Híbrida: IA Online (Antigravity) + IA Local (Ollama)

Este diretório implementa a arquitetura de **Execução Híbrida para Economia de Tokens** e **Ciclo de Aprendizado Contínuo** entre o **Google Antigravity (IA Online)** e o **Ollama Local (`gemma4`, `hermes3`, `qwen2.5-coder`)**, além da fila compartilhada do **Hermes Agent**.

---

## 🏗️ Como Funciona o Fluxo Híbrido (Opção 2 Ativa)

```
[ Usuário faz o pedido no Chat ]
               │
               ▼
[ 1. IA Online (Antigravity) ] ──► Raciocínio rápido: define tabelas, regras e arquitetura
               │
               ▼ (Envia briefing técnico enxuto via CLI)
[ 2. IA Local (Ollama - executor_ollama.py) ]
   ├── Carrega automaticamente as lições de `memoria_aprendizado_ollama.json`
   ├── Gera o código SQL / Documentação Var-F7 / Script Python (Zero Tokens Online)
   └── Salva o arquivo no destino
               │
               ▼
[ 3. IA Online Revisa o Resultado ]
   ├── Se estiver 100% correto ──► Entrega imediatamente ao usuário
   └── Se encontrar erro ────────► 1) Corrige o arquivo final
                                   2) Executa `executor_ollama.py ensinar`
                                   3) Grava a regra em `LICOES_OLLAMA.md` para o Ollama NUNCA repetir o erro!
```

---

## 📁 Estrutura de Arquivos da Orquestração

* `scripts/executor_ollama.py`: Motor híbrido que conecta a IA Online ao Ollama local (`http://127.0.0.1:11434`), roteia para o modelo ideal (`gemma4:latest`, `hermes3:latest`, `qwen2.5-coder:1.5b`) e gerencia a memória de aprendizado contínuo.
* `memoria_aprendizado_ollama.json`: Banco de dados estruturado com todas as correções e regras ensinadas pela IA Online à IA Local.
* `LICOES_OLLAMA.md`: Painel legível (gerado automaticamente) com o histórico de lições aprendidas pelo Ollama e estatísticas de execuções locais.
* `scripts/despachante_hermes.py`: Utilitário para criação e gerenciamento de tarefas na fila Markdown.
* `tarefas/pendentes/`, `em_execucao/`, `concluidas/`, `falhas/`: Diretórios da fila de tarefas.
* `templates/`: Modelos padronizados (`modelo_tarefa_sql.md`, `modelo_tarefa_automacao.md`).

---

## 🚀 Comandos do Motor Híbrido (`executor_ollama.py`)

### 1. Delegar uma tarefa definida pela IA Online para o Ollama Local
```powershell
python orquestracao/scripts/executor_ollama.py executar `
  --categoria "sql" `
  --prompt "Crie query Oracle usando MRL_CUSTODIA somando VLRTOTALVDA e QTDVDA por NROEMPRESA..." `
  --saida "Aplicativos/gerenciamento_sql/querys/exemplo.sql"
```

### 2. Ensinar uma correção ao Ollama (Ciclo Anti-Reincidência)
```powershell
python orquestracao/scripts/executor_ollama.py ensinar `
  --categoria "sql" `
  --erro "Usou operador matemático fora do CASE com parênteses" `
  --regra "Sempre aplicar a operação aritmética internamente dentro do THEN e do ELSE" `
  --errado "(CASE WHEN X=1 THEN A ELSE B END) - C" `
  --correto "CASE WHEN X=1 THEN A - C ELSE B - C END"
```

### 3. Consultar todas as lições que o Ollama já aprendeu
```powershell
python orquestracao/scripts/executor_ollama.py licoes
```
