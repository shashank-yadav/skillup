# Agent Skill Learning PoC

## Goal

Build a minimal proof of concept demonstrating that an AI agent can improve its performance through experience **without changing model weights**.

The agent learns by generating and updating a standard `SKILL.md` file from previous successful and failed trajectories.

We want to demonstrate:

> Same model + same environment + learned `SKILL.md` → higher success rate on unseen tasks.

This is an experiment, not a production framework. Keep the implementation simple.

---

# 1. Environment

Use **ALFWorld** as the initial environment.

Repository:

`https://github.com/alfworld/alfworld`

ALFWorld provides interactive text-based household tasks with deterministic success/failure signals.

Example task:

> Put a heated apple in the fridge.

The agent may need to:

1. Find the apple.
2. Pick it up.
3. Find a microwave.
4. Heat the apple.
5. Find the refrigerator.
6. Put the apple inside.

The environment provides observations after every action and determines whether the task was successfully completed.

---

# 2. Experiment

We want to compare two conditions.

## Baseline

```text
Model
  ↓
ALFWorld task
  ↓
Actions
  ↓
Success / Failure
```

The model receives normal instructions explaining how to interact with ALFWorld.

It does NOT receive learned skills.

Measure its success rate on a fixed evaluation set.

Example:

```text
100 evaluation tasks
37 successful
63 failed

Success rate: 37%
```

---

## Skill-Augmented Agent

Use the same:

* model
* system prompt
* tools
* environment
* evaluation tasks
* inference settings

But additionally provide a learned `SKILL.md`.

```text
Model
  +
SKILL.md
  ↓
ALFWorld
```

Measure success again.

The primary metric is:

```text
Success rate without SKILL.md
vs.
Success rate with SKILL.md
```

---

# 3. Learning Data

Initially, do NOT implement online learning or reinforcement learning.

Use existing ALFWorld trajectories where possible.

A trajectory should contain:

```text
Task

Observation
Action
Observation
Action
Observation
Action
...

Final result:
SUCCESS / FAILURE
```

We want examples of both successful and failed attempts.

Start with approximately:

```text
50 successful trajectories
50 failed trajectories
```

The exact number is not important. Make it configurable.

If suitable existing trajectories are difficult to use, generate trajectories by running the baseline agent against ALFWorld.

Store trajectories locally in a simple JSONL format.

Example:

```json
{
  "task": "...",
  "steps": [
    {
      "observation": "...",
      "action": "..."
    }
  ],
  "success": false
}
```

---

# 4. Skill Trainer

Create a simple LLM-based trainer.

Input:

```text
Current SKILL.md
+
successful trajectories
+
failed trajectories
```

Ask the trainer to identify **generalizable strategies that would improve performance on future unseen ALFWorld tasks**.

The trainer should NOT memorize specific tasks.

For example, bad learning:

```text
The apple in task 42 was inside cabinet 3.
```

Good learning:

```text
When searching for an object, systematically inspect containers rather than repeatedly moving between rooms.
```

Another example:

```text
For tasks requiring an object to be heated and then placed somewhere:

1. Locate the object.
2. Locate the heating appliance.
3. Heat the object before traveling to the final destination.
4. Verify that the object is still being held after heating.
5. Move to the destination and place it.
```

---

# 5. SKILL.md

Use a normal Agent Skills-style file.

Example:

```text
skills/
  alfworld/
    SKILL.md
```

Initial version:

```markdown
---
name: alfworld
description: Strategies for completing interactive household tasks in ALFWorld.
---

# ALFWorld

Complete the requested household task efficiently.

Observe the environment carefully before taking actions.
```

The trainer produces an improved version.

For example:

```markdown
---
name: alfworld
description: Strategies for completing interactive household tasks in ALFWorld.
---

# ALFWorld

## Planning

Break tasks into:

1. Find target object.
2. Acquire required object.
3. Perform required transformation.
4. Locate destination.
5. Place object.

## Searching

Search systematically.

Avoid repeatedly visiting locations that have already been fully inspected.

Inspect containers when the requested object is not immediately visible.

## Object transformations

Complete required transformations such as heating, cooling, cleaning or slicing before moving to the final destination.

## Failure recovery

If an action fails:

1. Read the environment response.
2. Determine which prerequisite was missing.
3. Correct that prerequisite.
4. Retry the action.

Do not repeatedly execute an invalid action without changing state.
```

The actual content must be generated from trajectories rather than hardcoded.

---

# 6. Trainer Prompt

Start with a simple prompt.

Conceptually:

```text
You are training an AI agent to perform tasks in ALFWorld.

Below are trajectories from previous attempts.

Some succeeded and some failed.

Your job is to extract generalizable strategies that would help the agent perform better on NEW tasks.

Update the provided SKILL.md.

Rules:

- Learn general strategies, not task-specific facts.
- Identify recurring causes of failure.
- Identify strategies associated with successful trajectories.
- Prefer concrete procedures over vague advice.
- Keep the skill concise.
- Remove advice that appears incorrect or unhelpful.
- Do not mention individual training tasks.
- Return the complete updated SKILL.md.
```

Pass trajectories after these instructions.

---

# 7. Evaluation

Create a held-out evaluation set.

Training trajectories must NOT come from these tasks.

Run every evaluation task twice.

### Condition A

```text
Agent
+
base ALFWorld instructions
```

### Condition B

```text
Agent
+
base ALFWorld instructions
+
learned SKILL.md
```

Everything else should remain identical.

Record:

```text
task_id
baseline_success
skill_success
baseline_steps
skill_steps
baseline_tokens
skill_tokens
```

---

# 8. Primary Results

Produce a simple result summary.

Example:

```text
Model: Qwen

Evaluation tasks: 100

Without skill:
Success: 38%

With learned skill:
Success: 56%

Improvement:
+18 percentage points
```

Also report:

```text
Average steps per successful task

Average tokens per task
```

The main result we care about is success rate.

---

# 9. Important Experimental Controls

Do not evaluate the skill on trajectories used to generate it.

Do not change prompts, models or inference settings between baseline and skill runs.

Use the same evaluation tasks for both conditions.

Where possible, control randomness or run enough tasks that randomness does not dominate the result.

Save every trajectory so results can be inspected later.

---

# 10. Project Structure

Keep the repository minimal.

```text
agent-skill-poc/

  README.md

  config.yaml

  environment/
    alfworld.py

  agent/
    agent.py

  trainer/
    trainer.py
    prompt.md

  skills/
    alfworld/
      SKILL.md

  data/
    training/
    evaluation/

  results/

  run_baseline.py
  train_skill.py
  evaluate_skill.py
```

Do not introduce unnecessary abstractions or frameworks.

---

# 11. CLI

Ideally support:

```bash
python run_baseline.py
```

Generates baseline trajectories and/or baseline evaluation results.

```bash
python train_skill.py
```

Reads training trajectories and generates:

```text
skills/alfworld/SKILL.md
```

Then:

```bash
python evaluate_skill.py
```

Runs the baseline and skill conditions and prints the comparison.

Eventually this could become:

```bash
gym train alfworld
gym eval alfworld
```

But do NOT build that abstraction yet.

---

# 12. What We Are NOT Building

Do not implement:

* model fine-tuning
* GRPO/PPO
* vector databases
* complicated memory systems
* multi-agent systems
* dynamic curriculum generation
* skill marketplaces
* MCP infrastructure
* distributed execution
* web UI
* user accounts
* production infrastructure

Those can come later.

The first objective is solely to answer:

> **Can experience from previous agent trajectories be distilled into a portable `SKILL.md` that measurably improves the same model on unseen interactive tasks?**

---

# 13. Success Criteria

The PoC succeeds if we can demonstrate a repeatable improvement such as:

```text
Model alone
42% success

Model + learned SKILL.md
58% success
```

without modifying the model weights.

If this works, the next experiment should test whether the learning process itself can be iterative:

```text
SKILL v0
 ↓
experience
 ↓
SKILL v1
 ↓
new experience
 ↓
SKILL v2
 ↓
...
```

Only after establishing this effect should we build a generalized open-source gym/training framework.
