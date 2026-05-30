---
name: data-dictionary-lookup
description: "Query the TOTVS Protheus ERP data dictionary (SX2 tables, SX3 fields, SIX indexes, SX6 parameters, SX5 generic tables, SX7 triggers, SX1 questions, SX9 relationships, SXB standard lookups, SXG/SXA groups). Use when the user asks 'what fields does SA1 have', 'what is the index of SE1', 'parameter MV_ESTADO', 'generic table 12', 'triggers for field A1_COD', 'standard lookup SA1', 'table structure', 'data dictionary'. Also use during refactoring, migration, or code improvements when dictionary impact validation is needed to confirm whether changes affect fields, triggers, indexes, parameters, or table relationships."
license: MIT
metadata:
  domain: Protheus
  maintainer: Customizações ADVPL/TLPP
  author: Thalion Starforge
  version: '4.1.0'
  category: Documentation
---

# Protheus Data Dictionary Lookup

## Overview

Consulta estruturada ao dicionário de dados do Protheus ERP. Permite buscar tabelas, campos, índices, parâmetros, tabelas genéricas, triggers, perguntas de parametrização, relacionamentos e lookups padrão (consultas SQL via `execute-sql` e documentação TDN via ferramentas de busca).

## Quando usar

- Descobrir campos e tipos de uma tabela
- Verificar índices disponíveis
- Consultar valor e propósito de um parâmetro (MV_*)
- Buscar conteúdo de tabela genérica (SX5)
- Verificar triggers associadas a um campo
- Consultar perguntas de parametrização (SX1)
- Verificar relacionamentos entre tabelas (SX9)
- Consultar lookups padrão (SXB)
- Encontrar modo de compartilhamento de tabela
- **Validação de impacto no dicionário**: durante refatorações, migrações ou melhorias, consultar o dicionário para confirmar se mudanças afetam campos, triggers, índices, parâmetros ou relacionamentos das tabelas envolvidas