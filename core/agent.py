"""LLM-driven agent loop -- environment-agnostic.

The agent is stateless across the API boundary: at every step we rebuild a
single prompt containing the task, the trajectory so far, the current
observation, and the admissible commands, and ask the model to pick exactly
one of them. This keeps token accounting simple and avoids relying on
multi-turn chat state.

This module only depends on the `core.environment.Environment` contract
(reset/step/close plus the standard `info` dict keys) -- it has no knowledge
of any specific environment. Environment-specific setup lives in
`environments/<name>/env.py`.
"""

from dataclasses import dataclass, field

from core.environment import Environment
from core.llm import ModelClient

BASE_INSTRUCTIONS = """You are an agent completing a task in an interactive text-based environment.

At each turn you receive an observation describing what you currently perceive, and a
list of admissible commands: the only actions the environment will accept right now.

Rules:
- Respond with exactly one command, copied verbatim from the admissible commands list.
- Do not add explanations, punctuation, or extra text -- output only the command.
- Interact with objects using the exact names shown in the observation and admissible
  commands (e.g. "apple 1", "fridge 1").
- The task is complete only when the environment tells you so; keep acting until then
  or until you run out of steps.
"""


def build_system_prompt(skill_text: str | None) -> str:
    if not skill_text:
        return BASE_INSTRUCTIONS
    return f"{BASE_INSTRUCTIONS}\n\n# Learned strategies\n\n{skill_text}"


def detect_stuck_cycle(history: list[dict]) -> list[str] | None:
    """Return the repeating action cycle if the agent's last actions consist of a
    short cycle (length 1-5) repeated three times back to back, else None.

    Inspection of real trajectories showed ~65% of failures across every
    condition (baseline included) end this way -- the agent gets stuck
    re-examining/re-opening the same object or bouncing between two
    locations until it runs out of steps, rather than failing to search
    broadly enough. No skill text ever addressed this because it's a
    runtime behavior problem, not something a static strategy doc fixes."""
    actions = [step["action"] for step in history]
    for cycle_len in (1, 2, 3, 4, 5):
        needed = cycle_len * 3
        if len(actions) < needed:
            continue
        tail = actions[-needed:]
        cycle = tail[-cycle_len:]
        if tail == cycle * 3:
            return cycle
    return None


def filter_stuck_actions(admissible_commands: list[str], cycle: list[str] | None) -> list[str]:
    """Remove the cycling action(s) from the choices offered, so the model can't just
    keep picking the same thing again -- a soft text notice alone was tested and found
    to not change behavior: the model acknowledges it, then repeats anyway. Falls back
    to the unfiltered list if removing the cycle would leave nothing to choose from."""
    if not cycle:
        return admissible_commands
    cycle_set = set(cycle)
    filtered = [c for c in admissible_commands if c not in cycle_set]
    return filtered if filtered else admissible_commands


def format_step_prompt(
    task: str, history: list[dict], observation: str, admissible_commands: list[str],
    stuck_notice: str | None = None,
) -> str:
    lines = [f"Task: {task}", ""]
    if history:
        lines.append("History:")
        for i, step in enumerate(history, 1):
            lines.append(f"{i}. Observation: {step['observation']}")
            lines.append(f"   Action: {step['action']}")
        lines.append("")
    lines.append(f"Current observation: {observation}")
    lines.append("")
    if stuck_notice:
        lines.append(f"SUPERVISOR NOTICE: {stuck_notice}")
        lines.append("")
    if admissible_commands:
        lines.append("Admissible commands:")
        for cmd in admissible_commands:
            lines.append(f"- {cmd}")
        lines.append("")
        lines.append("Respond with exactly one admissible command and nothing else.")
    else:
        # No fixed action list -- e.g. a single-turn, free-form-answer task
        # (question answering, math, classification) rather than a discrete
        # multi-step action space like a game.
        lines.append("Respond with your answer as free text, and nothing else.")
    return "\n".join(lines)


def parse_action(raw_text: str, admissible_commands: list[str]) -> str:
    cleaned = raw_text.strip().strip('"').strip("'").strip()
    if not admissible_commands:
        # Free-form task: nothing to match against, so the cleaned response is the answer.
        return cleaned
    for cmd in admissible_commands:
        if cmd.strip().lower() == cleaned.lower():
            return cmd
    for cmd in admissible_commands:
        if cmd.strip().lower() in cleaned.lower() or cleaned.lower() in cmd.strip().lower():
            return cmd
    return admissible_commands[0]


@dataclass
class EpisodeResult:
    task: str
    task_id: str = ""
    steps: list = field(default_factory=list)
    success: bool = False
    total_tokens: int = 0

    def to_json(self) -> dict:
        return {
            "task": self.task,
            "task_id": self.task_id,
            "steps": self.steps,
            "success": self.success,
            "total_tokens": self.total_tokens,
        }


def run_episode(
    env: Environment,
    client: ModelClient,
    model: str,
    temperature: float,
    max_tokens: int,
    max_steps: int,
    skill_text: str | None = None,
) -> EpisodeResult:
    observation, info = env.reset()
    task = info["task"]
    system_prompt = build_system_prompt(skill_text)

    result = EpisodeResult(task=task, task_id=info.get("task_id", ""))
    history: list[dict] = []
    admissible_commands = info["admissible_commands"]

    for _ in range(max_steps):
        stuck_notice = None
        cycle = detect_stuck_cycle(history)
        step_admissible = admissible_commands
        if cycle:
            cycle_str = " -> ".join(cycle)
            step_admissible = filter_stuck_actions(admissible_commands, cycle)
            stuck_notice = (
                f"You repeated the action pattern [{cycle_str}] multiple times without making "
                f"progress. Those actions have been removed from your choices below -- pick "
                f"something else."
            )
        user_prompt = format_step_prompt(task, history, observation, step_admissible, stuck_notice)
        raw_text, usage = client.chat(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        result.total_tokens += usage.get("total_tokens", 0)
        action = parse_action(raw_text, step_admissible)

        step_record = {"observation": observation, "action": action}
        result.steps.append(step_record)
        history.append(step_record)

        observation, done, info = env.step(action)
        if done:
            result.success = bool(info.get("won", False))
            break
        admissible_commands = info["admissible_commands"]

    return result
