---
name: sql-optimization
description: 'Universal SQL performance optimization assistant for comprehensive query tuning, indexing strategies, and database performance analysis across SQL databases (PostgreSQL, SQL Server, Oracle). Provides execution plan analysis, pagination optimization, batch operations, and performance monitoring guidance. Use when user says "optimize SQL", "slow query", "index strategy", "execution plan analysis".'
license: MIT
metadata:
  domain: Protheus
  maintainer: Customizações ADVPL/TLPP
  author: Thalion Starforge
  version: '4.2.0'
  category: Code Quality and Review
---

# SQL Performance Optimization Assistant

Expert SQL performance optimization for ${selection} (or entire project if no selection). Focus on universal SQL optimization techniques that work across PostgreSQL, SQL Server, Oracle, and other SQL databases.

## Core Optimization Areas

This skill covers query performance analysis, index strategy, subquery optimization, JOIN optimization, pagination, aggregation, query anti-patterns, batch operations, temporary tables, index management, and performance monitoring.

For all universal SQL optimization patterns with BAD/GOOD code examples, see [sql-optimization-patterns.md](references/sql-optimization-patterns.md).

## Universal Optimization Checklist

### Query Structure
- [ ] Avoiding SELECT * in production queries
- [ ] Using appropriate JOIN types (INNER vs LEFT/RIGHT)
- [ ] Filtering early in WHERE clauses
- [ ] Using EXISTS instead of IN for subqueries when appropriate
- [ ] Avoiding functions in WHERE clauses that prevent index usage

### Index Strategy
- [ ] Creating indexes on frequently queried columns
- [ ] Using composite indexes in the right column order
- [ ] Avoiding over-indexing (impacts INSERT/UPDATE performance)
- [ ] Using covering indexes where beneficial
- [ ] Creating partial indexes for specific query patterns

### Data Types and Schema
- [ ] Using appropriate data types for storage efficiency