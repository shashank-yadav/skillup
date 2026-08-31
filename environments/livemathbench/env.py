"""LiveMathematicianBench -- one of the six benchmarks SkillOpt (Microsoft)
evaluated on: multiple-choice questions about theorems/proofs from recent
arXiv math papers (graduate/research-level, deliberately hard to memorize
since it's continuously updated with new papers).

This is a real `Environment` plugin rather than the generic hf_dataset
adapter, because the task needs genuine assembly (question + all answer
choices rendered as a lettered list) and letter-only grading -- the exact
case the adapter's docstring says should get a dedicated implementation
instead of being forced through a prompt_column/answer_column config.

The HF dataset ships a single physical "train" split (608 rows: a
`question`, one `correct_choice` dict, and 4 `choices` dicts, each
{"label", "text"}). This framework wants three logical splits
(train/valid_seen/valid_unseen), so `livemathbench.split_ranges` in
config.yaml carves disjoint offset ranges out of that one physical split --
same idea as hf_dataset's dict-form split_map, just local to this plugin
since there's no separate adapter config schema to reuse here.
"""

import datasets

from core.environment import register


class LiveMathBenchEnvironment:
    def __init__(self, config: dict, split: str, offset: int = 0, count: int | None = None):
        cfg = config["livemathbench"]
        if split not in cfg["split_ranges"]:
            raise ValueError(f"Unknown split '{split}', expected one of {list(cfg['split_ranges'])}")
        base = cfg["split_ranges"][split]
        base_offset, base_count = base.get("offset", 0), base.get("count")

        ds = datasets.load_dataset(cfg["dataset_name"], split="train")

        lo = base_offset + offset
        hi = lo + count if count is not None else (base_offset + base_count if base_count is not None else len(ds))
        if base_count is not None:
            hi = min(hi, base_offset + base_count)
        hi = min(hi, len(ds))
        rows = ds.select(range(lo, hi))

        self.rows = []
        for i, row in enumerate(rows):
            mcq = row["mcq"]
            choices = sorted([mcq["correct_choice"], *mcq["choices"]], key=lambda c: c["label"])
            options_text = "\n".join(f"{c['label']}. {c['text']}" for c in choices)
            prompt = f"{mcq['question']}\n\nOptions:\n{options_text}"
            self.rows.append({
                "prompt": prompt,
                "answer": mcq["correct_choice"]["label"],
                "id": f"{split}[{lo + i}]",
            })
        self.num_tasks = len(self.rows)
        self._cursor = -1

    def reset(self) -> tuple[str, dict]:
        self._cursor += 1
        row = self.rows[self._cursor]
        info = {
            "admissible_commands": [],  # free-form answer -- reply with the choice letter
            "won": False,
            "task_id": row["id"],
            "task": row["prompt"],
        }
        return row["prompt"], info

    def step(self, action: str) -> tuple[str, bool, dict]:
        row = self.rows[self._cursor]
        answer = action.strip().upper()
        # Accept a bare letter or "A." / "A)" / "Answer: A" style responses -- take
        # the first standalone A-E token rather than requiring an exact match, since
        # a free-text agent will often wrap the letter in a sentence.
        won = any(tok.strip(".):") == row["answer"] for tok in answer.split()) or answer == row["answer"]
        info = {
            "admissible_commands": [],
            "won": won,
            "task_id": row["id"],
            "task": "",
        }
        return "", True, info  # single-turn: always done after one step

    def close(self) -> None:
        pass


register("livemathbench", LiveMathBenchEnvironment)
