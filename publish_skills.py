"""Publish a trained environment's skills and results into `skills/<env>/
<model>/`, the curated, model-namespaced directory this repo ships
alongside its code -- distinct from `experiments/<env>/skills/`, which is
scratch working state for one local training run.

Namespacing by model matters because the same environment will eventually
be trained with more than one model: today everything here is trained
with a single cheap model (see config.yaml), but nothing about the layout
assumes that stays true, so a second model's results land next to the
first instead of overwriting it.

Usage:
    python publish_skills.py --env mbpp
    python publish_skills.py --env mbpp --model google/gemini-2.5-flash-lite  # override the configured model
"""

import argparse
import shutil
from pathlib import Path

from util import load_config, resolve_path

REPO_ROOT = Path(__file__).parent


def model_slug(model: str) -> str:
    return model.replace("/", "_")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--env", required=True, help="Registered environment name, e.g. 'mbpp'.")
    parser.add_argument("--model", default=None, help="Override the model label (default: config.yaml's agent_model).")
    args = parser.parse_args()

    config = load_config(args.env)
    model = args.model or config["model"]["agent_model"]
    slug = model_slug(model)

    skills_src = resolve_path(args.env, config["paths"]["skill_dir"])
    if not skills_src.exists() or not any(skills_src.glob("SKILL*.md")):
        raise SystemExit(f"No trained skills found at {skills_src}. Run train_skill.py first.")

    dest = REPO_ROOT / "skills" / args.env / slug
    dest.mkdir(parents=True, exist_ok=True)

    published = []
    for skill_file in sorted(skills_src.glob("SKILL*.md")):
        shutil.copy(skill_file, dest / skill_file.name)
        published.append(skill_file.name)

    results_summary = resolve_path(args.env, config["paths"]["results_summary"])
    results_table = resolve_path(args.env, config["paths"]["results_table"])
    for results_file in (results_summary, results_table):
        if results_file.exists():
            shutil.copy(results_file, dest / results_file.name)
            published.append(results_file.name)

    print(f"Published {len(published)} file(s) to {dest}:")
    for name in published:
        print(f"  {name}")
    if not results_table.exists():
        print("\nNo results/summary.txt found -- run evaluate_skill.py first so published skills ship with numbers, not just files.")


if __name__ == "__main__":
    main()
