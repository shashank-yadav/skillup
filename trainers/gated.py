"""Gated strategy: SkillOpt-style bounded edits with a validation gate.

Each round proposes a small structured insight delta, evaluates the
resulting candidate on a held-out dev split, and only keeps it if it beats
the current best dev success rate. Rejected edits are logged and shown to
the next round so it doesn't repeat them.
"""

from pathlib import Path

from core import skill
from core.trainer import TrainerContext, dev_eval, format_episode_failures, format_trajectory_group, register

PROMPT_PATH = Path(__file__).parent / "prompts" / "gated.md"


def run(ctx: TrainerContext) -> dict:
    successes = [t for t in ctx.trajectories if t["success"]]
    failures = [t for t in ctx.trajectories if not t["success"]]
    success_block = format_trajectory_group(successes)
    failed_block = format_trajectory_group(failures)
    template = PROMPT_PATH.read_text()

    preamble, insights = skill.parse_insights(ctx.current_skill)

    print(f"[gated] baseline dev-eval ({ctx.dev_tasks} tasks)...")
    env = ctx.make_env()
    best_score, dev_results = dev_eval(env, ctx, skill.render_insights(preamble, insights), ctx.dev_tasks)
    env.close()
    print(f"[gated] baseline dev success rate: {best_score:.2f}")

    best_insights = insights
    dev_failures_block = format_episode_failures(dev_results)
    rejected_log: list[str] = []
    history = [{"round": 0, "action": "baseline", "dev_success_rate": best_score, "accepted": True}]

    for round_number in range(1, ctx.rounds + 1):
        print(f"\n[gated] round {round_number}/{ctx.rounds}: proposing edit...")
        prompt = template.format(
            round_number=round_number,
            current_insights=skill.format_insight_list(best_insights),
            success_trajectories=success_block,
            failed_trajectories=failed_block,
            dev_failures=dev_failures_block,
            rejected_edits="\n\n---\n\n".join(rejected_log) if rejected_log else "(none yet)",
        )
        raw_text, _usage = ctx.client.chat(
            model=ctx.model, messages=[{"role": "user", "content": prompt}],
            temperature=ctx.trainer_temperature, max_tokens=ctx.trainer_max_tokens,
        )
        delta = skill.extract_insight_delta(raw_text)
        candidate_insights, added = skill.apply_delta(list(best_insights), delta)
        candidate_skill = skill.render_insights(preamble, candidate_insights)
        print(f"[gated] round {round_number}: add={added!r} remove={delta['remove']!r} "
              f"-- evaluating on {ctx.dev_tasks} dev tasks...")

        env = ctx.make_env()
        candidate_score, candidate_results = dev_eval(env, ctx, candidate_skill, ctx.dev_tasks)
        env.close()

        accepted = candidate_score > best_score
        history.append({
            "round": round_number, "dev_success_rate": candidate_score, "accepted": accepted,
            "added": added, "removed": delta["remove"],
        })

        if accepted:
            print(f"[gated] round {round_number}: ACCEPTED ({best_score:.2f} -> {candidate_score:.2f})")
            best_insights = candidate_insights
            best_score = candidate_score
            dev_failures_block = format_episode_failures(candidate_results)
        else:
            print(f"[gated] round {round_number}: REJECTED (scored {candidate_score:.2f}, did not beat {best_score:.2f})")
            rejected_log.append(
                f"Round {round_number} (dev success rate {candidate_score:.2f}, "
                f"did not beat {best_score:.2f}): add={added!r} remove={delta['remove']!r}"
            )

    return {"skill": skill.render_insights(preamble, best_insights), "history": history}


register("gated", run)
