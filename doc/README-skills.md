# Catálogo de Skills Equipes_agentes

Explore as skills disponíveis para suas squads. Instale qualquer skill com:

```bash
npx Equipes_agentes install <nome-da-skill>
```

## Skills Disponíveis

| Skill | Tipo | Descrição | Variáveis de Amb. | Instalação |
|-------|------|-------------|----------|---------|
| [gemini-api-dev](./gemini-api-dev/) | prompt | Desenvolvimento geral com a API Gemini (Python, JS, Go, Java). | _(padrão)_ | `npx Equipes_agentes install gemini-api-dev` |
| [governanca-dados-varejo](./governanca-dados-varejo/) | hybrid | Governança, limpeza e glossário de negócio (Filial 015 = CD). | _(padrão)_ | `npx Equipes_agentes install governanca-dados-varejo` |
| [vertex-ai-api-dev](./vertex-ai-api-dev/) | prompt | Guia o uso da API Gemini no Google Cloud Vertex AI. | `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION` | `npx Equipes_agentes install vertex-ai-api-dev` |
| [gemini-live-api-dev](./gemini-live-api-dev/) | prompt | Streaming bidirecional em tempo real (Voz/Vídeo) com Gemini Live. | _(padrão)_ | `npx Equipes_agentes install gemini-live-api-dev` |
| [gemini-interactions-api](./gemini-interactions-api/) | prompt | API unificada para chat, agentes e tarefas em segundo plano (Deep Research). | _(padrão)_ | `npx Equipes_agentes install gemini-interactions-api` |

## Tipos de Skill

- **mcp** -- Conecta a um servidor MCP externo (transporte stdio ou HTTP)
- **script** -- Executa um script local (Node.js, Python, etc.)
- **hybrid** -- Combina acesso a servidor MCP com capacidades de script local
- **prompt** -- Instruções comportamentais puras para os agentes

## Estrutura de Diretórios

Cada skill vive em sua própria pasta com um arquivo `SKILL.md`:

```
skills/
  gemini-api-dev/
    SKILL.md
  vertex-ai-api-dev/
    SKILL.md
  gemini-live-api-dev/
    SKILL.md
  gemini-interactions-api/
    SKILL.md
```

O arquivo `SKILL.md` contém frontmatter YAML (nome, tipo, versão, configuração de MCP/script, variáveis de ambiente, categorias) e um corpo Markdown com instruções de uso e operações disponíveis.

## Adicionando uma Nova Skill

1. Crie uma nova pasta em `skills/` com o ID da skill como nome
2. Adicione um arquivo `SKILL.md` com frontmatter YAML válido e corpo Markdown
3. Se a skill incluir scripts, coloque-os em uma subpasta `scripts/`
4. Atualize este README para incluir a nova skill na tabela do catálogo
