---
name: create-implementation-plan
description: 'Create machine-readable implementation plan files for features, refactoring, upgrades, design, architecture, or infrastructure. Use when a user says "create implementation plan", "plan this upgrade", "plan this refactor", or needs a structured, phased plan with requirements, constraints, tasks, and validation criteria saved to the /plan/ directory.'
license: MIT
metadata:
  domain: Protheus
  maintainer: Customizações ADVPL/TLPP
  author: Thalion Starforge
  version: '4.1.0'
  category: Documentation and Planning
---

# Create Implementation Plan

## Diretriz principal

O objetivo é criar um arquivo de plano de implementação para `${input:PlanPurpose}`. A saída deve ser legível por máquina, determinística e estruturada para execução autônoma por outros sistemas de IA ou humanos.

## Contexto de execução

Este prompt é projetado para comunicação AI-to-AI e processamento automatizado. Todas as instruções devem ser interpretadas literalmente e executadas sistematicamente sem interpretação humana.

## Requisitos principais

- Gerar planos de implementação totalmente executáveis por agentes IA ou humanos
- Usar linguagem determinística e sem ambiguidade
- Estruturar todo o conteúdo para parsing e execução automatizada
- Garantir autossuficiência sem dependências externas para entendimento

## Estrutura do plano

Planos devem conter fases atômicas com tarefas executáveis. Cada fase deve ser processável independentemente, salvo dependências explícitas.

## Arquitetura das fases

- Cada fase deve ter critérios de conclusão mensuráveis
- Tarefas em fases podem ser executadas em paralelo salvo dependências
- Descrições de tarefas devem incluir caminhos de arquivos, funções e detalhes exatos
- Nenhuma tarefa deve exigir interpretação ou decisão humana