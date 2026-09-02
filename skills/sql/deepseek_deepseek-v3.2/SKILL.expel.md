---
name: sql
description: Strategies for writing correct SQL queries against a given schema.
---

# SQL

Write a single SQLite query that answers the question against the given
schema. Respond with only the query -- no explanation, no markdown code
fences, no semicolon-separated multiple statements.

## Insights

- When the task asks for a single value (like total, count, average, max, min) for a specific condition, use a SELECT with an aggregate function (SUM, COUNT, AVG, MAX, MIN) and a WHERE clause to filter.
- If the task requires grouping results by one or more categories, use GROUP BY with the appropriate column(s), often combined with aggregate functions.
- For tasks that involve data from multiple tables, use JOIN to combine them, specifying the matching columns in the ON condition.
- When filtering by date ranges or specific time periods, use appropriate date functions (e.g., strftime, DATE) and comparison operators (>=, <=, BETWEEN).
- For tasks asking for the top N results (e.g., highest, lowest, top 3), use ORDER BY combined with LIMIT.
- When the task asks for a list of items that meet a condition, use SELECT with a WHERE clause to filter rows.
- When the task asks for a percentage or ratio, use a CASE statement inside an aggregate function (like COUNT) and divide by the total count.
- When the task asks for items that are not present in another table or condition, use a subquery with NOT IN or a LEFT JOIN with a NULL check.
