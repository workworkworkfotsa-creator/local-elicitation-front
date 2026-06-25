"""FakeModelClient — a scripted ModelClient for the test harness (no model loaded).

Returns predefined responses in order (scriptable for the PUSH 2-turn listening test later) and
records every call, so tests can assert what the front actually sent (messages, grammar).
"""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass

from front.model_client import Message


class ScriptExhaustedError(RuntimeError):
    """Raised when generate() is called but no scripted response remains."""


@dataclass(frozen=True)
class Call:
    """A record of one generate() invocation, for test assertions."""

    messages: tuple[Message, ...]
    grammar: str | None


class FakeModelClient:
    """A ModelClient whose outputs are scripted up front; satisfies the ModelClient Protocol."""

    def __init__(self, scripted_responses: Sequence[str]) -> None:
        self._responses: deque[str] = deque(scripted_responses)
        self.calls: list[Call] = []

    def generate(self, messages: Sequence[Message], *, grammar: str | None = None) -> str:
        self.calls.append(Call(messages=tuple(messages), grammar=grammar))
        if not self._responses:
            raise ScriptExhaustedError("FakeModelClient: no scripted response left")
        return self._responses.popleft()
