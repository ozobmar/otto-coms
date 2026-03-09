#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detect platform for venv activation
if [ -d "$SCRIPT_DIR/.venv/Scripts" ]; then
    source "$SCRIPT_DIR/.venv/Scripts/activate"
else
    source "$SCRIPT_DIR/.venv/bin/activate"
fi

otto-coms "$@"
