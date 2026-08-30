"""ExpeL strategy: incremental insight accumulation, no validation gate.

Each round proposes a small structured insight delta and always accepts it
-- unlike `gated`, there's no held-out check, so this can drift without
converging on anything better than baseline (and did, in this session's
runs). Kept as a useful contrast case.
"""

from pathlib import Path

from core import skill
from core.trainer import TrainerContext, format_trajectory_group, register

PROMPT_PATH = Path(__file__).parent / "prompts" / "expel.md"


def run(ctx: TrainerContext) -> dict:
    successes = [t for t in ctx.trajectories if t["success"]]
    failures = [t for t in ctx.trajectories if not t["success"]]
    success_block = format_trajectory_group(successes)
    failed_block = format_trajectory_group(failures)
    template = PROMPT_PATH.read_text()

    preamble, insights = skill.parse_insights(ctx.current_skill)
    history = []

    for round_number in range(1, ctx.rounds + 1):
        print(f"[expel] round {round_number}/{ctx.rounds}: proposing insights...")
        prompt = template.format(
            round_number=round_number,
            current_insights=skill.format_insight_list(insights),
            success_trajectories=success_block,
            failed_trajectories=failed_block,
        )
        raw_text, _usage = ctx.client.chat(
            model=ctx.model, messages=[{"role": "user", "content": prompt}],
            temperature=ctx.trainer_temperature, max_tokens=ctx.trainer_max_tokens,
        )
        delta = skill.extract_insight_delta(raw_text)
        insights, added = skill.apply_delta(insights, delta)
        print(f"[expel] round {round_number}: added={added!r} removed={delta['remove']!r} "
              f"({len(insights)} insights total)")

        history.append({
            "round": round_number, "accepted": True, "added": added, "removed": delta["remove"],
        })

    return {"skill": skill.render_insights(preamble, insights), "history": history}


register("expel", run)
