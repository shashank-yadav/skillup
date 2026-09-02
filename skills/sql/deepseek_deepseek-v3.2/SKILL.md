---
name: sql
description: Strategies for writing correct SQL queries against a given schema.
---

# SQL

Write a single SQLite query that answers the question against the given
schema. Respond with only the query -- no explanation, no markdown code
fences, no semicolon-separated multiple statements.

## General Procedure

1. **Parse the question** to identify the required output columns, filtering conditions, aggregations, grouping, and ordering.
2. **Examine the schema** to locate relevant tables and columns. Note data types and relationships (foreign keys).
3. **Construct the query** step by step:
   - Start with `SELECT` columns. Use table aliases for clarity, especially with joins.
   - Add `FROM` and necessary `JOIN` clauses using explicit join conditions (e.g., `ON table1.id = table2.foreign_id`).
   - Apply `WHERE` conditions to filter rows. For date ranges, use `BETWEEN` or comparisons (`>=` and `<=`). For partial matches, use `LIKE` only when necessary.
   - Add `GROUP BY` if aggregations (`SUM`, `AVG`, `COUNT`, `MAX`, `MIN`) are used per group.
   - Use `HAVING` only for conditions on aggregated results.
   - Add `ORDER BY` for sorting and `LIMIT` for top‑N results.
4. **Verify correctness**:
   - Ensure joins do not inadvertently filter out needed rows (use `LEFT JOIN` if retaining all rows from one table is required).
   - Check that aggregate functions match the question (e.g., `SUM` for totals, `AVG` for averages).
   - Confirm date filters use the correct column and format (SQLite dates are strings in `YYYY‑MM‑DD` format; use `strftime` for extracting parts like month or year).
   - For “highest”/“lowest” queries, use `ORDER BY ... DESC/ASC LIMIT 1` or a subquery with `MAX`/`MIN`.
   - For “unique” or “distinct” values, use `DISTINCT` in the `SELECT` clause.
   - When the question asks for “each” category, include a `GROUP BY` on that category.
5. **Write the final query** as a single, well‑formatted SQL statement. Do not include a trailing semicolon.

## Common Pitfalls to Avoid

- **Missing joins**: When data spans multiple tables, join them explicitly. Do not assume a single table contains all needed columns.
- **Incorrect date handling**: For “last N years” or specific months, use `strftime('%Y', date_column)` or `strftime('%m', date_column)`. For relative dates (e.g., “last 6 months”), use `DATE('now', '-6 months')`.
- **Overlooking NULLs**: When checking for absence (e.g., “have not supplied”), include `IS NULL` in the condition.
- **Misinterpreting “each”**: If the question asks for results per group (e.g., “per week”, “per country”), you must include a `GROUP BY` on the grouping column(s).
- **Incomplete filtering**: Apply all relevant filters from the question in the `WHERE` clause. Do not rely on sample data values.
- **Assuming schema names**: Do not include schema prefixes (e.g., `defense.`) unless they are explicitly part of the provided `CREATE TABLE` statement.
- **Hard‑coding values**: Avoid hard‑coding specific names, IDs, or dates that are not explicitly given in the question. Use the described criteria (e.g., `region = 'APAC'`) instead.
- **Ignoring compound conditions**: For “and”/“or” logic, use parentheses to ensure correct precedence.
- **Forgetting DISTINCT**: When the question asks for “unique” combinations, add `DISTINCT` to the `SELECT`.
