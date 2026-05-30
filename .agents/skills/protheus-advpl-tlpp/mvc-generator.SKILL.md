---
name: mvc-generator
description: "Generate Protheus MVC (Model-View-Controller) screen structures including ModelDef, ViewDef, MenuDef, and BrowseDef functions. Supports single-entity (Modelo 1) and master-detail (Modelo 3) patterns with FWFormModel, FWFormView, FWFormBrowse, validations, triggers, and entry point hooks. Use when user says 'create MVC screen', 'ModelDef ViewDef', 'FWFormModel', 'master-detail screen'."
license: MIT
metadata:
  domain: Protheus
  maintainer: Customizações ADVPL/TLPP
  author: Thalion Starforge
  version: '4.1.0'
  category: Code Generation
---

# Protheus MVC Generator

## Overview

Generate complete Protheus MVC screen implementations following the TOTVS framework patterns. Protheus MVC separates business rules (Model), visual presentation (View), and navigation/actions (Controller/Browse) using the `FWFormModel`, `FWFormView`, and `FWFormBrowse` framework classes. This skill generates the three mandatory functions (`ModelDef`, `ViewDef`, `MenuDef`) plus the Browse function that composes them.

## When to Use

Use this skill when:

- Creating a new CRUD screen for a Protheus table
- Building a master-detail form (e.g., invoice header + items)
- Generating MVC boilerplate from a table alias
- Adding validations, triggers, and entry point hooks to MVC screens
- Migrating legacy AxCadastro/Mbrowse screens to MVC

---

## MVC Architecture in Protheus

### Core Components

```
┌─────────────────────────────────────────┐
│  Main Function (e.g., MYMOD01)          │
│  ├── MenuDef()  → Menu actions          │
│  └── FWFormBrowse → Browse grid         │
│       ├── ModelDef() → Business rules   │