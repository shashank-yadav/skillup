---
name: sql
description: Strategies for writing correct SQL queries against a given schema.
---

# SQL

Write a single SQLite query that answers the question against the given
schema. Respond with only the query -- no explanation, no markdown code
fences, no semicolon-separated multiple statements.

## Insights

- When a query involves multiple tables, join them using appropriate keys.
- When filtering by date ranges, use BETWEEN for inclusive ranges.
- When filtering by multiple specific values, use IN for conciseness.
