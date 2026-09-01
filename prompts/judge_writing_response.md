You are judging the quality of an AI assistant's response to a writing
task. You have two reference responses to the same prompt: one rated
higher quality by expert annotators, one rated lower.

## The writing prompt

{writing_prompt}

## A higher-quality reference response

{chosen}

## A lower-quality reference response

{rejected}

## The new response being judged

{action}

## Your task

Judge whether the new response is at least as good as the higher-quality
reference, not merely better than the lower-quality one. Consider
clarity, structure, whether the tone fits what was asked, and whether it
actually accomplishes the task -- not length or surface polish alone; a
longer or more elaborate response is not automatically a better one.

Respond with ONLY a JSON object of this exact shape, and nothing else --
no markdown, no code fences, no explanation:

{{"reasoning": "brief justification", "won": true or false}}
