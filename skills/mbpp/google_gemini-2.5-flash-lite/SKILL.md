---
name: mbpp
description: Strategies for solving MBPP Python programming problems.
---

# MBPP

Write a Python function that satisfies the given tests. Respond with only
the function definition(s) needed -- no explanation, no example usage, no
markdown code fences, no test code of your own.

## General Strategies

### Input Validation and Edge Cases
- Always consider edge cases such as empty inputs, zero values, negative numbers, and inputs that might cause division by zero.
- For functions involving lists or sequences, handle cases where the input is empty or has only one element.
- For mathematical functions, check for invalid inputs (e.g., negative numbers for square roots, angles outside valid ranges).

### Algorithm Selection and Implementation
- **Sorting:** If the problem involves ordering or finding relationships based on order, sorting the input is often a crucial first step.
- **Iteration and Accumulation:** Many problems require iterating through a collection and accumulating a result (sum, count, max, min, etc.). Use appropriate data structures (like sets for uniqueness, dictionaries for counts/grouping) to optimize these operations.
- **String Manipulation:** For string problems, leverage built-in string methods (`.split()`, `.join()`, `.replace()`, `.upper()`, `.isdigit()`) and consider regular expressions for more complex pattern matching and replacement.
- **Mathematical Operations:** For numerical problems, use the `math` module for functions like `sqrt`, `pi`, and trigonometric operations. Be mindful of floating-point precision.
- **Bitwise Operations:** For problems involving bit manipulation, understand the common bitwise operators (`&`, `|`, `^`, `~`, `<<`, `>>`) and their applications in tasks like setting/clearing bits or checking parity.
- **Dynamic Programming:** For problems that can be broken down into overlapping subproblems, consider dynamic programming approaches to store and reuse intermediate results.

### Code Structure and Readability
- Use meaningful variable names.
- Add comments to explain complex logic or non-obvious steps.
- Ensure functions have clear docstrings explaining their purpose, arguments, and return values.

### Testing and Debugging
- Pay close attention to the provided test cases. They often reveal hidden requirements or edge cases.
- If a solution fails, carefully re-examine the test cases and the logic, especially for the failing inputs.
- Consider the data types involved and potential type errors.

## Specific Strategies

### List/Sequence Manipulation
- **Removing elements:** Use slicing (`lst[:k-1] + lst[k:]`) or list comprehensions for efficient removal.
- **Reversing elements:** Slicing (`[::-1]`) is a concise way to reverse sequences.
- **Swapping elements:** Direct index assignment (`lst[0], lst[-1] = lst[-1], lst[0]`) is efficient for swapping first and last elements.
- **Moving elements:** For moving specific elements (like zeros to the end), use two pointers or create new lists based on conditions.
- **Rotating lists:** Slicing is effective for right or left rotations: `lst[-n:] + lst[:-n]` for right rotation by `n`.

### String Manipulation
- **Replacing characters/substrings:** Use `.replace()` for simple replacements or `re.sub()` for pattern-based replacements.
- **Extracting information:** Use string methods like `.find()`, `.split()`, or regular expressions (`re.search()`) to locate and extract parts of strings.
- **Character type checks:** `.isdigit()` is useful for identifying numeric characters.

### Mathematical Computations
- **Averages:** Sum elements and divide by the count. Handle empty collections to avoid division by zero.
- **Powers:** Use the `**` operator or `math.pow()`.
- **Trigonometry and Geometry:** Utilize the `math` module for `sin`, `cos`, `pi`, etc. Ensure angles are in the correct units (radians vs. degrees).
- **Prime numbers:** Implement trial division up to the square root of the number.
- **Bitwise operations:**
    - To set the rightmost unset bit: `n | (n + 1)`
    - To toggle middle bits: Construct a mask that excludes the first and last bits and XOR with the number.

### Data Structures
- **Sets:** Use sets for efficient membership testing and to find unique elements.
- **Dictionaries:** Use dictionaries for counting occurrences, grouping items, or mapping values to keys.

### Common Pitfalls
- **Off-by-one errors:** Be careful with loop ranges and index calculations, especially when dealing with 0-based vs. 1-based indexing.
- **Floating-point precision:** When comparing or performing calculations with floats, consider potential precision issues. Rounding might be necessary.
- **Mutability:** Be aware of whether you are modifying a list in-place or creating a new one.
- **Hashability:** Ensure that elements you try to add to sets or use as dictionary keys are hashable (e.g., tuples are hashable, lists are not). Convert lists to tuples if needed.
