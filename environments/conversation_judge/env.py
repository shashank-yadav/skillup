"""LLM-as-judge environment for training on a corpus of past conversations.

Unlike every other environment here, this one doesn't have a re-runnable
world to step through -- a past conversation is a fixed, historical
artifact, not something you can roll out fresh under a candidate skill.
What it CAN do is ask: "given this candidate skill, and the same situation
that came up before, does the agent's new response avoid the mistake that
was actually made last time (or keep matching what actually worked)?" --
a judged proxy for re-running history, not a real re-run.

This is deliberately built as a normal `Environment` plugin (not a special
code path) so it plugs into the *existing* pipeline unchanged: `reset()`
serves one held-out episode's situation as a free-form prompt, the agent
(under `core.agent.run_episode`, informed by whatever candidate skill is
under test) writes a fresh response, and `step()` calls an LLM judge instead
of executing/matching. That means `gated`'s validation gate, `core.trainer.
dev_eval`, and `core.runner`'s parallel rollout all Just Work against a
conversation corpus with no code changes -- only this plugin plus
`convert_conversation.py` (which builds the corpus) are new.

Expects episodes already segmented by convert_conversation.py:
{"task_id", "task" (the situation), "success" (bool, how it actually went),
"outcome_note" (why)} -- see prompts/segment_conversation.md for the exact
shape produced.
"""

import json
from pathlib import Path

from core.environment import register
from core.llm import ModelClient
from core.skill import extract_json

PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "judge_conversation_response.md"

_SUCCESS_INSTRUCTION = (
    "Does the new response follow the same effective approach described above (or an "
    "equally good alternative)? Answer true if it's consistent with what worked, false "
    "if it deviates into a worse approach."
)
_FAILURE_INSTRUCTION = (
    "Does the new response avoid the mistake described above? Answer true if it avoids "
    "that mistake (even if imperfect in other ways), false if it repeats the same "
    "mistake or a clear variant of it."
)


class ConversationJudgeEnvironment:
    def __init__(self, config: dict, split: str, offset: int = 0, count: int | None = None):
        cfg = config["conversation_judge"]
        split_map = cfg["split_map"]
        if split not in split_map:
            raise ValueError(f"Unknown split '{split}', expected one of {list(split_map)}")

        episodes_path = Path(cfg["episodes_path"])
        all_episodes = json.loads(episodes_path.read_text())
        base = split_map[split]
        base_offset, base_count = base.get("offset", 0), base.get("count")
        lo = base_offset + offset
        hi = lo + count if count is not None else (base_offset + base_count if base_count is not None else len(all_episodes))
        if base_count is not None:
            hi = min(hi, base_offset + base_count)
        hi = min(hi, len(all_episodes))

        self.rows = [
            {"id": f"{split}[{lo + i}]", **ep}
            for i, ep in enumerate(all_episodes[lo:hi])
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
            "task": row["task"],
        }
        return row["task"], info

    def step(self, action: str) -> tuple[str, bool, dict]:
        row = self.rows[self._cursor]
        prompt = PROMPT_PATH.read_text().format(
            situation=row["task"],
            outcome_label="WHAT WORKED" if row["success"] else "MISTAKE MADE (and how it was corrected)",
            outcome_note=row["outcome_note"],
            action=action,
            judge_instruction=_SUCCESS_INSTRUCTION if row["success"] else _FAILURE_INSTRUCTION,
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


register("conversation_judge", ConversationJudgeEnvironment)
