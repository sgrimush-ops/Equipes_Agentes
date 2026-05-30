---
name: sql-code-review
description: 'Universal SQL code review assistant that performs comprehensive security, maintainability, and code quality analysis across SQL databases (PostgreSQL, SQL Server, Oracle). Focuses on SQL injection prevention, access control, code standards, and anti-pattern detection. Complements SQL optimization prompt for complete development coverage. Use when user says "review SQL", "SQL security audit", "SQL anti-patterns", "check SQL quality".'
license: MIT
metadata:
  domain: Protheus
  maintainer: Customizações ADVPL/TLPP
  author: Thalion Starforge
  version: '4.2.0'
  category: Code Quality and Review
---

# SQL Code Review

Perform a thorough SQL code review of ${selection} (or entire project if no selection) focusing on security, performance, maintainability, and database best practices.

## Review Categories

### 🔒 Security

- **SQL Injection Prevention** — all user inputs must be parameterized; no string concatenation in queries
- **Access Control** — principle of least privilege, role-based permissions, schema security
- **Data Protection** — avoid `SELECT *` on sensitive tables, enforce audit logging and data masking

### ⚡ Performance

- **Query Structure** — eliminate `SELECT DISTINCT *`, prefer explicit JOINs over comma-separated FROM
- **Index Strategy** — verify indexes for WHERE/JOIN columns, flag over-indexing and unused indexes
- **Join Optimization** — correct join types, optimal join order, no accidental Cartesian products
- **Aggregation** — replace correlated subqueries with JOIN/GROUP BY when possible

### 🛠️ Code Quality

- **Formatting** — consistent uppercase keywords, aligned columns, proper indentation
- **Naming** — descriptive table/column names, no reserved words as identifiers, consistent casing
- **Schema Design** — appropriate normalization, optimal data types, proper constraints and defaults

### 🗄️ Database Compatibility

- **ANSI SQL first** — use COALESCE, CASE WHEN, ANSI JOINs, FETCH FIRST for portability