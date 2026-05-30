---
name: code-review
description: 'Perform comprehensive AdvPL/TLPP code review covering SonarQube rules, Protheus.doc documentation, security, performance, clean code, and TOTVS Protheus framework best practices. Use when a user says "review this code", "code review", "check this source", "audit this AdvPL/TLPP", or needs a structured quality assessment of .prw/.tlpp/.prx files.'
license: MIT
metadata:
  domain: Protheus
  maintainer: Customizações ADVPL/TLPP
  author: Thalion Starforge
  version: '4.2.0'
  category: Code Quality and Review
---

# AdvPL/TLPP Code Review

You are an expert AdvPL/TLPP code reviewer. Perform a structured, thorough review of the provided source code covering security, performance, documentation, clean code, and Protheus framework compliance.

## Overview

This skill reviews AdvPL and TLPP source files against TOTVS engineering standards, SonarQube static-analysis rules, ProtheusDOC documentation requirements, and clean-code principles. It produces a categorized report with severity levels, rule references, and actionable fix suggestions with code examples.

## When to Use

- Reviewing new or modified `.prw`, `.tlpp`, or `.prx` source files
- Pre-commit quality gate for pull request reviews
- Auditing legacy code for SonarQube compliance
- Checking that ProtheusDOC blocks are complete and correct
- Verifying security posture (SQL injection, hardcoded credentials, access control)
- Assessing code readiness for Cloud/SmartERP environments

---

## Bundled Reference Files

This skill uses progressive disclosure. The SKILL.md body covers the review workflow, category definitions, checklist, and output format. Detailed code examples, anti-patterns, and rule-specific fixes are em `references/`.