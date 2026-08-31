# skill-rl

**A framework for turning an AI agent's experience into a portable, reusable skill — from a benchmark environment, or from your own real conversations.**

Every time you open a new session with a coding agent, it starts from
zero. It doesn't remember the correction you gave it yesterday, the
pattern that worked well last week, or the mistake it keeps making on
your codebase specifically. skill-rl closes that gap: it turns experience
— either from structured training environments, or from conversations you
actually had — into a `SKILL.md`, a small portable strategy document your
agent loads back in, so it gets better at *your* workflow instead of
staying frozen at day one, every day.

**This is not a new agent, a new harness, or a new model.** It doesn't
replace Claude Code, Codex, OpenCode, Cursor, or whatever you already use
— it plugs into them. Skills produced here are plain `SKILL.md` files in
the same Agent Skills convention those tools already read (`<skills-dir>/<name>/SKILL.md`);
dropping one in is a file copy, not an integration.

## Two ways to build a skill

The point either way: you don't have to depend on a skill someone else
wrote and hope it fits. You generate your own, from your own data, and
*validate* it — measure whether it actually helps before you trust it —
rather than taking a hand-authored file on faith.

**Train against a dataset or environment.** Point skill-rl at a coding
benchmark, a QA dataset, an interactive simulator, or any Hugging Face
dataset, and it runs a real training loop: roll out episodes, distill what
worked and what didn't into candidate skill edits, validate each candidate
against held-out tasks before keeping it, repeat. Five different training
algorithms ship out of the box, from a simple single-shot distillation to a
full reimplementation of Microsoft's published SkillOpt method, so you can
see which one actually earns its keep on your task before committing to
it — refine an existing skill or create a new one from scratch, entirely
from data you control.

**Distill from a real conversation.** The most direct path when there's no
formal dataset: you had a session with your agent, corrected it a few
times, and don't want to make those corrections again next week. Point
`distill_conversation.py` at the transcript and it extracts the
generalizable lessons — what went wrong and what you said to fix it, what
worked and was approved — into a skill your agent picks up automatically
next time. Callable mid-conversation, in any harness, via a skill of its
own (`.claude/skills/distill-conversation/`): just tell your agent to
"remember this" and it does the rest. Have many past conversations instead
of one? `convert_conversation.py` builds a proper held-out split and runs
them through the same validation-gated trainer the benchmark results below
use, instead of a single unchecked pass.

Both paths produce the same thing: a plain markdown file, immediately
usable, that makes the *same, frozen* model measurably better — no
fine-tuning, no weight updates, nothing to deploy but a text file.

## Does it actually work?

Yes, on 3 of 4 benchmarks tested, with real held-out evaluation (never seen
during training) and every condition run under identical model/prompt/step
settings so the skill text is the only variable. And every one of these
numbers was produced by a **small, cheap model** (`google/gemini-2.5-flash-lite`)
— not a frontier model doing the heavy lifting. The point of a skill is to
let a model you can afford to run at volume behave like it learned
something, without touching its weights:

| Benchmark | Baseline (no skill) | Best result | Best strategy |
|---|---|---|---|
| ALFWorld (embodied household tasks) | 17.2% | **27.6%** (+10.4pp) | ExpeL-style |
| SearchQA (trivia QA) | 50.0% | **74.0%** (+24.0pp) | single-shot rewrite |
| MBPP (Python programming) | 39.0% | **51.0%** (+12.0pp) | SkillOpt-style |
| LiveMathematicianBench (research-level math MCQ) | 29.0% | 31.0% (+2.0pp) | single-shot rewrite |

This isn't a novel idea working only in a toy setting, either. `reflact`
here is a faithful port of Microsoft's published SkillOpt method (see
below), and their own reported numbers on the *same benchmarks* -- at
frontier-model scale -- show the same underlying algorithm producing much
larger gains: LiveMathematicianBench **37.6% → 66.9%** (+29.3pp) with
GPT-5.5, and a related SkillOpt-Lite variant reporting **31.2% → 58.8%**
(+27.6pp) on GPT-4o and **36.6% → 73.6%** (+37.0pp) on GPT-5.5. The
underlying method is real, published, and independently shown to work; what
this repo adds is a from-scratch, verified-faithful implementation of it
(plus four other strategies) that you can point at your own environment,
dataset, or conversations with a model you can actually afford to run.

The honest finding underneath the first table: **no single training algorithm
wins everywhere.** A dead-simple single-shot rewrite beat every more
sophisticated method on two of the four benchmarks; a fuller,
validation-gated pipeline modeled on published research won on a third;
and on the hardest benchmark (graduate-level math, where every question is
about a genuinely different theorem), almost nothing helped at all — a
real, informative negative result, not a bug. That's not a weakness of the
framework, it's the actual point of having five interchangeable
strategies: you can find out empirically which one earns its complexity on
*your* task, in an afternoon, instead of guessing.

This repo ships its own meta-skill (`.claude/skills/skill-rl/SKILL.md`) —
if you're driving it from an agent that reads that convention (Claude Code,
Codex, ...), it already knows the commands below.

## Quick start: train against a benchmark or dataset (ALFWorld)

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

## Quick start: distill a skill from a conversation you already had

No environment, no setup beyond an API key. A transcript is a JSON list of
`{"role", "content"}` turns (or just plain text) -- not tied to one
harness's log format.

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install pyyaml requests
export OPENROUTER_API_KEY=sk-or-...

python distill_conversation.py --transcript conv.json --target ~/.claude/skills --name my-project
```

That's it — `~/.claude/skills/my-project/SKILL.md` now exists (or was
extended, if it already did), and any Agent-Skills-aware harness picks it
up on its next session. Got many past conversations, not just one, and want
real validation rather than a single unchecked pass? See
["Distilling a skill from a real conversation"](#distilling-a-skill-from-a-real-conversation-not-a-benchmark)
below for `convert_conversation.py`, which builds a proper train/held-out
split and runs it through the same validation-gated trainer the benchmark
results above use.

The framework itself is deliberately generic underneath this:

- **Environments** are pluggable (`environments/`) -- ALFWorld (multi-turn
  embodied tasks), SearchQA and LiveMathematicianBench (single-turn QA/MCQ,
  via a generic Hugging Face dataset adapter and a dedicated plugin,
  respectively), and MBPP (Python programming, with real code-execution
  grading) ship as reference implementations, but the agent loop and
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

## Distilling a skill from a real conversation, not a benchmark

Everything in "Quick start: train against a benchmark or dataset" above
trains against a structured environment. These two scripts instead turn a
real AI-agent conversation -- corrections included -- into a skill, no
environment required:

```bash
# One conversation, right now: extend/create a skill in place.
python distill_conversation.py --transcript conv.json --target ~/.claude/skills --name my-project

# A corpus of conversations: proper train/dev split + gated.py's validation gate.
python convert_conversation.py --transcripts conv1.json conv2.json ... --name my-project
python train_skill.py --env my-project --strategy gated
python evaluate_skill.py --env my-project
```

A transcript is a JSON list of `{"role", "content"}` turns (or just plain
text) -- not tied to one harness's log format.

`distill_conversation.py` is a single LLM call per conversation: find
corrections and confirmed successes, propose a bounded add/remove insight
edit, apply it directly -- no validation gate, matching `expel`'s
ungated-accumulation design. Good for "learn from this conversation, right
now."

`convert_conversation.py` is for when there are enough past conversations to
warrant real validation. `reflact`/`avo` don't apply here: their gate needs
a *live, re-runnable* environment to roll fresh episodes out against, and a
past conversation isn't re-runnable. What conversations actually look like
structurally is a fixed, pre-collected batch of labeled episodes -- exactly
what `gated`/`expel` already consume. So this script segments each
transcript into episodes (one per attempt, split on corrections so a
mistake-then-fix becomes a real failure episode followed by a real success
episode, not one episode that's vacuously "successful" because it ended
well), holds some out, and points a generated `experiments/<name>/`
at `environments/conversation_judge` for the held-out portion -- an
`Environment` whose `step()` asks an LLM judge "does this new response,
written under the candidate skill, avoid the mistake actually made last
time (or still match what actually worked)?" instead of executing or
matching anything. That's a judged proxy for re-running history, not a real
re-run, but it's the closest honest substitute -- and because it's a normal
`Environment` plugin, `gated`, `core.trainer.dev_eval`, and
`evaluate_skill.py` all work against it completely unchanged.

To make this callable *from inside* a live conversation in any harness that
reads the Agent Skills convention, see
`.claude/skills/distill-conversation/SKILL.md` (also installed at
`~/.claude/skills/distill-conversation/`) -- it tells an agent how to
export the relevant excerpt and invoke `distill_conversation.py`
mid-conversation, not just after the fact.

## Project structure

```
core/                    environment-agnostic framework
  environment.py           Environment protocol + registry
  agent.py                 the LLM agent loop (run_episode) -- no env-specific code
  llm.py                   OpenAI-compatible chat client (targets OpenRouter)
  skill.py                 skill file I/O + insight-list helpers shared by trainers
  conversation.py          transcript-formatting helper shared by the two conversation scripts
  trainer.py                TrainerContext + trainer registry + shared dev-eval helpers
  runner.py                process-based parallel episode runner

environments/            one subpackage per environment; each self-registers
  alfworld/env.py           ALFWorld plugin (wraps its TextWorld backend)
  mbpp/env.py                MBPP plugin (subprocess-sandboxed code-execution grading)
  conversation_judge/env.py  LLM-as-judge plugin for convert_conversation.py's held-out episodes

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
distill_conversation.py, convert_conversation.py               build skills from real conversations instead
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
still implement `Environment` directly, the way `environments/mbpp/env.py`
does (subprocess-executing generated code against test assertions) or
`environments/conversation_judge/env.py` does (an LLM judge instead of
literal execution or matching); the HF adapter is intentionally thin.

## Adding a new training algorithm

Create `trainers/<name>.py` exposing:

```python
def run(ctx: core.trainer.TrainerContext) -> dict:
    ...
    return {"skill": updated_skill_text, "history": [...]}
```

`TrainerContext` carries the LLM client, model settings, the current skill
text, the training trajectories, a round count, and (for strategies that
validate candidates against held-out tasks) `dev_tasks` and everything
`core.trainer.dev_eval` needs to roll out fresh episodes. Reuse
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

## reflact: a fuller port of Microsoft SkillOpt

`reflact` (named after SkillOpt's own internal designation for its
algorithm) replicates the real published method rather than a
reinterpretation of it: on-policy rollout against the live "train" split
every step (not a fixed pre-collected batch, unlike every other strategy
here), one analyst call per minibatch of trajectories, hierarchical
failure/success patch aggregation, a cosine-decaying edit budget (their
published default), gate tracking against both a running "current" and a
best-ever skill, and an epoch-boundary "slow update" mechanism with its own
protected skill region. Hyperparameters default to SkillOpt's own published
config (`batch_size=40`, `minibatch_size=merge_batch_size=8`,
`edit_budget: 4 -> 2`), verified by running the actual upstream
`microsoft/SkillOpt` repository against the same cheap model used
throughout this README -- its gate rejected every step on SearchQA,
identical in kind to what `reflact` does here, confirming the port
faithfully reproduces the real algorithm's behavior rather than just its
shape.

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
