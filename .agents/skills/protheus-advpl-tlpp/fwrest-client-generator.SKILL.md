---
name: fwrest-client-generator
description: "Generate AdvPL/TLPP code that CONSUMES external REST APIs using the FWRest client class. Covers GET, POST, PUT, DELETE verbs, header construction, query/path parameters, JSON body serialization, authentication (No Auth, HTTP Basic, Bearer Token/JWT, OAuth 2.0), timeout, SSL, status code handling, error treatment, and TLPP try/catch patterns. Use when user says 'consume REST API', 'call external API', 'FWRest', 'oRestClient', 'integrate with third-party API', 'HTTP client AdvPL', 'POST JSON Protheus', 'Bearer token AdvPL'."
license: MIT
metadata:
  domain: Protheus
  maintainer: Customizações ADVPL/TLPP
  author: Thalion Starforge
  version: '4.1.0'
  category: Code Generation
---

# FWRest Client Generator

## Overview

Generate production-ready AdvPL/TLPP code that **consumes** external REST APIs using the framework `FWRest` class. `FWRest` is the **HTTP client** class — it is the counterpart to the `@Get/@Post` annotation-based REST server (see `tlpp-rest-endpoint-generator` for *exposing* endpoints, not consuming them).

`FWRest` wraps low-level HTTP socket calls and supports the four standard verbs **GET, POST, PUT, DELETE** (no native PATCH support). It handles SSL automatically through `appserver.ini` socket configuration.

## When to Use

Use this skill when generating code that:

- Calls a third-party REST API from inside Protheus (integrations with CRMs, payment gateways, ERPs, government services, etc.)
- Sends JSON payloads to external services
- Pulls data from external endpoints into a Protheus routine
- Needs HTTP Basic, Bearer/JWT, or OAuth 2.0 authentication
- Replaces legacy `HTTPCGet` / `HTTPCPost` / `HTTPQuote` calls with the framework client

**Do NOT use** this skill for:

- Exposing endpoints from Protheus → use [`../tlpp-rest-endpoint-generator/SKILL.md`](../tlpp-rest-endpoint-generator/SKILL.md)
- Workstation-side HTTP calls that must run on the user's machine → use `HTTPCGet`/`HTTPCPost` with WebAgent
- File downloads from non-REST endpoints → use `HTTPQuote` or `WSDownload`

---

## FWRest Architecture