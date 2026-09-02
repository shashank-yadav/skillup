---
name: sql
description: Strategies for writing correct SQL queries against a given schema.
---

# SQL

Write a single SQLite query that answers the question against the given
schema. Respond with only the query -- no explanation, no markdown code
fences, no semicolon-separated multiple statements.

## Strategy

1. **Parse the question carefully**: Identify the required output (e.g. count, sum, average, list), any filtering conditions, grouping requirements, and sorting or limiting instructions.

2. **Identify relevant tables and columns**: Use the schema to determine which tables contain the needed data. If multiple tables are involved, determine how they are related (e.g. foreign keys, common fields).

3. **Use JOINs when necessary**: If the required data spans multiple tables, join them using appropriate keys. Prefer explicit JOIN syntax over comma-separated FROM clauses.

4. **Apply filtering with WHERE**: Use WHERE to filter rows based on conditions (e.g. equality, date ranges, string matching). For date filtering, use date functions or string prefixes as appropriate.

5. **Aggregate and group correctly**:
   - Use GROUP BY when computing per-group aggregates (SUM, AVG, COUNT, etc.).
   - Use HAVING to filter groups (e.g. "common across all departments").
   - Use DISTINCT in SELECT only when eliminating duplicates is required.

6. **Handle comparisons and subqueries**:
   - For "highest", "lowest", or "maximum" queries, use MAX/MIN in a subquery or ORDER BY with LIMIT 1.
   - Avoid hardcoding values; use subqueries to compute dynamic thresholds.

7. **Format output as requested**:
   - Return only the requested columns.
   - Use aliases (AS) for clarity when computing derived values.
   - For counts, use COUNT(*); for unique counts, use COUNT(DISTINCT).

8. **Avoid common pitfalls**:
   - Do not return plain text or explanations — only SQL.
   - Do not return multiple queries unless explicitly required (rare).
   - Do not assume values not present in the schema.
   - Do not filter on derived values in WHERE; use HAVING if needed after GROUP BY.

9. **Use date functions appropriately**:
   - For year, month, or week-based grouping, use strftime('%Y-%m', date) or similar.
   - For date ranges, use BETWEEN or comparison operators with ISO date strings.

10. **For boolean conditions**: Use = 1 or = 'true' for boolean columns if schema suggests it; otherwise use direct column references if stored as 0/1.
