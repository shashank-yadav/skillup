"""Trainer plugin contract + shared helpers.

Each trainer strategy (naive/gated/expel/avo, or one you add) implements
`run(ctx: TrainerContext) -> {"skill": str, "history": list[dict]}` and
registers itself under a string name via `register()`.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Callable

from core.llm import ModelClient
from core.runner import run_parallel


@dataclass
class TrainerContext:
    client: ModelClient           # for the trainer's own distillation call (always direct API)
    model: str
    trainer_temperature: float
    trainer_max_tokens: int
    current_skill: str
    trajectories: list[dict]
    rounds: int
    dev_split: str = "valid_seen"
    harness: str = "api"
    config: dict | None = None     # the full merged experiment config, needed to rebuild env+backend per worker process
    dev_tasks: int = 0
    max_steps: int = 0
    max_parallel_workers: int = 10
    extra: dict[str, Any] = field(default_factory=dict)


_REGISTRY: dict[str, Callable[[TrainerContext], dict]] = {}


def register(name: str, fn: Callable[[TrainerContext], dict]) -> None:
    _REGISTRY[name] = fn


def get(name: str) -> Callable[[TrainerContext], dict]:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown trainer strategy '{name}'. Registered: {list(_REGISTRY)}")
    return _REGISTRY[name]


def available() -> list[str]:
    return list(_REGISTRY)


def load_trajectories(path: str) -> list[dict]:
    trajectories = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                trajectories.append(json.loads(line))
    return trajectories


def format_trajectory(traj: dict, index: int) -> str:
    outcome = "SUCCESS" if traj["success"] else "FAILURE"
    lines = [f"### Trajectory {index} ({outcome})", f"Task: {traj['task']}"]
    for i, step in enumerate(traj["steps"], 1):
        lines.append(f"{i}. Observation: {step['observation']}")
        lines.append(f"   Action: {step['action']}")
    return "\n".join(lines)


def format_trajectory_group(trajectories: list[dict]) -> str:
    if not trajectories:
        return "(none)"
    return "\n\n".join(format_trajectory(t, i) for i, t in enumerate(trajectories, 1))


def _rollout_worker(offset: int, count: int, args: dict) -> list:
    """Runs in its own process (see core.runner.run_parallel) -- a fresh
    process doesn't inherit the parent's already-registered plugins, so this
    re-imports what it needs and rebuilds the environment/backend fresh from
    picklable arguments, the same pattern evaluate_skill.py's shard worker
    uses. This is what makes gated/avo's dev-eval rounds (and reflact's live
    train rollouts) fast regardless of which environment is configured --
    nothing here is ALFWorld-specific."""
    import environments  # noqa: F401 -- registers plugins in this process
    from core.agent import run_episode
    from core.backend import build_backend
    from core.environment import get as get_environment

    config = args["config"]
    absolute_offset = args["base_offset"] + offset
    env = get_environment(config["environment"])(config, split=args["split"], offset=absolute_offset, count=count)
    backend = build_backend(config, args["harness"])
    try:
        return [
            run_episode(env, backend, args["max_steps"], skill_text=args["skill_text"])
            for _ in range(count)
        ]
    finally:
        env.close()


def run_rollout(
    ctx: TrainerContext, split: str, skill_text: str, n_tasks: int, base_offset: int = 0,
) -> tuple[float, list]:
    """Run n_tasks fresh episodes on `split` under skill_text, starting at
    `base_offset` within that split, parallelized across
    ctx.max_parallel_workers processes, and return (success_rate, results).
    Generic over which split -- `dev_eval` below is just this pinned to
    ctx.dev_split with base_offset=0; `reflact` (SkillOpt-style) also calls
    this directly against the "train" split to get on-policy rollouts under
    the *current* skill each step, advancing base_offset each step so it
    samples a fresh batch instead of the same first n_tasks every time."""
    args = {
        "config": ctx.config, "split": split, "base_offset": base_offset,
        "harness": ctx.harness, "max_steps": ctx.max_steps, "skill_text": skill_text,
    }
    results = run_parallel(_rollout_worker, n_tasks, ctx.max_parallel_workers, args)
    success_rate = sum(1 for r in results if r.success) / len(results) if results else 0.0
    return success_rate, results


def dev_eval(ctx: TrainerContext, skill_text: str, n_tasks: int) -> tuple[float, list]:
    """Run n_tasks fresh episodes under skill_text, parallelized across
    ctx.max_parallel_workers processes, and return (success_rate, results)."""
    return run_rollout(ctx, ctx.dev_split, skill_text, n_tasks)


def format_episode_failures(results: list) -> str:
    failed = [r for r in results if not r.success]
    if not failed:
        return "(none -- all held-out validation tasks succeeded)"
    return "\n\n".join(format_trajectory(r.to_json(), i) for i, r in enumerate(failed, 1))
