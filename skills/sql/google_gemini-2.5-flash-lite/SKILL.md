---
name: sql
description: Strategies for writing correct SQL queries against a given schema.
---

# SQL

Write a single SQLite query that answers the question against the given
schema. Respond with only the query -- no explanation, no markdown code
fences, no semicolon-separated multiple statements.

## Strategies

- **Identify the core question:** Determine what information needs to be retrieved or aggregated.
- **Map question to tables and columns:** Identify the relevant tables and columns that contain the necessary data.
- **Use `SELECT` for desired columns:** Specify the columns to be returned.
- **Use `FROM` to specify the table(s):** Indicate the table(s) to query from.
- **Use `WHERE` for filtering:** Apply conditions to filter rows based on specific criteria.
- **Use `JOIN` for combining tables:** When data is spread across multiple tables, use appropriate `JOIN` clauses (e.g., `INNER JOIN`, `LEFT JOIN`) based on the relationship between tables.
- **Use `GROUP BY` for aggregation:** When aggregating data (e.g., `SUM`, `AVG`, `COUNT`, `MAX`, `MIN`), group the results by relevant columns.
- **Use aggregate functions:** Employ functions like `SUM`, `AVG`, `COUNT`, `MAX`, `MIN` to perform calculations on groups of rows.
- **Use `ORDER BY` for sorting:** Sort the results in ascending (`ASC`) or descending (`DESC`) order.
- **Use `LIMIT` to restrict results:** If only a specific number of rows are needed, use `LIMIT`.
- **Use `LIKE` for pattern matching:** Employ `LIKE` with wildcards (`%`, `_`) for flexible string comparisons.
- **Use `IN` for multiple values:** Use `IN` to specify a list of possible values for a condition.
- **Use `BETWEEN` for ranges:** Use `BETWEEN` for conditions that fall within a specified range.
- **Use `STRFTIME` for date/time formatting:** Extract parts of dates (e.g., year, month, week) for filtering or grouping.
- **Use `CAST` for type conversion:** Convert data types when necessary for calculations (e.g., `CAST(SUM(column) AS REAL)` for accurate division).
- **Handle string literals correctly:** Enclose string literals in single quotes (`'`).
- **Handle boolean values:** Use `TRUE` or `FALSE` for boolean comparisons.
- **Use aliases for clarity:** Use table aliases (e.g., `T1`, `T2`) and column aliases (e.g., `AS total_value`) to make queries more readable, especially with joins.
- **Subqueries for complex conditions:** Use subqueries when a condition depends on the result of another query.
- **Be precise with conditions:** Ensure all conditions in the `WHERE` clause accurately reflect the task requirements.
- **Check for missing table/column names:** Ensure all referenced tables and columns exist in the schema.
- **Ensure correct syntax for date functions:** Verify the correct format for date functions like `STRFTIME`.
- **Avoid trailing commas or semicolons:** The output should be a single, valid SQL query without extra punctuation.
