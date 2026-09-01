"""Writing-quality environment using m-a-p/Writing-Preference-Bench.

No exact-match or executable ground truth exists for writing quality, so
grading is LLM-judge based -- the same mechanism
environments/conversation_judge/env.py uses. This dataset gives the judge
a stronger reference than a single historical outcome, though: every
prompt ships both a `chosen` (higher-quality, expert-annotated) and a
`rejected` (lower-quality) response, so the judge compares the new
response against a concrete example of what "good" looks like AND a
concrete example of what to avoid, not just one prior verdict.

The dataset is ~1800 rows, roughly half Chinese and half English prompts
across many genres (role-play, travel writing, thank-you/apology letters,
book/movie reviews, fairy tales, tutorials, academic abstracts, debate
scripts, ad copy, eulogies, poetry, ...). Filtered to the English-ish
subset here (~1200 rows) since the rest of this framework -- agent
prompts, judge prompts, the README -- is English-only; the Chinese half
is left on the table rather than silently mixed in.
"""

from pathlib import Path

import datasets

from core.environment import register
from core.llm import ModelClient
from core.skill import extract_json

PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "judge_writing_response.md"
_ASCII_RATIO_THRESHOLD = 0.85


def _is_english_ish(text: str) -> bool:
    if not text:
        return False
    return sum(1 for c in text if ord(c) < 128) / len(text) > _ASCII_RATIO_THRESHOLD


class WritingEnvironment:
    def __init__(self, config: dict, split: str, offset: int = 0, count: int | None = None):
        cfg = config.get("writing", {})
        dataset_name = cfg.get("dataset_name", "m-a-p/Writing-Preference-Bench")
        hf_split = cfg.get("hf_split", "train")
        split_ranges = cfg.get("split_ranges", {
            "train": {"offset": 0, "count": 700},
            "valid_seen": {"offset": 700, "count": 200},
            "valid_unseen": {"offset": 900},
        })
        if split not in split_ranges:
            raise ValueError(f"Unknown split '{split}', expected one of {list(split_ranges)}")

        ds = datasets.load_dataset(dataset_name, split=hf_split)
        english_rows = ds.filter(lambda row: _is_english_ish(row["prompt"]))

        base = split_ranges[split]
        base_offset, base_count = base.get("offset", 0), base.get("count")
        lo = base_offset + offset
        hi = lo + count if count is not None else (base_offset + base_count if base_count is not None else len(english_rows))
        if base_count is not None:
            hi = min(hi, base_offset + base_count)
        hi = min(hi, len(english_rows))
        rows = english_rows.select(range(lo, hi))

        self.rows = [
            {
                "id": f"{split}[{lo + i}]",
                "prompt": row["prompt"],
                "chosen": row["chosen"]["response"],
                "rejected": row["rejected"]["response"],
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
            writing_prompt=row["prompt"], chosen=row["chosen"], rejected=row["rejected"], action=action,
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


register("writing", WritingEnvironment)
