# skill-rl

A small framework for testing one idea: can experience from an agent's own
trajectories be distilled into a portable `SKILL.md` — a plain markdown
strategy document — that measurably improves the *same, frozen* model on
unseen tasks, with no weight updates? See [PLAN.md](PLAN.md) for the full
research motivation and design.

The framework is deliberately generic:

- **Environments** are pluggable (`environments/`) -- ALFWorld (multi-turn
  embodied tasks), SearchQA and LiveMathematicianBench (single-turn QA/MCQ,
  via a generic Hugging Face dataset adapter and a dedicated plugin,
  respectively) ship as reference implementations, but the agent loop and
  trainers never import anything environment-specific.
- **Training algorithms** are pluggable (`trainers/`) -- five strategies ship
  today: naive single-shot rewrite, a SkillOpt-style validation-gated editor,
  an ExpeL-style incremental insight accumulator, an AVO-style population
  search with crossover and a real supervisor agent, and `reflact`, a fuller
  port of Microsoft SkillOpt's actual training algorithm (on-policy rollout,
  per-minibatch reflection, hierarchical aggregation, a cosine-scheduled edit
  budget, and epoch-boundary slow-update) -- each independently swappable.
- **Experiments** live under `experiments/<env>/` -- config, generated
  skills, trajectory data, and results for one environment, kept together
  and gitignored where it's regenerable.
- **Parallel by default** -- `evaluate_skill.py` runs every condition across
  many concurrent OS processes automatically; no more hand-launching shard
  commands.
- **Trainable through your own harness, not just the API** -- `--harness cli`
  routes rollout through an external CLI tool (Claude Code, OpenCode, ...)
  instead of a direct API call, so a skill reflects how that tool actually
  behaves.

This repo ships its own meta-skill (`.claude/skills/skill-rl/SKILL.md`) --
if you're driving it from an agent that reads that convention (Claude Code,
Codex, ...), it already knows the commands below.

## Quick start (ALFWorld)

Requires Python 3.9-3.11 (ALFWorld's TextWorld dependency doesn't support
newer Pythons).

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install "setuptools<81" wheel   # alfworld's legacy build needs pkg_resources
pip install alfworld pyyaml requests
```

> On Apple Silicon, plain `pip install alfworld` (no `[full]`/`[vis]` extras)
> works natively. The `[full]` extra pulls in `visdom`, which fails to build
> on modern setuptools -- and isn't needed, since this only uses the text
> environment.

Download the ALFWorld game files (a few GB, cached under `~/.cache/alfworld`
by default):

```bash
export ALFWORLD_DATA="$HOME/.cache/alfworld"
alfworld-download
```

Set an OpenRouter API key (used for both the agent and the trainer):

```bash
export OPENROUTER_API_KEY=sk-or-...
```

Model choice lives in [config.yaml](config.yaml); everything ALFWorld-specific
(task counts, split sizes, per-strategy knobs) lives in
[experiments/alfworld/config.yaml](experiments/alfworld/config.yaml).

## Usage

```bash
# 1. Generate training trajectories by running the skill-less agent against
#    the "train" split until the configured success/failure quotas fill.
python collect_trajectories.py --env alfworld

# 2. Distill those trajectories into an updated skill. --strategy all trains
#    every registered strategy so they can be compared in one eval pass.
python train_skill.py --env alfworld --strategy all

# 3. Evaluate on held-out tasks, once without a skill and once per trained
#    variant, using identical model/prompt/settings. Runs every condition
#    across many concurrent processes automatically.
python evaluate_skill.py --env alfworld

# 4. Drop a trained skill into whatever coding-agent harness you already
#    use -- see "Using a trained skill in your own harness" below.
python install_skill.py --env alfworld --strategy naive --target ~/.claude/skills
```

`evaluate_skill.py` prints a success-rate comparison table and writes, under
`experiments/alfworld/`:

- `data/evaluation/baseline_trajectories.jsonl` / `skill_trajectories_<strategy>.jsonl`
- `results/summary.json` (per-task detail) and `results/summary.txt` (the printed table)

Run a single strategy or condition directly when iterating:

```bash
python train_skill.py --env alfworld --strategy gated
python evaluate_skill.py --env alfworld --condition gated
```

## Training through your own harness instead of the API

By default every episode's action-selection call goes straight to the model
API (`core/backend.py`'s `ApiBackend`). Pass `--harness cli` to route it
through an external harness's CLI instead -- so training trajectories (and
therefore the skill later distilled from them) come from how a tool you
already use actually behaves, not from a raw completion:

```bash
python collect_trajectories.py --env alfworld --harness cli
python train_skill.py --env alfworld --strategy gated --harness cli   # affects gated/avo's dev-eval rollouts
python evaluate_skill.py --env alfworld --harness cli
```

This needs `harness.cli.command` set in `config.yaml` -- a shell command
template with `{system_prompt}`/`{user_prompt}` placeholders (substituted in,
shell-quoted, before running), not hardcoded to one product. For Claude
Code, verified end to end:

```yaml
harness:
  cli:
    command: >-
      claude -p {user_prompt} --system-prompt {system_prompt}
      --tools "" --no-session-persistence --output-format text
    timeout_s: 120
```

`--tools ""` and `--no-session-persistence` make Claude Code behave like a
plain chat completion for this purpose -- one clean action back per call,
no tool-use noise, no leftover session state. The same pattern (a
print-and-exit mode, a way to force a system prompt, a way to disable tool
use) should carry over to any similar CLI-based harness; only the command
template changes. Expect ~5-10x the latency of a direct API call, since each
turn spins up a fresh session, and note that usage/token accounting is
unavailable for most external CLIs (`total_tokens` stays 0 for episodes run
this way) and that every call spends whatever account the harness itself is
configured to use.

## Using a trained skill in your own harness

Every skill this framework produces is a plain `SKILL.md`: a YAML
frontmatter (`name`, `description`) plus a markdown body -- the same shape
Claude Code, Codex, OpenCode, and the shared `~/.agents/skills` convention
all already read, each as one `<skills-dir>/<name>/SKILL.md`. There's no
conversion step:

```bash
python install_skill.py --env alfworld --strategy naive --target ~/.claude/skills
python install_skill.py --env alfworld --strategy gated --target ~/.codex/skills --name alfworld-gated
python install_skill.py --env alfworld --strategy naive --target ./.claude/skills   # project-level
```

For a harness with no native skill-loading at all, the file still works --
just paste its body into a system prompt or append it to your own
instructions, the way `core.agent.build_system_prompt` does internally.

## Project structure

```
core/                    environment-agnostic framework
  environment.py           Environment protocol + registry
  agent.py                 the LLM agent loop (run_episode) -- no env-specific code
  llm.py                   OpenAI-compatible chat client (targets OpenRouter)
  skill.py                 skill file I/O + insight-list helpers shared by trainers
  trainer.py                TrainerContext + trainer registry + shared dev-eval helpers
  runner.py                process-based parallel episode runner

environments/            one subpackage per environment; each self-registers
  alfworld/env.py           ALFWorld plugin (wraps its TextWorld backend)

trainers/                 one module per training algorithm; each self-registers
  naive.py / gated.py / expel.py / avo.py / reflact.py
  prompts/                  each strategy's LLM prompt template

experiments/<env>/        one environment's config + generated artifacts
  config.yaml               task counts, split sizes, per-strategy knobs
  skills/                   SKILL.initial.md (pristine v0) + each trained variant
  data/                     generated trajectories (gitignored -- regenerable)
  results/                  summary.json / summary.txt from evaluate_skill.py

collect_trajectories.py, train_skill.py, evaluate_skill.py    entry points
install_skill.py                                               drop a trained skill into any harness's skill dir
```

## Adding a new environment

Create `environments/<name>/env.py` implementing the `core.environment.Environment`
contract:

```python
class YourEnvironment:
    num_tasks: int
    def reset(self) -> tuple[str, dict]: ...          # -> (observation, info)
    def step(self, action: str) -> tuple[str, bool, dict]: ...  # -> (observation, done, info)
    def close(self) -> None: ...
```

`info` must always carry the same four keys, whatever the environment:
`admissible_commands` (the actions accepted right now -- pass `[]` for a
single-turn, free-form-answer task with no fixed action space, like a QA or
math dataset; the agent loop switches to "answer in free text" automatically
when this is empty), `won` (meaningful once `done=True`), `task_id` (a stable
unique id for the episode), and `task` (a human-readable description, set on
`reset`). Anything environment-specific -- a `__init__(self, config, split,
offset=0, count=None)` signature that reads its own section of the config,
quirky pseudo-commands, parsing a task description out of raw text -- stays
inside your plugin.

Register it at import time (`core.environment.register("yourname", YourEnvironment)`)
and import the module from `environments/__init__.py`. Then add
`experiments/<yourname>/config.yaml` (copy ALFWorld's as a starting point) and
`experiments/<yourname>/skills/SKILL.initial.md`. Nothing else changes --
`collect_trajectories.py --env yourname` and friends work immediately.

`environments/hf_dataset/env.py` is a reference single-turn adapter for any
Hugging Face dataset with a prompt column and a reference-answer column --
point it at a dataset name + column names via config and it works with no
new code (needs `pip install datasets`, kept optional since ALFWorld doesn't
need it). A dataset needing custom grading or multi-turn interaction should
still implement `Environment` directly; the adapter is intentionally thin.

## Adding a new training algorithm

Create `trainers/<name>.py` exposing:

```python
def run(ctx: core.trainer.TrainerContext) -> dict:
    ...
    return {"skill": updated_skill_text, "history": [...]}
```

`TrainerContext` carries the LLM client, model settings, the current skill
text, the training trajectories, a round count, and (for strategies that
validate candidates against held-out tasks) `make_env` / `dev_tasks`. Reuse
`core.skill`'s helpers (`parse_insights`/`render_insights`/`apply_delta`/...)
if you want the same "preamble + flat insight list, edited via small
structured deltas" representation the existing strategies use -- full-document
rewrites were found to be fragile with cheap models (repetition collapse, or
copying the prompt's own context back as if it were an edit); a bounded delta
avoids that since merging happens in Python, not in the model.

Register it (`core.trainer.register("yourname", run)`), import it from
`trainers/__init__.py`, and it's immediately available via
`--strategy yourname`.

## AVO's supervisor agent

`avo` tracks whether the population's best dev score has improved each
generation. When it hasn't for `STAGNATION_PATIENCE` generations in a row,
a separate supervisor LLM call (`trainers/prompts/avo_supervisor.md`) is
made -- given every lineage's current insights and score, the shared
knowledge base, and recent accept/reject history -- to diagnose *why* the
population is stuck (converged lineages proposing redundant edits, the same
kind of edit repeatedly rejected, edits too timid to escape a local optimum,
...) and prescribe a directive for that generation's proposers, which
replaces the normal bounded-edit instruction for every lineage until the
population improves again. This is a real agentic call, not a fixed
fallback string, so its intervention differs based on what's actually
happening in the population; a fixed exploratory-edit instruction is used
only if that call's response fails to parse.

## Parallelization

`core/runner.py` splits a condition's tasks into `max_parallel_workers`
(config.yaml) contiguous shards and runs each in its own OS process
concurrently, returning combined results in task order. This is
process-based rather than thread-based on purpose: ALFWorld's PDDL backend
(the `tatsu` grammar parser it uses to load and step through games) keeps
shared, non-reentrant state and was found -- via an actual concurrency
stress test, not a theoretical concern -- to corrupt and crash under
multiple threads, even with just the game-loading step serialized behind a
lock. Separate processes share no memory, so this doesn't apply to them. The
LLM API call is still I/O-bound and the actual bottleneck, so this still
gives real wall-clock speedup; each process's environment setup cost is paid
concurrently across processes, not multiplied by the shard count.

`evaluate_skill.py --condition <label> [--shard-index I --shard-count N]`
exposes the same work as a single process/shard, for isolating a crash or
distributing shards across separate machines; `--merge` assembles a complete
set of shard files into the combined report.

## Experimental controls

- Training trajectories come from the `train` split; evaluation uses
  `valid_unseen`, a disjoint set of environments/objects the skill cannot
  have memorized.
- Every condition in `evaluate_skill.py` uses the same model, temperature,
  max_tokens, and step budget; the only difference is which skill text (if
  any) is appended to the system prompt.
- Every trajectory, in training and every eval condition, is saved to JSONL
  for later inspection.
- The environment's game-file ordering is sorted explicitly rather than
  relying on filesystem traversal order, which was found to differ across
  concurrently-running processes -- this keeps every condition's task
  sequence identical and reproducible regardless of run-to-run concurrency.
