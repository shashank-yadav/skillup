"""Frontend development -- React component implementation graded by real
Jest tests, adapted from onekq-ai/WebApp1K-React (paired success/failure
test cases for real-world UI scenarios: blogging, e-commerce, fitness
tracking, ...).

Unlike WebApp1K's own eval harness (which runs its full 1000-scenario suite
sequentially against one shared staging directory via run_eval.py /
prepare_staging.py), this framework runs many episodes concurrently, so
each episode gets its own temp directory instead: node_modules is
symlinked in from a one-time `npm install` at environments/frontend/
js_project/ rather than reinstalled per episode, which would be far too
slow, while babel.config.js/jest.config.js are copied in and the test file
+ candidate code are written fresh each time.

WebApp1K's HF dataset (Category, Scenario, Success Case, Failure Case,
Github URL) doesn't include the original test file's header imports or the
component's import identifier -- and that identifier isn't even consistent
across the original suite (`CMS`, `YourComponent`, `ProductPage`, ...
confirmed by sampling several real test files). Rather than guess it, every
task here uses one fixed convention instead: the candidate always exports a
default component from `Solution.js`, imported in the test as `Component`.
This is a deliberate adaptation, not a byte-for-byte reproduction of
WebApp1K's own harness.

Requires Node.js/npm and a one-time `npm install` in js_project/ (see
install.sh --with-frontend). Not needed for any other environment.
"""

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import datasets

from core.environment import register

_CODE_FENCE_RE = re.compile(r"```(?:jsx?|javascript)?\s*\n(.*?)\n```", re.DOTALL)
_EXEC_TIMEOUT_S = 30

_JSX_TAG_RE = re.compile(r"<([A-Z][A-Za-z0-9]*)\b")
_KNOWN_WRAPPERS = {"MemoryRouter"}

_JS_PROJECT_DIR = Path(__file__).parent / "js_project"

_TEST_HEADER = """\
import React from 'react';
import { render, screen, act, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import fetchMock from 'fetch-mock';
import '@testing-library/jest-dom';
import Component from './Solution';

afterEach(() => {
  fetchMock.reset();
  fetchMock.restore();
});

"""


def _extract_code(action: str) -> str:
    """Pull code out of a ```jsx ...``` fence if present, else use the
    response as-is (models are asked to respond with bare code, but often
    wrap it in a fence anyway)."""
    match = _CODE_FENCE_RE.search(action)
    return match.group(1).strip() if match else action.strip()


def _normalize_component_identifier(test_body: str) -> str:
    """The dataset's Success/Failure Case text isn't identifier-agnostic --
    it references the original suite's per-scenario component name directly
    in JSX (`<CMS />`, `<YourComponent />`, `<ProductPage />`, ...), which
    isn't given anywhere in the HF row itself. Detect it (any capitalized
    JSX tag other than MemoryRouter) and rewrite every occurrence to
    `Component`, matching the fixed import in `_TEST_HEADER`. A handful of
    rows (~1 in 500, sampled) reference two different original identifiers;
    collapsing both to `Component` avoids a dangling undefined reference
    rather than trying to guess which one is "correct"."""
    identifiers = {m for m in _JSX_TAG_RE.findall(test_body) if m not in _KNOWN_WRAPPERS}
    for ident in identifiers:
        test_body = re.sub(rf"\b{re.escape(ident)}\b", "Component", test_body)
    return test_body


class FrontendEnvironment:
    def __init__(self, config: dict, split: str, offset: int = 0, count: int | None = None):
        cfg = config.get("frontend", {})
        dataset_name = cfg.get("dataset_name", "onekq-ai/WebApp1K-React")
        split_ranges = cfg.get("split_ranges", {
            "train": {"offset": 0, "count": 700},
            "valid_seen": {"offset": 700, "count": 150},
            "valid_unseen": {"offset": 850},
        })
        if split not in split_ranges:
            raise ValueError(f"Unknown split '{split}', expected one of {list(split_ranges)}")

        ds = datasets.load_dataset(dataset_name, split="train")
        base = split_ranges[split]
        base_offset, base_count = base.get("offset", 0), base.get("count")
        lo = base_offset + offset
        hi = lo + count if count is not None else (base_offset + base_count if base_count is not None else len(ds))
        if base_count is not None:
            hi = min(hi, base_offset + base_count)
        hi = min(hi, len(ds))
        rows = ds.select(range(lo, hi))

        self.rows = []
        for i, row in enumerate(rows):
            body = _normalize_component_identifier(row["Success Case"] + "\n\n" + row["Failure Case"])
            test_content = _TEST_HEADER + body
            prompt = (
                f"Category: {row['Category']}\n\n"
                "Generate Solution.js -- a React component, default export, "
                "named `Component` at import time -- to pass the tests below:\n\n"
                f"{test_content}\n\nReturn code only."
            )
            self.rows.append({
                "id": f"{split}[{lo + i}]",
                "prompt": prompt,
                "test_content": test_content,
            })
        self.num_tasks = len(self.rows)
        self._cursor = -1

    def reset(self) -> tuple[str, dict]:
        self._cursor += 1
        row = self.rows[self._cursor]
        info = {
            "admissible_commands": [],  # free-form code -- no discrete action space
            "won": False,
            "task_id": row["id"],
            "task": row["prompt"],
        }
        return row["prompt"], info

    def step(self, action: str) -> tuple[str, bool, dict]:
        row = self.rows[self._cursor]
        code = _extract_code(action)

        won = False
        # Own temp dir per episode (parallel episodes would otherwise clobber
        # each other's Solution.js/Solution.test.js in a shared directory);
        # node_modules is symlinked, not reinstalled, to keep this fast.
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
                (tmp_path / "node_modules").symlink_to(_JS_PROJECT_DIR / "node_modules")
                shutil.copy(_JS_PROJECT_DIR / "babel.config.js", tmp_path / "babel.config.js")
                shutil.copy(_JS_PROJECT_DIR / "jest.config.js", tmp_path / "jest.config.js")
                (tmp_path / "Solution.js").write_text(code)
                (tmp_path / "Solution.test.js").write_text(row["test_content"])

                result = subprocess.run(
                    [str(_JS_PROJECT_DIR / "node_modules" / ".bin" / "jest"), "Solution.test.js"],
                    capture_output=True, text=True, timeout=_EXEC_TIMEOUT_S, cwd=tmp_dir,
                )
                won = result.returncode == 0
        except subprocess.TimeoutExpired:
            won = False

        info = {"admissible_commands": [], "won": won, "task_id": row["id"], "task": ""}
        return "", True, info  # single-turn: always done after one step

    def close(self) -> None:
        pass


register("frontend", FrontendEnvironment)
