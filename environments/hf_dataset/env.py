"""Generic single-turn environment adapter for any Hugging Face dataset.

Wraps a HF dataset that has a prompt/question column and a reference-answer
column as a single-turn `Environment`: `reset()` surfaces one row's prompt,
the agent answers freely (no discrete admissible_commands -- there is no
fixed action space for a QA/math/classification task), and `step()`
immediately returns done=True with `won` set by comparing the answer to the
row's reference value(s).

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

`answer_column` may hold either a single string or a list of acceptable
strings per row (e.g. multiple valid phrasings) -- `won` is true if the
agent's answer case-insensitively matches any of them.

A `split_map` entry is normally just the underlying HF split name. For a
dataset that only ships two physical splits (train/validation) but this
framework wants three logical ones (train/valid_seen/valid_unseen), an
entry can instead be a dict carving a disjoint offset range out of one
physical split, so two logical splits never share a row:

    split_map:
      train: "train"
      valid_seen: {hf_split: "validation", offset: 0, count: 8500}
      valid_unseen: {hf_split: "validation", offset: 8500}   # count omitted -> rest of the split

Grading defaults to case-insensitive exact match. Set `answer_match:
"normalized"` for datasets whose reference answers use optional
parenthetical words (e.g. SearchQA's "(Lou) Gehrig", where both "Gehrig"
and "Lou Gehrig" should count correct) -- this strips articles/punctuation
and expands each reference into both the "parenthetical dropped" and
"parenthetical kept, parens removed" reading, then accepts a match against
either. It's still exact matching underneath, just against a wider set of
acceptable strings -- not fuzzy/semantic matching.

A dataset that needs genuinely custom grading (semantic similarity, partial
credit, etc.) or multi-turn interaction should implement
`core.environment.Environment` directly instead of using this adapter --
it's intentionally thin, not a general solution.
"""

import re

import datasets

from core.environment import register

_ARTICLE_RE = re.compile(r"^(the|a|an)\s+")
_PUNCT_RE = re.compile(r"[^\w\s]")
_WHITESPACE_RE = re.compile(r"\s+")
_PAREN_RE = re.compile(r"\(.*?\)")


def _clean(text: str) -> str:
    text = text.lower()
    text = _ARTICLE_RE.sub("", text)
    text = _PUNCT_RE.sub("", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def _normalized_variants(text: str) -> set[str]:
    """Both readings of an optional parenthetical: dropped, and kept-but-unparenthesized."""
    variants = {_clean(_PAREN_RE.sub("", text)), _clean(text.replace("(", "").replace(")", ""))}
    return {v for v in variants if v}


def _resolve_split(hf_cfg: dict, split: str) -> tuple[str, int, int | None]:
    """Returns (hf_split_name, base_offset, base_count) for one logical split."""
    spec = hf_cfg["split_map"][split]
    if isinstance(spec, str):
        return spec, 0, None
    return spec["hf_split"], spec.get("offset", 0), spec.get("count")


class HFDatasetEnvironment:
    def __init__(self, config: dict, split: str, offset: int = 0, count: int | None = None):
        hf_cfg = config["hf_dataset"]
        if split not in hf_cfg["split_map"]:
            raise ValueError(f"Unknown split '{split}', expected one of {list(hf_cfg['split_map'])}")

        self._answer_match = hf_cfg.get("answer_match", "exact")
        hf_split, base_offset, base_count = _resolve_split(hf_cfg, split)
        ds = datasets.load_dataset(hf_cfg["dataset_name"], hf_cfg.get("dataset_config"), split=hf_split)

        lo = base_offset + offset
        hi = lo + count if count is not None else (base_offset + base_count if base_count is not None else len(ds))
        if base_count is not None:
            hi = min(hi, base_offset + base_count)
        hi = min(hi, len(ds))
        rows = ds.select(range(lo, hi))

        prompt_column = hf_cfg["prompt_column"]
        answer_column = hf_cfg["answer_column"]
        self.rows = []
        for i, row in enumerate(rows):
            raw_answer = row[answer_column]
            answers = raw_answer if isinstance(raw_answer, list) else [raw_answer]
            self.rows.append({
                "prompt": str(row[prompt_column]),
                "answers": [str(a) for a in answers],
                "id": f"{split}[{lo + i}]",
            })
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
        if self._answer_match == "normalized":
            model_variants = _normalized_variants(action)
            won = any(model_variants & _normalized_variants(a) for a in row["answers"])
        else:
            answer = action.strip().lower()
            won = any(answer == a.strip().lower() for a in row["answers"])
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
