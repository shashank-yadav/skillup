---
name: livemathbench
description: Strategies for answering LiveMathematicianBench multiple-choice theorem questions.
---

# LiveMathematicianBench

Each question presents a mathematical theorem statement and asks you to
choose the correct answer from options A through E. Reason carefully about
the mathematical content, then respond with only the single letter (A, B,
C, D, or E) of the correct option -- no explanation, no restating the
option text.

## General strategies

1. **Identify the strongest statement.**  
   - The correct answer is often the strongest (most precise, most general, most informative) claim among the options that is still provably true.  
   - Compare options carefully: look for differences in quantifiers (e.g., “for every” vs. “there exists”), bounds (tight vs. loose), additional conditions, and conclusions.  
   - If an option says “One of the remaining options is correct, but a stronger result can be proven,” consider whether it is indeed the strongest among the given choices.

2. **Watch for subtle logical distinctions.**  
   - Pay close attention to logical connectors (“and”, “or”, “if … then”), quantifier order (“for every … there exists” vs. “there exists … for every”), and scope of assumptions.  
   - Distinguish between “converges” and “converges uniformly,” “exists” and “exists uniquely,” “O(·)” and “Θ(·),” “almost all” and “all.”

3. **Check for consistency with known theory.**  
   - Use familiarity with standard results (e.g., compactness theorems, classification theorems, asymptotic bounds) to eliminate options that are too weak or obviously false.  
   - When options include explicit constants or rates, consider whether they match known extremal examples or sharp bounds.

4. **Handle “equivalent” questions.**  
   - If the question asks for an equivalent formulation, verify that the chosen option is logically equivalent to the given conditions, not just a consequence.  
   - Look for bidirectional implications; avoid options that are only necessary or only sufficient.

5. **Avoid over-interpreting.**  
   - Do not read extra assumptions into the problem statement. Use only what is given.  
   - Do not rely on task-specific facts from the training trajectories; focus on the mathematical reasoning in the current question.

6. **When in doubt, choose the most informative true statement.**  
   - If multiple options seem plausible, pick the one that gives the most precise description (e.g., exact constant, exact asymptotic, full classification).  
   - If an option claims a stronger result than others and appears mathematically sound, it is likely correct.
