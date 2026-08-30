You are iteratively refining an AI agent's skill for ALFWorld, a text-based household
simulator. The skill is a list of insight bullets; you propose a small, bounded change
to that list, not a full rewrite. This is round {round_number}: propose one edit, it gets
evaluated against held-out tasks, and it is only kept if it measurably beats the current
best.

Rules:
- Propose at most 2 additions and at most 2 removals this round.
- Only propose an insight to ADD if it is not already covered (even if phrased
  differently) by one of the current insights listed below.
- Only propose an insight to REMOVE if the held-out failures below show it is wrong,
  or if a training trajectory directly contradicts it.
- Learn general strategies, not task-specific facts. Do not mention specific objects,
  locations, or task instances from the trajectories below -- describe the pattern, not
  the example.
- Prefer concrete, procedural insights over vague advice.

Respond with ONLY a JSON object of this exact shape, and nothing else -- no markdown, no
code fences, no explanation:

{{"add": ["new insight one"], "remove": ["exact text of an existing insight to delete"]}}

Use an empty list for "add" and/or "remove" if there is nothing to change.

## Current insights

{current_insights}

## Training trajectories (successes and failures)

### Successful trajectories

{success_trajectories}

### Failed trajectories

{failed_trajectories}

## Failures observed under the CURRENT insights on held-out validation tasks

Use these to diagnose what is still going wrong.

{dev_failures}

## Edits already tried and rejected in earlier rounds (did not beat the current best)

Do not repeat these -- try something different.

{rejected_edits}
