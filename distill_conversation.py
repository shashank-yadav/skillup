"""Distill a portable SKILL.md from a single AI-agent conversation --
corrections and confirmed successes become generalizable insights, so the
same mistakes aren't repeated in a future conversation.

Usage:
    python distill_conversation.py --transcript conv.json --target ~/.claude/skills --name my-project
    python distill_conversation.py --transcript conv.txt  --target ./.claude/skills --name my-project

The transcript is either a JSON list of {"role": "user"|"assistant",
"content": str} turns (the shape virtually any harness's own conversation
log already is), or plain text (pasted straight from a chat) -- this isn't
tied to one product. If a SKILL.md already exists at <target>/<name>/SKILL.md
its insights are extended with a small structured add/remove edit, the same
representation every trainer in this repo uses; otherwise a new one is
created.

To make this callable *from inside* a live conversation in any harness that
reads the Agent Skills convention (Claude Code, Codex, OpenCode, ...), see
`.claude/skills/distill-conversation/SKILL.md` -- it tells an agent how to
export the relevant excerpt and invoke this script mid-conversation.
"""

import argparse
from pathlib import Path

import yaml

from core import skill, skill_store
from core.conversation import format_transcript
from core.llm import ModelClient
from util import trainer_model_name

PROMPT_PATH = Path(__file__).parent / "prompts" / "distill_conversation.md"
ROOT_CONFIG_PATH = Path(__file__).parent / "config.yaml"

DEFAULT_SKILL_TEMPLATE = """---
name: {name}
description: Lessons learned from past conversations, so the same mistakes aren't repeated.
---

# {name}
"""


def load_root_config() -> dict:
    with open(ROOT_CONFIG_PATH) as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--transcript", required=True, help="Path to a conversation transcript (JSON turns or plain text).")
    parser.add_argument("--target", required=True, help="Destination skills directory, e.g. ~/.claude/skills")
    parser.add_argument("--name", required=True, help="Skill folder name -- distills into <target>/<name>/SKILL.md.")
    parser.add_argument("--edit-budget", type=int, default=6, help="Max insights to add in one pass.")
    args = parser.parse_args()

    transcript_text = format_transcript(Path(args.transcript).read_text())

    target_dir = Path(args.target).expanduser() / args.name
    skill_path = target_dir / "SKILL.md"
    if skill_path.exists():
        current_skill = skill_path.read_text()
        print(f"Extending existing skill at {skill_path}")
    else:
        current_skill = DEFAULT_SKILL_TEMPLATE.format(name=args.name)
        print(f"No existing skill at {skill_path} -- creating a new one")

    preamble, insights = skill.parse_insights(current_skill)

    config = load_root_config()
    client = ModelClient(config)
    model = trainer_model_name(config)

    prompt = PROMPT_PATH.read_text().format(
        edit_budget=args.edit_budget,
        current_insights=skill.format_insight_list(insights),
        transcript=transcript_text,
    )
    raw_text, _usage = client.chat(
        model=model, messages=[{"role": "user", "content": prompt}],
        temperature=config["model"]["trainer_temperature"], max_tokens=config["model"]["trainer_max_tokens"],
    )
    delta = skill.extract_insight_delta(raw_text)

    if not delta["add"] and not delta["remove"]:
        print("Nothing generalizable found in this conversation -- skill unchanged.")
        return

    new_insights, added = skill.apply_delta(list(insights), delta)
    new_text = skill.render_insights(preamble, new_insights)
    version, created = skill_store.save_version(
        target_dir, new_text,
        source=f"distill_conversation:{Path(args.transcript).name}",
        note=f"+{len(added)} insight(s)" if added else "no new insights",
    )

    print(f"\nAdded {len(added)} insight(s):")
    for text in added:
        print(f"  + {text}")
    removed = [r for r in delta["remove"] if r.strip() in {i.strip() for i in insights} and r.strip() not in {i.strip() for i in new_insights}]
    if removed:
        print(f"Removed {len(removed)} insight(s):")
        for text in removed:
            print(f"  - {text}")
    if created:
        print(f"\nWrote {skill_path} (v{version})")
    else:
        print(f"\n{skill_path} unchanged (still v{version})")


if __name__ == "__main__":
    main()
