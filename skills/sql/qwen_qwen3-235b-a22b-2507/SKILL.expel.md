---
name: sql
description: Strategies for writing correct SQL queries against a given schema.
---

# SQL

Write a single SQLite query that answers the question against the given
schema. Respond with only the query -- no explanation, no markdown code
fences, no semicolon-separated multiple statements.

## Insights

- Use GROUP BY to aggregate data by one or more columns when computing summary statistics
- Filter data using WHERE before aggregation to focus on relevant subsets
- Join related tables using foreign key relationships to combine information
- Use COUNT(DISTINCT column) to count unique values when duplicates may exist
- Filter date ranges using comparison operators with standardized date formats
- Use subqueries in WHERE clause to find records matching aggregate conditions
- Use ORDER BY with LIMIT to retrieve top or bottom records based on a specific metric
- Filter using date functions to extract and compare parts of dates when needed
