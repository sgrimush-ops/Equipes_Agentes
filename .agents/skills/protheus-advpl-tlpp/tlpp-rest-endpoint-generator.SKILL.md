---
name: tlpp-rest-endpoint-generator
description: "Generate TLPP REST endpoints using annotation-based routing (@Get, @Post, @Put, @Patch, @Delete) with the oRest object. Follows TOTVS API standards (TTALK) including pagination, error model, standard headers, and Swagger documentation. Use when user says 'create REST endpoint', 'TLPP REST', '@Get annotation', 'oRest endpoint'."
license: MIT
metadata:
  domain: Protheus
  maintainer: Customizações ADVPL/TLPP
  author: Thalion Starforge
  version: '4.2.0'
  category: Code Generation
---

# TLPP REST Endpoint Generator

## Overview

Generate production-ready TLPP REST endpoints using the native annotation-based REST framework. TLPP REST replaces the legacy WsRESTful pattern with a simpler, annotation-driven approach. Each endpoint is a function decorated with an HTTP verb annotation and uses the global `oRest` object to handle requests and responses.

## When to Use

Use this skill when:

- Creating new REST API endpoints in TLPP
- Implementing TOTVS TTALK-compliant APIs
- Generating CRUD endpoints for Protheus entities
- Building integration APIs for external systems
- Migrating WsRESTful services to TLPP REST

---

## TLPP REST Architecture

### How It Works

1. A function is annotated with an HTTP verb annotation (e.g., `@Get("/path")`)
2. The TLPP REST Server automatically registers the route at startup via annotation scanning
3. When a request matches the route, the annotated function is invoked
4. The function uses the global `oRest` object to read the request and write the response
5. Swagger/OpenAPI documentation is generated automatically from the annotations