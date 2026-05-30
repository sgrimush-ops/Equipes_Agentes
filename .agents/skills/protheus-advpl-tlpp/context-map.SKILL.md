---
name: context-map
description: 'Generate a context map of all files relevant to a task before implementing changes. Use when a user says "map the codebase for this change", "what files are affected", "show me dependencies", or before starting implementation to identify files to modify, dependencies, test files, and reference patterns.'
license: MIT
metadata:
  domain: Protheus
  maintainer: Customizações ADVPL/TLPP
  author: Thalion Starforge
  version: '4.1.0'
  category: Documentation and Planning
---

# Context Map

## Quando usar

- Antes de implementar mudanças e precisar entender o impacto no código
- Identificar arquivos, dependências e testes relacionados a uma tarefa
- Encontrar padrões de referência e implementações similares
- Criar análise pré-implementação para reduzir mudanças perdidas

## Task

{{task_description}}

## Instruções

1. Busque arquivos relacionados à tarefa
2. Identifique dependências diretas (importações/exportações)
3. Encontre testes relacionados
4. Busque padrões similares existentes

## Output Format

```markdown
## Context Map