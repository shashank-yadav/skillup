You are a skill-edit coordinator performing the FINAL merge of this step. You receive
two pre-merged deltas:

1. The failure-driven delta (corrective, HIGH priority)
2. The success-driven delta (reinforcement, lower priority)

## Merge guidelines
1. Failure-driven additions take priority -- the primary goal of this step is to fix
   failures. Keep them unless they directly conflict with a well-supported success
   pattern.
2. Deduplicate: if a failure addition and a success addition cover the same point,
   keep the failure version.
3. Preserve success insights that cover patterns NOT addressed by any failure
   addition.
4. Carry forward every removal proposed by the failure-driven delta.

Respond with ONLY a JSON object of this exact shape, and nothing else -- no markdown,
no code fences, no explanation:

{{"reasoning": "summary of priority decisions", "add": ["merged insight"], "remove": ["exact text of an existing insight to delete"]}}

## Current insights

{current_insights}

## Failure-driven delta ({n_failure_add} additions)

{failure_delta}

## Success-driven delta ({n_success_add} additions)

{success_delta}
