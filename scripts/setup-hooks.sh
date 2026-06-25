#!/usr/bin/env bash
# Enable the versioned git hooks for THIS clone.
# `core.hooksPath` is per-clone (not versioned), so every fresh clone runs this once:
#   bash scripts/setup-hooks.sh
set -euo pipefail
cd "$(dirname "$0")/.."
git config core.hooksPath .githooks
chmod +x .githooks/* 2>/dev/null || true
echo "Hooks enabled: core.hooksPath -> .githooks (pre-commit defensive guard active)"
