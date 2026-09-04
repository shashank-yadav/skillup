"""Humanized-writing environment using Hello-SimpleAI/HC3.

No exact-match ground truth exists for "does this sound human," so
grading is LLM-judge based, the same mechanism environments/writing/env.py
uses. HC3 gives the judge a specifically useful pair: for the same
question, real Reddit/forum human answers alongside real ChatGPT answers
to that exact question -- a genuine human/AI contrast pair, not just a
higher/lower quality pair. The judge is asked directly whether the
candidate reads like the human reference or falls into the AI reference's
patterns (em dashes, hedging, listicle structure, "furthermore"/"in
conclusion" scaffolding, and the like), not just whether it's well-written.

HC3 only loads through the HF auto-converted parquet branch --
Hello-SimpleAI/HC3 itself ships a legacy loading script current
`datasets` versions reject outright ("Dataset scripts are no longer
supported"). `human_answers`/`chatgpt_answers` are lists (a question can
have multiple answers of each); this takes the first of each, matching
how environments/writing/env.py takes a single chosen/rejected pair per
row rather than the full set.
"""

from pathlib import Path

import datasets

from core.environment import register
from core.llm import ModelClient
from core.skill import extract_json

PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "judge_humanized_writing_response.md"
_HF_REVISION = "refs/convert/parquet"  # HC3's own repo has no loadable default revision


class HumanizedWritingEnvironment:
    def __init__(self, config: dict, split: str, offset: int = 0, count: int | None = None):
        cfg = config.get("humanized_writing", {})
        dataset_name = cfg.get("dataset_name", "Hello-SimpleAI/HC3")
        hf_split = cfg.get("hf_split", "train")
        split_ranges = cfg.get("split_ranges", {
            "train": {"offset": 0, "count": 700},
            "valid_seen": {"offset": 700, "count": 200},
            "valid_unseen": {"offset": 900, "count": 300},
        })
        if split not in split_ranges:
            raise ValueError(f"Unknown split '{split}', expected one of {list(split_ranges)}")

        ds = datasets.load_dataset(dataset_name, split=hf_split, revision=_HF_REVISION)
        ds = ds.filter(lambda row: row["human_answers"] and row["chatgpt_answers"])

        base = split_ranges[split]
        base_offset, base_count = base.get("offset", 0), base.get("count")
        lo = base_offset + offset
        hi = lo + count if count is not None else (base_offset + base_count if base_count is not None else len(ds))
        if base_count is not None:
            hi = min(hi, base_offset + base_count)
        hi = min(hi, len(ds))
        rows = ds.select(range(lo, hi))

        self.rows = [
            {
                "id": f"{split}[{lo + i}]",
                "prompt": row["question"],
                "human": row["human_answers"][0],
                "ai": row["chatgpt_answers"][0],
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
            question=row["prompt"], human_answer=row["human"], ai_answer=row["ai"], action=action,
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


register("humanized_writing", HumanizedWritingEnvironment)
