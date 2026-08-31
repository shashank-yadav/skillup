"""Copy a trained skill into the directory layout any Agent-Skills-compatible
harness expects: <target>/<name>/SKILL.md. This works as-is for Claude Code,
Codex, OpenCode, the shared ~/.agents/skills convention, or a project-level
.claude/skills/ -- they all read the same "SKILL.md with a name/description
frontmatter, one folder per skill" layout, and this framework's skills
already use that exact shape.

Usage:
    python install_skill.py --env alfworld --strategy naive --target ~/.claude/skills
    python install_skill.py --env alfworld --strategy gated --target ~/.codex/skills --name alfworld-gated
"""

import argparse
from pathlib import Path

from core import skill_store
from util import load_config, resolve_path


def skill_source_path(env: str, strategy: str, config: dict) -> Path:
    if strategy == "naive":
        return resolve_path(env, config["paths"]["skill_file"])
    return resolve_path(env, config["paths"]["skill_dir"]) / f"SKILL.{strategy}.md"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--env", required=True, help="Registered environment name, e.g. 'alfworld'.")
    parser.add_argument("--strategy", default="naive", help="Which trained strategy's skill to install.")
    parser.add_argument("--target", required=True, help="Destination skills directory, e.g. ~/.claude/skills")
    parser.add_argument("--name", default=None,
                         help="Skill folder name (default: '<env>' for naive, '<env>-<strategy>' otherwise).")
    args = parser.parse_args()

    config = load_config(args.env)
    source = skill_source_path(args.env, args.strategy, config)
    if not source.exists():
        raise SystemExit(f"No trained skill found at {source}. Run train_skill.py first.")

    name = args.name or (args.env if args.strategy == "naive" else f"{args.env}-{args.strategy}")
    target_root = Path(args.target).expanduser()
    target_dir = target_root / name
    dest = target_dir / "SKILL.md"
    version, created = skill_store.save_version(
        target_dir, source.read_text(),
        source=f"install_skill:{args.env}/{args.strategy}",
        note="deployed trained skill",
    )

    if created:
        print(f"Installed {source} -> {dest} (v{version})")
    else:
        print(f"{dest} already matches {source} (v{version}, no new version recorded)")
    print(f"Any Agent-Skills-compatible harness pointed at {target_root} will load this as skill '{name}'.")


if __name__ == "__main__":
    main()
