"""A Backend answers one (system_prompt, user_prompt) turn and returns
(text, usage). This is what `core.agent.run_episode` calls each step to pick
an action -- swapping the backend lets rollout (and therefore training,
since training trajectories come from rollout) run through a direct API
call, or through an external harness someone already has installed (Claude
Code, OpenCode, ...), so a skill can be learned from whatever tool a person
actually uses day to day, not just skill-rl's own loop.
"""

import shlex
import subprocess
from typing import Protocol

from core.llm import ModelClient


class Backend(Protocol):
    def chat(self, system_prompt: str, user_prompt: str) -> tuple[str, dict]: ...


class ApiBackend:
    """Direct API calls via core.llm.ModelClient -- the default."""

    def __init__(self, client: ModelClient, model: str, temperature: float, max_tokens: int):
        self.client = client
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def chat(self, system_prompt: str, user_prompt: str) -> tuple[str, dict]:
        return self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )


class CliHarnessBackend:
    """Shells out to any CLI tool that accepts a system prompt and a user
    prompt and prints a single text response -- not hardcoded to one
    product. Config-driven (`harness.cli.command` in config.yaml), e.g. for
    Claude Code:

        command: >-
          claude -p {user_prompt} --system-prompt {system_prompt}
          --tools "" --no-session-persistence --output-format text

    Verified against Claude Code's `-p` mode: with tool use disabled and
    session persistence off, it responds with exactly the chosen action and
    nothing else -- the same shape as a raw chat completion, at the cost of
    roughly 5-10x the latency of a direct API call, since each turn spins up
    a fresh session rather than reusing an open connection. Usage/token
    accounting is unavailable for most external CLIs, so `total_tokens`
    stays 0 for episodes run this way -- and every call spends whatever
    account/credits the harness itself is configured to use, separate from
    this framework's own API key.
    """

    def __init__(self, config: dict):
        cli_cfg = config["harness"]["cli"]
        self.command_template = cli_cfg["command"]
        self.timeout_s = cli_cfg.get("timeout_s", 120)

    def chat(self, system_prompt: str, user_prompt: str) -> tuple[str, dict]:
        command = self.command_template.format(
            system_prompt=shlex.quote(system_prompt),
            user_prompt=shlex.quote(user_prompt),
        )
        proc = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=self.timeout_s)
        return proc.stdout.strip(), {}


def build_backend(config: dict, harness: str) -> Backend:
    if harness == "api":
        client = ModelClient(config)
        return ApiBackend(
            client, config["model"]["agent_model"],
            config["model"]["agent_temperature"], config["model"]["agent_max_tokens"],
        )
    if harness == "cli":
        return CliHarnessBackend(config)
    raise ValueError(f"Unknown harness '{harness}', expected 'api' or 'cli'.")
