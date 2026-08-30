"""Trainer plugin contract + shared helpers.

Each trainer strategy (naive/gated/expel/avo, or one you add) implements
`run(ctx: TrainerContext) -> {"skill": str, "history": list[dict]}` and
registers itself under a string name via `register()`.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Callable

from core.agent import run_episode
from core.backend import Backend
from core.environment import Environment
from core.llm import ModelClient


@dataclass
class TrainerContext:
    client: ModelClient          # for the trainer's own distillation call (always direct API)
    model: str
    trainer_temperature: float
    trainer_max_tokens: int
    current_skill: str
    trajectories: list[dict]
    rounds: int
    make_env: Callable[[], Environment] | None = None  # fresh dev-eval environment, or None
    backend: Backend | None = None  # rollout backend for dev-eval (gated/avo) -- api or an external harness
    dev_tasks: int = 0
    max_steps: int = 0
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


def dev_eval(env: Environment, ctx: TrainerContext, skill_text: str, n_tasks: int) -> tuple[float, list]:
    """Run n_tasks fresh episodes under skill_text and return (success_rate, results)."""
    results = [
        run_episode(env, ctx.backend, ctx.max_steps, skill_text=skill_text)
        for _ in range(n_tasks)
    ]
    success_rate = sum(1 for r in results if r.success) / len(results) if results else 0.0
    return success_rate, results


def format_episode_failures(results: list) -> str:
    failed = [r for r in results if not r.success]
    if not failed:
        return "(none -- all held-out validation tasks succeeded)"
    return "\n\n".join(format_trajectory(r.to_json(), i) for i, r in enumerate(failed, 1))
