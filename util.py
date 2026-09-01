"""Small shared helpers used by the top-level collect/train/evaluate scripts."""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent


def experiment_dir(env: str) -> Path:
    return REPO_ROOT / "experiments" / env


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursive dict merge -- a bare `dict.update` would let an
    environment config that sets e.g. `model: {agent_max_tokens: 1024}`
    silently wipe out the rest of the root config's `model` block
    (agent_model, api_key_env, ...) instead of overriding just that one
    key."""
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(env: str, root_config_path: str = "config.yaml") -> dict:
    """Merge the shared root config (model settings, parallelism) with the
    environment-specific config under experiments/<env>/config.yaml."""
    with open(REPO_ROOT / root_config_path) as f:
        config = yaml.safe_load(f)
    env_config_path = experiment_dir(env) / "config.yaml"
    if not env_config_path.exists():
        raise FileNotFoundError(
            f"No config found for environment '{env}' at {env_config_path}."
        )
    with open(env_config_path) as f:
        env_config = yaml.safe_load(f)
    return _deep_merge(config, env_config)


def trainer_model_name(config: dict) -> str:
    return config["model"]["trainer_model"] or config["model"]["agent_model"]


def resolve_path(env: str, config_path: str) -> Path:
    return experiment_dir(env) / config_path
