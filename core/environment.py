"""Environment plugin contract.

Every environment (ALFWorld, or a new one someone adds) implements this shape and
registers itself under a string name. `core/agent.py` only ever talks to this
interface -- it never imports anything environment-specific.

`step`/`reset` return an `info` dict using the same keys regardless of environment:
    "admissible_commands": list[str]  -- the only actions accepted right now
    "won": bool                        -- only meaningful once done=True
    "task_id": str                     -- stable unique id for this episode's task
    "task": str                        -- human-readable task description

Environment-specific quirks (a pseudo "help" command, how to parse a task
description out of raw text, wrapper setup, etc.) belong in the plugin, not here.
"""

from typing import Callable, Protocol


class Environment(Protocol):
    num_tasks: int

    def reset(self) -> tuple[str, dict]: ...

    def step(self, action: str) -> tuple[str, bool, dict]: ...

    def close(self) -> None: ...


_REGISTRY: dict[str, Callable[..., Environment]] = {}


def register(name: str, factory: Callable[..., Environment]) -> None:
    _REGISTRY[name] = factory


def get(name: str) -> Callable[..., Environment]:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown environment '{name}'. Registered: {list(_REGISTRY)}")
    return _REGISTRY[name]


def available() -> list[str]:
    return list(_REGISTRY)
