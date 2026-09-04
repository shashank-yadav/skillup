"""Code-review environment using fasterinnerlooper/codereviewer -- a
re-host of Microsoft's real CodeReviewer corpus: actual GitHub PR diffs
paired with the actual human reviewer's comment on that diff.

No exact-match ground truth exists for "is this a good review comment,"
so grading is LLM-judge based, the same mechanism environments/writing/
env.py uses -- but with a narrower question than generic writing quality:
does the candidate's review raise the same substantive concern the real
reviewer raised on this exact diff, not just "is it well-written."

Loading this dataset is unusually fragile. `datasets.load_dataset(...,
streaming=True)` (this file's original approach) avoided an indefinite
hang the plain non-streaming `.select()` loader hit on this dataset, but
every environment/trainer episode reconstructs its own Environment in a
fresh worker process (core/trainer.py's `_rollout_worker`) -- so under
`train_skill.py`'s parallel dev-eval rollouts, up to
`max_parallel_workers` processes independently called `load_dataset`
against this *uncached* dataset at once. Confirmed (via `train_skill.py
--env code_review --strategy all`'s `gated` round) that this races on the
`datasets` library's on-disk cache bookkeeping and crashes with
`FileNotFoundError: .../<hash>.incomplete/dataset_info.json` -- concurrent
processes each trying to finalize the same cache directory. Switching to
this dataset's `refs/convert/parquet` mirror doesn't help: the
`train_generation` config isn't preserved there (only a `default` config
that pulls every config's shards, ~1.2GB, to get one), so instead this
downloads just the one parquet shard needed directly (bypassing
`datasets.load_dataset` and its config/cache resolution entirely), to a
local file with an atomic download-then-rename -- safe even if several
worker processes hit it before the first download finishes, since only
one process's `os.replace` wins and the rest just see the file already
there.
"""

import os
import tempfile
import urllib.request
from pathlib import Path

import pyarrow.parquet as pq

from core.environment import register
from core.llm import ModelClient
from core.skill import extract_json

PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "judge_code_review_response.md"
_CACHE_DIR = Path(__file__).parent / ".cache"
_PARQUET_URL = (
    "https://huggingface.co/datasets/fasterinnerlooper/codereviewer/resolve/"
    "refs%2Fconvert%2Fparquet/train_generation/train/0000.parquet"
)


def _ensure_parquet_shard(url: str, dest: Path) -> Path:
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dest.parent, suffix=".part")
    os.close(fd)
    try:
        urllib.request.urlretrieve(url, tmp_path)
        os.replace(tmp_path, dest)  # atomic -- safe if another process wins the race
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    return dest


class CodeReviewEnvironment:
    def __init__(self, config: dict, split: str, offset: int = 0, count: int | None = None):
        cfg = config.get("code_review", {})
        buffer_size = cfg.get("buffer_size", 2000)  # how many rows to pull from the parquet shard, at init
        split_ranges = cfg.get("split_ranges", {
            "train": {"offset": 0, "count": 700},
            "valid_seen": {"offset": 700, "count": 200},
            "valid_unseen": {"offset": 900, "count": 300},
        })
        if split not in split_ranges:
            raise ValueError(f"Unknown split '{split}', expected one of {list(split_ranges)}")

        shard_path = _ensure_parquet_shard(_PARQUET_URL, _CACHE_DIR / "train_generation_0000.parquet")
        table = pq.read_table(shard_path, columns=["patch", "msg"])
        buffered = []
        for patch, msg in zip(table.column("patch"), table.column("msg")):
            patch, msg = patch.as_py(), msg.as_py()
            if patch and msg:
                buffered.append({"patch": patch, "msg": msg})
            if len(buffered) >= buffer_size:
                break

        base = split_ranges[split]
        base_offset, base_count = base.get("offset", 0), base.get("count")
        lo = base_offset + offset
        hi = lo + count if count is not None else (base_offset + base_count if base_count is not None else len(buffered))
        if base_count is not None:
            hi = min(hi, base_offset + base_count)
        hi = min(hi, len(buffered))
        rows = buffered[lo:hi]

        self.rows = [
            {
                "id": f"{split}[{lo + i}]",
                "prompt": (
                    f"Review this code change and write a single review comment "
                    f"pointing out the most important issue, if any:\n\n```diff\n{row['patch']}\n```"
                ),
                "reference_review": row["msg"],
            }
            for i, row in enumerate(rows)
        ]
        self.num_tasks = len(self.rows)
        self._cursor = -1
        self._client = ModelClient(config)
        self._judge_model = config["model"]["trainer_model"] or config["model"]["agent_model"]
        self._judge_temperature = config["model"]["trainer_temperature"]
        self._judge_max_tokens = 500

    def reset(self) -> tuple[str, dict]:
        self._cursor += 1
        row = self.rows[self._cursor]
        info = {
            "admissible_commands": [],  # free-form response -- no discrete action space
            "won": False,
            "task_id": row["id"],
            "task": row["prompt"],
        }
        return row["prompt"], info

    def step(self, action: str) -> tuple[str, bool, dict]:
        row = self.rows[self._cursor]
        prompt = PROMPT_PATH.read_text().format(
            diff=row["prompt"], reference_review=row["reference_review"], action=action,
        )
        raw_text, _usage = self._client.chat(
            model=self._judge_model, messages=[{"role": "user", "content": prompt}],
            temperature=self._judge_temperature, max_tokens=self._judge_max_tokens,
        )
        data = extract_json(raw_text)
        won = bool(data.get("won")) if data else False

        info = {"admissible_commands": [], "won": won, "task_id": row["id"], "task": ""}
        return "", True, info  # single-turn: always done after one step

    def close(self) -> None:
        pass


register("code_review", CodeReviewEnvironment)
