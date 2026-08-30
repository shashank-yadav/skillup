"""Read training trajectories and distill them into an updated SKILL.md,
using one of several pluggable trainer strategies.

Usage:
    python train_skill.py --env alfworld [--strategy naive|gated|expel|avo|all] [--rounds N] [--harness api|cli]

All strategies start from the same pristine skills/SKILL.initial.md, so their
outputs are directly comparable. "naive" writes skills/SKILL.md (the
PLAN.md-standard path); "gated", "expel", and "avo" write sibling
SKILL.<strategy>.md files so multiple strategies can coexist and be compared
by evaluate_skill.py in one run.

`--harness` only affects gated/avo's held-out dev-eval rollouts (the actual
training trajectories always come from collect_trajectories.py, which has
its own --harness flag): `api` (default) calls the model directly; `cli`
routes each turn through an external harness's CLI (see core/backend.py and
`harness.cli.command` in config.yaml) -- e.g. Claude Code, so a candidate
skill edit gets validated against how that harness actually behaves, not
just a raw completion.

To add a new training algorithm: create trainers/<name>.py implementing
`run(ctx: core.trainer.TrainerContext) -> {"skill": str, "history": [...]}`
and register it there (see trainers/naive.py for the simplest example) --
this script doesn't need to change.
"""

import argparse
import json

import environments  # noqa: F401 -- registers all environment plugins
import trainers  # noqa: F401 -- registers all trainer strategies
from core.backend import build_backend
from core.environment import get as get_environment
from core.llm import ModelClient
from core.trainer import TrainerContext
from core.trainer import get as get_trainer
from core.trainer import load_trajectories
from util import load_config, resolve_path, trainer_model_name


def skill_path_for(env: str, strategy: str, config: dict):
    if strategy == "naive":
        return resolve_path(env, config["paths"]["skill_file"])
    return resolve_path(env, config["paths"]["skill_dir"]) / f"SKILL.{strategy}.md"


def build_context(
    env: str, strategy: str, config: dict, client: ModelClient, trajectories: list[dict], rounds: int, harness: str,
) -> TrainerContext:
    exp = config["experiment"]
    current_skill = resolve_path(env, config["paths"]["initial_skill_file"]).read_text()

    make_env = None
    backend = None
    dev_tasks = 0
    extra: dict = {}
    if strategy == "gated":
        make_env = lambda: get_environment(env)(config, split="valid_seen")  # noqa: E731
        backend = build_backend(config, harness)
        dev_tasks = exp["num_dev_tasks"]
    elif strategy == "avo":
        make_env = lambda: get_environment(env)(config, split="valid_seen")  # noqa: E731
        backend = build_backend(config, harness)
        dev_tasks = exp["avo_dev_tasks_per_candidate"]
        extra["population_size"] = exp.get("avo_population_size", 3)

    return TrainerContext(
        client=client,
        model=trainer_model_name(config),
        trainer_temperature=config["model"]["trainer_temperature"],
        trainer_max_tokens=config["model"]["trainer_max_tokens"],
        current_skill=current_skill,
        trajectories=trajectories,
        rounds=rounds,
        make_env=make_env,
        backend=backend,
        dev_tasks=dev_tasks,
        max_steps=exp["max_steps"],
        extra=extra,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--env", required=True, help="Registered environment name, e.g. 'alfworld'.")
    parser.add_argument("--strategy", default="naive", choices=["naive", "gated", "expel", "avo", "all"])
    parser.add_argument("--rounds", type=int, default=None)
    parser.add_argument("--harness", default="api", choices=["api", "cli"],
                         help="Backend for gated/avo's dev-eval rollouts: direct API, or an external harness's CLI.")
    args = parser.parse_args()

    config = load_config(args.env)
    rounds = args.rounds or config["experiment"]["trainer_rounds"]

    trajectories_path = resolve_path(args.env, config["paths"]["training_trajectories"])
    if not trajectories_path.exists():
        raise SystemExit(
            f"No training trajectories found at {trajectories_path}. Run collect_trajectories.py first."
        )
    trajectories = load_trajectories(str(trajectories_path))
    print(f"Loaded {len(trajectories)} training trajectories "
          f"({sum(1 for t in trajectories if t['success'])} success, "
          f"{sum(1 for t in trajectories if not t['success'])} failure)")

    client = ModelClient(config)
    strategy_names = ["naive", "gated", "expel", "avo"] if args.strategy == "all" else [args.strategy]

    all_history = {}
    for strat in strategy_names:
        print(f"\n=== Training strategy: {strat} ({rounds} round(s)) ===")
        ctx = build_context(args.env, strat, config, client, trajectories, rounds, args.harness)
        result = get_trainer(strat)(ctx)

        skill_path = skill_path_for(args.env, strat, config)
        skill_path.parent.mkdir(parents=True, exist_ok=True)
        skill_path.write_text(result["skill"].rstrip() + "\n")
        print(f"[{strat}] wrote {skill_path}")

        all_history[strat] = result["history"]

    rounds_log_path = resolve_path(args.env, config["paths"]["trainer_rounds_log"])
    rounds_log_path.parent.mkdir(parents=True, exist_ok=True)
    rounds_log_path.write_text(json.dumps(all_history, indent=2))
    print(f"\nWrote round history to {rounds_log_path}")


if __name__ == "__main__":
    main()
