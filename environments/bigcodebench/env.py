"""BigCodeBench -- harder, more realistic Python programming tasks than
MBPP: diverse standard-library and third-party function calls, more
complex instructions, unittest-based test suites instead of bare asserts.
Only one physical split ships ("v0.1.4"), carved into train/valid_seen/
valid_unseen the same way environments/livemathbench/env.py does for
LiveMathematicianBench.

Grading is the same subprocess-execution approach as
environments/mbpp/env.py: candidate code + the task's unittest.TestCase
class + a `unittest.main()` call, run in a subprocess with a timeout,
exit code 0 means every test passed.
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

import datasets

from core.environment import register

_CODE_FENCE_RE = re.compile(r"```(?:python|py)?\s*\n(.*?)\n```", re.DOTALL)
_EXEC_TIMEOUT_S = 10


def _extract_code(action: str) -> str:
    match = _CODE_FENCE_RE.search(action)
    return match.group(1).strip() if match else action.strip()


class BigCodeBenchEnvironment:
    def __init__(self, config: dict, split: str, offset: int = 0, count: int | None = None):
        cfg = config.get("bigcodebench", {})
        dataset_name = cfg.get("dataset_name", "bigcode/bigcodebench")
        hf_split = cfg.get("hf_split", "v0.1.4")
        split_ranges = cfg.get("split_ranges", {
            "train": {"offset": 0, "count": 600},
            "valid_seen": {"offset": 600, "count": 150},
            "valid_unseen": {"offset": 750},
        })
        if split not in split_ranges:
            raise ValueError(f"Unknown split '{split}', expected one of {list(split_ranges)}")

        ds = datasets.load_dataset(dataset_name, split=hf_split)
        base = split_ranges[split]
        base_offset, base_count = base.get("offset", 0), base.get("count")
        lo = base_offset + offset
        hi = lo + count if count is not None else (base_offset + base_count if base_count is not None else len(ds))
        if base_count is not None:
            hi = min(hi, base_offset + base_count)
        hi = min(hi, len(ds))
        rows = ds.select(range(lo, hi))

        self.rows = [
            {"id": f"{split}[{lo + i}]", "prompt": row["instruct_prompt"], "test": row["test"]}
            for i, row in enumerate(rows)
        ]
        self.num_tasks = len(self.rows)
        self._cursor = -1

    def reset(self) -> tuple[str, dict]:
        self._cursor += 1
        row = self.rows[self._cursor]
        info = {
            "admissible_commands": [],  # free-form code -- no discrete action space
            "won": False,
            "task_id": row["id"],
            "task": row["prompt"],
        }
        return row["prompt"], info

    def step(self, action: str) -> tuple[str, bool, dict]:
        row = self.rows[self._cursor]
        code = _extract_code(action)
        program = "\n".join([code, row["test"], "unittest.main()"])

        won = False
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(program)
                tmp_path = f.name
            result = subprocess.run(
                [sys.executable, tmp_path], capture_output=True, text=True, timeout=_EXEC_TIMEOUT_S,
            )
            won = result.returncode == 0
        except subprocess.TimeoutExpired:
            won = False
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        info = {"admissible_commands": [], "won": won, "task_id": row["id"], "task": ""}
        return "", True, info  # single-turn: always done after one step

    def close(self) -> None:
        pass


register("bigcodebench", BigCodeBenchEnvironment)
