"""Generate training trajectories by running the skill-less baseline agent
against an environment's "train" split, until the configured success/failure
quotas are filled.

Usage:
    python collect_trajectories.py --env alfworld [--harness api|cli]

`--harness cli` routes every action-selection call through an external
harness's CLI (see core/backend.py and `harness.cli.command` in
config.yaml) instead of a direct API call -- so the training trajectories
this produces, and therefore the skill later distilled from them, come from
whatever tool a person actually uses (Claude Code, OpenCode, ...), not just
skill-rl's own loop.
"""

import argparse
import json

import environments  # noqa: F401 -- registers all environment plugins
from core.agent import run_episode
from core.backend import build_backend
from core.environment import get as get_environment
from util import load_config, resolve_path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--env", required=True, help="Registered environment name, e.g. 'alfworld'.")
    parser.add_argument("--harness", default="api", choices=["api", "cli"],
                         help="Backend for action selection: direct API, or an external harness's CLI.")
    args = parser.parse_args()

    config = load_config(args.env)
    exp = config["experiment"]

    env_factory = get_environment(args.env)
    env = env_factory(config, split="train")

    backend = build_backend(config, args.harness)
    max_steps = config["experiment"]["max_steps"]

    target_success = exp["num_train_success"]
    target_fail = exp["num_train_fail"]
    max_episodes = exp["max_train_episodes"]

    out_path = resolve_path(args.env, config["paths"]["training_trajectories"])
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n_success = 0
    n_fail = 0
    episode = 0

    with open(out_path, "w") as out_f:
        while (n_success < target_success or n_fail < target_fail) and episode < max_episodes:
            if episode >= env.num_tasks:
                print(f"Exhausted train split after {episode} episodes ({env.num_tasks} tasks available).")
                break
            episode += 1

            result = run_episode(env, backend, max_steps, skill_text=None)

            if result.success and n_success >= target_success:
                print(f"[{episode}] success quota full, skipping (task: {result.task})")
                continue
            if not result.success and n_fail >= target_fail:
                print(f"[{episode}] failure quota full, skipping (task: {result.task})")
                continue

            out_f.write(json.dumps(result.to_json()) + "\n")
            out_f.flush()
            if result.success:
                n_success += 1
            else:
                n_fail += 1

            status = "SUCCESS" if result.success else "FAILURE"
            print(f"[{episode}] {status} ({len(result.steps)} steps, {result.total_tokens} tokens): {result.task}")
            print(f"  progress: {n_success}/{target_success} success, {n_fail}/{target_fail} failure")

    env.close()
    print(f"\nWrote {n_success + n_fail} trajectories to {out_path}")
    print(f"  success: {n_success}, failure: {n_fail}")
    if n_success < target_success or n_fail < target_fail:
        print("Warning: quotas not fully met (ran out of episodes). Consider raising max_train_episodes.")


if __name__ == "__main__":
    main()
