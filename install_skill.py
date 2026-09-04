"""Copy a trained skill into the directory layout any Agent-Skills-compatible
harness expects: <target>/<name>/SKILL.md. This works as-is for Claude Code,
Codex, OpenCode, the shared ~/.agents/skills convention, or a project-level
.claude/skills/ -- they all read the same "SKILL.md with a name/description
frontmatter, one folder per skill" layout, and this framework's skills
already use that exact shape.

Looks first for a freshly local-trained skill under experiments/<env>/skills/,
then falls back to this repo's own published copy under skills/<env>/<model>/
-- so this also works right after a fresh clone, with no training required.

Usage:
    python install_skill.py --env alfworld --strategy naive --target ~/.claude/skills
    python install_skill.py --env alfworld --strategy gated --target ~/.codex/skills --name alfworld-gated
    python install_skill.py --env frontend --best --target ~/.claude/skills
"""

import argparse
import json
from pathlib import Path

from core import skill_store
from publish_skills import model_slug
from util import REPO_ROOT, load_config, resolve_path


def published_dir(env: str, model: str) -> Path:
    return REPO_ROOT / "skills" / env / model_slug(model)


def skill_source_path(env: str, strategy: str, config: dict, model: str) -> Path:
    filename = "SKILL.md" if strategy == "naive" else f"SKILL.{strategy}.md"
    local = resolve_path(env, config["paths"]["skill_dir"]) / filename
    if local.exists():
        return local
    return published_dir(env, model) / filename


def best_strategy(env: str, model: str) -> tuple[str, float]:
    """Reads the published summary.json's improvement_pp (evaluate_skill.py's
    per-strategy percentage-point delta over baseline) and picks the top
    one. Refuses rather than silently installing a skill that measured
    worse than no skill at all -- that's happened for real (see the
    README's "Does it work?" section), and --best shouldn't paper over it."""
    summary_path = published_dir(env, model) / "summary.json"
    if not summary_path.exists():
        raise SystemExit(
            f"No published results at {summary_path} to pick a best strategy from -- "
            "run evaluate_skill.py + publish_skills.py first, or pass --strategy explicitly."
        )
    improvements = json.loads(summary_path.read_text()).get("improvement_pp", {})
    if not improvements:
        raise SystemExit(f"{summary_path} has no improvement_pp data.")
    strategy, pp = max(improvements.items(), key=lambda kv: kv[1])
    if pp <= 0:
        raise SystemExit(
            f"No trained strategy beat baseline for {env}/{model_slug(model)} "
            f"(best is '{strategy}' at {pp:+.1f}pp). Baseline is the honest choice here -- "
            f"pass --strategy {strategy} explicitly if you want it anyway."
        )
    return strategy, pp


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--env", required=True, help="Registered environment name, e.g. 'alfworld'.")
    parser.add_argument("--strategy", default="naive", help="Which trained strategy's skill to install.")
    parser.add_argument("--best", action="store_true",
                         help="Ignore --strategy and install whichever published strategy scored highest "
                              "over baseline (reads skills/<env>/<model>/summary.json). Refuses if none did.")
    parser.add_argument("--model", default=None,
                         help="Model label for the published fallback dir (default: config.yaml's agent_model).")
    parser.add_argument("--target", required=True, help="Destination skills directory, e.g. ~/.claude/skills")
    parser.add_argument("--name", default=None,
                         help="Skill folder name (default: '<env>' for naive, '<env>-<strategy>' otherwise).")
    args = parser.parse_args()

    config = load_config(args.env)
    model = args.model or config["model"]["agent_model"]

    strategy = args.strategy
    if args.best:
        strategy, pp = best_strategy(args.env, model)
        print(f"--best: '{strategy}' scored highest for {args.env}/{model_slug(model)} ({pp:+.1f}pp vs baseline)")

    source = skill_source_path(args.env, strategy, config, model)
    if not source.exists():
        raise SystemExit(
            f"No trained skill found at {source}. Run train_skill.py first, "
            f"or check skills/{args.env}/{model_slug(model)}/ for a published one."
        )

    name = args.name or (args.env if strategy == "naive" else f"{args.env}-{strategy}")
    target_root = Path(args.target).expanduser()
    target_dir = target_root / name
    dest = target_dir / "SKILL.md"
    version, created = skill_store.save_version(
        target_dir, source.read_text(),
        source=f"install_skill:{args.env}/{strategy}",
        note="deployed trained skill",
    )

    if created:
        print(f"Installed {source} -> {dest} (v{version})")
    else:
        print(f"{dest} already matches {source} (v{version}, no new version recorded)")
    print(f"Any Agent-Skills-compatible harness pointed at {target_root} will load this as skill '{name}'.")


if __name__ == "__main__":
    main()
