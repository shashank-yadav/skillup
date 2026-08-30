"""Parallel episode runner.

Uses process-based parallelism, not threads: ALFWorld's PDDL backend (the
`tatsu` grammar parser it uses to load and step through game files) keeps
shared, non-reentrant parser state, and was found -- via an actual
concurrency stress test, not a theoretical concern -- to corrupt and crash
when multiple threads touch it concurrently, even with the game-loading
step alone serialized behind a lock. Separate OS processes avoid this
entirely since they share no memory.

The LLM API call is still the actual bottleneck and is I/O-bound, so this
still gives real wall-clock speedup -- just via `ProcessPoolExecutor`
instead of threads. This replaces this project's original approach of
hand-launching N separate `python evaluate_skill.py --shard-index ...`
background commands: the same process-per-shard isolation, orchestrated by
one function call instead of by hand.
"""

from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def shard_bounds(n_tasks: int, shard_index: int, shard_count: int) -> tuple[int, int]:
    """Deterministic, disjoint, order-preserving split of [0, n_tasks) into
    shard_count contiguous ranges (as equal as an integer split allows)."""
    base, remainder = divmod(n_tasks, shard_count)
    start = shard_index * base + min(shard_index, remainder)
    size = base + (1 if shard_index < remainder else 0)
    return start, size


def run_parallel(
    worker: Callable[[int, int, Any], list[T]],
    n_tasks: int,
    max_workers: int,
    worker_args: Any,
) -> list[T]:
    """Split [0, n_tasks) into up to `max_workers` contiguous shards and run
    `worker(offset, size, worker_args)` for each in its own process,
    concurrently. `worker` must be a module-level function and `worker_args`
    must be picklable (plain dicts/lists/strings/numbers) -- both cross a
    process boundary. Returns results in task order (shard 0's first, etc)."""
    max_workers = max(1, min(max_workers, n_tasks))
    shards = [shard_bounds(n_tasks, i, max_workers) for i in range(max_workers)]

    results: list[list[T] | None] = [None] * max_workers
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(worker, offset, size, worker_args): i for i, (offset, size) in enumerate(shards)}
        for future in as_completed(futures):
            i = futures[future]
            results[i] = future.result()

    return [item for chunk in results for item in chunk]
