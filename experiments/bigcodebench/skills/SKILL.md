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

### Input Validation and Error Handling
- **Check for invalid inputs**: Before performing operations, validate that inputs are of the expected type and format. Handle edge cases such as empty lists, zero values, or invalid file paths.
- **Raise specific exceptions**: When errors occur due to invalid inputs or unexpected conditions, raise appropriate exceptions (e.g., `ValueError`, `FileNotFoundError`, `statistics.StatisticsError`) with informative messages.
- **Handle subprocess errors**: When using `subprocess`, use `check=True` or explicitly check the return code and capture `stderr` to handle command execution failures gracefully.

### Data Manipulation and Transformation
- **Use appropriate libraries**: Leverage libraries like `pandas`, `numpy`, `collections`, `itertools`, `random`, `statistics`, `scipy`, and `sklearn` for efficient data manipulation, statistical calculations, and machine learning tasks.
- **Handle missing values**: Before performing calculations or visualizations, address missing values (NaNs) by imputing them (e.g., with the column's mean) or by dropping rows/columns as appropriate for the task.
- **Type conversion**: Ensure data types are correct before performing operations. For example, convert string representations of numbers or dictionaries to their actual types using `int()`, `float()`, `ast.literal_eval()`, or `json.loads()`.
- **Data normalization and scaling**: Use `StandardScaler` or `MinMaxScaler` from `sklearn.preprocessing` when data requires normalization or scaling for certain algorithms or visualizations.

### File Operations
- **Check file/directory existence**: Before reading from or writing to files/directories, verify their existence using `os.path.exists()`. Create directories if they don't exist using `os.makedirs()`.
- **Safe file handling**: Use `with open(...)` for file operations to ensure files are properly closed, even if errors occur.
- **Archiving and compression**: Utilize libraries like `zipfile` and `shutil` for creating archives and `tarfile` or `subprocess` with `tar` for creating compressed archives.

### Visualization
- **Clear plot labeling**: Ensure all plots have descriptive titles, x-axis labels, and y-axis labels.
- **Appropriate plot types**: Choose visualization types (e.g., bar plot, histogram, heatmap, scatter plot, line plot, box plot, KDE plot) that best represent the data and the task's requirements.
- **Handle empty data for plotting**: If a plot cannot be generated due to empty or insufficient data, return `None` or an appropriate indicator as specified by the task.
- **Figure and Axes management**: When creating plots, manage `Figure` and `Axes` objects correctly, especially when returning them or saving plots to files.

### Algorithmic Strategies
- **Iterate and aggregate**: For tasks involving processing collections of items (lists, dictionaries, files), iterate through them and aggregate results using appropriate methods (e.g., `sum()`, `mean()`, `Counter()`, `reduce()`).
- **Conditional logic**: Implement conditional logic (`if/else`) to handle different scenarios, such as varying input lengths, specific data patterns, or error conditions.
- **Regular expressions**: Use `re` for pattern matching and text manipulation, especially when dealing with strings, file names, or specific text formats.

### Code Structure and Readability
- **Import necessary modules**: Ensure all required modules are imported at the beginning of the function.
- **Use meaningful variable names**: Choose descriptive names for variables to improve code clarity.
- **Add comments**: Include comments to explain complex logic or non-obvious steps.
- **Follow function signature**: Adhere to the provided function signature, including default arguments and type hints.
- **Return expected types**: Ensure the function returns values of the types specified in the task description.

---
