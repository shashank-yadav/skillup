---
name: sql
description: Strategies for writing correct SQL queries against a given schema.
---

# SQL

Write a single SQLite query that answers the question against the given schema. Respond with only the query -- no explanation, no markdown code fences, no semicolon-separated multiple statements.

## General Strategies

1. **Read the question carefully.** Identify the exact columns, tables, aggregations, and conditions requested.
2. **Examine the schema.** Note table names, column names, data types, and relationships (e.g., foreign keys).
3. **Break down the question into SQL components:**
   - **SELECT:** Which columns to output? Use aggregate functions (SUM, AVG, COUNT, MAX, MIN) if needed.
   - **FROM:** Which tables? Use JOINs if multiple tables are involved.
   - **WHERE:** What filters apply? Pay attention to exact string matches, date ranges, and numeric comparisons.
   - **GROUP BY:** If aggregating over groups, group by the non‑aggregated columns.
   - **ORDER BY:** If sorting is required.
   - **LIMIT:** If only the top N results are needed.
4. **Use a single query.** Do not output multiple statements or separate queries.
5. **Check for common pitfalls:**
   - **Date filtering:** Use proper SQLite date functions (`strftime`, `DATE`) or direct comparisons when the schema provides exact dates.
   - **String matching:** Use `=` for exact matches unless wildcards (`LIKE`) are truly required.
   - **Aggregations with GROUP BY:** Every non‑aggregated column in the SELECT must appear in the GROUP BY clause.
   - **Handling NULLs:** Use `IS NULL` or `IS NOT NULL`; be careful with comparisons.
   - **Joins:** Specify the join condition explicitly; prefer `INNER JOIN` unless you need all rows from one side.
6. **Test mentally:** Does the query return the exact columns and rows the question asks for? Does it avoid extra or missing data?
7. **Keep it simple.** Avoid unnecessary subqueries or complexity unless required (e.g., for max/min per group).
8. **No formatting.** Output only the plain SQL query, no markdown, no semicolon, no extra text.
