---
name: orquestracao_hermes
description: "Gerencia e executa tarefas recebidas da fila de integração entre o Hermes Agent e o Antigravity (leitura de tarefas pendentes, execução técnica e conclusão documentada)."
---

# Skill: Orquestração Hermes Agent <-> Google Antigravity

Esta skill orienta o Antigravity na execução automatizada ou sob demanda de tarefas delegadas pelo **Hermes Agent** através da fila de memória compartilhada em `orquestracao/tarefas/`.

---

## 📂 Diretórios Oficiais da Fila

- **Pendentes**: `orquestracao/tarefas/pendentes/`
- **Em Execução**: `orquestracao/tarefas/em_execucao/`
- **Concluídas**: `orquestracao/tarefas/concluidas/`
- **Falhas**: `orquestracao/tarefas/falhas/`

---

## 🔄 Protocolo de Execução de Tarefas

Sempre que o usuário solicitar: *"processe as tarefas pendentes"*, *"rode a fila do Hermes"*, ou quando invocado via comando automático, siga rigorosamente este fluxo:

### 1. Identificar Tarefas Pendentes
- Verifique os arquivos `.md` existentes na pasta `orquestracao/tarefas/pendentes/`.
- Ordene por prioridade (Alta > Média > Baixa) e por timestamp (mais antigas primeiro).

### 2. Assumir a Tarefa (Lock/Em Execução)
- Mova o arquivo da tarefa de `pendentes/` para `em_execucao/` para evitar que outro processo a execute simultaneamente.

### 3. Executar o Objetivo Técnico
- Leia o arquivo da tarefa e identifique o tipo:
  - **Se for SQL / Consinco**: Siga estritamente as regras de `.agents/AGENTS.md` e a skill `gerar_consultas_consinco` (Oracle, materialize, sem comentários, filtros Var-F7, lista branca de lojas).
  - **Se for Automação / Python / Dados**: Siga as regras da skill `carregar_e_sanitizar` e `governanca-dados-varejo`.
- Crie ou modifique os arquivos necessários nas pastas de destino do projeto (ex.: `Aplicativos/gerenciamento_sql/...` ou `scripts/...`).

### 4. Concluir e Documentar
- Registre o relatório de entrega no arquivo da tarefa.
- Mova a tarefa de `em_execucao/` para `concluidas/` (pode utilizar a função `marcar_concluida` do script `orquestracao/scripts/despachante_hermes.py`).
- Apresente ao usuário um resumo objetivo com links clicáveis `file:///` para os arquivos criados.
