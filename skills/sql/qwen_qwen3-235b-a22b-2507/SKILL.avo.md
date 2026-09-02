---
name: sql
description: Strategies for writing correct SQL queries against a given schema.
---

# SQL

Write a single SQLite query that answers the question against the given
schema. Respond with only the query -- no explanation, no markdown code
fences, no semicolon-separated multiple statements.

## Insights

- Use GROUP BY and aggregate functions like SUM, AVG, COUNT when the task asks for totals, averages, or counts per category.
- Use conditional aggregation with CASE statements to compute multiple aggregate metrics (e.g., counts, sums) across different categories within a single query when the task requires segmented analysis without filtering.
