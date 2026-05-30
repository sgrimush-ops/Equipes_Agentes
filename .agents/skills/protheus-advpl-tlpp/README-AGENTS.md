# README-AGENTS.md — protheus-advpl-tlpp

Este diretório centraliza todas as skills, templates e padrões para automação, revisão e documentação de sistemas Protheus/AdvPL/TLPP no ecossistema Equipes_Agentes.

## Skills disponíveis
- **advpl-tlpp-sdd**: Checklists, templates e guias para todo o ciclo de vida do software
- **mvc-generator**: Geração de código MVC padrão Protheus
- **query-builder**: Padrões para queries cross-database
- **code-review**: Checklist de revisão, padrões de segurança e qualidade
- **sql-code-review**: Padrões para revisão de SQL
- **sql-optimization**: Otimização de queries
- **fwrest-client-generator**: Geração de clientes REST
- **refactor**: Padrões de refatoração
- **tir-test-generator**: Geração de testes TIR
- **data-dictionary-lookup**: Consulta ao dicionário de dados
- **create-implementation-plan**: Quebra de tarefas e planejamento
- **context-map**: Mapeamento de contexto e dependências
- **entry-point-designer**: Design de entry points TLPP
- **advpl-to-tlpp-migration**: Padrões de migração AdvPL → TLPP

## Como usar
1. Consulte o README de cada skill para exemplos e integração.
2. Use os arquivos de referência para padronizar fluxos, acelerar onboarding e garantir qualidade.
3. Solicite ao agente Equipes_Agentes exemplos, templates ou explicações detalhadas.

## Estrutura recomendada
- skills/ — skills de domínio (MVC, REST, Entry Point, Query, etc.)
- references/ — exemplos, templates, padrões e checklists
- scripts/ — utilitários e automações

## Recomendações
- Sempre consulte a documentação da skill antes de usar.
- Prefira TLPP para novos desenvolvimentos, AdvPL apenas para legados.
- Documente tudo com ProtheusDOC.
- Use checklist de revisão antes de subir código para produção.
