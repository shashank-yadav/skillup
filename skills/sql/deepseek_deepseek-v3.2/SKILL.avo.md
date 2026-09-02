---
name: sql
description: Strategies for writing correct SQL queries against a given schema.
---

# SQL

Write a single SQLite query that answers the question against the given
schema. Respond with only the query -- no explanation, no markdown code
fences, no semicolon-separated multiple statements.

## Insights

- When the task asks for a total sum, average, count, or other aggregate of a specific subset, use a WHERE clause to filter rows before applying the aggregate function.
- For tasks that ask for 'each' or 'per' group, use GROUP BY on the grouping column(s) and include the aggregate function(s) in the SELECT clause.
