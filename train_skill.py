"""Read training trajectories and distill them into an updated SKILL.md,
using one of several pluggable trainer strategies.

Usage:
    python train_skill.py --env alfworld [--strategy naive|gated|expel|avo|reflact|all] [--rounds N] [--harness api|cli]

All strategies start from the same pristine skills/SKILL.initial.md, so their
outputs are directly comparable. "naive" writes skills/SKILL.md (the
canonical path); "gated", "expel", "avo", and "reflact" write sibling
SKILL.<strategy>.md files so multiple strategies can coexist and be compared
by evaluate_skill.py in one run. "reflact" (a port of Microsoft SkillOpt's
core algorithm) is not included in --strategy all -- it rolls out live
training episodes every round instead of reusing collect_trajectories.py's
output, so it costs meaningfully more per round; run it explicitly.

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

    dev_tasks = 0
    extra: dict = {}
    if strategy == "gated":
        dev_tasks = exp["num_dev_tasks"]
    elif strategy == "avo":
        dev_tasks = exp["avo_dev_tasks_per_candidate"]
        extra["population_size"] = exp.get("avo_population_size", 3)
    elif strategy == "reflact":
        dev_tasks = exp.get("reflact_dev_tasks", exp.get("num_dev_tasks", 20))
        extra = dict(exp.get("reflact", {}))  # all keys optional -- trainers/reflact.py has its own defaults

    return TrainerContext(
        client=client,
        model=trainer_model_name(config),
        trainer_temperature=config["model"]["trainer_temperature"],
        trainer_max_tokens=config["model"]["trainer_max_tokens"],
        current_skill=current_skill,
        trajectories=trajectories,
        rounds=rounds,
        dev_split="valid_seen",
        harness=harness,
        config=config,
        dev_tasks=dev_tasks,
        max_steps=exp["max_steps"],
        max_parallel_workers=config.get("max_parallel_workers", 10),
        extra=extra,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--env", required=True, help="Registered environment name, e.g. 'alfworld'.")
    parser.add_argument("--strategy", default="naive", choices=["naive", "gated", "expel", "avo", "reflact", "all"])
    parser.add_argument("--rounds", type=int, default=None)
    parser.add_argument("--harness", default="api", choices=["api", "cli"],
                         help="Backend for gated/avo's dev-eval rollouts: direct API, or an external harness's CLI.")
    parser.add_argument("--model", default=None,
                         help="Override config.yaml's agent_model AND trainer_model with this OpenRouter model id.")
    args = parser.parse_args()

    config = load_config(args.env)
    if args.model:
        config["model"]["agent_model"] = args.model
        config["model"]["trainer_model"] = args.model
    rounds = args.rounds or config["experiment"]["trainer_rounds"]

    strategy_names = ["naive", "gated", "expel", "avo"] if args.strategy == "all" else [args.strategy]
    # "reflact" ignores ctx.trajectories entirely -- its Rollout stage is on-policy,
    # rolling out the "train" split live under the current skill each step, so it
    # needs no pre-collected trajectories file at all.
    needs_trajectories = any(s != "reflact" for s in strategy_names)

    trajectories_path = resolve_path(args.env, config["paths"]["training_trajectories"])
    trajectories: list[dict] = []
    if trajectories_path.exists():
        trajectories = load_trajectories(str(trajectories_path))
        print(f"Loaded {len(trajectories)} training trajectories "
              f"({sum(1 for t in trajectories if t['success'])} success, "
              f"{sum(1 for t in trajectories if not t['success'])} failure)")
    elif needs_trajectories:
        raise SystemExit(
            f"No training trajectories found at {trajectories_path}. Run collect_trajectories.py first."
        )

    client = ModelClient(config)

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
