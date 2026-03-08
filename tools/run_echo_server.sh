#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Detect platform for venv activation
if [ -d "$REPO_DIR/.venv/Scripts" ]; then
    source "$REPO_DIR/.venv/Scripts/activate"
else
    source "$REPO_DIR/.venv/bin/activate"
fi

python "$SCRIPT_DIR/echo_server.py" "$@"
