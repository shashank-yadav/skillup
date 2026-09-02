---
name: sql
description: Strategies for writing correct SQL queries against a given schema.
---

# SQL

Write a single SQLite query that answers the question against the given
schema. Respond with only the query -- no explanation, no markdown code
fences, no semicolon-separated multiple statements.

## Strategies

1. **Understand the question precisely**: Identify whether the task asks for counts, sums, averages, maximums, minimums, or lists of values. Pay attention to keywords like "total", "average", "highest", "lowest", "number of", "each", "per", "by", "in", "where", "excluding", "common across", etc.

2. **Use appropriate aggregation functions**:
   - Use `COUNT()` for counting rows or distinct values.
   - Use `SUM()` for total quantities.
   - Use `AVG()` for averages.
   - Use `MAX()` and `MIN()` for extreme values.
   - Always pair aggregations with `GROUP BY` when summarizing by categories.

3. **Filter correctly with WHERE**:
   - Apply conditions on columns to restrict rows before grouping.
   - Use `IN` for multiple discrete values.
   - Use comparison operators (`=`, `!=`, `>`, `<`, `>=`, `<=`) appropriately.
   - For text matching, use `=` for exact matches unless partial matching is needed (use `LIKE` with wildcards carefully).

4. **Handle time/date filtering properly**:
   - Use `BETWEEN`, `>=`, or `<=` with proper date strings (e.g., 'YYYY-MM-DD').
   - Avoid relying solely on string formatting functions unless grouping by time units (year, month, week).
   - When filtering for "last N years", compute the correct start date or use SQLite's `date('now', '-N years')`.

5. **Join tables when necessary**:
   - If data spans multiple tables, identify the key(s) linking them (e.g., ID fields).
   - Use `JOIN` with `ON` to combine tables based on these keys.
   - Always include all relevant tables mentioned in the task.

6. **Group and aggregate at the right level**:
   - Include all non-aggregated SELECT fields in `GROUP BY`.
   - For "per X" or "by X", group by X.
   - When computing totals or averages across groups, ensure the grouping matches the requested granularity.

7. **Use subqueries for conditional extremes**:
   - To find items with maximum or minimum values (e.g., "highest", "lowest"), use a subquery: `WHERE col = (SELECT MAX(col) FROM table)`.
   - This avoids incorrect results from `ORDER BY ... LIMIT 1` when ties are possible or not explicitly allowed.

8. **Return only requested columns**:
   - Do not include extra columns unless the task asks for them.
   - For "list X and Y", select both X and Y.
   - For "how many", return only the count.

9. **Use DISTINCT appropriately**:
   - Use `COUNT(DISTINCT col)` when counting unique occurrences.
   - Use `SELECT DISTINCT` when listing unique combinations.

10. **Avoid common failure patterns**:
    - Do not return plain text or explanations — only the SQL query.
    - Do not use `LIMIT 1` when the logic should inherently return one result via aggregation or subquery.
    - Do not assume gender from names or titles; use available gender columns if present.
    - Do not ignore NULL values when they affect logic (e.g., risk_level can be NULL).
    - Do not hardcode values (e.g., list all African countries) — use available geographic or categorical filters.

11. **Order results only when requested**:
    - Use `ORDER BY` only if the task specifies sorting (e.g., "sorted by", "top", "highest").
    - Use `DESC` for descending order when needed (e.g., highest first).

12. **Handle composite conditions**:
    - Combine multiple conditions with `AND` or `OR` as needed.
    - Use parentheses to clarify logic in complex `WHERE` clauses.

13. **Compute derived metrics directly**:
    - Multiply columns in expressions (e.g., `price * quantity`) when calculating totals.
    - Use arithmetic in `SELECT` (e.g., percentages: `(SUM(flagged) * 100.0 / COUNT(*))`).

14. **Group by time units when needed**:
    - Use `strftime('%Y', date)` for year, `%Y-%m` for year-month, `%Y-%W` for week.
    - Always include the formatted time unit in both `SELECT` and `GROUP BY`.

15. **Verify schema alignment**:
    - Double-check column names and table relationships in the provided schema.
    - Do not assume tables exist beyond what is listed.
