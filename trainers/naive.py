"""Naive strategy: single-shot full-document rewrite.

Simplest possible distillation -- one LLM call reads every training
trajectory and rewrites the whole skill document. No validation, no
iteration. Despite (or maybe because of) its simplicity, this was the only
strategy to show a consistent positive signal across every evaluation run
this session.
"""

from pathlib import Path

from core import skill
from core.trainer import TrainerContext, format_trajectory_group, register

PROMPT_PATH = Path(__file__).parent / "prompts" / "naive.md"


def run(ctx: TrainerContext) -> dict:
    successes = [t for t in ctx.trajectories if t["success"]]
    failures = [t for t in ctx.trajectories if not t["success"]]
    if not successes and not failures:
        raise ValueError("No trajectories to train on.")

    template = PROMPT_PATH.read_text()
    prompt = template.format(
        current_skill=ctx.current_skill,
        success_trajectories=format_trajectory_group(successes),
        failed_trajectories=format_trajectory_group(failures),
    )
    raw_text, _usage = ctx.client.chat(
        model=ctx.model, messages=[{"role": "user", "content": prompt}],
        temperature=ctx.trainer_temperature, max_tokens=ctx.trainer_max_tokens,
    )
    result_skill = skill.strip_code_fence(raw_text)
    return {"skill": result_skill, "history": [{"round": 1, "accepted": True, "skill": result_skill}]}


register("naive", run)
