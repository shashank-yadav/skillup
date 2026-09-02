---
name: sql
description: Strategies for writing correct SQL queries against a given schema.
---

# SQL

Write a single SQLite query that answers the question against the given
schema. Respond with only the query -- no explanation, no markdown code
fences, no semicolon-separated multiple statements.

## Insights

- When the task asks for a total or sum, use the SUM() aggregation function in the SELECT clause.
- When the task asks for a count of distinct items, use COUNT(DISTINCT column).
