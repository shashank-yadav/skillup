---
name: distill-conversation
description: Turn corrections and confirmed successes from THIS conversation into a portable SKILL.md, so the same mistakes aren't repeated in future conversations. Use this when the user says something like "remember this", "don't make that mistake again", "learn from this", or asks you to create or update a skill from how this conversation went.
---

# distill-conversation

This conversation itself is training data. When the user corrected you, that
correction implies a generalizable lesson; when something you did was
approved or just worked, that's a pattern worth reinforcing. This skill
turns that into an updated `SKILL.md` using SkillUp's
`distill_conversation.py` -- the same structured add/remove insight-editing
every trainer in that repo uses, just applied to a conversation transcript
instead of RL episodes.

## When to use this

The user asks you to remember something from this session, avoid repeating
a mistake, or explicitly says to create/update a skill from the
conversation so far. Don't wait to be asked at the very end -- if they say
it mid-conversation, distill what's happened *so far*.

## How to do it

1. **Write out the relevant excerpt.** You have this conversation's context
   already -- reconstruct the turns that matter (the corrections, the
   approved approaches; you don't need every message, just the ones with a
   lesson in them) as a JSON file:

   ```json
   [
     {"role": "user", "content": "..."},
     {"role": "assistant", "content": "..."},
     ...
   ]
   ```

   Save it somewhere temporary (e.g. your scratchpad if you have one, or
   `/tmp`). Plain text works too if JSON is inconvenient -- the script
   accepts either.

2. **Run the distiller** (`cd` into wherever SkillUp is checked out on this
   machine first; `--target`/`--name` follow the same `<target>/<name>/SKILL.md`
   layout Claude Code, Codex, OpenCode, and `~/.agents/skills` all read):

   ```bash
   source .venv/bin/activate
   export OPENROUTER_API_KEY=sk-or-...   # ask the user for this if it's not already set
   python distill_conversation.py \
     --transcript /path/to/excerpt.json \
     --target ~/.claude/skills \
     --name <project-or-topic-name>
   ```

   Use `--target ./.claude/skills` instead for a project-level install. Pick
   `--name` to describe what the skill is *about* (e.g. the project name, or
   the kind of task), not "distill-conversation" itself -- each distilled
   skill is its own thing, separate from this one.

3. **Report what changed.** The script prints exactly which insights were
   added or removed -- summarize that for the user rather than just saying
   "done". If a skill already existed at that path, this extends it (small
   structured edit); if not, it creates a fresh one.

## Why this representation

Insights are added/removed as short, generalizable bullets -- not a full
rewrite of the skill file. Full-document rewrites were found (in SkillUp's
own experiments) to be fragile with cheap models; a bounded structured edit
is more reliable and keeps a clean history of what was learned and why.
Each proposed insight is checked against what's already there, so repeated
distillation across many conversations accumulates rather than duplicates.
