#!/usr/bin/env bash
# One-shot setup: virtualenv, dependencies, and the two meta-skills copied
# into whatever agent harness is actually installed on this machine. Meant
# to be run by an agent, not typed by hand -- see the README's "Install
# this by asking your agent" section for the exact prompt.
#
# Usage:
#   ./install.sh                 core deps only (fine for MBPP/SearchQA/
#                                 LiveMathematicianBench/conversation distillation)
#   ./install.sh --with-alfworld also installs ALFWorld's extra dependencies
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

PY=""
for candidate in python3.11 python3.10 python3.9 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PY="$candidate"
        break
    fi
done
if [ -z "$PY" ]; then
    echo "No python3 interpreter found on PATH." >&2
    exit 1
fi

if [ ! -d .venv ]; then
    echo "Creating virtualenv at .venv with $PY..."
    "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "Installing core dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

if [ "${1:-}" = "--with-alfworld" ]; then
    echo "Installing ALFWorld dependencies..."
    pip install -q -r requirements-alfworld.txt
fi

echo ""
echo "Installing meta-skills into every agent harness found on this machine..."
install_meta_skills() {
    # `cp -r src dst` nests instead of overwriting when dst already exists
    # (e.g. a rerun), so clear the destination first -- this only ever
    # touches the two meta-skill folders this script itself manages.
    local skills_dir="$1"
    mkdir -p "$skills_dir"
    rm -rf "$skills_dir/skillup" "$skills_dir/distill-conversation"
    cp -r .claude/skills/skillup "$skills_dir/skillup"
    cp -r .claude/skills/distill-conversation "$skills_dir/distill-conversation"
}

for dir in "$HOME/.claude" "$HOME/.codex"; do
    if [ -d "$dir" ]; then
        install_meta_skills "$dir/skills"
        echo "  -> $dir/skills/{skillup,distill-conversation}"
    fi
done
install_meta_skills "$HOME/.agents/skills"
echo "  -> $HOME/.agents/skills/{skillup,distill-conversation} (shared convention, for any other harness)"

echo ""
if [ -z "${OPENROUTER_API_KEY:-}" ]; then
    echo "OPENROUTER_API_KEY is not set. Not needed for this install step, but"
    echo "every training/evaluation/distillation call needs it. Set it with:"
    echo "  export OPENROUTER_API_KEY=sk-or-..."
else
    echo "OPENROUTER_API_KEY is already set."
fi

echo ""
echo "Done. python -c \"import yaml, requests, datasets\" to sanity-check the install."
