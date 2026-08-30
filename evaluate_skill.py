"""Run the held-out evaluation set once without any skill, and once per
learned SKILL.md variant found in skills/ (SKILL.md, SKILL.gated.md,
SKILL.expel.md, ...), using the identical model, prompts, and inference
settings, and report the success-rate comparison across all conditions.

By default each condition runs across `max_parallel_workers` (config.yaml)
concurrent OS processes via core/runner.py's process pool -- one call kicks
off the whole thing instead of hand-launching N background commands. The LLM
API call is I/O-bound and the actual bottleneck, so this gives real
wall-clock speedup even though each process pays its own environment setup
cost (that cost is paid concurrently across processes, not multiplied by N).

Usage:
    python evaluate_skill.py --env alfworld
        Run every condition (each parallelized internally) in sequence,
        then report the comparison.

    python evaluate_skill.py --env alfworld --condition naive
    python evaluate_skill.py --env alfworld --condition naive --shard-index 0 --shard-count 3
        Run just ONE condition (optionally just one shard of it) -- for
        isolating a crash, or distributing shards across separate machines.
        Each still parallelizes internally.

    python evaluate_skill.py --env alfworld --merge
        Skip running anything; read whichever condition trajectory files (or
        complete shard sets) exist on disk and produce the combined report.

Add --harness cli to route every action-selection call through an external
harness's CLI (Claude Code, OpenCode, ...) instead of a direct API call --
useful for checking a skill's effect against how a real harness actually
behaves, not just a raw completion. See core/backend.py.
"""

import argparse
import json
import re

import environments  # noqa: F401 -- registers all environment plugins
from core.runner import run_parallel, shard_bounds
from util import load_config, resolve_path

SKILL_FILE_RE = re.compile(r"^SKILL(?:\.(?P<variant>[^.]+))?\.md$")


def discover_skill_files(env: str, config: dict) -> dict:
    skill_dir = resolve_path(env, config["paths"]["skill_dir"])
    initial_path = resolve_path(env, config["paths"]["initial_skill_file"]).resolve()
    variants = {}
    for path in sorted(skill_dir.glob("SKILL*.md")):
        if path.resolve() == initial_path:
            continue
        match = SKILL_FILE_RE.match(path.name)
        if not match:
            continue
        label = match.group("variant") or "naive"
        variants[label] = path
    return variants


def condition_path(env: str, config: dict, label: str):
    paths = config["paths"]
    if label == "baseline":
        return resolve_path(env, paths["eval_baseline_trajectories"])
    eval_path = resolve_path(env, paths["eval_skill_trajectories"])
    return eval_path.with_name(f"{eval_path.stem}_{label}{eval_path.suffix}")


def shard_path(env: str, config: dict, label: str, shard_index: int, shard_count: int):
    base = condition_path(env, config, label)
    return base.with_name(f"{base.stem}.shard{shard_index}of{shard_count}{base.suffix}")


def write_jsonl(path, dicts: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for d in dicts:
            f.write(json.dumps(d) + "\n")


def read_jsonl(path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def read_condition_results(env: str, config: dict, label: str) -> list[dict] | None:
    """Read a condition's full results, assembling and caching them from a
    complete set of shard files first if the canonical file isn't there yet."""
    canonical = condition_path(env, config, label)
    if canonical.exists():
        return read_jsonl(canonical)

    shard_re = re.compile(rf"^{re.escape(canonical.stem)}\.shard(\d+)of(\d+){re.escape(canonical.suffix)}$")
    parsed = []
    for p in canonical.parent.glob(f"{canonical.stem}.shard*of*{canonical.suffix}"):
        match = shard_re.match(p.name)
        if match:
            parsed.append((int(match.group(1)), int(match.group(2)), p))
    if not parsed:
        return None

    total = parsed[0][1]
    indices_found = {i for i, t, _ in parsed if t == total}
    if any(t != total for _, t, _ in parsed) or indices_found != set(range(total)):
        print(f"Note: incomplete/inconsistent shards for '{label}' ({len(parsed)} found, expected {total} matching); "
              f"waiting for the rest before assembling.")
        return None

    parsed.sort(key=lambda x: x[0])
    combined = [row for _, _, p in parsed for row in read_jsonl(p)]
    write_jsonl(canonical, combined)
    print(f"Assembled {len(combined)} results for '{label}' from {total} shards -> {canonical}")
    return combined


def summarize(results: list[dict]) -> dict:
    n = len(results)
    successes = sum(1 for r in results if r["success"])
    success_steps = [len(r["steps"]) for r in results if r["success"]]
    return {
        "n_tasks": n,
        "n_success": successes,
        "success_rate": successes / n if n else 0.0,
        "avg_steps_successful": sum(success_steps) / len(success_steps) if success_steps else 0.0,
        "avg_tokens": sum(r["total_tokens"] for r in results) / n if n else 0.0,
    }


def format_table(summary: dict) -> str:
    lines = [f"Model: {summary['model']}", "", f"Evaluation tasks: {summary['n_eval_tasks']}", ""]
    for label, s in summary["conditions"].items():
        title = "Without skill (baseline)" if label == "baseline" else f"With learned skill [{label}]"
        lines.append(f"{title}:")
        lines.append(f"  Success: {s['n_success']}/{s['n_tasks']} ({s['success_rate'] * 100:.1f}%)")
        lines.append(f"  Avg steps (successful tasks): {s['avg_steps_successful']:.1f}")
        lines.append(f"  Avg tokens/task: {s['avg_tokens']:.0f}")
        lines.append("")
    lines.append("Improvement over baseline:")
    for label, pp in summary["improvement_pp"].items():
        lines.append(f"  [{label}]: {pp:+.1f} percentage points")
    return "\n".join(lines)


def build_and_write_summary(env: str, config: dict, model: str, all_results: dict[str, list[dict]]):
    paths = config["paths"]
    n_tasks = min(len(r) for r in all_results.values())

    for label, results in all_results.items():
        if label == "baseline":
            continue
        mismatches = sum(
            1 for a, b in zip(all_results["baseline"][:n_tasks], results[:n_tasks]) if a["task_id"] != b["task_id"]
        )
        if mismatches:
            print(f"Warning: {mismatches}/{n_tasks} task pairs for '{label}' did not line up with baseline "
                  f"(env ordering differed between runs).")

    summaries = {label: summarize(results[:n_tasks]) for label, results in all_results.items()}

    per_task = []
    for i in range(n_tasks):
        row = {"task_id": all_results["baseline"][i]["task_id"], "task": all_results["baseline"][i]["task"]}
        for label, results in all_results.items():
            row[f"{label}_success"] = results[i]["success"]
            row[f"{label}_steps"] = len(results[i]["steps"])
            row[f"{label}_tokens"] = results[i]["total_tokens"]
        per_task.append(row)

    summary = {
        "model": model,
        "n_eval_tasks": n_tasks,
        "conditions": summaries,
        "improvement_pp": {
            label: (summaries[label]["success_rate"] - summaries["baseline"]["success_rate"]) * 100
            for label in summaries if label != "baseline"
        },
        "per_task": per_task,
    }

    results_summary_path = resolve_path(env, paths["results_summary"])
    results_summary_path.parent.mkdir(parents=True, exist_ok=True)
    results_summary_path.write_text(json.dumps(summary, indent=2))

    table = format_table(summary)
    resolve_path(env, paths["results_table"]).write_text(table)

    print("\n" + table)
    print(f"\nWrote {results_summary_path} and {paths['results_table']}")


def _run_shard(offset: int, count: int, args: dict) -> list[dict]:
    """Runs in its own process (see core.runner.run_parallel) -- a fresh
    process doesn't inherit the parent's already-registered plugins, so this
    re-imports what it needs. Only picklable arguments (plain dict/str/int)
    cross the process boundary, hence `args` rather than closures."""
    import environments  # noqa: F401 -- registers plugins in this process
    from core.agent import run_episode
    from core.backend import build_backend
    from core.environment import get as get_environment

    config = args["config"]
    label = args["label"]
    absolute_offset = args["base_offset"] + offset
    env = get_environment(args["env"])(config, split="valid_unseen", offset=absolute_offset, count=count)
    backend = build_backend(config, args["harness"])
    max_steps = config["experiment"]["max_steps"]
    skill_text = args["skill_text"]

    results = []
    for _ in range(count):
        result = run_episode(env, backend, max_steps, skill_text=skill_text)
        status = "SUCCESS" if result.success else "FAILURE"
        print(f"  [{label}] {status} ({len(result.steps)} steps, {result.total_tokens} tokens): {result.task}")
        results.append(result.to_json())
    env.close()
    return results


def run_condition(
    env: str, config: dict, label: str, skill_path, offset: int, n_tasks: int, max_workers: int, harness: str,
) -> list[dict]:
    """Run n_tasks episodes (starting at `offset` within the eval split) for one
    condition, parallelized across max_workers processes via core.runner."""
    skill_text = skill_path.read_text() if skill_path else None
    args = {"env": env, "config": config, "label": label, "skill_text": skill_text, "base_offset": offset, "harness": harness}
    print(f"Condition: {label}" + (f" ({skill_path.name})" if skill_path else " (no skill)"))
    return run_parallel(_run_shard, n_tasks, max_workers, args)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--env", required=True, help="Registered environment name, e.g. 'alfworld'.")
    parser.add_argument("--condition", default=None,
                         help="Run only this one condition ('baseline' or a discovered skill variant label) and exit.")
    parser.add_argument("--shard-index", type=int, default=None,
                         help="With --condition: run only this shard (0-based) of --shard-count total shards.")
    parser.add_argument("--shard-count", type=int, default=None,
                         help="With --condition: total number of shards to split this condition's tasks into.")
    parser.add_argument("--merge", action="store_true",
                         help="Skip running anything; merge whichever condition trajectory files exist into the report.")
    parser.add_argument("--max-workers", type=int, default=None,
                         help="Override config.yaml's max_parallel_workers.")
    parser.add_argument("--harness", default="api", choices=["api", "cli"],
                         help="Backend for action selection: direct API, or an external harness's CLI.")
    args = parser.parse_args()

    config = load_config(args.env)
    max_workers = args.max_workers or config.get("max_parallel_workers", 10)
    total_tasks = config["experiment"]["num_eval_tasks"]
    skill_variants = discover_skill_files(args.env, config)

    if args.condition:
        if bool(args.shard_index is not None) != bool(args.shard_count is not None):
            raise SystemExit("--shard-index and --shard-count must be given together.")
        if args.condition != "baseline" and args.condition not in skill_variants:
            raise SystemExit(f"Unknown condition '{args.condition}'. Available: baseline, {', '.join(skill_variants)}")
        skill_path = None if args.condition == "baseline" else skill_variants[args.condition]

        if args.shard_count:
            offset, n_tasks = shard_bounds(total_tasks, args.shard_index, args.shard_count)
            out_path = shard_path(args.env, config, args.condition, args.shard_index, args.shard_count)
        else:
            offset, n_tasks = 0, total_tasks
            out_path = condition_path(args.env, config, args.condition)

        results = run_condition(args.env, config, args.condition, skill_path, offset, n_tasks, max_workers, args.harness)
        write_jsonl(out_path, results)
        print(f"\nWrote {out_path}")
        return

    if not skill_variants:
        raise SystemExit(f"No trained SKILL.md variants found under experiments/{args.env}/skills/. Run train_skill.py first.")

    model = config["model"]["agent_model"]

    if args.merge:
        baseline_results = read_condition_results(args.env, config, "baseline")
        if baseline_results is None:
            raise SystemExit("No baseline results (or complete shard set) found. Run --condition baseline first.")
        all_results = {"baseline": baseline_results}
        for label in skill_variants:
            results = read_condition_results(args.env, config, label)
            if results is not None:
                all_results[label] = results
            else:
                print(f"Skipping '{label}': no results (or complete shard set) found yet.")
        build_and_write_summary(args.env, config, model, all_results)
        return

    # Default: run every condition in this one process, each fully parallelized.
    print(f"Evaluating on {total_tasks} held-out (valid_unseen) tasks with model {model} "
          f"(up to {max_workers} concurrent workers per condition)")
    print(f"Skill variants: {', '.join(skill_variants)}\n")

    all_results = {}
    baseline_results = run_condition(args.env, config, "baseline", None, 0, total_tasks, max_workers, args.harness)
    write_jsonl(condition_path(args.env, config, "baseline"), baseline_results)
    all_results["baseline"] = baseline_results

    for label, skill_path in skill_variants.items():
        print()
        results = run_condition(args.env, config, label, skill_path, 0, total_tasks, max_workers, args.harness)
        write_jsonl(condition_path(args.env, config, label), results)
        all_results[label] = results

    build_and_write_summary(args.env, config, model, all_results)


if __name__ == "__main__":
    main()
