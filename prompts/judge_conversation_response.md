You are judging whether an AI coding assistant's response to a situation
avoids a real, previously-observed mistake -- or matches a real,
previously-observed successful pattern. This situation happened before; you
know how it actually went, and you're checking whether a NEW response
(written under a candidate skill's guidance) does at least as well.

## The situation

{situation}

## What actually happened last time

{outcome_label}: {outcome_note}

## The new response (written under the candidate skill's guidance)

{action}

## Your task

{judge_instruction}

Respond with ONLY a JSON object of this exact shape, and nothing else -- no
markdown, no code fences, no explanation:

{{"reasoning": "brief justification", "won": true or false}}
