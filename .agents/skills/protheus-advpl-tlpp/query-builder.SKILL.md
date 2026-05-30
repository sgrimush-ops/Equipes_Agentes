---
name: query-builder
description: "Build optimized and safe SQL queries for Protheus tables. Automatically includes mandatory filters (D_E_L_E_T_, branch), suggests appropriate indexes from SIX patterns, generates both Embedded SQL (preferring FWExecStatement) and Workarea (DBSelectArea/DBSeek) versions, and warns about common Protheus SQL pitfalls. Use when user says 'build query', 'SQL for Protheus table', 'FWExecStatement', 'TCQuery', 'Workarea vs SQL'."
license: MIT
metadata:
  domain: Protheus
  maintainer: Customizações ADVPL/TLPP
  author: Thalion Starforge
  version: '4.2.0'
  category: Code Generation
---

# Protheus Query Builder

## Overview

Build correct, safe, and optimized SQL queries for Protheus ERP tables. Protheus has unique database conventions — mandatory soft-delete filters, multi-branch filtering, Hungarian notation for fields, data dictionary-driven schemas, and specific index patterns — that every query must respect. This skill generates queries that follow these conventions and helps choose between Workarea access and Embedded SQL.

## When to Use

Use this skill when:

- Writing SQL queries against Protheus tables (SA1, SD1, SF2, etc.)
- Building parameterized SQL queries (`FWExecStatement`, `TCSqlExec`) in AdvPL/TLPP
- Optimizing existing queries for Protheus-specific patterns
- Deciding between Workarea access and Embedded SQL
- Ensuring mandatory filters are not missing
- Generating safe queries that prevent SQL injection

---

## Bundled Reference Files

This skill uses progressive disclosure. The SKILL.md body covers conventions, decision logic, the checklist, and anti-patterns. Detailed code templates and cross-database reference tables are in the `references/` directory — read them on demand based on the scenario:

| Reference File | When to Read | Content |
| --- | --- | --- |
| [references/query-patterns-and-examples.md](references/query-patterns-and-examples.md) | Generating **query code** — Workarea, Embedded SQL, multi-table JOINs, TCSqlExec updates, counting, or reviewing SQL injection prevention examples | Full code templates for all 5 query patterns, safe/unsafe FWExecStatement examples, LIKE clause parameterization |
| [references/cross-database-compatibility.md](references/cross-database-compatibility.md) | Handling **cross-database concerns** — ChangeQuery(), TCGetDB(), DBAccess macros, or translating functions between MSSQL / PostgreSQL / Oracle | ChangeQuery and TCGetDB code examples, DBAccess macros table, cross-database function equivalents (9 operations × 4 dialects) |