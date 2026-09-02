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

- Always check for edge cases like empty inputs, missing files, or invalid data before proceeding with core logic.
- When a function returns multiple outputs (e.g., DataFrame and plot), ensure both are correctly generated and returned.
- Validate input parameters and handle exceptions early to provide clear error messages.
- When using external commands or subprocesses, handle potential failures gracefully with try-except blocks and provide informative error messages.
- For data processing tasks, ensure that edge cases like empty inputs or missing data are handled explicitly to avoid runtime errors.
- When creating visualizations, always set appropriate labels, titles, and layout to make the plot clear and informative.
- When handling file operations, ensure the target directory exists before writing files, creating it if necessary.
- For statistical calculations, handle edge cases like empty input or single-element lists to avoid runtime errors.
- When using external libraries for data transformation (e.g., StandardScaler, PCA), ensure input data is properly shaped and missing values are handled.
