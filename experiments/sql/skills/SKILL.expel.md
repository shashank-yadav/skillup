---
name: sql
description: Strategies for writing correct SQL queries against a given schema.
---

# SQL

Write a single SQLite query that answers the question against the given
schema. Respond with only the query -- no explanation, no markdown code
fences, no semicolon-separated multiple statements.

## Insights

- When a query involves multiple tables, join them using appropriate foreign keys.
- When filtering by date, use date functions to extract the relevant parts of the date (e.g., year, month).
- When filtering by a range of dates, use the BETWEEN operator.
- When filtering by multiple values in a single column, use the IN operator.
