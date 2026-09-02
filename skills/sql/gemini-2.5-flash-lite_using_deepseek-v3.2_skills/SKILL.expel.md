---
name: sql
description: Strategies for writing correct SQL queries against a given schema.
---

# SQL

Write a single SQLite query that answers the question against the given
schema. Respond with only the query -- no explanation, no markdown code
fences, no semicolon-separated multiple statements.

## Insights

- When the task asks for a single value (like total, average, maximum) from a filtered subset, use SELECT with an aggregate function (SUM, AVG, MAX, etc.) and a WHERE clause to filter.
- For tasks that require grouping results by a category (e.g., 'per each', 'by each', 'for each'), use GROUP BY with the appropriate column(s).
- If the task involves data from multiple tables that are related (e.g., joining information about entities), use JOIN to combine the tables on the matching key columns.
- When the task asks for a specific number of top or bottom results (e.g., 'highest', 'lowest', 'top N'), use ORDER BY with LIMIT to retrieve them.
- When the task involves filtering based on a condition that is not a simple equality (e.g., 'more than', 'above', 'after'), use comparison operators (<, >, <=, >=, !=) or date functions in the WHERE clause.
- When the task asks for a count of distinct items or unique combinations, use COUNT(DISTINCT column) or SELECT DISTINCT.
- When the task asks for a percentage or proportion, compute it using a CASE statement or conditional aggregation inside an aggregate function.
- For tasks that involve date ranges (e.g., 'last N years', 'in Q1', 'between dates'), use date functions and comparison operators in the WHERE clause to filter.
- If the task asks for items that meet multiple conditions across different tables, use JOIN with appropriate ON conditions and WHERE filters to combine and filter the data.
