"""MBPP (Mostly Basic Python Problems) -- a lightweight, programming-related
environment. Real train/validation/test splits ship with the dataset (no
split-carving needed, unlike SearchQA/LiveMathematicianBench).

Unlike every other environment here, grading requires actually *running*
model-generated code: the agent's response is combined with the task's
test-setup code and its assert-statement test list, written to a temp file,
and executed in a subprocess with a timeout. This is the same basic approach
real MBPP/HumanEval harnesses use -- process isolation + a timeout, not a
sandboxed container. Fine for a local research repo running its own
API-driven model's output; do not point this at untrusted input.
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
    """Pull code out of a ```python ...``` fence if present, else use the
    response as-is (models are asked to respond with bare code, but often
    wrap it in a fence anyway)."""
    match = _CODE_FENCE_RE.search(action)
    return match.group(1).strip() if match else action.strip()


class MBPPEnvironment:
    def __init__(self, config: dict, split: str, offset: int = 0, count: int | None = None):
        cfg = config.get("mbpp", {})
        dataset_name = cfg.get("dataset_name", "google-research-datasets/mbpp")
        split_map = cfg.get("split_map", {"train": "train", "valid_seen": "validation", "valid_unseen": "test"})
        if split not in split_map:
            raise ValueError(f"Unknown split '{split}', expected one of {list(split_map)}")

        ds = datasets.load_dataset(dataset_name, split=split_map[split])
        end = None if count is None else offset + count
        rows = ds.select(range(offset, min(end, len(ds)) if end is not None else len(ds)))

        self.rows = [
            {
                "id": f"{split}[{offset + i}]",
                "prompt": (
                    f"{row['text']}\n\nYour code must satisfy these tests:\n"
                    + "\n".join(row["test_list"])
                ),
                "test_setup_code": row["test_setup_code"] or "",
                "test_list": row["test_list"],
            }
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
        program = "\n".join([row["test_setup_code"], code, *row["test_list"]])

        won = False
        # Run in a throwaway cwd, not this repo's working directory -- some
        # MBPP problems involve file I/O, and a candidate solution shouldn't
        # be able to leave fixtures sitting in the repo root (confirmed as a
        # real issue for BigCodeBench's tasks; MBPP's are simpler but the
        # same risk exists in principle).
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir) / "candidate.py"
                tmp_path.write_text(program)
                result = subprocess.run(
                    [sys.executable, str(tmp_path)], capture_output=True, text=True,
                    timeout=_EXEC_TIMEOUT_S, cwd=tmp_dir,
                )
                won = result.returncode == 0
        except subprocess.TimeoutExpired:
            won = False

        info = {
            "admissible_commands": [],
            "won": won,
            "task_id": row["id"],
            "task": "",
        }
        return "", True, info  # single-turn: always done after one step

    def close(self) -> None:
        pass


register("mbpp", MBPPEnvironment)
