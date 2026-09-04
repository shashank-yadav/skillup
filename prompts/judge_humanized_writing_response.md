You are judging whether an AI assistant's response to a question reads
as genuinely human-written, not as AI-generated text. You have two real
reference answers to the exact same question: one written by a real
person, one written by an AI.

## The question

{question}

## A real human's answer to this question

{human_answer}

## An AI's answer to this question

{ai_answer}

## The new response being judged

{action}

## Your task

Judge whether the new response reads like the human answer, not the AI
answer. Do not judge factual correctness or thoroughness -- judge
writing style. Specifically check for these common AI-writing tells,
and mark the response as failing if it shows several of them clearly:

- Em dash overuse, especially as a substitute for a comma or period
- Hedging or throat-clearing before getting to the point ("It's worth
  noting that...", "It's important to understand...")
- Listicle structure or bullet points where the human answer just talks
  in plain sentences
- Formulaic scaffolding ("Firstly... Furthermore... In conclusion...")
- Vague attributions ("Some people believe...", "Many argue...") instead
  of a direct, opinionated answer
- Rule-of-three phrasing (three examples, three adjectives in a row) used
  as a rhetorical crutch rather than because three items are actually
  needed
- Corporate or promotional-sounding vocabulary for an ordinary, casual
  question
- Ending with an unprompted summary of what was just said

A response can be well-organized and still read as human if a real
person would plausibly write it that way for this specific question.

Respond with ONLY a JSON object of this exact shape, and nothing else --
no markdown, no code fences, no explanation:

{{"reasoning": "brief justification", "won": true or false}}
