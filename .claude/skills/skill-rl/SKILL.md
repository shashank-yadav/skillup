---
name: skill-rl
description: Operate this repo (skill-rl) -- a framework for distilling agent trajectories into a portable SKILL.md and evaluating whether it measurably improves the same frozen model on unseen tasks. Use this skill when asked to train a skill for an environment, evaluate a trained skill, add a new environment or training algorithm to this repo, or install a trained skill into another harness (Claude Code, Codex, OpenCode, ...).
---

# skill-rl

Trains and evaluates portable `SKILL.md` files -- no model weight updates.
Environments and training algorithms are both pluggable; ALFWorld/SearchQA/
LiveMathematicianBench and five strategies (naive/gated/expel/avo/reflact)
ship as references. See `README.md` for full depth; this skill is the fast
path for common operations.

## Setup (once)

```bash
source .venv/bin/activate          # created with python3.9-3.11 (ALFWorld's TextWorld dep caps this)
export OPENROUTER_API_KEY=sk-or-...
export ALFWORLD_DATA="$HOME/.cache/alfworld"   # only needed for the alfworld environment
```

If `.venv` doesn't exist yet, follow the "Quick start" section of `README.md`.

## Core loop, for one environment (e.g. "alfworld")

```bash
python collect_trajectories.py --env alfworld              # -> experiments/alfworld/data/training/trajectories.jsonl
python train_skill.py --env alfworld --strategy all         # -> experiments/alfworld/skills/SKILL*.md
python evaluate_skill.py --env alfworld                     # -> experiments/alfworld/results/summary.txt
```

- `--strategy all` trains naive/gated/expel/avo in one pass so `evaluate_skill.py`
  compares all of them against baseline in the same run; `--strategy naive`
  (etc.) trains just one. `reflact` isn't in `all` -- it rolls out live training
  episodes every step instead of reusing pre-collected trajectories, so it
  costs meaningfully more; run it explicitly with `--strategy reflact`.
- `evaluate_skill.py` runs every condition in parallel across
  `max_parallel_workers` (config.yaml) OS processes automatically -- no
  manual shard orchestration needed. Read `results/summary.txt` for the
  headline success-rate table, `results/summary.json` for per-task detail.
- Both scripts read `experiments/<env>/config.yaml` for task counts/split
  sizes and the root `config.yaml` for model choice -- check those before
  assuming a knob doesn't exist.

## Installing a trained skill into another harness

```bash
python install_skill.py --env alfworld --strategy naive --target ~/.claude/skills
```

Copies the trained `SKILL.md` to `<target>/<name>/SKILL.md`. This works
as-is for Claude Code, Codex, OpenCode, or the shared `~/.agents/skills`
convention -- they all read the same frontmatter + markdown shape this repo
already produces. Use `--target ./.claude/skills` for a project-level
install instead of a user-level one.

## Training through an external harness instead of the API

Add `--harness cli` to `collect_trajectories.py` / `train_skill.py` /
`evaluate_skill.py` to route every action-selection call through an
external CLI tool (Claude Code, OpenCode, ...) instead of a direct API
call, so the resulting skill reflects how that tool actually behaves. Needs
`harness.cli.command` set in `config.yaml` (a shell template with
`{system_prompt}`/`{user_prompt}` placeholders) -- see `core/backend.py`
and the "Training through your own harness" section of `README.md` for the
verified Claude Code command.

## Adding a new environment

Create `environments/<name>/env.py` implementing `core.environment.Environment`
(`reset()`/`step()`/`close()`/`num_tasks`, with `info` always carrying
`admissible_commands`/`won`/`task_id`/`task`; pass `admissible_commands=[]`
for a free-form single-turn task like QA, not a discrete-action game). Call
`core.environment.register("name", YourClass)` at import time, import the
module from `environments/__init__.py`, then add
`experiments/<name>/config.yaml` (copy `experiments/alfworld/config.yaml`)
and `experiments/<name>/skills/SKILL.initial.md`. The three scripts above
work immediately with `--env name` -- nothing else changes. For a dataset
already on Hugging Face with a prompt column and a reference-answer column,
`environments/hf_dataset/env.py` is a ready-made adapter -- just point
`experiments/<name>/config.yaml`'s `hf_dataset:` section at it, no new code.

## Adding a new training algorithm

Create `trainers/<name>.py` exposing `run(ctx: core.trainer.TrainerContext)
-> {"skill": str, "history": [...]}`, call `core.trainer.register("name",
run)` at import time, and import it from `trainers/__init__.py`. It's then
available as `--strategy name`. Reuse `core.skill`'s helpers
(`parse_insights`/`render_insights`/`apply_delta`/`extract_insight_delta`)
for the "preamble + flat insight list, edited via small structured deltas"
representation the existing strategies use -- full-document rewrites are
fragile with cheap models (repetition collapse, or the model copying the
prompt's own context back as if it were an edit); reuse `core.trainer.dev_eval`
for a validation-gated strategy's held-out scoring.

## Where things actually live

```
core/            environment-agnostic framework (agent loop, backend, trainer registry, parallel runner)
environments/    one plugin per environment, self-registering
trainers/        one module per training algorithm, self-registering
experiments/<env>/   that environment's config.yaml, skills/, data/, results/
```

Don't guess at file locations or config keys -- `grep` for the relevant
registry (`core/environment.py`, `core/trainer.py`) or read
`experiments/<env>/config.yaml` directly; the shape is small enough that
reading beats assuming.
