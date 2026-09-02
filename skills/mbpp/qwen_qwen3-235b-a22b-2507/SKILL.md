---
name: mbpp
description: Strategies for solving MBPP Python programming problems.
---

# MBPP

Write a Python function that satisfies the given tests. Respond with only
the function definition(s) needed -- no explanation, no example usage, no
markdown code fences, no test code of your own.

## General Strategies

- Carefully analyze the test cases to infer the expected behavior, including edge cases.
- Handle edge cases explicitly, such as empty inputs, zero, negative numbers, or single-element inputs.
- Use built-in functions and libraries (e.g., `math`, `re`, `zip`, `map`, `lambda`) when appropriate for clarity and correctness.
- For list or string manipulation, consider list comprehensions, slicing, and built-in methods like `split`, `join`, `strip`, `replace`, or `isdigit`.
- When processing sequences, iterate carefully and maintain state (e.g., using sets or dictionaries) to track seen elements or counts.
- For mathematical functions, ensure correct formulas and use floating-point arithmetic when needed.
- When working with recursion, ensure base cases are correct and recursive calls progress toward termination.
- For sorting and dynamic programming problems, sort input if order is not guaranteed, and use DP arrays to store intermediate results.
- When using regular expressions, anchor patterns (e.g., `^`, `\b`) and escape special characters when matching literals.
- Return values exactly as specified (e.g., strings, tuples, lists) and ensure no syntax errors (e.g., unclosed strings, missing returns).
- Avoid off-by-one errors in loops and indexing, especially when using ranges or slicing.
- For bit manipulation, use bitwise operators (`|`, `&`, `^`, `<<`, `>>`) and understand binary representations.
- When flattening or transforming nested structures, use nested loops or comprehensions with `zip(*...)` for transposition.
- Always validate input constraints (e.g., IP address octets in [0,255]) and return correct error responses.
- For geometric or trigonometric calculations, use `math.pi` and correct formulas (e.g., area, arc length, lateral surface).
- In recursive or iterative sequences (e.g., Fibonacci-like), initialize base values correctly and iterate from known states.
- When comparing floating-point results, rely on exact decimal matches as per test expectations.
- For problems involving pairs or combinations, use nested loops with proper indexing to avoid duplicates.
- Ensure string matching patterns correctly handle zero or one occurrence using `?` and full string coverage.
