---
name: bigcodebench
description: Strategies for solving BigCodeBench Python programming problems.
---

# BigCodeBench

Write a Python function that satisfies the given instructions and passes
its hidden unit tests. Respond with only the function definition(s)
needed -- no explanation, no example usage, no markdown code fences, no
test code of your own.

## General Strategies

1. **Read Instructions Carefully**: Identify required inputs, outputs, error handling, and any special constraints (e.g., default values, specific data types, formatting). Pay attention to edge cases explicitly mentioned.

2. **Handle Edge Cases**: Check for empty inputs, invalid values, and boundary conditions. Return appropriate values (e.g., empty list, None, 0) or raise specified exceptions as instructed.

3. **Validate Inputs Early**: If the task specifies input validation (e.g., negative length, missing files), perform checks at the start and raise clear exceptions with the exact messages indicated.

4. **Follow Output Format Precisely**: Return the exact data type specified (e.g., tuple, DataFrame, Axes, dict, list). If returning multiple items, ensure the order matches the description.

5. **Use Provided Imports**: Do not add extra imports unless necessary. The starter code includes required modules; use them as intended.

6. **Implement Robust Error Handling**: For file operations, network requests, or subprocess calls, catch exceptions and raise the specified error types with the exact message format required.

7. **Adhere to Naming and Structure**: Keep default parameter values as given. Use constants if provided. Maintain column names, plot labels, and titles exactly as specified.

8. **Ensure Self-Contained Code**: The function should run independently without relying on external state or global variables not passed as arguments.

9. **Test with Simple Examples**: Mentally verify the function works for basic cases, including defaults. Ensure loops terminate, recursive structures are bounded, and resources are closed.

10. **Avoid Overcomplication**: Implement the minimum required logic. Do not add extra features, optimizations, or steps not requested.

## Common Pitfalls to Avoid

- **Missing Returns**: Ensure all code paths return the correct type, especially in conditionals.
- **Incorrect Exception Messages**: Use the exact string format shown in the instructions for raised exceptions.
- **Modifying Inputs**: Unless specified, avoid altering input data structures; copy if necessary.
- **Ignoring Defaults**: Use default parameter values exactly as provided in the starter code.
- **Plotting Errors**: When returning matplotlib objects, avoid calling `plt.show()` unless required; instead, return the Axes or Figure object.
- **Assumptions About Data**: Do not assume specific column names or data shapes beyond what the instructions specify.
