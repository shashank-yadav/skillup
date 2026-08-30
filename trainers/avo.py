"""AVO-style strategy: population search with crossover and stagnation handling.

`population_size` skill lineages evolve in parallel, each gated by its own
dev-split score (like `gated`, but per lineage). Accepted/rejected edits from
every lineage feed a shared knowledge base that all lineages see. Each
generation, the two best-scoring lineages are cross-bred into a merged
candidate that replaces the worst lineage if it scores higher. A lineage
that hasn't improved the population's best score in `STAGNATION_PATIENCE`
generations is told to try a more radical edit instead of a small one.
"""

from pathlib import Path

from core import skill
from core.trainer import TrainerContext, dev_eval, format_episode_failures, format_trajectory_group, register

PROMPT_PATH = Path(__file__).parent / "prompts" / "avo.md"
DEFAULT_POPULATION_SIZE = 3
STAGNATION_PATIENCE = 2
_EDIT_BUDGET_NORMAL = "Propose at most 2 additions and at most 2 removals this generation."
_EDIT_BUDGET_STAGNATION = (
    "This lineage has stagnated -- no lineage has improved in the last couple of "
    "generations. Propose a more exploratory change: at most 4 additions, and try a "
    "substantially different angle than what is already in the current insights or the "
    "knowledge base below, rather than a small refinement."
)


def run(ctx: TrainerContext) -> dict:
    population_size = ctx.extra.get("population_size", DEFAULT_POPULATION_SIZE)
    successes = [t for t in ctx.trajectories if t["success"]]
    failures = [t for t in ctx.trajectories if not t["success"]]
    success_block = format_trajectory_group(successes)
    failed_block = format_trajectory_group(failures)
    template = PROMPT_PATH.read_text()

    preamble, seed_insights = skill.parse_insights(ctx.current_skill)

    def score(insights: list[str], label: str):
        env = ctx.make_env()
        s, results = dev_eval(env, ctx, skill.render_insights(preamble, insights), ctx.dev_tasks)
        env.close()
        return s, results

    def propose(lineage_id: int, insights: list[str], dev_failures: str, knowledge_base: list[str], stagnant: bool) -> dict:
        kb_text = "\n".join(f"- {k}" for k in knowledge_base[-10:]) if knowledge_base else "(none yet)"
        prompt = template.format(
            lineage_id=lineage_id,
            current_insights=skill.format_insight_list(insights),
            success_trajectories=success_block,
            failed_trajectories=failed_block,
            dev_failures=dev_failures,
            knowledge_base=kb_text,
            edit_budget_note=_EDIT_BUDGET_STAGNATION if stagnant else _EDIT_BUDGET_NORMAL,
        )
        raw_text, _usage = ctx.client.chat(
            model=ctx.model, messages=[{"role": "user", "content": prompt}],
            temperature=ctx.trainer_temperature, max_tokens=ctx.trainer_max_tokens,
        )
        return skill.extract_insight_delta(raw_text)

    print(f"[avo] seeding population of {population_size} lineages ({ctx.dev_tasks} dev tasks each)...")
    lineages = []
    knowledge_base: list[str] = []
    history = []

    for i in range(population_size):
        delta = propose(i + 1, seed_insights, "(no prior evaluation yet -- initial seeding round)", [], stagnant=False)
        insights, added = skill.apply_delta(list(seed_insights), delta)
        s, results = score(insights, label=f"avo gen0 lineage{i + 1}")
        lineages.append({"insights": insights, "score": s, "dev_failures": format_episode_failures(results)})
        history.append({"generation": 0, "lineage": i + 1, "dev_success_rate": s, "added": added, "removed": delta["remove"]})
        print(f"[avo] gen0 lineage{i + 1}: added={added!r} -> dev success rate {s:.2f}")

    best_so_far = max(l["score"] for l in lineages)
    stagnant_generations = 0

    for gen in range(1, ctx.rounds + 1):
        stagnation_active = stagnant_generations >= STAGNATION_PATIENCE
        print(f"\n[avo] generation {gen}/{ctx.rounds}" + (" (stagnation intervention active)" if stagnation_active else ""))

        for i, lineage in enumerate(lineages):
            delta = propose(i + 1, lineage["insights"], lineage["dev_failures"], knowledge_base, stagnation_active)
            candidate_insights, added = skill.apply_delta(list(lineage["insights"]), delta)
            candidate_score, candidate_results = score(candidate_insights, label=f"avo gen{gen} lineage{i + 1}")

            accepted = candidate_score > lineage["score"]
            history.append({
                "generation": gen, "lineage": i + 1, "dev_success_rate": candidate_score,
                "accepted": accepted, "added": added, "removed": delta["remove"],
                "stagnation_intervention": stagnation_active,
            })

            if accepted:
                print(f"[avo] gen{gen} lineage{i + 1}: ACCEPTED ({lineage['score']:.2f} -> {candidate_score:.2f}), added={added!r}")
                knowledge_base.append(
                    f"Gen{gen} lineage{i + 1} ADDED (helped, {lineage['score']:.2f}->{candidate_score:.2f}): {added}"
                )
                lineage["insights"] = candidate_insights
                lineage["score"] = candidate_score
                lineage["dev_failures"] = format_episode_failures(candidate_results)
            else:
                print(f"[avo] gen{gen} lineage{i + 1}: REJECTED (scored {candidate_score:.2f}, did not beat {lineage['score']:.2f})")
                if added:
                    knowledge_base.append(
                        f"Gen{gen} lineage{i + 1} REJECTED (did not beat {lineage['score']:.2f}, got {candidate_score:.2f}): {added}"
                    )

        if population_size >= 3:
            ranked = sorted(range(population_size), key=lambda idx: lineages[idx]["score"], reverse=True)
            best_idx, second_idx, worst_idx = ranked[0], ranked[1], ranked[-1]
            merged_insights = skill.crossover(lineages[best_idx]["insights"], lineages[second_idx]["insights"])
            merged_score, merged_results = score(merged_insights, label=f"avo gen{gen} crossover")
            crossover_accepted = merged_score > lineages[worst_idx]["score"]
            history.append({
                "generation": gen, "lineage": "crossover", "dev_success_rate": merged_score,
                "accepted": crossover_accepted, "parents": [best_idx + 1, second_idx + 1], "replaced": worst_idx + 1,
            })
            if crossover_accepted:
                print(f"[avo] gen{gen} crossover ({best_idx + 1}x{second_idx + 1}): ACCEPTED "
                      f"({lineages[worst_idx]['score']:.2f} -> {merged_score:.2f}), replaced lineage{worst_idx + 1}")
                lineages[worst_idx] = {
                    "insights": merged_insights, "score": merged_score,
                    "dev_failures": format_episode_failures(merged_results),
                }
            else:
                print(f"[avo] gen{gen} crossover ({best_idx + 1}x{second_idx + 1}): REJECTED "
                      f"(scored {merged_score:.2f}, did not beat lineage{worst_idx + 1}'s {lineages[worst_idx]['score']:.2f})")

        current_best = max(l["score"] for l in lineages)
        stagnant_generations = 0 if current_best > best_so_far else stagnant_generations + 1
        best_so_far = max(best_so_far, current_best)
        print(f"[avo] gen{gen} best-so-far: {best_so_far:.2f}" + (f" (stagnant {stagnant_generations} gen(s))" if stagnant_generations else ""))

    best_lineage = max(lineages, key=lambda l: l["score"])
    return {"skill": skill.render_insights(preamble, best_lineage["insights"]), "history": history}


register("avo", run)
