# Orquestração Híbrida: Hermes Agent + Google Antigravity

Este diretório implementa a arquitetura de **Memória Compartilhada (Agent OS)** e **Fila Desacoplada de Tarefas** entre o **Hermes Agent** e o **Google Antigravity**.

---

## 🏗️ Como Funciona o Fluxo

```
[ Gatilho Externo ]
       │
       ▼
[ Hermes Agent ]  ──(Gera Briefing/Task)──>  [ orquestracao/tarefas/pendentes/ ]
                                                            │
                                                            ▼
                                              [ Google Antigravity ]
                                              (Lê contexto, executa código/SQL/testes)
                                                            │
                                                            ▼
                                              [ orquestracao/tarefas/concluidas/ ]
                                              (Grava resultado, artefatos e logs)
```

1. **Hermes Agent (Retaguarda / Automação Externa)**:
   - Monitora eventos (mensagens no Telegram/Discord/WhatsApp, cron noturno, webhooks, scraping).
   - Quando precisa de uma alteração de código, nova consulta SQL, automação de dados ou refatoração, cria um arquivo Markdown dentro de `orquestracao/tarefas/pendentes/`.

2. **Google Antigravity (Executor Especialista)**:
   - Lê a tarefa com todo o contexto do repositório (`.agents/skills`, regras do ERP Consinco, regras de governança).
   - Executa a tarefa (escreve código, valida sintaxe, testa, documenta).
   - Move a tarefa para `orquestracao/tarefas/concluidas/` e adiciona o bloco de resultado e arquivos gerados.

---

## 📁 Estrutura de Pastas

* `tarefas/pendentes/`: Tarefas aguardando execução pelo Antigravity.
* `tarefas/em_execucao/`: Tarefas que estão sendo processadas no momento.
* `tarefas/concluidas/`: Tarefas finalizadas com relatório de entrega e links de arquivos.
* `tarefas/falhas/`: Tarefas que encontraram impedimentos ou dados incorretos.
* `templates/`: Modelos padronizados de solicitação (`modelo_tarefa_sql.md`, `modelo_tarefa_automacao.md`).
* `scripts/`:
  * `despachante_hermes.py`: Utilitário Python para criar novas tarefas via script ou terminal.
  * `executor_fila.py`: Utilitário para listar, processar ou validar tarefas da fila.

---

## 🚀 Como Usar no Dia a Dia

### 1. Criando uma tarefa via Hermes (ou via linha de comando)
```bash
python orquestracao/scripts/despachante_hermes.py criar \
  --titulo "Criar Query de Vendas por Departamento" \
  --tipo "sql" \
  --descricao "Preciso de uma query Oracle para a tela Var-F7 com filtro de filial e período"
```

### 2. Executando no Antigravity
No chat do Antigravity, você (ou o disparador automático) simplesmente executa:
> *"Processe as tarefas pendentes em `@orquestracao/tarefas/pendentes/`"*

O Antigravity identificará a demanda, utilizará as skills cabíveis (ex.: `gerar_consultas_consinco`, `consulta-criacao-filtros`), gerará a solução e marcará como concluída.
