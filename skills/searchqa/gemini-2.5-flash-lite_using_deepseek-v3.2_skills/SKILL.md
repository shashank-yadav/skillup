---
name: searchqa
description: Strategies for answering SearchQA trivia questions.
---

# SearchQA

Answer the trivia question with the shortest correct answer possible -- a
name, term, or short phrase. Do not explain your reasoning, restate the
question, or add extra words.

## General Strategy

- The answer is almost always a single word or a short, specific phrase (e.g., "John Adams", "cud", "UV index", "business class").
- Do not produce sentences, explanations, or commentary. The successful examples show only the answer.
- If the clue contains a number in parentheses like (3), (5), or (8), it usually indicates the number of letters in the answer for a crossword-style clue. Provide only the word that fits.
- For quotes or poetic lines, identify the most famous person, place, or thing they refer to, not the quote itself.
- For clues that are just a name or place (e.g., "Cook Islands"), the answer is typically the most specific associated item (like a capital), not a description.
- Avoid conversational responses like "I'm ready to begin" or "I don't understand." Always output a guess in the required short format.
- When a clue references a person by a description (e.g., "Outlaw: 'Murdered by a traitor...'"), answer with the name of the person described (e.g., "Jesse James"), not the traitor or an explanation.
