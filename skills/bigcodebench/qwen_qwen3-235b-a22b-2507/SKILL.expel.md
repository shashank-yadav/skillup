---
name: bigcodebench
description: Strategies for solving BigCodeBench Python programming problems.
---

# BigCodeBench

Write a Python function that satisfies the given instructions and passes
its hidden unit tests. Respond with only the function definition(s)
needed -- no explanation, no example usage, no markdown code fences, no
test code of your own.

## Insights

- Handle edge cases like empty input or missing data explicitly at the start of the function.
- When processing data, always validate input types and handle type conversions safely.
- For file operations, check existence and permissions before attempting to read or write.
- When processing data structures, validate their contents (e.g. types, required fields) and handle invalid data explicitly.
- For operations involving external resources (e.g. network, filesystem), use appropriate context managers or cleanup routines to ensure resource safety.
- When processing data structures, explicitly handle cases where input data is empty or missing required keys before performing operations.
- For tasks involving external commands or subprocesses, validate command success and handle errors using appropriate exception handling and logging.
