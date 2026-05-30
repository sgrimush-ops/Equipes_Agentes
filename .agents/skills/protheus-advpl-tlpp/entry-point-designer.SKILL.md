---
name: entry-point-designer
description: "Design and document Protheus Entry Points (Pontos de Entrada). Always generates TLPP by default; only generates AdvPL (.prw) when the user explicitly requests AdvPL. Covers User Function signatures, PARAMIXB parameter layouts, return value specifications, and ProtheusDOC documentation. Use when user says 'create entry point', 'ponto de entrada', 'PARAMIXB', 'User Function hook', 'ponto de entrada TLPP', 'ponto de entrada ADVPL'."
license: MIT
metadata:
  domain: Protheus
  maintainer: Customizações ADVPL/TLPP
  author: Thalion Starforge
  version: '5.1.0'
  category: Code Generation
---

# Protheus Entry Point Designer

## Overview

Design, implement, and document Protheus Entry Points (Pontos de Entrada). Entry Points are the standard extensibility mechanism in TOTVS Protheus, allowing customization of standard ERP routines without modifying the original source code.

## Language Priority — TLPP First

**TLPP is the default and mandatory output language for every new Entry Point.** Only generate AdvPL (`.prw`) when the user explicitly requests it (e.g., "em AdvPL", "como .prw", "legacy AdvPL", "sem TLPP").

- Default: generate `.tlpp` with `#include "tlpp-core.th"`, type annotations, `Try-Catch`, and namespaced helpers when applicable
- Opt-in AdvPL: only when the user is explicit. If the request is ambiguous (e.g., the project still has many `.prw` files), confirm before falling back to AdvPL
- Migrating an existing `.prw` Entry Point: prefer rewriting in TLPP unless the user requires keeping the original extension

## When to Use

- Creating a new Entry Point to customize standard Protheus behavior
- Documenting existing Entry Points
- Designing the PARAMIXB interface for custom Entry Points
- Migrating legacy Entry Points to TLPP

---

## How Entry Points Work

1. A standard TOTVS routine (e.g., MATA010, FINA010) calls `ExistBlock("PE_NAME")` at predefined extension points
2. If a `User Function` with the matching name exists in the RPO, it is executed
3. The standard routine passes parameters via the `PARAMIXB` array (Private variable)