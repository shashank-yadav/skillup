"""Inspect, diff, roll back, and merge deployed skills -- SKILL.md files
under a skills directory such as ~/.claude/skills, versioned by
core/skill_store.py every time distill_conversation.py or install_skill.py
writes one.

Usage:
    python skill_manager.py list --target ~/.claude/skills
    python skill_manager.py show my-project --target ~/.claude/skills
    python skill_manager.py log my-project --target ~/.claude/skills
    python skill_manager.py diff my-project --target ~/.claude/skills [--from N] [--to N]
    python skill_manager.py rollback my-project --target ~/.claude/skills --to N
    python skill_manager.py merge other-name my-project --target ~/.claude/skills [--delete-src]

`rollback` doesn't rewrite history -- it writes the old content back as a
new version (like a revert, not a checkout), so the log stays a complete
record of what actually happened. `merge` folds one skill's insights into
another (deduping near-identical ones, same as every trainer's crossover)
for when the same project ended up distilled under two different names.
"""

import argparse
import difflib
import shutil
from datetime import datetime
from pathlib import Path

import yaml

from core import skill, skill_store


def _skill_dir(target: str, name: str) -> Path:
    skill_dir = Path(target).expanduser() / name
    if not (skill_dir / "SKILL.md").exists():
        raise SystemExit(f"No skill named '{name}' at {skill_dir}")
    return skill_dir


def _frontmatter_description(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end == -1:
        return ""
    try:
        front = yaml.safe_load(text[3:end]) or {}
    except yaml.YAMLError:
        return ""
    return str(front.get("description", "")) if isinstance(front, dict) else ""


def cmd_list(args):
    target = Path(args.target).expanduser()
    if not target.exists():
        print(f"No skills directory at {target}")
        return

    rows = []
    for skill_dir in sorted(p for p in target.iterdir() if p.is_dir() and (p / "SKILL.md").exists()):
        text = (skill_dir / "SKILL.md").read_text()
        _, insights = skill.parse_insights(text)
        versions = skill_store.list_versions(skill_dir)
        last_when = datetime.fromtimestamp(versions[-1]["timestamp"]).strftime("%Y-%m-%d") if versions else "-"
        rows.append((skill_dir.name, str(len(insights)), str(len(versions)), last_when, _frontmatter_description(text)))

    if not rows:
        print(f"No skills found under {target}")
        return

    widths = [max(len(r[i]) for r in rows + [("NAME", "INSIGHTS", "VERSIONS", "UPDATED", "DESCRIPTION")]) for i in range(5)]
    header = ("NAME", "INSIGHTS", "VERSIONS", "UPDATED", "DESCRIPTION")
    for row in [header] + rows:
        print("  ".join(cell.ljust(w) for cell, w in zip(row, widths)))


def cmd_show(args):
    print((_skill_dir(args.target, args.name) / "SKILL.md").read_text())


def cmd_log(args):
    skill_dir = _skill_dir(args.target, args.name)
    versions = skill_store.list_versions(skill_dir)
    if not versions:
        print("No version history (this skill predates skill_manager.py, or was written outside it).")
        return
    for v in versions:
        when = datetime.fromtimestamp(v["timestamp"]).strftime("%Y-%m-%d %H:%M")
        note = f"  -- {v['note']}" if v.get("note") else ""
        print(f"v{v['version']}  {when}  {v['source']}{note}")


def cmd_diff(args):
    skill_dir = _skill_dir(args.target, args.name)
    versions = skill_store.list_versions(skill_dir)
    if not versions:
        print("No version history to diff.")
        return
    to_v = args.to if args.to is not None else versions[-1]["version"]
    from_v = args.from_ if args.from_ is not None else max(to_v - 1, versions[0]["version"])
    if from_v == to_v:
        print("from and to are the same version.")
        return
    a = skill_store.get_version(skill_dir, from_v)["text"]
    b = skill_store.get_version(skill_dir, to_v)["text"]
    diff = difflib.unified_diff(a.splitlines(keepends=True), b.splitlines(keepends=True), fromfile=f"v{from_v}", tofile=f"v{to_v}")
    output = "".join(diff)
    print(output if output else "(no textual difference)")


def cmd_rollback(args):
    skill_dir = _skill_dir(args.target, args.name)
    target_version = skill_store.get_version(skill_dir, args.to)
    version, created = skill_store.save_version(
        skill_dir, target_version["text"], source="rollback", note=f"reverted to v{args.to}",
    )
    if created:
        print(f"Rolled back '{args.name}' to the content of v{args.to} (recorded as v{version}).")
    else:
        print(f"'{args.name}' is already at that content (v{version}); nothing to do.")


def cmd_merge(args):
    src_dir = _skill_dir(args.target, args.src)
    dst_dir = _skill_dir(args.target, args.dst)

    _, src_insights = skill.parse_insights(src_dir.joinpath("SKILL.md").read_text())
    dst_text = dst_dir.joinpath("SKILL.md").read_text()
    dst_preamble, dst_insights = skill.parse_insights(dst_text)

    merged = skill.crossover(dst_insights, src_insights)
    added_count = len(merged) - len(dst_insights)
    new_text = skill.render_insights(dst_preamble, merged)

    version, created = skill_store.save_version(
        dst_dir, new_text, source=f"merge:{args.src}", note=f"merged {added_count} insight(s) from '{args.src}'",
    )
    if created:
        print(f"Merged '{args.src}' into '{args.dst}' -> v{version} ({added_count} new insight(s), {len(merged)} total).")
    else:
        print(f"Nothing to merge -- every insight in '{args.src}' is already in '{args.dst}'.")

    if args.delete_src:
        shutil.rmtree(src_dir)
        print(f"Removed {src_dir}")
    else:
        print(f"'{args.src}' left in place -- rerun with --delete-src to remove it once you've checked '{args.dst}'.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--target", required=True, help="Skills directory, e.g. ~/.claude/skills")

    sub.add_parser("list", parents=[common], help="List every skill under --target.")

    p_show = sub.add_parser("show", parents=[common], help="Print a skill's current SKILL.md.")
    p_show.add_argument("name")

    p_log = sub.add_parser("log", parents=[common], help="Print a skill's version history.")
    p_log.add_argument("name")

    p_diff = sub.add_parser("diff", parents=[common], help="Diff two versions of a skill (default: previous vs. current).")
    p_diff.add_argument("name")
    p_diff.add_argument("--from", dest="from_", type=int, default=None)
    p_diff.add_argument("--to", type=int, default=None)

    p_rollback = sub.add_parser("rollback", parents=[common], help="Restore an older version's content as a new version.")
    p_rollback.add_argument("name")
    p_rollback.add_argument("--to", type=int, required=True)

    p_merge = sub.add_parser("merge", parents=[common], help="Fold one skill's insights into another.")
    p_merge.add_argument("src", help="Skill to merge from.")
    p_merge.add_argument("dst", help="Skill to merge into (this one is updated).")
    p_merge.add_argument("--delete-src", action="store_true", help="Remove the source skill's directory after merging.")

    args = parser.parse_args()
    {
        "list": cmd_list,
        "show": cmd_show,
        "log": cmd_log,
        "diff": cmd_diff,
        "rollback": cmd_rollback,
        "merge": cmd_merge,
    }[args.command](args)


if __name__ == "__main__":
    main()
