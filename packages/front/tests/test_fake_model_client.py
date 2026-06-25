"""Tier A — the FakeModelClient harness (no model, no GGUF).

Defines the ModelClient seam contract: scripted responses in order, raises when exhausted, and
records calls so later tests (PUSH 2-turn, grammar wiring) can assert what the front sent.
"""

from __future__ import annotations

import pytest
from front.fake_model_client import Call, FakeModelClient, ScriptExhaustedError
from front.model_client import Message, ModelClient


def test_fake_satisfies_model_client_protocol() -> None:
    fake = FakeModelClient(["x"])
    assert isinstance(fake, ModelClient)  # structural conformance (runtime_checkable)


def test_returns_scripted_responses_in_order() -> None:
    fake = FakeModelClient(["first", "second"])
    turn = [Message(role="user", content="hi")]
    assert fake.generate(turn) == "first"
    assert fake.generate(turn) == "second"


def test_raises_when_script_exhausted() -> None:
    fake = FakeModelClient(["only"])
    fake.generate([Message(role="user", content="hi")])
    with pytest.raises(ScriptExhaustedError):
        fake.generate([Message(role="user", content="again")])


def test_records_calls_for_assertions() -> None:
    fake = FakeModelClient(["ok"])
    messages = [Message(role="system", content="answer X"), Message(role="user", content="why?")]
    fake.generate(messages, grammar='root ::= "X"')
    assert fake.calls == [Call(messages=tuple(messages), grammar='root ::= "X"')]


def test_usable_where_a_model_client_is_expected() -> None:
    # Demonstrates the DI seam: anything structurally a ModelClient plugs in.
    def first_reply(client: ModelClient) -> str:
        return client.generate([Message(role="user", content="ping")])

    assert first_reply(FakeModelClient(["pong"])) == "pong"
