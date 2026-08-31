"""Version history for deployed skills (SKILL.md files under a target skills
directory, e.g. ~/.claude/skills/<name>/).

Every write made through `save_version` appends a full-text snapshot to
`<skill_dir>/.skillup/history.jsonl` before touching SKILL.md, so
`skill_manager.py` can list, diff, and roll back changes without depending
on the target directory being a git repo -- ~/.claude/skills usually isn't
one. This is separate from `core/skill.py`'s bare `save()`, which trainers
still use for their own experiment-scoped files (experiments/<env>/skills/*.md)
-- those are intermediate training artifacts, not deployed skills, and don't
need a history.
"""

import json
import time
from pathlib import Path

from core import skill

HISTORY_DIR = ".skillup"
HISTORY_FILE = "history.jsonl"


def _history_path(skill_dir: Path) -> Path:
    return Path(skill_dir) / HISTORY_DIR / HISTORY_FILE


def list_versions(skill_dir: Path) -> list[dict]:
    """Oldest first. Empty if this skill has never been written through
    `save_version` (e.g. it predates this module, or was hand-edited)."""
    path = _history_path(skill_dir)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def get_version(skill_dir: Path, version: int) -> dict:
    for v in list_versions(skill_dir):
        if v["version"] == version:
            return v
    raise ValueError(f"No version {version} for skill at {skill_dir}")


def _append(skill_dir: Path, text: str, source: str, note: str) -> dict:
    versions = list_versions(skill_dir)
    record = {
        "version": versions[-1]["version"] + 1 if versions else 1,
        "timestamp": time.time(),
        "source": source,
        "note": note,
        "text": text,
    }
    path = _history_path(skill_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")
    return record


def save_version(skill_dir: Path, new_text: str, source: str, note: str = "") -> tuple[int, bool]:
    """Writes `new_text` to <skill_dir>/SKILL.md and records it as a new
    version, unless it's identical to the current version (a no-op write,
    e.g. reinstalling an unchanged trained skill). Returns (version, created).

    If SKILL.md already exists on disk but has no history yet, its current
    content is seeded as v1 ("adopted") before the new write is recorded, so
    pre-existing skills gain history retroactively instead of losing their
    prior content the first time this is called.
    """
    skill_dir = Path(skill_dir)
    existing_path = skill_dir / "SKILL.md"
    versions = list_versions(skill_dir)
    if not versions and existing_path.exists():
        _append(skill_dir, existing_path.read_text(), source="adopted", note="pre-existing file, seeded as v1")
        versions = list_versions(skill_dir)

    if versions and versions[-1]["text"].strip() == new_text.strip():
        return versions[-1]["version"], False

    record = _append(skill_dir, new_text, source=source, note=note)
    skill.save(existing_path, new_text)
    return record["version"], True
