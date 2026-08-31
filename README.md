# SkillUp

![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)
![Agent Skills compatible](https://img.shields.io/badge/Agent%20Skills-compatible-brightgreen)
![No weight updates](https://img.shields.io/badge/model%20weights-untouched-orange)
![MIT license](https://img.shields.io/badge/license-MIT-lightgrey)

**SkillUp gives your AI agent dynamic skills that evolve with every use.**

Every new AI-agent session starts from zero: it doesn't remember
yesterday's correction, last week's working pattern, or the mistake it
keeps making on your task. SkillUp turns that experience, from a training
environment or your own conversations, into a `SKILL.md`: a portable
strategy document your agent loads next time instead of resetting every
session. Coding is one use case among many; anything an agent does
repeatedly (research, support, data work) works the same way.

**This is not a new agent, harness, or model.** It doesn't replace Claude
Code, Codex, OpenCode, Cursor, or whatever you already use -- it plugs into
them. Skills produced here are plain `SKILL.md` files in the same Agent
Skills convention those tools already read (`<skills-dir>/<name>/SKILL.md`).
Installing one is a file copy, not an integration.

On a small, cheap model (`google/gemini-2.5-flash-lite`, not a frontier
one), a skill trained here took MBPP from 39% to 51% and SearchQA from 50%
to 74%, measured on held-out tasks never seen during training. Full
numbers below in [Does it work?](#does-it-work).

---

## Contents

- [Install](#install)
- [Use it](#use-it)
- [Two ways to build a skill](#two-ways-to-build-a-skill)
- [Does it work?](#does-it-work)
- [Quick start: MBPP](#quick-start-mbpp)
- [Quick start: a conversation you already had](#quick-start-a-conversation-you-already-had)
- [Managing skills: history, diff, rollback, merge](#managing-skills-history-diff-rollback-merge)
- [Project structure](#project-structure)
- [Adding a new environment](#adding-a-new-environment)
- [Adding a new training algorithm](#adding-a-new-training-algorithm)

## Install

Point your agent at the repo and paste this:

```text
Clone https://github.com/shashank-yadav/skillup, run ./install.sh from
inside it, then check whether OPENROUTER_API_KEY is set in this shell --
if not, ask me for it and export it. Tell me when you're ready.
```

`install.sh` creates a virtualenv, installs dependencies, and copies this
repo's two meta-skills into every agent skills directory it finds
(`~/.claude/skills`, `~/.codex/skills`, the shared `~/.agents/skills`
convention). The only thing it can't do is hand over your API key, which
is why the prompt tells your agent to ask. Safe to rerun.

## Use it

Two meta-skills ship with this repo, so an agent that reads the Agent
Skills convention already knows what to do once installed: `skillup`
(train and evaluate skills) and `distill-conversation` (build a skill from
a conversation, callable mid-session). Ask in plain language:

- "Train a skill for MBPP and evaluate it."
- "Distill a skill from this conversation and save it as my-project."
- "Add a new environment for `<your dataset>` and train `gated` on it."

Everything below is what your agent runs on your behalf -- useful if you
want to run a step by hand or understand what's happening.

## Two ways to build a skill

**Train against a dataset or environment.** Point SkillUp at a coding
benchmark, a QA dataset, an interactive simulator, or any Hugging Face
dataset. It rolls out episodes, distills what worked and didn't into
candidate skill edits, and validates each candidate against held-out tasks
before keeping it. Five training algorithms ship out of the box, from a
single-shot distillation to a full port of Microsoft's published SkillOpt
method -- measure which one earns its keep before committing to it.

**Distill from a conversation.** No formal dataset needed: point
`distill_conversation.py` at a transcript of a session where you corrected
your agent a few times, and it extracts the generalizable lessons into a
skill. Callable mid-conversation ("remember this") through its own skill.
For a corpus of past conversations, `convert_conversation.py` builds a
held-out split and runs the same validation-gated trainer the results
below use.

Both paths produce the same thing: a markdown file that makes the same,
frozen model measurably better. No fine-tuning, no weight updates, nothing
to deploy but a text file.

## Does it work?

Yes, on 3 of 4 benchmarks, measured on held-out data never seen during
training, every condition run under identical model, prompt, and step
settings so skill text is the only variable. Every number below is from a
small, cheap model (`google/gemini-2.5-flash-lite`), not a frontier one:

| Benchmark | Baseline | Best result | Best strategy |
|---|---|---|---|
| ALFWorld (embodied household tasks) | 17.2% | **27.6%** (+10.4pp) | `expel` |
| SearchQA (trivia QA) | 50.0% | **74.0%** (+24.0pp) | `naive` |
| MBPP (Python programming) | 39.0% | **51.0%** (+12.0pp) | `reflact` |
| LiveMathematicianBench (research-level math MCQ) | 29.0% | 31.0% (+2.0pp) | `naive` |

`reflact` is a faithful port of Microsoft's published SkillOpt method (see
[reflact and avo](#reflact-and-avo-the-two-non-obvious-strategies) below).
Their own numbers on the same benchmarks, at frontier-model scale, show
larger gains for the same algorithm: LiveMathematicianBench **37.6% ->
66.9%** with GPT-5.5, and a SkillOpt-Lite variant reporting up to **+37.0pp**
on GPT-5.5. This repo verifies that method, plus four other strategies,
against a model you can afford to run at volume.

**No single strategy wins everywhere.** `naive`, the simplest strategy
here, beat every more sophisticated method on two of four benchmarks;
`reflact`, the fullest port of published research, won a third. On the
hardest benchmark (graduate-level math, a different theorem every
question) almost nothing helped -- an informative negative result, not a
bug. That's why five interchangeable strategies ship: measure which one
earns its complexity on your task instead of guessing.

**The conversation path was checked the same way, not just asserted.** Run
end to end against 120 real conversations from the public
OpenAssistant/oasst2 dataset, standing in for "conversations you already
had": segmented into 157 episodes, 47 held out, scored by an LLM judge
(`environments/conversation_judge`) on 23 conversations never used for
training:

| Strategy | Held-out success | vs. baseline |
|---|---|---|
| Baseline (no skill) | 30.4% | -- |
| `avo` | 30.4% | +0.0pp |
| `gated` | 39.1% | +8.7pp |
| `expel` | 39.1% | +8.7pp |
| `naive` | 47.8% | +17.4pp |
| `reflact` | not applicable | -- |

`reflact` structurally can't run here: it rolls out fresh episodes against
a live **train** split every step, and a past conversation isn't
re-runnable -- there's only the held-out `valid_seen`/`valid_unseen` splits
`convert_conversation.py` builds.

Read `naive`'s number with more caution than the rest. It roughly tripled
average response length (811 vs. 258 tokens) with a long, generic
best-practices document rather than lessons traceable to specific
corrections -- plausibly winning partly by being more thorough, not by
having learned something specific, the same full-document-rewrite tendency
noted elsewhere in this README. `gated` and `expel`'s smaller gains came
from single, targeted insights instead (`gated`'s: "when asked to provide
specific numerical data, prioritize verifiable sources," traceable to a
real disagreement in the source conversations about Wikipedia's
reliability). `avo`'s population search reached 0.85 on its own 20-task
dev pool during training but didn't transfer to the held-out set at all --
overfitting the small dev pool made easy to reach, caught exactly because
a held-out check existed. At n=23, one flipped task is 4.3 percentage
points, so treat this as directional, not precise -- but directional is
what the question needed: yes, distilling from real conversations
measurably changes held-out performance.

## Quick start: MBPP

MBPP (Python programming problems) needs only an API key and the core
dependencies `./install.sh` already installed, so it's the fastest way to
see the whole pipeline run:

```bash
python collect_trajectories.py --env mbpp     # roll out the skill-less agent until quotas fill
python train_skill.py --env mbpp --strategy all   # distill a skill per strategy, one comparison pass
python evaluate_skill.py --env mbpp            # baseline + every trained variant, in parallel
python install_skill.py --env mbpp --strategy naive --target ~/.claude/skills
```

`evaluate_skill.py` writes `results/summary.json` (per-task detail) and
`results/summary.txt` (the printed table) under `experiments/mbpp/`. Model
choice lives in [config.yaml](config.yaml); everything MBPP-specific in
[experiments/mbpp/config.yaml](experiments/mbpp/config.yaml). Swap
`--env mbpp` for `--env searchqa`, `--env livemathbench`, or `--env
alfworld` (heavier setup -- Python 3.9-3.11 and a multi-gigabyte download,
see [experiments/alfworld/config.yaml](experiments/alfworld/config.yaml)).

Iterate on a single strategy or condition directly:

```bash
python train_skill.py --env mbpp --strategy gated
python evaluate_skill.py --env mbpp --condition gated
```

## Quick start: a conversation you already had

```bash
python distill_conversation.py --transcript conv.json --target ~/.claude/skills --name my-project
```

A transcript is a JSON list of `{"role", "content"}` turns (or plain text)
-- not tied to one harness's log format. This extends
`~/.claude/skills/my-project/SKILL.md` if it exists, or creates it, picked
up by any Agent-Skills-aware harness next session. For many past
conversations and a real validation gate instead of one unchecked pass,
see [Distilling a skill from a conversation](#distilling-a-skill-from-a-conversation-not-a-benchmark)
below.

## Training through your own harness instead of the API

By default, every action-selection call goes straight to the model API
(`core/backend.py`'s `ApiBackend`). Pass `--harness cli` to route it
through an external harness's CLI instead, so trajectories, and the skill
distilled from them, reflect how that tool behaves:

```bash
python collect_trajectories.py --env mbpp --harness cli
python train_skill.py --env mbpp --strategy gated --harness cli
python evaluate_skill.py --env mbpp --harness cli
```

Needs `harness.cli.command` set in `config.yaml` -- a shell template with
`{system_prompt}`/`{user_prompt}` placeholders, not hardcoded to one
product. Verified end to end for Claude Code:

```yaml
harness:
  cli:
    command: >-
      claude -p {user_prompt} --system-prompt {system_prompt}
      --tools "" --no-session-persistence --output-format text
    timeout_s: 120
```

`--tools ""` and `--no-session-persistence` make Claude Code behave like a
plain chat completion -- one clean action back per call, no tool-use noise,
no leftover session state. The same pattern (print-and-exit, a forced
system prompt, tools disabled) should carry over to any similar CLI
harness. Expect roughly 5-10x the latency of a direct API call, and no
usage/token accounting for most external CLIs.

## Using a trained skill in your own harness

Every skill this framework produces is a plain `SKILL.md`: frontmatter
plus a markdown body, the same shape Claude Code, Codex, OpenCode, and the
shared `~/.agents/skills` convention already read. No conversion step:

```bash
python install_skill.py --env mbpp --strategy naive --target ~/.claude/skills
python install_skill.py --env mbpp --strategy gated --target ~/.codex/skills --name mbpp-gated
python install_skill.py --env mbpp --strategy naive --target ./.claude/skills   # project-level
```

For a harness with no native skill-loading at all, the file still works --
paste its body into a system prompt, the way
`core.agent.build_system_prompt` does internally.

## Managing skills: history, diff, rollback, merge

`install_skill.py` and `distill_conversation.py` both write through
`core/skill_store.py`, which versions every change to a deployed skill
(full-text snapshots in `<target>/<name>/.skillup/history.jsonl`, not git
-- `~/.claude/skills` usually isn't a repo). Writing the exact same content
twice is a no-op; a pre-existing hand-edited skill gets adopted as v1 the
first time something writes to it.

```bash
python skill_manager.py list --target ~/.claude/skills
python skill_manager.py log my-project --target ~/.claude/skills
python skill_manager.py diff my-project --target ~/.claude/skills             # or --from N --to N
python skill_manager.py rollback my-project --target ~/.claude/skills --to 3  # a new version, not a rewrite
python skill_manager.py merge other-name my-project --target ~/.claude/skills # fold one skill into another
```

`merge` exists for a specific failure mode: distilling the same project
under two different `--name`s by accident. It dedupes near-identical
insights the same way every trainer's crossover step does, and leaves the
source skill's directory in place unless you pass `--delete-src`. None of
this decides *which* installed skill a harness loads for a given
conversation -- that's the harness's own job, matching each skill's
`description` frontmatter against what you're doing.

## Distilling a skill from a conversation, not a benchmark

```bash
# One conversation, right now: extend/create a skill in place.
python distill_conversation.py --transcript conv.json --target ~/.claude/skills --name my-project

# A corpus of conversations: train/dev split + gated.py's validation gate.
python convert_conversation.py --transcripts conv1.json conv2.json ... --name my-project
python train_skill.py --env my-project --strategy gated
python evaluate_skill.py --env my-project
```

`distill_conversation.py` is a single LLM call per conversation: find
corrections and confirmed successes, propose a bounded add/remove insight
edit, apply it directly -- no validation gate, matching `expel`'s
ungated-accumulation design. Suited to "learn from this conversation,
right now."

`convert_conversation.py` is for when there are enough past conversations
to warrant validation. `reflact` doesn't apply here (see
[Does it work?](#does-it-work)); `gated`/`expel`/`avo` do, since they only
need a fixed, pre-collected batch of episodes plus a held-out split --
exactly what a conversation corpus already is. This script segments each
transcript into episodes (split on corrections, so a mistake-then-fix
becomes a failure episode followed by a success episode, never one
vacuously "successful" episode because it ended well), holds some out, and
points a generated `experiments/<name>/` at `environments/conversation_judge`
for the held-out portion: an `Environment` whose `step()` asks an LLM judge
whether a new response, written under the candidate skill, avoids the
mistake made last time (or still matches what worked), instead of
executing or matching anything -- a judged proxy for re-running history,
not a real re-run, but the closest available substitute. Because it's a
normal `Environment` plugin, `gated`, `core.trainer.dev_eval`, and
`evaluate_skill.py` all work against it unchanged.

Callable mid-conversation in any harness that reads the Agent Skills
convention through `.claude/skills/distill-conversation/SKILL.md` (also
installed at `~/.claude/skills/distill-conversation/`) -- it tells an
agent how to export the relevant excerpt and invoke
`distill_conversation.py` mid-conversation, not just after the fact.

## Project structure

```
core/                    environment-agnostic framework
  environment.py           Environment protocol + registry
  agent.py                 the LLM agent loop (run_episode) -- no env-specific code
  llm.py                   OpenAI-compatible chat client (targets OpenRouter)
  skill.py                 skill file I/O + insight-list helpers shared by trainers
  skill_store.py           version history for deployed skills (used by install/distill, not trainers)
  conversation.py          transcript-formatting helper shared by the two conversation scripts
  trainer.py               TrainerContext + trainer registry + shared dev-eval helpers
  runner.py                process-based parallel episode runner

environments/            one subpackage per environment; each self-registers
  alfworld/env.py           ALFWorld plugin (wraps its TextWorld backend)
  mbpp/env.py               MBPP plugin (subprocess-sandboxed code-execution grading)
  conversation_judge/env.py LLM-as-judge plugin for convert_conversation.py's held-out episodes

trainers/                one module per training algorithm; each self-registers
  naive.py / gated.py / expel.py / avo.py / reflact.py
  prompts/                  each strategy's LLM prompt template

experiments/<env>/       one environment's config + generated artifacts
  config.yaml               task counts, split sizes, per-strategy knobs
  skills/                   SKILL.initial.md (pristine v0) + each trained variant
  data/                     generated trajectories (gitignored -- regenerable)
  results/                  summary.json / summary.txt from evaluate_skill.py

collect_trajectories.py, train_skill.py, evaluate_skill.py    entry points
install_skill.py                                               drop a trained skill into any harness's skill dir
distill_conversation.py, convert_conversation.py               build skills from conversations instead
skill_manager.py                                               list/show/log/diff/rollback/merge deployed skills
install.sh, requirements.txt, requirements-alfworld.txt        one-shot setup (see Install above)
```

## Adding a new environment

Implement `core.environment.Environment` in `environments/<name>/env.py`:

```python
class YourEnvironment:
    num_tasks: int
    def reset(self) -> tuple[str, dict]: ...                    # -> (observation, info)
    def step(self, action: str) -> tuple[str, bool, dict]: ...  # -> (observation, done, info)
    def close(self) -> None: ...
```

`info` must always carry the same four keys: `admissible_commands` (pass
`[]` for a single-turn, free-form-answer task with no fixed action space,
like QA or math -- the agent loop switches to free text automatically),
`won` (meaningful once `done=True`), `task_id`, and `task`. Everything
environment-specific -- a `__init__(self, config, split, offset=0,
count=None)` signature, quirky pseudo-commands, parsing a task description
out of raw text -- stays inside your plugin.

Register it (`core.environment.register("yourname", YourEnvironment)`),
import the module from `environments/__init__.py`, add
`experiments/<yourname>/config.yaml` (copy ALFWorld's as a starting point)
and `skills/SKILL.initial.md`. Nothing else changes --
`collect_trajectories.py --env yourname` and friends work immediately.

`environments/hf_dataset/env.py` is a reference single-turn adapter for
any Hugging Face dataset with a prompt column and a reference-answer
column -- point it at a dataset name and column names via config, no new
code (`pip install datasets`, kept optional since ALFWorld doesn't need
it). Custom grading or multi-turn interaction should still implement
`Environment` directly, like `environments/mbpp/env.py` (subprocess code
execution against test assertions) or `environments/conversation_judge/env.py`
(an LLM judge instead of literal matching).

## Adding a new training algorithm

```python
def run(ctx: core.trainer.TrainerContext) -> dict:
    ...
    return {"skill": updated_skill_text, "history": [...]}
```

`TrainerContext` carries the LLM client, model settings, the current skill
text, training trajectories, a round count, and (for strategies that
validate candidates against held-out tasks) `dev_tasks` and everything
`core.trainer.dev_eval` needs to roll out fresh episodes. Reuse
`core.skill`'s helpers (`parse_insights`/`render_insights`/`apply_delta`)
for the same "preamble + flat insight list, edited via small structured
deltas" representation the existing strategies use -- full-document
rewrites were found fragile with cheap models (repetition collapse, or
copying the prompt's own context back as if it were an edit); a bounded
delta avoids that since merging happens in Python, not in the model.

Register it (`core.trainer.register("yourname", run)`), import it from
`trainers/__init__.py`, and it's available via `--strategy yourname`.

---

## reflact and avo: the two non-obvious strategies

`reflact` (named after SkillOpt's own internal designation) replicates
Microsoft's published method rather than reinterpreting it: on-policy
rollout against the live `train` split every step (not a fixed
pre-collected batch, unlike every other strategy here), one analyst call
per minibatch of trajectories, hierarchical failure/success patch
aggregation, a cosine-decaying edit budget, gate tracking against both a
running "current" and a best-ever skill, and an epoch-boundary "slow
update" with its own protected skill region. Hyperparameters default to
SkillOpt's own published config (`batch_size=40`,
`minibatch_size=merge_batch_size=8`, `edit_budget: 4 -> 2`), verified by
running the upstream `microsoft/SkillOpt` repository against the same
cheap model used throughout this README: its gate rejected every step on
SearchQA, matching what `reflact` does here, confirming the port
reproduces the algorithm's behavior and not just its shape.

`avo` tracks whether the population's best dev score has improved each
generation. After `STAGNATION_PATIENCE` stagnant generations in a row, a
separate supervisor LLM call (`trainers/prompts/avo_supervisor.md`)
diagnoses why the population is stuck (converged lineages proposing
redundant edits, the same edit type repeatedly rejected, edits too timid
to escape a local optimum) and prescribes a directive that replaces the
normal bounded-edit instruction for every lineage until the population
improves again. This is an agentic call, not a fixed fallback: a static
exploratory-edit instruction is used only if that call's response fails to
parse.

## Implementation notes

**Parallelization.** `core/runner.py` splits a condition's tasks into
`max_parallel_workers` (config.yaml) contiguous shards, each running in
its own OS process concurrently, combined in task order. Process-based
rather than thread-based on purpose: ALFWorld's PDDL backend (the `tatsu`
grammar parser) keeps shared, non-reentrant state that a concurrency
stress test found corrupts and crashes under multiple threads, even with
game-loading serialized behind a lock; separate processes share no memory.
`evaluate_skill.py --condition <label> [--shard-index I --shard-count N]`
exposes the same work as a single process/shard, for isolating a crash or
distributing shards across machines; `--merge` assembles a complete set of
shard files into the combined report.

**Experimental controls.** Training trajectories come from the `train`
split; evaluation uses `valid_unseen`, a disjoint set the skill cannot
have memorized. Every condition in `evaluate_skill.py` uses the same
model, temperature, max_tokens, and step budget -- the only difference is
which skill text (if any) is appended to the system prompt. Every
trajectory, in training and every eval condition, is saved to JSONL for
later inspection. Game-file ordering is sorted explicitly rather than
relying on filesystem traversal order, which was found to differ across
concurrently-running processes.
