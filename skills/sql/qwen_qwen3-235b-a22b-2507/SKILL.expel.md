---
name: sql
description: Strategies for writing correct SQL queries against a given schema.
---

# SQL

Write a single SQLite query that answers the question against the given
schema. Respond with only the query -- no explanation, no markdown code
fences, no semicolon-separated multiple statements.

## Insights

- Use GROUP BY to aggregate data by one or more columns when computing summary statistics like sums, averages, or counts.
- Filter rows using WHERE before grouping when the query requires conditions on individual records.
- Use JOINs to combine data from multiple tables based on a related column, especially when the task involves entities and their attributes across tables.
- Use HAVING to filter grouped data when the condition involves aggregate functions.
- Filter with WHERE on date ranges using standard date formats or date functions when querying time-based data.
- When a query requires finding values that match the maximum or minimum of a column, use a subquery to first determine that extreme value.
- Use DISTINCT in COUNT to count unique values when duplicates may exist in the data.
- Filter date ranges using standard date formats and comparison operators like >, <, or BETWEEN for time-based queries.
- When a query asks for the highest or lowest value, use ORDER BY with LIMIT 1 instead of a subquery if only one row is needed.
