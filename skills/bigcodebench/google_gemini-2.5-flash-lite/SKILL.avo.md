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

- When processing lists of data, consider using `itertools.chain.from_iterable` to flatten nested iterables for easier processing.
- When dealing with file system operations, always check for the existence of directories and files before attempting to operate on them to prevent `FileNotFoundError`.
- Iterate over a dictionary's values and flatten them into a single list.
- Count the occurrences of items in a list using a Counter object.
