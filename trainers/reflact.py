"""ReflACT strategy: a port of Microsoft SkillOpt's core training algorithm
(github.com/microsoft/SkillOpt, internally named "ReflACT") -- Rollout,
Reflect, Aggregate, Select, Update, Evaluate/Gate -- onto this repo's
insight-list skill representation and single-API-backend infrastructure.

Ported faithfully (the stages that actually shape training dynamics):
  - Rollout: on-policy -- every step rolls out a fresh batch from the
    "train" split under the *current* skill, not a fixed pre-collected
    skill-less baseline set. This is why, unlike naive/gated/expel/avo,
    this trainer ignores `ctx.trajectories` entirely.
  - Reflect: one analyst LLM call per minibatch of trajectories (failures
    and successes analyzed separately), not one call over everything.
  - Aggregate: hierarchical merging of per-minibatch deltas into one
    pooled candidate delta, failure-driven patches taking priority over
    success-driven ones in the final combine.
  - Select: how many of the pooled candidate additions to actually apply
    this step (their "learning rate") is controlled every step, not just
    on stagnation like avo's binary trigger. Default matches their
    published configs: a cosine-decaying budget (edit_budget -> min_edit_budget
    over training); `reflact_lr_control_mode: autonomous` switches this to
    their alternative per-step LLM decision instead of the schedule. Either
    way, a ranking call then picks the top-budget additions from the pool.
  - Evaluate/Gate: candidate vs. *both* a running "current" skill and the
    best-ever "best" skill (current can wander below best and still keep
    training; only a new best-beater updates the final output), with an
    optional semantic-density penalty that docks the gate score if a
    skill gets bloated with keyword-stuffing (MUST/ALWAYS/CRITICAL/...).

  - Slow update: at each epoch boundary, a fixed set of "longitudinal"
    sample tasks is rolled out under the epoch's ending skill and compared
    against the same tasks' rollout under the *previous* epoch's ending
    skill (regressed / persistent-fail / improved / stable-success). A
    dedicated LLM call reflects on that comparison plus its own prior
    guidance and writes updated free-form guidance into a protected region
    of the skill (`core.skill`'s `SLOW_UPDATE_START/END` markers) that
    ordinary step-level edits can never touch. Unlike the main gate, this
    update is force-accepted unconditionally by default (matches their
    `slow_update_gate_with_selection: false`) -- it runs on a completely
    separate track from accept/reject/best-tracking above. This was added
    after comparing against a real run of the upstream repo: on SearchQA,
    their main gate rejected every single step (identical in kind to ours),
    and 100% of their reported improvement came from this mechanism alone.

Deliberately NOT ported (out of scope -- see the real repo for the full
system): their general op-based text-patch DSL with arbitrary
insert_after/replace/delete spans (we keep this repo's simpler add/remove
insight-list delta so every trainer shares `core.skill`'s helpers), the
meta-skill layer and the appendix/skill-aware-reflection mechanism, "soft"
partial-credit scoring (every environment here is binary win/lose, so soft
== hard), and all deployment infra (Azure OpenAI, Ray, 7 backend configs,
resume/checkpoint state -- this repo already has its own harness
abstraction, core/backend.py).

Hyperparameters default to the real repo's published `configs/_base_/default.yaml`
(and its `searchqa`/`livemathematicianbench` overrides, which don't touch these
values): batch_size=40, gradient.minibatch_size=merge_batch_size=8,
analyst_workers=16, optimizer.learning_rate=4 (max edit budget),
min_learning_rate=2, lr_control_mode=fixed with lr_scheduler=cosine (NOT the
autonomous per-step LLM decision -- that exists in their repo but isn't what
their published SearchQA/LiveMathematicianBench configs actually use), and
train_size/num_epochs=4 determining the total step count the same way their
engine/trainer.py does: steps_per_epoch = ceil(train_size / batch_size),
total_steps = num_epochs * steps_per_epoch. Also fixed here to match their
design: Rollout now advances through the train pool each step (base_offset
rotates by batch_size, wrapping at train_size) instead of resampling the same
first `batch_size` tasks every step. Slow update defaults match their base
config too: use_slow_update=True, slow_update_samples=20,
slow_update_gate_with_selection=False (force-accept).
"""

import json
import math
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from core import skill
from core.trainer import TrainerContext, dev_eval, format_trajectory, format_trajectory_group, register, run_rollout

PROMPT_DIR = Path(__file__).parent / "prompts"

_LEADING_WORDS = {
    "must", "always", "never", "only", "critical", "important",
    "resolve", "prefer", "ensure", "strict", "verify",
}


def _load(name: str) -> str:
    return (PROMPT_DIR / f"{name}.md").read_text()


def _semantic_density(skill_text: str) -> float:
    """Fraction of words that are high-influence keywords -- a proxy for
    keyword-stuffed, bloated skill text (SkillOpt's anti-bloat regularizer)."""
    words = re.findall(r"[a-zA-Z0-9]+", skill_text.lower())
    if not words:
        return 0.0
    return sum(1 for w in words if w in _LEADING_WORDS) / len(words)


def _build_longitudinal_comparison(prev_results: list, curr_results: list) -> tuple[str, int]:
    """Categorize the same tasks' outcomes under two skill versions into
    regressed/persistent_fail/improved/stable_success and format for the
    slow-update prompt. Returns (comparison_text, n_common_tasks)."""
    prev_by_id = {r.task_id: r for r in prev_results}
    buckets: dict[str, list[tuple]] = {"regressed": [], "persistent_fail": [], "improved": [], "stable_success": []}
    for curr in curr_results:
        prev = prev_by_id.get(curr.task_id)
        if prev is None:
            continue
        if prev.success and not curr.success:
            buckets["regressed"].append((prev, curr))
        elif not prev.success and not curr.success:
            buckets["persistent_fail"].append((prev, curr))
        elif not prev.success and curr.success:
            buckets["improved"].append((prev, curr))
        else:
            buckets["stable_success"].append((prev, curr))

    n_common = sum(len(v) for v in buckets.values())
    parts = [
        f"Total samples: {n_common}\n"
        f"- Improved (wrong->right): {len(buckets['improved'])}\n"
        f"- Regressed (right->wrong): {len(buckets['regressed'])}\n"
        f"- Persistent failures (wrong->wrong): {len(buckets['persistent_fail'])}\n"
        f"- Stable successes (right->right): {len(buckets['stable_success'])}\n"
    ]
    for key, label in (
        ("regressed", "Regressions (right->wrong) -- HIGHEST PRIORITY"),
        ("persistent_fail", "Persistent Failures (wrong->wrong)"),
        ("improved", "Improvements (wrong->right)"),
    ):
        entries = buckets[key]
        if not entries:
            parts.append(f"### {label}\n(none)\n")
            continue
        lines = [f"### {label}"]
        for prev, curr in entries:
            lines.append(f"\n#### Task {curr.task_id}\nPrev epoch: {'PASS' if prev.success else 'FAIL'}"
                         f"\nCurr epoch: {'PASS' if curr.success else 'FAIL'}")
            lines.append("Prev epoch trajectory:\n" + format_trajectory(prev.to_json(), 1))
            lines.append("Curr epoch trajectory:\n" + format_trajectory(curr.to_json(), 1))
        parts.append("\n".join(lines))
    return "\n\n".join(parts), n_common


def _scheduled_edit_budget(mode: str, step: int, total_steps: int, max_lr: int, min_lr: int) -> int:
    """Port of skillopt/optimizer/scheduler.py's constant/linear/cosine
    formulas exactly (1-indexed step, clamped to total_steps)."""
    if mode == "constant" or total_steps <= 1:
        return max_lr
    t = min(step, total_steps) / total_steps
    if mode == "linear":
        lr = max_lr + (min_lr - max_lr) * t
    elif mode == "cosine":
        lr = min_lr + 0.5 * (max_lr - min_lr) * (1 + math.cos(math.pi * t))
    else:
        raise ValueError(f"Unknown reflact_lr_scheduler '{mode}'; expected constant, linear, or cosine")
    return max(min_lr, round(lr))


def run(ctx: TrainerContext) -> dict:
    cfg = ctx.extra
    batch_size = cfg.get("reflact_batch_size", 40)
    minibatch_size = cfg.get("reflact_minibatch_size", 8)
    merge_batch_size = max(2, cfg.get("reflact_merge_batch_size", 8))
    lr_control_mode = cfg.get("reflact_lr_control_mode", "fixed")
    lr_scheduler = cfg.get("reflact_lr_scheduler", "cosine")
    max_edit_budget = cfg.get("reflact_edit_budget", 4)
    min_edit_budget = cfg.get("reflact_min_edit_budget", 2)
    use_semantic_density = cfg.get("reflact_use_semantic_density", True)
    semantic_density_weight = cfg.get("reflact_semantic_density_weight", 0.05)
    workers = cfg.get("reflact_analyst_workers", 16)
    use_slow_update = cfg.get("reflact_use_slow_update", True)
    slow_update_samples = cfg.get("reflact_slow_update_samples", 20)
    slow_update_gate_with_selection = cfg.get("reflact_slow_update_gate_with_selection", False)

    # Step count: steps_per_epoch = ceil(train_size / batch_size), total = num_epochs * that
    # -- same derivation as their engine/trainer.py. train_size defaults to their
    # published searchqa value (400); override reflact_train_size per environment
    # (e.g. to match a smaller "train" split) via experiments/<env>/config.yaml's
    # `experiment.reflact.reflact_train_size`.
    num_epochs = cfg.get("reflact_num_epochs", 4)
    train_size = cfg.get("reflact_train_size", 400)
    steps_per_epoch = math.ceil(train_size / batch_size)
    steps = num_epochs * steps_per_epoch

    preamble, seed_insights = skill.parse_insights(ctx.current_skill)

    def _chat(prompt: str) -> str:
        raw_text, _usage = ctx.client.chat(
            model=ctx.model, messages=[{"role": "user", "content": prompt}],
            temperature=ctx.trainer_temperature, max_tokens=ctx.trainer_max_tokens,
        )
        return raw_text

    def full_skill_text(insights: list[str], slow_update_content: str) -> str:
        rendered = skill.render_insights(preamble, insights)
        return skill.replace_slow_update_field(rendered, slow_update_content) if slow_update_content else rendered

    def score_text(skill_text: str):
        return dev_eval(ctx, skill_text, ctx.dev_tasks)

    def score(insights: list[str]):
        return score_text(skill.render_insights(preamble, insights))

    def gate_score(hard: float, skill_text: str) -> float:
        s = hard
        if use_semantic_density:
            s += semantic_density_weight * _semantic_density(skill_text)
        return s

    def slow_update_call(prev_skill_text: str, curr_skill_text: str, prev_guidance: str,
                          prev_results: list, curr_results: list) -> dict | None:
        comparison_text, n_pairs = _build_longitudinal_comparison(prev_results, curr_results)
        prompt = _load("reflact_slow_update").format(
            prev_skill=prev_skill_text, curr_skill=curr_skill_text,
            prev_guidance=prev_guidance.strip() or "(No previous guidance -- this is the first slow update.)",
            n_pairs=n_pairs, comparison_text=comparison_text,
        )
        data = skill.extract_json(_chat(prompt))
        content = data.get("slow_update_content") if data else None
        if not isinstance(content, str) or not content.strip():
            return None
        return {"reasoning": str(data.get("reasoning", "")).strip(), "slow_update_content": content.strip()}

    def analyst_call(template_name: str, current_insights: list[str], batch: list, edit_budget: int) -> dict:
        prompt = _load(template_name).format(
            edit_budget=edit_budget,
            current_insights=skill.format_insight_list(current_insights),
            batch_size=len(batch),
            trajectories=format_trajectory_group([r.to_json() for r in batch]),
        )
        return skill.extract_insight_delta(_chat(prompt))

    def merge_call(template_name: str, deltas: list[dict], current_insights: list[str], level: int) -> dict:
        prompt = _load(template_name).format(
            current_insights=skill.format_insight_list(current_insights),
            n_deltas=len(deltas), level=level,
            deltas=json.dumps(deltas, ensure_ascii=False, indent=2),
        )
        return skill.extract_insight_delta(_chat(prompt))

    def hierarchical_merge(template_name: str, deltas: list[dict], current_insights: list[str]) -> dict:
        if not deltas:
            return {"add": [], "remove": []}
        current = list(deltas)
        level = 0
        while len(current) > 1:
            level += 1
            batches = [current[i:i + merge_batch_size] for i in range(0, len(current), merge_batch_size)]
            next_level: list[dict | None] = [None] * len(batches)
            to_merge = []
            for idx, b in enumerate(batches):
                if len(b) == 1:
                    next_level[idx] = b[0]
                else:
                    to_merge.append((idx, b))
            if to_merge:
                with ThreadPoolExecutor(max_workers=workers) as ex:
                    futs = {
                        ex.submit(merge_call, template_name, b, current_insights, level): idx
                        for idx, b in to_merge
                    }
                    for fut in as_completed(futs):
                        next_level[futs[fut]] = fut.result()
            current = next_level
        return current[0]

    def merge_final(failure_delta: dict, success_delta: dict, current_insights: list[str]) -> dict:
        prompt = _load("reflact_merge_final").format(
            current_insights=skill.format_insight_list(current_insights),
            n_failure_add=len(failure_delta["add"]),
            failure_delta=json.dumps(failure_delta, ensure_ascii=False, indent=2),
            n_success_add=len(success_delta["add"]),
            success_delta=json.dumps(success_delta, ensure_ascii=False, indent=2),
        )
        return skill.extract_insight_delta(_chat(prompt))

    def rank_and_select(current_insights: list[str], pool: list[str], budget: int) -> list[str]:
        if len(pool) <= budget:
            return pool
        pool_desc = "\n".join(f"[{i}] {text}" for i, text in enumerate(pool))
        prompt = _load("reflact_ranking").format(
            current_insights=skill.format_insight_list(current_insights),
            n_pool=len(pool), budget=budget, pool=pool_desc,
        )
        data = skill.extract_json(_chat(prompt))
        if data and isinstance(data.get("selected_indices"), list):
            selected, seen = [], set()
            for idx in data["selected_indices"]:
                if isinstance(idx, int) and 0 <= idx < len(pool) and idx not in seen:
                    selected.append(pool[idx])
                    seen.add(idx)
                if len(selected) >= budget:
                    break
            if selected:
                return selected
        return pool[:budget]  # fallback: truncate

    def autonomous_edit_budget(current_insights: list[str], pool: list[str], rollout_hard: float, rollout_n: int) -> int:
        if not pool:
            return 0
        pool_desc = "\n".join(f"[{i}] {text}" for i, text in enumerate(pool))
        prompt = _load("reflact_lr_autonomous").format(
            current_insights=skill.format_insight_list(current_insights),
            rollout_n=rollout_n, rollout_success_rate=f"{rollout_hard:.4f}",
            n_pool=len(pool), pool=pool_desc,
        )
        data = skill.extract_json(_chat(prompt))
        if data and "learning_rate" in data:
            try:
                return max(0, min(int(data["learning_rate"]), len(pool)))
            except (TypeError, ValueError):
                pass
        return min(max_edit_budget, len(pool))

    print(f"[reflact] baseline dev-eval ({ctx.dev_tasks} tasks)...")
    baseline_hard, _ = score(seed_insights)
    current_insights = list(seed_insights)
    current_slow_update_content = ""
    current_score = gate_score(baseline_hard, skill.render_insights(preamble, current_insights))
    best_insights, best_score = list(current_insights), current_score
    print(f"[reflact] baseline: hard={baseline_hard:.2f} gate_score={current_score:.4f}")

    history = [{"step": 0, "action": "baseline", "rollout_hard": baseline_hard, "gate_score": current_score}]

    # Slow update: a fixed longitudinal sample set (near the tail of the train
    # pool, to reduce overlap with early rollout batches) rolled out once under
    # the baseline skill to seed the "previous epoch" comparison state.
    prev_epoch_skill_text = None
    prev_epoch_results: list = []
    prev_epoch_slow_update_content = ""
    if use_slow_update:
        longitudinal_offset = max(0, train_size - slow_update_samples)
        longitudinal_count = min(slow_update_samples, train_size)
        print(f"[reflact] slow-update baseline rollout ({longitudinal_count} fixed longitudinal tasks)...")
        prev_epoch_skill_text = full_skill_text(current_insights, current_slow_update_content)
        _, prev_epoch_results = run_rollout(
            ctx, "train", prev_epoch_skill_text, longitudinal_count, base_offset=longitudinal_offset,
        )

    for step in range(1, steps + 1):
        print(f"\n[reflact] step {step}/{steps}")
        current_skill_text = full_skill_text(current_insights, current_slow_update_content)

        # ① ROLLOUT -- live train-split episodes under the CURRENT skill (on-policy),
        # advancing through the train pool each step instead of resampling the same batch.
        # The last chunk of each epoch is smaller when train_size isn't a multiple of
        # batch_size (mirrors steps_per_epoch = ceil(train_size / batch_size) naturally
        # producing a smaller final batch) -- without this clamp, that chunk's requested
        # count overflows past the "train" split's own boundary and crashes the environment.
        base_offset = ((step - 1) * batch_size) % train_size
        this_batch_size = min(batch_size, train_size - base_offset)
        rollout_hard, rollout_results = run_rollout(ctx, "train", current_skill_text, this_batch_size, base_offset=base_offset)
        failures = [r for r in rollout_results if not r.success]
        successes = [r for r in rollout_results if r.success]
        print(f"[reflact] step {step}: rollout hard={rollout_hard:.2f} ({len(failures)} fail, {len(successes)} success)")

        # ② REFLECT -- one analyst call per minibatch, parallelized
        fail_batches = [failures[i:i + minibatch_size] for i in range(0, len(failures), minibatch_size)]
        succ_batches = [successes[i:i + minibatch_size] for i in range(0, len(successes), minibatch_size)]

        fail_deltas: list[dict] = []
        succ_deltas: list[dict] = []
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {}
            for b in fail_batches:
                futs[ex.submit(analyst_call, "reflact_analyst_error", current_insights, b, max_edit_budget)] = "fail"
            for b in succ_batches:
                futs[ex.submit(analyst_call, "reflact_analyst_success", current_insights, b, max_edit_budget)] = "succ"
            for fut in as_completed(futs):
                (fail_deltas if futs[fut] == "fail" else succ_deltas).append(fut.result())

        print(f"[reflact] step {step}: reflect -> {len(fail_deltas)} failure delta(s), {len(succ_deltas)} success delta(s)")

        if not any(d["add"] or d["remove"] for d in fail_deltas + succ_deltas):
            print(f"[reflact] step {step}: no patches -- skill unchanged")
            history.append({"step": step, "action": "skip_no_patches", "rollout_hard": rollout_hard,
                             "current_score": current_score, "best_score": best_score})
        else:
            # ③ AGGREGATE -- hierarchical merge, failure-priority final combine
            merged_failure = hierarchical_merge("reflact_merge_failure", fail_deltas, current_insights)
            merged_success = hierarchical_merge("reflact_merge_success", succ_deltas, current_insights)

            if merged_failure["add"] or merged_failure["remove"]:
                merged = (
                    merge_final(merged_failure, merged_success, current_insights)
                    if (merged_success["add"] or merged_success["remove"])
                    else merged_failure
                )
            else:
                merged = merged_success

            pool = merged["add"]
            print(f"[reflact] step {step}: aggregate -> {len(pool)} candidate addition(s), {len(merged['remove'])} removal(s)")

            # ④ SELECT -- decide this step's edit budget, then rank+trim the pool
            if lr_control_mode == "autonomous":
                edit_budget = autonomous_edit_budget(current_insights, pool, rollout_hard, len(rollout_results))
            else:
                edit_budget = min(_scheduled_edit_budget(lr_scheduler, step, steps, max_edit_budget, min_edit_budget), len(pool))
            selected_add = rank_and_select(current_insights, pool, edit_budget) if pool else []
            print(f"[reflact] step {step}: select -> budget={edit_budget} ({lr_control_mode}/{lr_scheduler}), kept {len(selected_add)}/{len(pool)}")

            # ⑤ UPDATE
            candidate_insights, added = skill.apply_delta(list(current_insights), {"add": selected_add, "remove": merged["remove"]})

            # ⑥ EVALUATE / GATE -- vs. both current and best-ever. Scored on
            # insights alone (no slow-update section) -- that mechanism is a
            # fully separate, epoch-boundary-only track (see below); mixing it
            # into this per-step comparison would make best_score describe a
            # skill state best_insights alone can no longer reproduce once
            # slow-update content moves on.
            candidate_text = skill.render_insights(preamble, candidate_insights)
            candidate_hard, _ = score_text(candidate_text)
            candidate_score = gate_score(candidate_hard, candidate_text)

            if candidate_score > current_score:
                action = "accept_new_best" if candidate_score > best_score else "accept"
                print(f"[reflact] step {step}: {action.upper()} (gate {current_score:.4f} -> {candidate_score:.4f}, "
                      f"hard={candidate_hard:.2f}), added={added!r} removed={merged['remove']!r}")
                current_insights, current_score = candidate_insights, candidate_score
                if action == "accept_new_best":
                    best_insights, best_score = candidate_insights, candidate_score
            else:
                action = "reject"
                print(f"[reflact] step {step}: REJECTED (gate {candidate_score:.4f} did not beat current {current_score:.4f})")

            history.append({
                "step": step, "action": action, "rollout_hard": rollout_hard, "edit_budget": edit_budget,
                "added": added, "removed": merged["remove"], "candidate_hard": candidate_hard,
                "candidate_gate_score": candidate_score, "current_score": current_score, "best_score": best_score,
            })

        # SLOW UPDATE -- epoch boundary only, independent of this step's fast-update
        # outcome above. Force-accepted by default (matches their
        # slow_update_gate_with_selection: false); optionally gated instead.
        if use_slow_update and step % steps_per_epoch == 0:
            curr_epoch_skill_text = full_skill_text(current_insights, current_slow_update_content)
            print(f"[reflact] step {step}: slow-update epoch boundary -- rolling out {longitudinal_count} fixed longitudinal tasks...")
            _, curr_epoch_results = run_rollout(
                ctx, "train", curr_epoch_skill_text, longitudinal_count, base_offset=longitudinal_offset,
            )
            result = slow_update_call(
                prev_epoch_skill_text, curr_epoch_skill_text, prev_epoch_slow_update_content,
                prev_epoch_results, curr_epoch_results,
            )
            if result is None:
                print(f"[reflact] step {step}: slow-update call failed to parse -- guidance unchanged")
            else:
                new_content = result["slow_update_content"]
                if slow_update_gate_with_selection:
                    candidate_su_text = full_skill_text(current_insights, new_content)
                    su_hard, _ = score_text(candidate_su_text)
                    su_score = gate_score(su_hard, candidate_su_text)
                    applied = su_score > current_score
                    print(f"[reflact] step {step}: slow-update {'ACCEPTED' if applied else 'REJECTED'} "
                          f"(gated: {su_score:.4f} vs current {current_score:.4f})")
                else:
                    applied = True
                    print(f"[reflact] step {step}: slow-update force-accepted (unconditional)")
                if applied:
                    current_slow_update_content = new_content
                history.append({
                    "step": step, "action": "slow_update", "applied": applied,
                    "reasoning": result["reasoning"], "slow_update_content": current_slow_update_content,
                })
            prev_epoch_skill_text = full_skill_text(current_insights, current_slow_update_content)
            prev_epoch_results = curr_epoch_results
            prev_epoch_slow_update_content = current_slow_update_content

    # Reconcile the two independent tracks (gate-validated best_insights, and
    # whatever slow-update guidance is active) into the single exported skill --
    # keep whichever combination actually scores higher on our own held-out gate,
    # since slow-update's force-accept means it was never validated against
    # best_insights specifically (only against current_insights, epoch by epoch).
    if use_slow_update and current_slow_update_content:
        combined_text = full_skill_text(best_insights, current_slow_update_content)
        combined_hard, _ = score_text(combined_text)
        combined_score = gate_score(combined_hard, combined_text)
        print(f"[reflact] final: best-only gate={best_score:.4f} vs best+slow-update gate={combined_score:.4f}")
        chose = "best+slow_update" if combined_score > best_score else "best_only"
        history.append({"step": steps, "action": "final_reconcile", "chose": chose,
                         "best_only_score": best_score, "combined_score": combined_score})
        if chose == "best+slow_update":
            return {"skill": combined_text, "history": history}

    return {"skill": skill.render_insights(preamble, best_insights), "history": history}


register("reflact", run)
