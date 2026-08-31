```yaml
name: livemathbench
description: Strategies for answering LiveMathematicianBench multiple-choice theorem questions.
---

# LiveMathematicianBench

Each question presents a mathematical theorem statement and asks you to
choose the correct answer from options A through E. Reason carefully about
the mathematical content, then respond with only the single letter (A, B,
C, D, or E) of the correct option -- no explanation, no restating the
option text.

## General Strategies

### Understand the Goal
The primary goal is to select the correct multiple-choice answer. This requires careful reading and understanding of the question and all options.

### Analyze the Question
1.  **Identify Key Concepts:** Break down the theorem statement into its core mathematical concepts, definitions, and assumptions.
2.  **Identify the Question:** Determine precisely what is being asked. Is it about existence, uniqueness, equivalence, a specific property, or a bound?
3.  **Note Constraints/Assumptions:** Pay close attention to any conditions or hypotheses stated in the problem (e.g., "for every sequence," "there exists a constant," "assume that...").

### Evaluate Options Systematically
1.  **Read All Options:** Before committing to an answer, read all options to understand the range of possibilities and potential nuances.
2.  **Compare and Contrast:** Identify similarities and differences between options. Look for subtle wording changes that might alter the meaning significantly (e.g., "for all" vs. "there exists," "$\le$" vs. "$<$").
3.  **Look for Strongest Statement:** The goal is often to find the *strongest* valid statement. This means an option that makes a more precise, general, or encompassing claim, provided it is still true under the given conditions.
    *   Statements with universal quantifiers ("for all," "every") are generally stronger than existential ones ("there exists").
    *   Statements with tighter bounds or more specific conditions are stronger.
    *   Statements that cover more cases or have fewer exceptions are stronger.
4.  **Check for Validity:** For each option, assess its mathematical correctness based on the problem statement and general mathematical knowledge.
    *   If an option introduces new, unsupported assumptions, it is likely incorrect.
    *   If an option contradicts the problem statement or known mathematical facts, it is incorrect.
    *   If an option is a weaker version of another valid option, it is less likely to be the *strongest* correct statement.
5.  **Eliminate Incorrect Options:** Rule out options that are demonstrably false or weaker than other valid options.

### Focus on Quantifiers and Scope
*   **"For every" / "For all"**: These imply the statement must hold universally under the given conditions.
*   **"There exists"**: This implies the statement only needs to hold for at least one instance satisfying the conditions.
*   **"Strongest statement"**: This often means the statement with the most universal quantifiers, the tightest bounds, or the fewest exceptions, while remaining mathematically correct.

### Final Check
*   **Re-read the Question:** Ensure the chosen answer directly addresses the question asked.
*   **Verify Strength:** Confirm that the chosen answer is indeed the *strongest* among the valid options.
```
