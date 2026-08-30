"""Generic single-turn environment adapter for any Hugging Face dataset.

Wraps a HF dataset that has a prompt/question column and a reference-answer
column as a single-turn `Environment`: `reset()` surfaces one row's prompt,
the agent answers freely (no discrete admissible_commands -- there is no
fixed action space for a QA/math/classification task), and `step()`
immediately returns done=True with `won` set by comparing the answer to the
row's reference value.

This is the reference pattern for "an environment built from a Hugging Face
dataset" -- point it at any dataset name/config/split + column names via
`experiments/<name>/config.yaml`, no new code needed per dataset:

    environment: hf_dataset
    hf_dataset:
      dataset_name: "..."
      dataset_config: null
      prompt_column: "question"
      answer_column: "answer"
      split_map: {train: "train", valid_seen: "validation", valid_unseen: "test"}

A dataset that needs custom grading (not exact-match) or multi-turn
interaction should implement `core.environment.Environment` directly instead
of using this adapter -- it's intentionally thin, not a general solution.
"""

import datasets

from core.environment import register


class HFDatasetEnvironment:
    def __init__(self, config: dict, split: str, offset: int = 0, count: int | None = None):
        hf_cfg = config["hf_dataset"]
        if split not in hf_cfg["split_map"]:
            raise ValueError(f"Unknown split '{split}', expected one of {list(hf_cfg['split_map'])}")

        ds = datasets.load_dataset(
            hf_cfg["dataset_name"], hf_cfg.get("dataset_config"), split=hf_cfg["split_map"][split],
        )
        end = None if count is None else offset + count
        rows = ds.select(range(offset, end if end is not None else len(ds)))

        prompt_column = hf_cfg["prompt_column"]
        answer_column = hf_cfg["answer_column"]
        self.rows = [
            {"prompt": str(row[prompt_column]), "answer": str(row[answer_column]), "id": f"{split}[{offset + i}]"}
            for i, row in enumerate(rows)
        ]
        self.num_tasks = len(self.rows)
        self._cursor = -1

    def reset(self) -> tuple[str, dict]:
        self._cursor += 1
        row = self.rows[self._cursor]
        info = {
            "admissible_commands": [],  # free-form answer -- no discrete action space
            "won": False,
            "task_id": row["id"],
            "task": row["prompt"],
        }
        return row["prompt"], info

    def step(self, action: str) -> tuple[str, bool, dict]:
        row = self.rows[self._cursor]
        won = action.strip().lower() == row["answer"].strip().lower()
        info = {
            "admissible_commands": [],
            "won": won,
            "task_id": row["id"],
            "task": "",
        }
        return "", True, info  # single-turn: always done after one step

    def close(self) -> None:
        pass


register("hf_dataset", HFDatasetEnvironment)
