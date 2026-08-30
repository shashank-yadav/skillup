"""ALFWorld environment plugin.

Wraps ALFWorld's TextWorld backend behind the `core.environment.Environment`
contract, normalizing its info dict into the standard keys every environment
plugin returns (admissible_commands/won/task_id/task) and hiding ALFWorld
quirks (a "help" pseudo-command, parsing the task description out of raw
observation text) inside this module.
"""

import os
import re
import threading

import alfworld.agents.environment as environment
import textworld
import textworld.gym
from alfworld.agents.environment.alfred_tw_env import AlfredDemangler, AlfredInfos

from core.environment import register

SPLIT_TO_TRAIN_EVAL = {
    "train": "train",
    "valid_seen": "eval_in_distribution",
    "valid_unseen": "eval_out_of_distribution",
}
TASK_LINE_RE = re.compile(r"Your task is to:\s*(.+)")


def resolve_data_dir(data_dir_env: str, default: str) -> str:
    path = os.environ.get(data_dir_env) or default
    path = os.path.expanduser(os.path.expandvars(path))
    if not os.path.isdir(path):
        raise FileNotFoundError(
            f"ALFWorld data directory not found at '{path}'. "
            f"Set ${data_dir_env} or run `alfworld-download`."
        )
    return path


def build_alfworld_config(data_dir: str, task_types, max_steps: int) -> dict:
    """Minimal config AlfredTWEnv needs, without touching the RL/vision
    sections of alfworld's full base_config.yaml."""
    return {
        "dataset": {
            "data_path": os.path.join(data_dir, "json_2.1.1", "train"),
            "eval_id_data_path": os.path.join(data_dir, "json_2.1.1", "valid_seen"),
            "eval_ood_data_path": os.path.join(data_dir, "json_2.1.1", "valid_unseen"),
            "num_train_games": -1,
            "num_eval_games": -1,
        },
        "logic": {
            "domain": os.path.join(data_dir, "logic", "alfred.pddl"),
            "grammar": os.path.join(data_dir, "logic", "alfred.twl2"),
        },
        "env": {
            "type": "AlfredTWEnv",
            "domain_randomization": False,
            "task_types": list(task_types),
            "expert_timeout_steps": 150,
            "expert_type": "handcoded",
            "goal_desc_human_anns_prob": 0.0,
        },
        "general": {"training_method": "dqn"},
        "rl": {"training": {"max_nb_steps_per_episode": max_steps}},
    }


def extract_task(observation: str) -> str:
    match = TASK_LINE_RE.search(observation)
    return match.group(1).strip() if match else observation.strip()


def _first(value):
    return value[0] if isinstance(value, (list, tuple)) else value


def _first_infos(infos: dict) -> dict:
    return {k: _first(v) for k, v in infos.items()}


_GAME_FILES_CACHE: dict[tuple, list[str]] = {}
_CACHE_LOCK = threading.Lock()

# TextWorld's PDDL game loader (via the `tatsu` grammar parser) keeps shared,
# non-reentrant parser state and was found to corrupt/crash when two threads
# load a game at the same moment -- verified by an actual concurrency stress
# test, not a theoretical concern. Every reset() triggers a fresh game load
# (each reset advances to a different game file), so this lock is held on
# every reset, not just once at startup -- but loading is fast (well under a
# second; the PDDL solver preprocessing that dominates it is local CPU work),
# so serializing just that moment costs little next to the LLM API calls
# that dominate an episode's wall-clock time, which stay fully concurrent.
_RESET_LOCK = threading.Lock()


def _cached_game_files(config: dict, split: str) -> list[str]:
    """The expensive part: AlfredTWEnv.collect_game_files() walks and filters
    thousands of directories (~5-10s). Do it once per (data path, task types)
    and reuse the sorted list for every subsequent environment instance in
    this process, instead of repeating the walk per instance -- which is what
    happened when this project ran each shard as its own OS process. Locked
    so N threads racing on a cold cache at startup don't all pay the cost.

    Sorted explicitly: os.walk()'s order is not guaranteed, and was found
    this session to actually differ across concurrently-running processes
    reading the same directory tree. Sorting makes ordering a pure function
    of the file set, immune to filesystem traversal timing."""
    train_eval = SPLIT_TO_TRAIN_EVAL[split]
    data_path_key = {
        "train": config["dataset"]["data_path"],
        "eval_in_distribution": config["dataset"]["eval_id_data_path"],
        "eval_out_of_distribution": config["dataset"]["eval_ood_data_path"],
    }[train_eval]
    key = (data_path_key, tuple(config["env"]["task_types"]))

    with _CACHE_LOCK:
        if key not in _GAME_FILES_CACHE:
            env_cls = environment.get_environment(config["env"]["type"])
            wrapper = env_cls(config, train_eval=train_eval)
            _GAME_FILES_CACHE[key] = sorted(wrapper.game_files)
        return _GAME_FILES_CACHE[key]


class AlfworldEnvironment:
    """Takes the generic merged experiment config (the dict `util.load_config()`
    returns, with a top-level "alfworld" section) -- all ALFWorld-specific config
    translation happens inside this constructor, so callers never need to know
    ALFWorld's internal nested config shape."""

    def __init__(self, config: dict, split: str, offset: int = 0, count: int | None = None):
        if split not in SPLIT_TO_TRAIN_EVAL:
            raise ValueError(f"Unknown split '{split}', expected one of {list(SPLIT_TO_TRAIN_EVAL)}")
        alfworld_cfg = config["alfworld"]
        data_dir = resolve_data_dir(alfworld_cfg["data_dir_env"], alfworld_cfg["data_dir_default"])
        max_steps = config["experiment"]["max_steps"]
        aw_config = build_alfworld_config(data_dir, alfworld_cfg["task_types"], max_steps)

        game_files = _cached_game_files(aw_config, split)
        end = None if count is None else offset + count
        self.game_files = game_files[offset:end]
        self.num_tasks = len(self.game_files)

        request_infos = textworld.EnvInfos(won=True, admissible_commands=True, extras=["gamefile"])
        wrappers = [AlfredDemangler(shuffle=False), AlfredInfos]
        env_id = textworld.gym.register_games(
            self.game_files, request_infos, batch_size=1, asynchronous=False,
            max_episode_steps=max_steps, wrappers=wrappers,
        )
        self._env = textworld.gym.make(env_id)

    def reset(self) -> tuple[str, dict]:
        with _RESET_LOCK:
            obs, infos = self._env.reset()
        obs, infos = _first(obs), _first_infos(infos)
        info = {
            "admissible_commands": [c for c in infos["admissible_commands"] if c != "help"],
            "won": bool(infos.get("won", False)),
            "task_id": infos.get("extra.gamefile", ""),
            "task": extract_task(obs),
        }
        return obs, info

    def step(self, action: str) -> tuple[str, bool, dict]:
        obs, _scores, dones, infos = self._env.step([action])
        obs, done, infos = _first(obs), _first(dones), _first_infos(infos)
        info = {
            "admissible_commands": [] if done else [c for c in infos["admissible_commands"] if c != "help"],
            "won": bool(infos.get("won", False)),
            "task_id": infos.get("extra.gamefile", ""),
            "task": "",
        }
        return obs, done, info

    def close(self) -> None:
        self._env.close()


register("alfworld", AlfworldEnvironment)
