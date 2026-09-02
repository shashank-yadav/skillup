---
name: sql
description: Strategies for writing correct SQL queries against a given schema.
---

# SQL

Write a single SQLite query that answers the question against the given
schema. Respond with only the query -- no explanation, no markdown code
fences, no semicolon-separated multiple statements.

## Insights

- When a query requires aggregating data across multiple tables, join the tables on their common keys and then apply the aggregation function.
- To filter data based on a date range, use date functions to extract the relevant year, month, or day and compare it to the desired range.
- When a query asks for the top or bottom N records based on a certain criteria, use ORDER BY with DESC or ASC and LIMIT.
