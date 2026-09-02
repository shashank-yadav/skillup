---
name: searchqa
description: Strategies for answering SearchQA trivia questions.
---

# SearchQA

Answer the trivia question with the shortest correct answer possible -- a
name, term, or short phrase. Do not explain your reasoning, restate the
question, or add extra words.

## Insights

- Before acting, analyze the task text for clues, keywords, and structure to understand what type of answer is required.
- Do not output an answer as the first action unless the task explicitly and unambiguously states the exact action to take.
- If the task is phrased as a riddle, puzzle, or pop culture reference, break it down into components and consider multiple interpretations before committing to an answer.
- When a task mentions a specific name, title, or phrase, verify that your proposed answer matches all given constraints (e.g., date, location, descriptor) before acting.
- If the task is a straightforward factual question, definition, or recall with a single unambiguous answer, provide that answer directly without intermediate analysis.
- If the task presents multiple possible answers or interpretations (e.g., using 'or', listing items, or implying a choice), analyze each option against the clues before selecting and outputting an answer.
- When a task uses indirect phrasing, descriptive clues, or implicit references, interpret the underlying subject based on contextual hints before answering.
