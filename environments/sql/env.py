"""Text-to-SQL environment using gretelai/synthetic_text_to_sql.

The standard academic text-to-SQL benchmarks (Spider, BIRD) distribute
their actual per-example SQLite database files as multi-gigabyte external
downloads (Spider's is a Google Drive zip), not through `datasets.
load_dataset` -- not something this repo can reliably fetch. gretelai's
synthetic set trades benchmark-standard status for being fully
self-contained: every row's `sql_context` is a complete CREATE TABLE +
INSERT script, so a fresh, correct SQLite database can be built in memory
for every single task, with no external file dependency at all.

Grading is real SQL execution, not string matching: run the task's
sql_context to build the database, then run both the gold query and the
candidate's query against it and compare result sets. This is the same
"execution accuracy" every real text-to-SQL benchmark uses -- exact row
match, order-insensitive unless the gold query itself specifies ORDER BY
(in which case row order is part of what's being checked, since
comparison is on the raw fetched rows).

Filtered to SELECT-only gold queries (~90% of the dataset): a DELETE or
UPDATE statement's `.fetchall()` is always `[]`, so comparing result sets
for one is meaningless -- any other query that also touches zero rows
would spuriously "match". BIRD-bench's own mini-dev benchmark applies the
same restriction for the same reason.
"""

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import datasets

from core.environment import register

_CODE_FENCE_RE = re.compile(r"```(?:sql)?\s*\n(.*?)\n```", re.DOTALL)
_EXEC_TIMEOUT_S = 10

_RUNNER = """
import json, sqlite3, sys

with open(sys.argv[1]) as f:
    payload = json.load(f)

conn = sqlite3.connect(":memory:")
try:
    conn.executescript(payload["context"])
    gold_rows = conn.execute(payload["gold_sql"]).fetchall()
    candidate_rows = conn.execute(payload["candidate_sql"]).fetchall()
    won = sorted(map(str, gold_rows)) == sorted(map(str, candidate_rows))
except Exception:
    won = False
print("WON" if won else "LOST")
"""


def _extract_sql(action: str) -> str:
    match = _CODE_FENCE_RE.search(action)
    return (match.group(1) if match else action).strip().rstrip(";")


class SQLEnvironment:
    def __init__(self, config: dict, split: str, offset: int = 0, count: int | None = None):
        cfg = config.get("sql", {})
        dataset_name = cfg.get("dataset_name", "gretelai/synthetic_text_to_sql")
        split_map = cfg.get("split_map", {
            "train": {"hf_split": "train", "offset": 0, "count": 600},
            "valid_seen": {"hf_split": "test", "offset": 0, "count": 150},
            "valid_unseen": {"hf_split": "test", "offset": 150},
        })
        if split not in split_map:
            raise ValueError(f"Unknown split '{split}', expected one of {list(split_map)}")

        base = split_map[split]
        hf_split = base["hf_split"]
        base_offset, base_count = base.get("offset", 0), base.get("count")

        ds = datasets.load_dataset(dataset_name, split=hf_split)
        ds = ds.filter(lambda row: row["sql"].strip().upper().startswith("SELECT"))
        lo = base_offset + offset
        hi = lo + count if count is not None else (base_offset + base_count if base_count is not None else len(ds))
        if base_count is not None:
            hi = min(hi, base_offset + base_count)
        hi = min(hi, len(ds))
        rows = ds.select(range(lo, hi))

        self.rows = [
            {
                "id": f"{split}[{lo + i}]",
                "prompt": (
                    f"{row['sql_prompt']}\n\nDatabase schema (SQLite):\n{row['sql_context']}\n\n"
                    "Respond with a single SQL query and nothing else -- no explanation, "
                    "no markdown code fences."
                ),
                "context": row["sql_context"],
                "gold_sql": row["sql"],
            }
            for i, row in enumerate(rows)
        ]
        self.num_tasks = len(self.rows)
        self._cursor = -1

    def reset(self) -> tuple[str, dict]:
        self._cursor += 1
        row = self.rows[self._cursor]
        info = {
            "admissible_commands": [],  # free-form SQL -- no discrete action space
            "won": False,
            "task_id": row["id"],
            "task": row["prompt"],
        }
        return row["prompt"], info

    def step(self, action: str) -> tuple[str, bool, dict]:
        row = self.rows[self._cursor]
        candidate_sql = _extract_sql(action)
        payload = {"context": row["context"], "gold_sql": row["gold_sql"], "candidate_sql": candidate_sql}

        won = False
        script_path = payload_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(_RUNNER)
                script_path = f.name
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(payload, f)
                payload_path = f.name
            result = subprocess.run(
                [sys.executable, script_path, payload_path],
                capture_output=True, text=True, timeout=_EXEC_TIMEOUT_S,
            )
            won = result.stdout.strip() == "WON"
        except subprocess.TimeoutExpired:
            won = False
        finally:
            if script_path:
                Path(script_path).unlink(missing_ok=True)
            if payload_path:
                Path(payload_path).unlink(missing_ok=True)

        info = {"admissible_commands": [], "won": won, "task_id": row["id"], "task": ""}
        return "", True, info  # single-turn: always done after one step

    def close(self) -> None:
        pass


register("sql", SQLEnvironment)
