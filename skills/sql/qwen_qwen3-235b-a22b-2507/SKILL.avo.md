---
name: sql
description: Strategies for writing correct SQL queries against a given schema.
---

# SQL

Write a single SQLite query that answers the question against the given
schema. Respond with only the query -- no explanation, no markdown code
fences, no semicolon-separated multiple statements.

## Insights

- Use GROUP BY and aggregate functions (e.g. SUM, AVG, COUNT) when the task asks for totals, averages, or counts per category.
- Use JOINs to combine data from multiple tables when the required information spans across them.
- Use subqueries with aggregate functions like MAX or MIN in the WHERE clause to find records matching the extreme value.
- When filtering by date ranges, use explicit comparisons or date functions to ensure correct temporal filtering.
