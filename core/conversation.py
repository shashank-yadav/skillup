"""Shared helpers for turning a raw conversation transcript into text an LLM
prompt can use. Used by both distill_conversation.py (single conversation,
in-place insight extraction) and convert_conversation.py (a corpus of
conversations, segmented into trainable episodes)."""

import json


def format_transcript(raw: str) -> str:
    """JSON list of {"role", "content"} turns if parseable, else the raw text
    as-is -- so a transcript can come from any harness's own conversation
    log, or just be pasted plain text."""
    try:
        turns = json.loads(raw)
    except json.JSONDecodeError:
        return raw.strip()
    if not isinstance(turns, list):
        return raw.strip()
    lines = []
    for turn in turns:
        if not isinstance(turn, dict):
            continue
        role = turn.get("role", "unknown")
        content = turn.get("content", "")
        lines.append(f"[{role}] {content}")
    return "\n\n".join(lines) if lines else raw.strip()
