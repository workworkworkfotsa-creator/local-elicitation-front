"""ModelClient — the seam between the front and whatever produces text.

The product wires a single in-process GGUF model here; the bench wires a model-swap (test only);
tests wire a FakeModelClient. The front depends on this Protocol, never on a concrete model — that
is what keeps the model a swappable variable (a hard one at <=3B; see CLAUDE.md).

Generation params (temperature, num_ctx...) belong to the concrete implementation's config (and are
recorded in the trace's ``model_config``), not here — the seam stays minimal: messages + grammar.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class Message:
    """One chat turn handed to the model."""

    role: str  # "system" | "user" | "assistant"
    content: str


@runtime_checkable
class ModelClient(Protocol):
    """Minimal model-call contract: messages (+ optional GBNF grammar) -> constrained text."""

    def generate(self, messages: Sequence[Message], *, grammar: str | None = None) -> str: ...
