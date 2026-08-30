You are extracting reusable insights from an AI agent's experience in ALFWorld, a
text-based household simulator. The agent's skill is a list of insight bullets; you
propose small changes to that list, not a full rewrite.

This is round {round_number}. Look at the current insights and the trajectories below,
and decide what to ADD or REMOVE.

Rules:
- Learn general strategies, not task-specific facts. Do not mention individual tasks,
  objects, or locations from the trajectories below.
- Only propose an insight to ADD if it is not already covered (even if phrased
  differently) by one of the current insights listed below.
- Only propose an insight to REMOVE if a trajectory below shows it is wrong or actively
  unhelpful.
- Prefer concrete, procedural insights over vague advice.
- Propose at most 3 additions and at most 2 removals this round.

Respond with ONLY a JSON object of this exact shape, and nothing else -- no markdown, no
code fences, no explanation:

{{"add": ["new insight one", "new insight two"], "remove": ["exact text of an existing insight to delete"]}}

Use an empty list for "add" and/or "remove" if there is nothing to change.

## Current insights

{current_insights}

## Successful trajectories

{success_trajectories}

## Failed trajectories

{failed_trajectories}
