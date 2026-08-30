"""Skill file representation and helpers.

A skill is markdown text with a YAML frontmatter (name/description) -- nothing
here parses that frontmatter structurally since no trainer needs to inspect it,
but this is the natural home for it if a future one does.

Several trainers (gated, expel, avo) represent the skill as a fixed preamble
plus a flat "## Insights" bullet list they edit via small structured deltas
rather than full-document rewrites. Full-document rewrites were found this
session to be fragile with cheap models -- either repetition collapse, or the
model copying the prompt's own trajectory dump back into the "rewritten" file
instead of writing a real edit. A bounded structured delta sidesteps both,
since merging into the insight list happens here in Python, not in the model.
These helpers are reusable by any trainer plugin that wants that representation.
"""

import difflib
import json
import re
from pathlib import Path

INSIGHTS_HEADING = "## Insights"
MAX_INSIGHTS = 12
SIMILARITY_THRESHOLD = 0.75


def load(path: str | Path) -> str:
    return Path(path).read_text()


def save(path: str | Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n")


def strip_code_fence(text: str) -> str:
    text = text.strip()
    match = re.match(r"^```(?:markdown|md)?\s*\n(.*)\n```$", text, re.DOTALL)
    return match.group(1).strip() if match else text


def parse_insights(text: str) -> tuple[str, list[str]]:
    """Split a skill doc into its fixed preamble and its flat insight-bullet list."""
    if INSIGHTS_HEADING in text:
        preamble, _, rest = text.partition(INSIGHTS_HEADING)
        insights = [line[2:].strip() for line in rest.splitlines() if line.strip().startswith("- ")]
        return preamble.rstrip(), insights
    return text.rstrip(), []


def render_insights(preamble: str, insights: list[str]) -> str:
    bullets = "\n".join(f"- {insight}" for insight in insights) if insights else "(none yet)"
    return f"{preamble}\n\n{INSIGHTS_HEADING}\n\n{bullets}\n"


def format_insight_list(insights: list[str]) -> str:
    return "\n".join(f"{i}. {insight}" for i, insight in enumerate(insights, 1)) if insights else "(none yet)"


def is_near_duplicate(candidate: str, existing: list[str]) -> bool:
    candidate_norm = candidate.strip().lower()
    return any(
        difflib.SequenceMatcher(None, candidate_norm, e.strip().lower()).ratio() > SIMILARITY_THRESHOLD
        for e in existing
    )


def crossover(insights_a: list[str], insights_b: list[str]) -> list[str]:
    merged = list(insights_a)
    for text in insights_b:
        if not is_near_duplicate(text, merged) and len(merged) < MAX_INSIGHTS:
            merged.append(text)
    return merged


def extract_insight_delta(raw_text: str) -> dict:
    """Pull {"add": [...], "remove": [...]} out of a model response, tolerating a
    stray code fence or surrounding prose despite the prompt asking for bare JSON."""
    text = strip_code_fence(raw_text).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {"add": [], "remove": []}
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"add": [], "remove": []}
    return {
        "add": [str(x) for x in data.get("add", []) if isinstance(x, str) and x.strip()],
        "remove": [str(x) for x in data.get("remove", []) if isinstance(x, str) and x.strip()],
    }


def apply_delta(insights: list[str], delta: dict) -> tuple[list[str], list[str]]:
    """Returns (new_insights, actually_added) -- near-duplicates and over-cap
    additions are silently dropped, so `actually_added` may be a subset of
    delta['add']."""
    insights = [i for i in insights if i.strip() not in {r.strip() for r in delta["remove"]}]
    added = []
    for text in delta["add"]:
        text = text.strip()
        if not text or is_near_duplicate(text, insights) or len(insights) >= MAX_INSIGHTS:
            continue
        insights.append(text)
        added.append(text)
    return insights, added
