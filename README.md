# SkillUp

![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)
![Agent Skills compatible](https://img.shields.io/badge/Agent%20Skills-compatible-brightgreen)
![No weight updates](https://img.shields.io/badge/model%20weights-untouched-orange)
![MIT license](https://img.shields.io/badge/license-MIT-lightgrey)

**SkillUp gives your AI agent dynamic skills that evolve with every use.**

Every new session with an AI agent starts from zero. It does not remember
yesterday's correction, last week's working pattern, or the mistake it
keeps making on your task. SkillUp turns that experience, from a training
environment or from your own conversations, into a `SKILL.md`: a portable
strategy document your agent loads on the next session so it improves at
your work instead of resetting every time. Coding is one use case among
many; anything an agent does repeatedly (research, support, data work,
whatever your harness handles) works the same way.

**This is not a new agent, harness, or model.** It does not replace Claude
Code, Codex, OpenCode, Cursor, or whatever you use now; it plugs into them.
Skills produced here are plain `SKILL.md` files in the same Agent Skills
convention those tools already read (`<skills-dir>/<name>/SKILL.md`).
Installing one is a file copy, not an integration.

On a small, cheap model (`google/gemini-2.5-flash-lite`, not a frontier
one), a skill trained here took MBPP from 39% to 51% and SearchQA from 50%
to 74%, measured on held-out tasks the skill never saw during training.
Full numbers, every benchmark, in [Does it work?](#does-it-work) below.

## Contents

- [Install this by asking your agent](#install-this-by-asking-your-agent)
- [Use it through your AI agent](#use-it-through-your-ai-agent)
- [Two ways to build a skill](#two-ways-to-build-a-skill)
- [Does it work?](#does-it-work)
- [Quick start: train against a benchmark (MBPP)](#quick-start-train-against-a-benchmark-or-dataset-mbpp)
- [Quick start: distill from a conversation](#quick-start-distill-a-skill-from-a-conversation-you-already-had)
- [Managing skills: history, diff, rollback, merge](#managing-skills-history-diff-rollback-merge)
- [Project structure](#project-structure)
- [Adding a new environment](#adding-a-new-environment)
- [Adding a new training algorithm](#adding-a-new-training-algorithm)

## Install this by asking your agent

You don't run any of this by hand. Point your agent (Claude Code, Codex,
Cursor, OpenCode, whatever you already use) at wherever you have this repo
checked out and paste this:

> Set up SkillUp from this repo: run `./install.sh`, then check whether
> `OPENROUTER_API_KEY` is set in this shell -- if not, ask me for it and
> export it. Then tell me you're ready.

That's the whole install. `install.sh` creates a virtualenv, installs
dependencies, and copies this repo's two meta-skills into every agent
skills directory it finds on your machine (`~/.claude/skills`,
`~/.codex/skills`, and the shared `~/.agents/skills` convention) -- the
only thing it can't do for you is hand over your OpenRouter API key, which
is why the prompt above tells your agent to ask. Rerunning it is safe; it
only ever updates its own files. Once it reports back, every command in
this README is something you ask for in plain language, not something you
type -- see below.

## Use it through your AI agent

This repo ships two meta-skills so an agent that reads the Agent Skills
convention already knows what to do once installed: `skillup` (train and
evaluate skills against an environment or dataset) and
`distill-conversation` (build a skill from a conversation, callable
mid-conversation). Tell it what you want, in plain language:

- "Train a skill for MBPP and evaluate it."
- "Distill a skill from this conversation and save it as backend-service."
- "Add a new environment for `<your dataset>` and train `gated` on it."

Your agent runs the underlying `python train_skill.py ...` calls itself;
the rest of this README is what it's executing, in case you want to run a
step by hand or understand what's happening.

## Two ways to build a skill

Both paths remove the need to depend on a skill someone else wrote and
hope it fits. You generate your own from your own data, and validate it:
measure whether it helps before you trust it, instead of taking a
hand-authored file on faith.

**Train against a dataset or environment.** Point SkillUp at a coding
benchmark, a QA dataset, an interactive simulator, or any Hugging Face
dataset. It runs a training loop: roll out episodes, distill what worked
and what didn't into candidate skill edits, validate each candidate
against held-out tasks before keeping it, repeat. Five training algorithms
ship out of the box, from a single-shot distillation to a full
reimplementation of Microsoft's published SkillOpt method, so you can
measure which one earns its keep on your task before committing to it.
Refine an existing skill or create one from scratch, from data you
control.

**Distill from a conversation.** For when there's no formal dataset: you
had a session with your agent, corrected it a few times, and don't want to
repeat those corrections next week. Point `distill_conversation.py` at the
transcript. It extracts the generalizable lessons, what went wrong and
what you said to fix it, what worked and was approved, into a skill your
agent loads next time. Callable mid-conversation in any harness through a
skill of its own (`.claude/skills/distill-conversation/`): tell your agent
to "remember this" and it handles the rest. For many past conversations,
`convert_conversation.py` builds a held-out split and runs them through the
same validation-gated trainer the benchmark results below use, instead of
one unchecked pass.

Both paths produce the same output: a plain markdown file that makes the
same, frozen model measurably better. No fine-tuning, no weight updates,
nothing to deploy but a text file.

## Does it work?

On 3 of 4 benchmarks tested, yes, measured with held-out evaluation data
never seen during training, every condition run under identical model,
prompt, and step settings so the skill text is the only variable. Every
number below came from a **small, cheap model**
(`google/gemini-2.5-flash-lite`), not a frontier model. A skill lets a
model you can afford to run at volume perform as if it learned something,
without touching its weights:

| Benchmark | Baseline (no skill) | Best result | Best strategy |
|---|---|---|---|
| ALFWorld (embodied household tasks) | 17.2% | **27.6%** (+10.4pp) | `expel` |
| SearchQA (trivia QA) | 50.0% | **74.0%** (+24.0pp) | `naive` |
| MBPP (Python programming) | 39.0% | **51.0%** (+12.0pp) | `reflact` |
| LiveMathematicianBench (research-level math MCQ) | 29.0% | 31.0% (+2.0pp) | `naive` |

`reflact` is a faithful port of Microsoft's published SkillOpt method (see
below). Their own reported numbers on the same benchmarks, at
frontier-model scale, show the same algorithm producing larger gains:
LiveMathematicianBench **37.6% -> 66.9%** (+29.3pp) with GPT-5.5, and a
related SkillOpt-Lite variant reporting **31.2% -> 58.8%** (+27.6pp) on
GPT-4o and **36.6% -> 73.6%** (+37.0pp) on GPT-5.5. This repo adds a
verified implementation of that method, plus four other strategies, that
you can point at your own environment, dataset, or conversations with a
model you can afford to run.

**No single training algorithm wins everywhere.** `naive`, the simplest
strategy here, beat every more sophisticated method on two of the four
benchmarks. `reflact`, the fullest port of published research, won a
third. On the hardest benchmark (graduate-level math, where every question
covers a different theorem), almost nothing helped: an informative
negative result, not a bug. That is why the framework ships five
interchangeable strategies: you can measure which one earns its complexity
on your task in an afternoon, instead of guessing.

**The conversation-distillation path was checked the same way, not just
asserted.** Everything above trains against a structured benchmark; the
other half of this repo (`convert_conversation.py`) distills a skill from
real conversations instead. To check that path holds up on data it wasn't
designed around, it was run end to end against 120 real multi-turn
conversations from the public OpenAssistant/oasst2 dataset, standing in
for "conversations you already had": segmented into 157 episodes, 47 held
out, trained, then scored by an LLM judge (`environments/conversation_judge`)
against 23 held-out conversations never used for training:

| Strategy | Held-out success | vs. baseline |
|---|---|---|
| Baseline (no skill) | 30.4% | -- |
| `avo` | 30.4% | +0.0pp |
| `gated` | 39.1% | +8.7pp |
| `expel` | 39.1% | +8.7pp |
| `naive` | 47.8% | +17.4pp |
| `reflact` | not applicable | -- |

`reflact` isn't in the table because it structurally can't run here, not
because it was skipped: it rolls out fresh episodes against the live
**train** split every step, and a past conversation isn't re-runnable --
there's no "train" split for it to sample from, only the held-out
`valid_seen`/`valid_unseen` splits `convert_conversation.py` builds. That's
also why `reflact` is absent from `## Two ways to build a skill` and
`convert_conversation.py`'s own docstring: it's reserved for the
benchmark-training path, where a live environment exists to roll out
against, not conversation distillation.

Read `naive`'s number with more caution than the others. It roughly
tripled average response length (811 vs. 258 tokens) with a long, generic
best-practices document rather than lessons traceable to specific
corrections in the source conversations -- plausibly winning partly by
being more thorough, not by having learned something specific; this is
the same full-document-rewrite tendency noted elsewhere in this README.
`gated` and `expel`'s smaller gains came from single, targeted insights
instead (`gated`'s: "when asked to provide specific numerical data,
prioritize verifiable sources," traceable to a real disagreement in the
source conversations about Wikipedia's reliability). `avo`'s population
search reached 0.85 on its own 20-task dev pool during training but
didn't transfer to the held-out set at all -- an overfitting result the
small dev pool made easy to reach, and the held-out check is exactly what
caught it. At n=23, one flipped task is 4.3 percentage points, so treat
this as a directional result, not a precise measurement. But directional
is what the question needed: yes, distilling a skill from real
conversations measurably changes held-out performance, in the same
direction validation exists to catch when it doesn't.

This repo ships its own meta-skill (`.claude/skills/skillup/SKILL.md`). An
agent that reads the Agent Skills convention (Claude Code, Codex, ...)
already knows the commands below.

## Quick start: train against a benchmark or dataset (MBPP)

MBPP (Python programming problems) needs nothing beyond an API key and the
core dependencies, so it's the fastest way to see the whole pipeline run.
If your agent already ran `./install.sh` (see above), skip straight to
"Usage" below -- this is the manual equivalent, for running by hand:

```bash
./install.sh
source .venv/bin/activate
export OPENROUTER_API_KEY=sk-or-...
```

Model choice lives in [config.yaml](config.yaml); everything MBPP-specific
(task counts, split sizes, per-strategy knobs) lives in
[experiments/mbpp/config.yaml](experiments/mbpp/config.yaml). Every
environment in `environments/` works the same way; swap `--env mbpp` for
`--env searchqa`, `--env livemathbench`, or `--env alfworld` below once
you're past the first run. ALFWorld (embodied, multi-turn household tasks)
needs more setup than the others: Python 3.9-3.11 specifically and a
one-time multi-gigabyte game-file download; see
[experiments/alfworld/config.yaml](experiments/alfworld/config.yaml) if you
want it.

## Usage

```bash
# 1. Generate training trajectories by running the skill-less agent against
#    the "train" split until the configured success/failure quotas fill.
python collect_trajectories.py --env mbpp

# 2. Distill those trajectories into an updated skill. --strategy all trains
#    every registered strategy so they can be compared in one eval pass.
python train_skill.py --env mbpp --strategy all

# 3. Evaluate on held-out tasks, once without a skill and once per trained
#    variant, using identical model/prompt/settings. Runs every condition
#    across many concurrent processes automatically.
python evaluate_skill.py --env mbpp

# 4. Drop a trained skill into whatever harness you already use -- see
#    "Using a trained skill in your own harness" below.
python install_skill.py --env mbpp --strategy naive --target ~/.claude/skills
```

`evaluate_skill.py` prints a success-rate comparison table and writes, under
`experiments/mbpp/`:

- `data/evaluation/baseline_trajectories.jsonl` / `skill_trajectories_<strategy>.jsonl`
- `results/summary.json` (per-task detail) and `results/summary.txt` (the printed table)

Run a single strategy or condition directly when iterating:

```bash
python train_skill.py --env mbpp --strategy gated
python evaluate_skill.py --env mbpp --condition gated
```

## Quick start: distill a skill from a conversation you already had

No environment, no setup beyond an API key. A transcript is a JSON list of
`{"role", "content"}` turns (or plain text) -- not tied to one harness's
log format.

```bash
./install.sh   # skip if your agent already ran this
source .venv/bin/activate
export OPENROUTER_API_KEY=sk-or-...

python distill_conversation.py --transcript conv.json --target ~/.claude/skills --name my-project
```

`~/.claude/skills/my-project/SKILL.md` now exists (or was extended, if it
already did), and any Agent-Skills-aware harness picks it up on its next
session. For many past conversations instead of one, and validation
instead of a single unchecked pass, see
["Distilling a skill from a conversation"](#distilling-a-skill-from-a-conversation-not-a-benchmark)
below for `convert_conversation.py`, which builds a train/held-out split
and runs it through the same validation-gated trainer the benchmark
results above use.

The framework itself is generic underneath this:

- **Environments** are pluggable (`environments/`) -- ALFWorld (multi-turn
  embodied tasks), SearchQA and LiveMathematicianBench (single-turn QA/MCQ,
  via a generic Hugging Face dataset adapter and a dedicated plugin,
  respectively), and MBPP (Python programming, with code-execution
  grading) ship as reference implementations, but the agent loop and
  trainers never import anything environment-specific.
- **Training algorithms** are pluggable (`trainers/`) -- five strategies ship
  today: `naive` (single-shot rewrite), `gated` (SkillOpt-style
  validation-gated editor), `expel` (ExpeL-style incremental insight
  accumulator), `avo` (AVO-style population search with crossover and a
  supervisor agent), and `reflact` (a fuller port of Microsoft SkillOpt's
  own training algorithm: on-policy rollout, per-minibatch reflection,
  hierarchical aggregation, a cosine-scheduled edit budget, and
  epoch-boundary slow-update) -- each independently swappable.
- **Experiments** live under `experiments/<env>/` -- config, generated
  skills, trajectory data, and results for one environment, kept together
  and gitignored where it's regenerable.
- **Parallel by default** -- `evaluate_skill.py` runs every condition across
  many concurrent OS processes automatically; no hand-launching shard
  commands.
- **Trainable through your own harness, not just the API** -- `--harness cli`
  routes rollout through an external CLI tool (Claude Code, OpenCode, ...)
  instead of a direct API call, so a skill reflects how that tool behaves.

## Training through your own harness instead of the API

By default every episode's action-selection call goes straight to the model
API (`core/backend.py`'s `ApiBackend`). Pass `--harness cli` to route it
through an external harness's CLI instead, so training trajectories (and
therefore the skill later distilled from them) come from how a tool you
already use behaves, not from a raw completion:

```bash
python collect_trajectories.py --env mbpp --harness cli
python train_skill.py --env mbpp --strategy gated --harness cli   # affects gated/avo's dev-eval rollouts
python evaluate_skill.py --env mbpp --harness cli
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
template changes. Expect roughly 5-10x the latency of a direct API call,
since each turn spins up a fresh session, and note that usage/token
accounting is unavailable for most external CLIs (`total_tokens` stays 0
for episodes run this way) and that every call spends whatever account the
harness itself is configured to use.

## Using a trained skill in your own harness

Every skill this framework produces is a plain `SKILL.md`: a YAML
frontmatter (`name`, `description`) plus a markdown body -- the same shape
Claude Code, Codex, OpenCode, and the shared `~/.agents/skills` convention
all already read, each as one `<skills-dir>/<name>/SKILL.md`. There's no
conversion step:

```bash
python install_skill.py --env mbpp --strategy naive --target ~/.claude/skills
python install_skill.py --env mbpp --strategy gated --target ~/.codex/skills --name mbpp-gated
python install_skill.py --env mbpp --strategy naive --target ./.claude/skills   # project-level
```

For a harness with no native skill-loading at all, the file still works --
paste its body into a system prompt or append it to your own instructions,
the way `core.agent.build_system_prompt` does internally.

## Managing skills: history, diff, rollback, merge

`install_skill.py` and `distill_conversation.py` both write through
`core/skill_store.py`, which versions every change to a deployed skill
(full-text snapshots in `<target>/<name>/.skillup/history.jsonl`, not git --
`~/.claude/skills` usually isn't a repo). Writing the exact same content
twice is a no-op, not a new version, and a pre-existing hand-edited skill
gets its current content adopted as v1 the first time something writes to
it, so nothing is lost by turning this on after the fact.

`skill_manager.py` is the CLI for that history:

```bash
python skill_manager.py list --target ~/.claude/skills                        # every skill: insights, versions, last update
python skill_manager.py log my-project --target ~/.claude/skills              # what changed, and when
python skill_manager.py diff my-project --target ~/.claude/skills             # previous vs. current (or --from N --to N)
python skill_manager.py rollback my-project --target ~/.claude/skills --to 3  # revert -- recorded as a new version, not a rewrite
python skill_manager.py merge other-name my-project --target ~/.claude/skills # fold one skill's insights into another
```

`merge` exists for a specific failure mode: distilling the same project
under two different `--name`s by accident, ending up with two skills a
harness might load inconsistently. It dedupes near-identical insights the
same way every trainer's crossover step does, and leaves the source skill's
directory in place unless you pass `--delete-src`.

What this doesn't do is decide *which* installed skill a harness loads for
a given conversation -- that's the harness's own job, matching each skill's
`description` frontmatter against what you're doing. This only manages the
history of each skill once it exists.

## Distilling a skill from a conversation, not a benchmark

Everything in "Quick start: train against a benchmark or dataset" above
trains against a structured environment. These two scripts instead turn an
AI-agent conversation, corrections included, into a skill, no environment
required:

```bash
# One conversation, right now: extend/create a skill in place.
python distill_conversation.py --transcript conv.json --target ~/.claude/skills --name my-project

# A corpus of conversations: train/dev split + gated.py's validation gate.
python convert_conversation.py --transcripts conv1.json conv2.json ... --name my-project
python train_skill.py --env my-project --strategy gated
python evaluate_skill.py --env my-project
```

A transcript is a JSON list of `{"role", "content"}` turns (or plain text)
-- not tied to one harness's log format.

`distill_conversation.py` is a single LLM call per conversation: find
corrections and confirmed successes, propose a bounded add/remove insight
edit, apply it directly -- no validation gate, matching `expel`'s
ungated-accumulation design. Suited to "learn from this conversation, right
now."

`convert_conversation.py` is for when there are enough past conversations to
warrant validation. `reflact` doesn't apply here: it rolls out fresh
episodes against the live train split every step, and a past conversation
isn't re-runnable. What conversations look like structurally is a fixed,
pre-collected batch of labeled episodes, exactly what `gated`/`expel`/`avo`
already consume (validated -- see "Does it work?" above). So this script segments each
transcript into episodes (one per attempt, split on corrections so a
mistake-then-fix becomes a failure episode followed by a success episode,
not one episode that's vacuously "successful" because it ended well),
holds some out, and points a generated `experiments/<name>/` at
`environments/conversation_judge` for the held-out portion -- an
`Environment` whose `step()` asks an LLM judge whether a new response,
written under the candidate skill, avoids the mistake made last time (or
still matches what worked), instead of executing or matching anything.
That's a judged proxy for re-running history, not a re-run, but the
closest available substitute. Because it's a normal `Environment` plugin,
`gated`, `core.trainer.dev_eval`, and `evaluate_skill.py` all work against
it unchanged.

To make this callable from inside a live conversation in any harness that
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
  skill_store.py            version history for deployed skills (used by install/distill, not trainers)
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
distill_conversation.py, convert_conversation.py               build skills from conversations instead
skill_manager.py                                               list/show/log/diff/rollback/merge deployed skills
install.sh, requirements.txt, requirements-alfworld.txt        one-shot setup (see "Install this by asking your agent")
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
point it at a dataset name and column names via config and it works with no
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
structured deltas" representation the existing strategies use --
full-document rewrites were found fragile with cheap models (repetition
collapse, or copying the prompt's own context back as if it were an edit);
a bounded delta avoids that since merging happens in Python, not in the
model.

Register it (`core.trainer.register("yourname", run)`), import it from
`trainers/__init__.py`, and it's immediately available via
`--strategy yourname`.

## AVO's supervisor agent

`avo` tracks whether the population's best dev score has improved each
generation. When it hasn't for `STAGNATION_PATIENCE` generations in a row,
a separate supervisor LLM call (`trainers/prompts/avo_supervisor.md`) is
made, given every lineage's current insights and score, the shared
knowledge base, and recent accept/reject history, to diagnose why the
population is stuck (converged lineages proposing redundant edits, the same
kind of edit repeatedly rejected, edits too timid to escape a local
optimum, ...) and prescribe a directive for that generation's proposers,
which replaces the normal bounded-edit instruction for every lineage until
the population improves again. This is an agentic call, not a fixed
fallback string, so its intervention differs based on what's happening in
the population; a fixed exploratory-edit instruction is used only if that
call's response fails to parse.

## reflact: a fuller port of Microsoft SkillOpt

`reflact` (named after SkillOpt's own internal designation for its
algorithm) replicates the published method rather than a reinterpretation
of it: on-policy rollout against the live "train" split every step (not a
fixed pre-collected batch, unlike every other strategy here), one analyst
call per minibatch of trajectories, hierarchical failure/success patch
aggregation, a cosine-decaying edit budget (their published default), gate
tracking against both a running "current" and a best-ever skill, and an
epoch-boundary "slow update" mechanism with its own protected skill region.
Hyperparameters default to SkillOpt's own published config (`batch_size=40`,
`minibatch_size=merge_batch_size=8`, `edit_budget: 4 -> 2`), verified by
running the upstream `microsoft/SkillOpt` repository against the same
cheap model used throughout this README: its gate rejected every step on
SearchQA, identical in kind to what `reflact` does here, confirming the
port reproduces the algorithm's behavior and not just its shape.

## Parallelization

`core/runner.py` splits a condition's tasks into `max_parallel_workers`
(config.yaml) contiguous shards and runs each in its own OS process
concurrently, returning combined results in task order. This is
process-based rather than thread-based on purpose: ALFWorld's PDDL backend
(the `tatsu` grammar parser it uses to load and step through games) keeps
shared, non-reentrant state and was found, via a concurrency stress test,
not a theoretical concern, to corrupt and crash under multiple threads,
even with just the game-loading step serialized behind a lock. Separate
processes share no memory, so this doesn't apply to them. The LLM API call
is still I/O-bound and the actual bottleneck, so this still gives wall-clock
speedup; each process's environment setup cost is paid concurrently across
processes, not multiplied by the shard count.

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
  concurrently-running processes; this keeps every condition's task
  sequence identical and reproducible regardless of run-to-run concurrency.
