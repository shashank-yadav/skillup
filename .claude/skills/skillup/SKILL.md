---
name: skillup
description: Operate this repo (SkillUp) -- a framework for distilling agent experience into a portable SKILL.md and evaluating whether it measurably improves the same frozen model on unseen tasks. Use this skill when asked to train a skill for an environment, evaluate a trained skill, add a new environment or training algorithm to this repo, or install a trained skill into another harness (Claude Code, Codex, OpenCode, ...).
---

# SkillUp

Trains and evaluates portable `SKILL.md` files -- no model weight updates.
Environments and training algorithms are both pluggable; ALFWorld/SearchQA/
LiveMathematicianBench/MBPP and five strategies (naive/gated/expel/avo/reflact)
ship as references. See `README.md` for full depth; this skill is the fast
path for common operations.

## Setup (once)

If `.venv` doesn't exist yet, run `./install.sh` from the repo root first --
it creates the venv, installs dependencies, and installs this and the
`distill-conversation` skill into every agent skills directory it finds
(`~/.claude/skills`, `~/.codex/skills`, `~/.agents/skills`). Safe to rerun.

```bash
source .venv/bin/activate
export OPENROUTER_API_KEY=sk-or-...   # ask the user for this if unset -- never invent one
export ALFWORLD_DATA="$HOME/.cache/alfworld"   # only needed for the alfworld environment
```

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

## Building a skill from a conversation instead of an environment

No benchmark needed. For one conversation, extend or create a skill in place:

```bash
python distill_conversation.py --transcript conv.json --target ~/.claude/skills --name my-project
```

For a corpus of past conversations, with a real held-out validation gate:

```bash
python convert_conversation.py --transcripts conv1.json conv2.json ... --name my-project
python train_skill.py --env my-project --strategy gated
python evaluate_skill.py --env my-project
```

See `.claude/skills/distill-conversation/SKILL.md` for how to invoke the
first one mid-conversation, in this repo or any other project.

## Installing a trained skill into another harness

```bash
python install_skill.py --env alfworld --strategy naive --target ~/.claude/skills
```

Writes the trained `SKILL.md` to `<target>/<name>/SKILL.md`, versioned (see
below). This works as-is for Claude Code, Codex, OpenCode, or the shared
`~/.agents/skills` convention -- they all read the same frontmatter +
markdown shape this repo already produces. Use `--target ./.claude/skills`
for a project-level install instead of a user-level one.

## Managing deployed skills: history, diff, rollback, merge

Every write `install_skill.py` or `distill_conversation.py` makes to a
`<target>/<name>/SKILL.md` is versioned by `core/skill_store.py` (full-text
snapshots in `<target>/<name>/.skillup/history.jsonl` -- not git, since
`~/.claude/skills` usually isn't a repo). A pre-existing hand-edited skill
gets its current content adopted as v1 automatically the first time
something writes to it. `skill_manager.py` is the CLI for that history:

```bash
python skill_manager.py list --target ~/.claude/skills                        # every skill: insights, version count, last update
python skill_manager.py log my-project --target ~/.claude/skills              # version history
python skill_manager.py diff my-project --target ~/.claude/skills             # previous vs. current (or --from N --to N)
python skill_manager.py rollback my-project --target ~/.claude/skills --to 3  # revert (recorded as a new version, not a rewrite)
python skill_manager.py merge other-name my-project --target ~/.claude/skills # fold one skill's insights into another
```

`merge` is the fix for the same project ending up distilled under two
different `--name`s -- it dedupes near-identical insights the same way
`core.skill.crossover` does for every trainer, and leaves the source skill
in place unless you pass `--delete-src`.

Skill *selection* at conversation start (which of several installed skills
a harness actually loads) is not something this repo controls -- that's the
harness's own job, matching its `description` frontmatter against what
you're doing.

## Training through an external harness instead of the API

Add `--harness cli` to `collect_trajectories.py` / `train_skill.py` /
`evaluate_skill.py` to route every action-selection call through an
external CLI tool (Claude Code, OpenCode, ...) instead of a direct API
call, so the resulting skill reflects how that tool behaves. Needs
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
