"""Workspace plumbing smoke test (Tier A) — no model, no GGUF.

The harness floor: if this fails, the workspace wiring is broken. It proves every block is
installed in the shared venv and importable, and that the `contract` boundary resolves.
"""

from __future__ import annotations

import importlib

BLOCKS = ("contract", "front", "consolidation", "generation")


def test_all_blocks_importable() -> None:
    for package_name in BLOCKS:
        module = importlib.import_module(package_name)
        assert module.__doc__, f"{package_name} must carry a module docstring"
