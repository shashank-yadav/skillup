You are one of several parallel lineages evolving an AI agent's skill (a list of insight
bullets) for ALFWorld, a text-based household simulator. This is lineage {lineage_id}.
Each lineage proposes its own edit every generation; an edit is only kept if it beats that
lineage's own previous score on held-out validation tasks. Periodically the two
best-performing lineages get cross-bred into a merged candidate, and a lineage that stops
improving is asked to try something more different rather than a small refinement.

{edit_budget_note}

Rules:
- Only propose an insight to ADD if it is not already covered (even if phrased
  differently) by one of this lineage's current insights below.
- Only propose an insight to REMOVE if the held-out failures below show it is wrong.
- Learn general strategies, not task-specific facts. Do not mention specific objects,
  locations, or task instances from the trajectories below -- describe the pattern, not
  the example.
- Prefer concrete, procedural insights over vague advice.

Respond with ONLY a JSON object of this exact shape, and nothing else -- no markdown, no
code fences, no explanation:

{{"add": ["new insight one"], "remove": ["exact text of an existing insight to delete"]}}

## This lineage's current insights

{current_insights}

## Training trajectories (successes and failures, shared across all lineages)

### Successful trajectories

{success_trajectories}

### Failed trajectories

{failed_trajectories}

## Failures observed under THIS lineage's current insights on held-out validation tasks

{dev_failures}

## Knowledge base: what other lineages have learned works or doesn't (shared)

{knowledge_base}
