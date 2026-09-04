You are judging whether an AI assistant's code review comment catches
the same real issue a human reviewer actually flagged on this exact
diff.

## The diff

{diff}

## What the real human reviewer actually said about this diff

{reference_review}

## The new review comment being judged

{action}

## Your task

Judge whether the new comment raises the same substantive concern as
the real reviewer's comment -- not whether it's phrased the same way,
and not whether it's a "nice" or thorough-sounding review in general.
A comment that's well-written but points at a different part of the
diff, or misses the actual concern entirely, should fail. A comment
that identifies the same underlying issue in different words, even more
concisely, should pass. If the real reviewer's comment is itself just a
style nitpick or a question rather than a bug, the new comment should
raise a comparable-weight concern to pass, not a more serious one that
wasn't actually there.

Respond with ONLY a JSON object of this exact shape, and nothing else --
no markdown, no code fences, no explanation:

{{"reasoning": "brief justification", "won": true or false}}
