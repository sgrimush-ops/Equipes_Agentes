# Estrutura da pasta .agents

A pasta `.agents` centraliza toda a inteligência do projeto, facilitando manutenção, consulta e evolução. Veja como está organizada:

## Subpastas principais

- **agents/**: Definições de agentes, arquivos .agent.md, scripts e YAMLs de pipeline/core.
- **skills/**: Skills modulares para uso por agentes e squads.
- **squads/**: Squads configuradas, pipelines e memórias específicas de squads.
- **rules/**: Arquivos de regras e políticas de uso.
- **memory/**: Scripts e arquivos de memória persistente ou seeds.
- **logs/**: Logs de execução e auditoria de agentes.
- **configs/**: Arquivos de configuração (ex: playwright.config.json).
- **best-practices/**: Documentos de melhores práticas para agentes e squads.
- **workflows/**: Workflows e pipelines de execução.
- **memory_db/**: Banco de dados de memória vetorial ou persistente.

## Exemplo de conteúdo

- `.agents/agents/` → especialista-dados.agent.md, runner.pipeline.md, office_server.py
- `.agents/skills/` → gemini-api-dev/, consulta-criacao-filtros/, etc.
- `.agents/squads/` → varejo-insight/, squad.yaml, _memory/
- `.agents/rules/` → rules.md
- `.agents/memory/` → kernel.py, seed_memory.py
- `.agents/logs/` → janitor_log.txt
- `.agents/configs/` → playwright.config.json
- `.agents/best-practices/` → gam_robustness_best_practices.md
- `.agents/workflows/` → Equipes_agentes.md
- `.agents/memory_db/` → chroma.sqlite3

## Observações
- Todos os arquivos de agentes, regras, memória e configuração estão centralizados.
- Não há mais dispersão em pastas como Agentes, .antigravity, .mcp_squad, etc.
- Para adicionar novos agentes, skills ou squads, utilize as subpastas correspondentes.

---

Dúvidas ou sugestões de melhoria, registre em `.agents/rules/` ou crie um novo documento em best-practices.
