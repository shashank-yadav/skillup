You are training an AI agent to perform tasks in ALFWorld, a text-based household simulator.

Below is the agent's current SKILL.md, followed by trajectories from previous attempts.
Some trajectories succeeded and some failed.

Your job is to extract generalizable strategies that would help the agent perform better
on NEW, unseen ALFWorld tasks, and to return an improved SKILL.md.

Rules:
- Learn general strategies, not task-specific facts.
- Identify recurring causes of failure across the failed trajectories.
- Identify strategies associated with successful trajectories.
- Prefer concrete procedures over vague advice.
- Keep the skill concise.
- Remove advice that appears incorrect or unhelpful, even if it was in the current SKILL.md.
- Do not mention individual training tasks, objects, or locations from the trajectories below.
- Preserve the YAML frontmatter (name/description) at the top of the file.
- Return the COMPLETE updated SKILL.md and nothing else -- no explanations, no code fences.

## Current SKILL.md

{current_skill}

## Successful trajectories

{success_trajectories}

## Failed trajectories

{failed_trajectories}
