# SkillUp

![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)
![Agent Skills compatible](https://img.shields.io/badge/Agent%20Skills-compatible-brightgreen)
![No weight updates](https://img.shields.io/badge/model%20weights-untouched-orange)
![MIT license](https://img.shields.io/badge/license-MIT-lightgrey)

**A framework for training and managing skills for AI agents.**

Point SkillUp at an existing dataset, environment, or your own past
conversations, and it trains a `SKILL.md` -- a portable strategy document
your agent loads next session -- and validates that it helps before
keeping it. Once trained, skills are managed like anything else you
maintain: versioned, diffed, rolled back, merged, and installed into
whatever harness you already use.

**Not a new agent, harness, or model.** It doesn't replace Claude Code,
Codex, OpenCode, Cursor, or whatever you already use -- it plugs into
them. Skills produced here are plain `SKILL.md` files in the same Agent
Skills convention those tools already read
(`<skills-dir>/<name>/SKILL.md`). Installing one is a file copy.

On a small, cheap model (`google/gemini-2.5-flash-lite`, not a frontier
one), a skill trained here took SearchQA from 50% to 74% and ALFWorld
from 17.2% to 27.6%, measured on held-out tasks never seen during
training. Full
numbers below in [Does it work?](#does-it-work).

---

## Contents

- [Install](#install)
- [Use it](#use-it)
- [Train a skill](#train-a-skill)
- [Does it work?](#does-it-work)
- [Does it hold up on a bigger model?](#does-it-hold-up-on-a-bigger-model)
- [Use existing skills](#use-existing-skills)
- [Manage a skill](#manage-a-skill)
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
(train, evaluate, and manage skills) and `distill-conversation` (build a
skill from a conversation, callable mid-session). Ask in plain language:

- "Train a skill for MBPP and evaluate it."
- "Distill a skill from this conversation and save it as my-project."
- "Add a new environment for `<your dataset>` and train `gated` on it."

Everything below is what your agent runs on your behalf -- useful if you
want to run a step by hand or understand what's happening.

## Train a skill

Training always follows the same loop, whatever the source: roll out
episodes under the current skill, distill what worked and didn't into a
candidate edit, validate the candidate against held-out tasks, keep it
only if it scores better. Five training algorithms ship out of the box,
from a single-shot distillation to a full port of Microsoft's published
SkillOpt method -- measure which one earns its keep before committing to
it. The only thing that changes is where the episodes come from.

### From a dataset or environment

Point SkillUp at a coding benchmark, a QA dataset, an interactive
simulator, or any Hugging Face dataset. MBPP needs only an API key and the
core dependencies `./install.sh` already installed, so it's the fastest
way to see the whole pipeline run:

```bash
python collect_trajectories.py --env mbpp        # roll out the skill-less agent until quotas fill
python train_skill.py --env mbpp --strategy all  # distill a skill per strategy, one comparison pass
python evaluate_skill.py --env mbpp               # baseline + every trained variant, in parallel
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

### From your own conversations

No formal dataset needed: point `distill_conversation.py` at a transcript
of a session where you corrected your agent a few times, and it extracts
the generalizable lessons into a skill.

```bash
python distill_conversation.py --transcript conv.json --target ~/.claude/skills --name my-project
```

A transcript is a JSON list of `{"role", "content"}` turns (or plain text)
-- not tied to one harness's log format. This is a single LLM call: find
corrections and confirmed successes, propose a bounded add/remove insight
edit, apply it directly -- no validation gate, matching `expel`'s
ungated-accumulation design. It extends `~/.claude/skills/my-project/SKILL.md`
if it exists, or creates it. Callable mid-conversation ("remember this")
through its own skill, `.claude/skills/distill-conversation/SKILL.md`
(also installed at `~/.claude/skills/distill-conversation/`).

For a corpus of past conversations, validated the same way training
against a benchmark is:

```bash
python convert_conversation.py --transcripts conv1.json conv2.json ... --name my-project
python train_skill.py --env my-project --strategy gated
python evaluate_skill.py --env my-project
```

`reflact` doesn't apply here (see [Does it work?](#does-it-work));
`gated`/`expel`/`avo` do, since they only need a fixed, pre-collected
batch of episodes plus a held-out split -- exactly what a conversation
corpus already is. `convert_conversation.py` segments each transcript into
episodes (split on corrections, so a mistake-then-fix becomes a failure
episode followed by a success episode, never one vacuously "successful"
episode because it ended well), holds some out, and points a generated
`experiments/<name>/` at `environments/conversation_judge` for the
held-out portion: an `Environment` whose `step()` asks an LLM judge
whether a new response, written under the candidate skill, avoids the
mistake made last time (or still matches what worked) -- a judged proxy
for re-running history, since a past conversation can't be re-run.
Because it's a normal `Environment` plugin, `gated`, `core.trainer.
dev_eval`, and `evaluate_skill.py` all work against it unchanged.

### Through your own harness, not just the API

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
plain chat completion -- one clean action back per call, no tool-use
noise, no leftover session state. The same pattern (print-and-exit, a
forced system prompt, tools disabled) should carry over to any similar
CLI harness. Expect roughly 5-10x the latency of a direct API call, and no
usage/token accounting for most external CLIs.

## Does it work?

Yes, on 3 of 4 benchmarks, measured on held-out data never seen during
training, every condition run under identical model, prompt, and step
settings so skill text is the only variable. Every number below is from a
small, cheap model (`google/gemini-2.5-flash-lite`), not a frontier one.

(A silent bug affected earlier versions of every number below except
ALFWorld/SearchQA/LiveMathematicianBench: `agent_max_tokens` defaulted to
64 everywhere, sized for those three benchmarks' short discrete answers,
and was truncating code and writing responses mid-output for MBPP,
BigCodeBench, SQL, Writing, and the conversation-distillation path --
inflating some results and flattening others. Fixed with per-environment
token budgets; every number below is a clean re-run.)

| Benchmark | Baseline | Best result | Best strategy |
|---|---|---|---|
| ALFWorld (embodied household tasks) | 17.2% | **27.6%** (+10.4pp) | `expel` |
| SearchQA (trivia QA) | 50.0% | **74.0%** (+24.0pp) | `naive` |
| MBPP (Python programming) | 81.0% | 83.0% (+2.0pp) | `avo`/`reflact` (tied) |
| LiveMathematicianBench (research-level math MCQ) | 27.0% | 32.0% (+5.0pp) | `naive` |

LiveMathematicianBench's numbers reflect a second, unrelated fix: the
dataset's own `correct_choice` label is "A" for 100% of its 608 rows
(confirmed directly), and an earlier version of this environment's
option-assembly code sorted choices by that original label -- meaning the
correct answer always rendered as option A, a 100%-reliable positional
exploit, not a subtle bias. One trainer strategy (`reflact`) partially
discovered it before the fix, inflating its measured gain on this
benchmark without any real improvement in reasoning behind it. Options are
now shuffled per-question with a reproducible seed and relabeled by their
new position; see `environments/livemathbench/env.py`.

`reflact` is a faithful port of Microsoft's published SkillOpt method (see
[reflact and avo](#reflact-and-avo-the-two-non-obvious-strategies) below).
Their own numbers on the same benchmarks, at frontier-model scale, show
larger gains for the same algorithm: LiveMathematicianBench **37.6% ->
66.9%** with GPT-5.5, and a SkillOpt-Lite variant reporting up to **+37.0pp**
on GPT-5.5. This repo verifies that method, plus four other strategies,
against a model you can afford to run at volume.

**No single strategy wins everywhere.** `naive`, the simplest strategy
here, beat every more sophisticated method on two of four benchmarks
(SearchQA, LiveMathematicianBench); on MBPP, `avo` and `reflact` tied for
best. On the hardest benchmark (graduate-level math, a different theorem
every question) almost nothing helped -- an informative negative result,
not a bug. That's why five interchangeable strategies ship: measure which
one earns its complexity on your task instead of guessing.

**The conversation path was checked the same way, not just asserted.** Run
end to end against 120 real conversations from the public
OpenAssistant/oasst2 dataset, standing in for "conversations you already
had": segmented into 157 episodes, 47 held out, scored by an LLM judge
(`environments/conversation_judge`) on 23 conversations never used for
training:

| Strategy | Held-out success | vs. baseline |
|---|---|---|
| Baseline (no skill) | 82.6% | -- |
| `avo` | 87.0% | +4.3pp |
| `gated` | 87.0% | +4.3pp |
| `expel` | 82.6% | +0.0pp |
| `naive` | 82.6% | +0.0pp |
| `reflact` | not applicable | -- |

`reflact` structurally can't run here: it rolls out fresh episodes against
a live **train** split every step, and a past conversation isn't
re-runnable -- there's only the held-out `valid_seen`/`valid_unseen` splits
`convert_conversation.py` builds.

`avo` and `gated` -- the two strategies that validate every candidate
against a held-out gate before keeping it -- are the top performers here;
`naive` and `expel`'s ungated edits landed exactly on baseline. `avo`'s
insights are concrete and traceable (generated code should include its
imports and be runnable, explanations should be broken into numbered
steps); `gated`'s is a single targeted rule (cite a source directly when
asked for one). At n=23, one flipped task is 4.3 percentage points, so
treat this as directional, not a precise measurement -- but directional
is what the question needed: yes, distilling from real conversations
measurably changes held-out performance.

**Three more domains were added to test how far this generalizes:**
`bigcodebench` (harder, more realistic Python problems), `sql`
(text-to-SQL, graded by real query execution against an in-memory SQLite
database, not string matching), and `writing` (quality across genres,
judged against expert-annotated reference pairs), trained and evaluated
the same way, same cheap model:

| Environment | Baseline | Best result | Best strategy |
|---|---|---|---|
| BigCodeBench (harder Python programming) | 28.0% | **34.0%** (+6.0pp) | `avo`/`expel` (tied) |
| SQL (text-to-SQL) | 37.0% | **40.0%** (+3.0pp) | `expel` |
| Writing (quality across genres) | 41.0% | 42.0% (+1.0pp) | `gated` |

BigCodeBench shows the clearest gain of the three, with sound, specific
insights behind it: validate a file path before opening it, check for
empty inputs and zero denominators before dividing. SQL and Writing moved
less. `expel`'s SQL insights are reasonable (join tables on their foreign
keys, use BETWEEN for date ranges) but only edge out baseline by 3pp;
part of that ceiling is the dataset itself, since roughly 7% of its gold
queries have real data-quality issues, the known cost of a synthetic set
traded for being fully self-contained (see `environments/sql/env.py`).
Writing barely moved at all, and the "winning" insight isn't about
writing at all -- a tell that +1pp here is noise, not signal, not a real
effect to trust. Generic writing advice doesn't reliably beat a capable
baseline once that baseline can finish its response; that's a believable
result, not a bug.

## Does it hold up on a bigger model?

Every benchmark above was re-run against two more capable models on
OpenRouter -- `qwen/qwen3-235b-a22b-2507` and `deepseek/deepseek-v3.2`,
both 40-70x cheaper per token than a frontier model like GPT-5.5 -- to
check whether the story changes with more capability behind the wheel,
not just whether it works on one small model:

| Environment | Qwen: baseline -> best | DeepSeek: baseline -> best |
|---|---|---|
| ALFWorld | 41.8% -> **51.5%** (+9.7pp, `avo`/`naive`) | 29.1% -> **53.0%** (+23.9pp, `avo`) |
| SearchQA | 51.0% -> **68.0%** (+17.0pp, `naive`) | 61.0% -> **80.0%** (+19.0pp, `expel`) |
| LiveMathematicianBench | 37.0% -> **74.0%** (+37.0pp, `reflact`) | 35.0% -> **64.0%** (+29.0pp, `reflact`) |
| MBPP | 81.0% -> 85.0% (+4.0pp, `gated`) | 81.0% -> 83.0% (+2.0pp, `naive`) |
| BigCodeBench | 40.0% -> 40.0% (+0.0pp, `avo`/`gated`) | 43.0% -> 41.0% (-2.0pp, `avo`, best case) |
| SQL | 53.0% -> **59.0%** (+6.0pp, `avo`/`expel`/`naive`) | 62.0% -> 45.0% (-17.0pp, `expel`, see below) |
| Writing | 50.0% -> **67.0%** (+17.0pp, `expel`) | 34.0% -> **53.0%** (+19.0pp, `naive`) |

`reflact`'s LiveMathematicianBench result isn't a one-model fluke: both
bigger models show the same pattern the cheap model did (every simpler
strategy flat or negative, `reflact` alone producing a large, real gain)
-- now with the positional exploit fixed, this is the clearest evidence in
this repo that on-policy rollout with iterative reflection earns its
extra cost specifically on the hardest reasoning tasks, not everywhere.

BigCodeBench flips from a clear win (cheap model, +6.0pp) to flat or
negative on both bigger models. The insights themselves stayed sound
(validate file paths, handle empty inputs) -- they just stopped helping
once the baseline no longer needed the reminder, and for DeepSeek actively
got in the way. Same shape as the cheap-model Writing result above: advice
calibrated for a weaker model doesn't transfer to a stronger one for free.

DeepSeek's SQL number needs a real caveat, not just a footnote. Every
skill condition collapsed 17-21 percentage points below baseline, and
investigating why (comparing real SQL syntax validity against the
raw model responses, not just re-running the eval) found roughly half of
the failures were genuine syntax errors -- responses cut off mid-string,
e.g. `WHERE orbit = 'High Earth Orbit` with no closing quote. This is not
a token-budget bug: completion length in every failing case was well
under the configured limit, and `finish_reason` was `stop`, not `length`.
Repeating the exact same prompt dozens of times concurrently, including
the literal prompts that failed in the real run, reproduced it 0 times in
isolation. The one pattern that held: baseline (short system prompt) sits
near normal, every skill condition (system prompt lengthened with
insights) collapses. That correlation, without a confirmed mechanism, is
the honest result -- a real DeepSeek/OpenRouter reliability issue under
longer system prompts on this task, not something in this repo's harness,
and not something to paper over with a cleaner-looking number.

## Use existing skills

Every skill trained here, including every number above, is published
under `skills/<env>/<model-slug>/` alongside the results that validated
it -- not just the code that produced it. Point your agent at one
directly instead of training your own:

```bash
cp skills/mbpp/google_gemini-2.5-flash-lite/SKILL.reflact.md ~/.claude/skills/mbpp/SKILL.md
```

`skills/<env>/<model-slug>/summary.txt` has the exact numbers that skill
was validated against, so you're not taking it on faith -- when a skill
didn't beat baseline (BigCodeBench and SQL above), that's visible right
in its own directory, not hidden.

The model shows up in the path on purpose: a skill trained by one model
doesn't necessarily transfer to another -- see
[Does it hold up on a bigger model?](#does-it-hold-up-on-a-bigger-model)
above, where the same skill that helps a small model sometimes does
nothing or actively hurts a bigger one. `publish_skills.py --env <name>
--model <id>` is the command that writes each one -- run once after
`evaluate_skill.py`, so nothing gets published without real numbers
behind it first.

Currently published, every environment under all three models
(`google_gemini-2.5-flash-lite`, `qwen_qwen3-235b-a22b-2507`,
`deepseek_deepseek-v3.2`): `alfworld`, `searchqa`, `mbpp`,
`livemathbench`, `bigcodebench`, `sql`, `writing`. More models land
alongside these, not replacing them.

## Manage a skill

Training isn't the end of a skill's life. Once one exists, it needs to
reach the harness you use, and stay reviewable and reversible as
it keeps changing.

### Install into your harness

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

### Version, diff, rollback, merge

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
  bigcodebench/env.py       harder Python problems, same grading shape as mbpp
  sql/env.py                text-to-SQL, graded by real SQLite execution
  writing/env.py            writing quality, LLM-judge graded against chosen/rejected pairs
  conversation_judge/env.py LLM-as-judge plugin for convert_conversation.py's held-out episodes

trainers/                one module per training algorithm; each self-registers
  naive.py / gated.py / expel.py / avo.py / reflact.py
  prompts/                  each strategy's LLM prompt template

experiments/<env>/       one environment's config + generated scratch state
  config.yaml               task counts, split sizes, per-strategy knobs
  skills/, data/, results/  gitignored -- whichever model last ran train_skill.py/
                            evaluate_skill.py against this environment, unlabeled
                            by model, fully regenerable

skills/<env>/<model>/    published, labeled, committed: skills + the results
                          that validated them (see Use existing skills above) --
                          the real reference, unlike the scratch copies above

collect_trajectories.py, train_skill.py, evaluate_skill.py    entry points
install_skill.py                                               drop a trained skill into any harness's skill dir
publish_skills.py                                               copy a trained skill + its results into skills/<env>/<model>/
distill_conversation.py, convert_conversation.py               build skills from conversations instead
skill_manager.py                                               list/show/log/diff/rollback/merge deployed skills
install.sh, requirements.txt, requirements-alfworld.txt,
  requirements-bigcodebench.txt                                 one-shot setup (see Install above)
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
