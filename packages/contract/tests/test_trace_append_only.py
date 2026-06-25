"""Tier A — the trace is append-only and faithfully captures the four primitives.

No model, no GGUF. This is the irreversible-primitive oracle from CLAUDE.md: no UPDATE/DELETE
possible; a later fact is a new row; an abandon leaves a readable partial trace.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime

import pytest
from contract.sqlite_trace import SqliteTraceRepository

CLOCK = datetime(2026, 6, 25, 12, 0, 0)


@pytest.fixture
def trace() -> SqliteTraceRepository:
    return SqliteTraceRepository.in_memory()


def _seeded_session(trace: SqliteTraceRepository) -> str:
    return trace.start_session(
        session_id="session-001",
        demandeur="filipe",
        model_name="granite-4.1-3b",
        model_config={"temperature": 0.0, "num_ctx": 4096},
        created_at=CLOCK,
    )


def test_session_roundtrip(trace: SqliteTraceRepository) -> None:
    _seeded_session(trace)
    session = trace.read_session("session-001")
    assert session.demandeur == "filipe"
    assert session.model_config["num_ctx"] == 4096  # JSON survived the TEXT column
    assert session.created_at == CLOCK


def test_update_is_forbidden(trace: SqliteTraceRepository) -> None:
    _seeded_session(trace)
    with pytest.raises(sqlite3.Error, match="append-only"):
        trace._connection.execute(  # reach the raw store: the DB itself must refuse
            "UPDATE session SET demandeur = 'someone-else' WHERE session_id = 'session-001'"
        )


def test_delete_is_forbidden(trace: SqliteTraceRepository) -> None:
    _seeded_session(trace)
    with pytest.raises(sqlite3.Error, match="append-only"):
        trace._connection.execute("DELETE FROM session WHERE session_id = 'session-001'")


def test_later_fact_is_a_new_row(trace: SqliteTraceRepository) -> None:
    session_id = _seeded_session(trace)
    first = trace.record_expression_de_besoin(
        session_id=session_id,
        request_type="croisement_fichiers",
        slots={"cle_jointure": "?"},
        created_at=CLOCK,
    )
    second = trace.record_expression_de_besoin(
        session_id=session_id,
        request_type="croisement_fichiers",
        slots={"cle_jointure": "ID Inter"},
        created_at=CLOCK,
    )
    snapshots = trace.read_expressions_de_besoin(session_id)
    assert [s.expression_de_besoin_id for s in snapshots] == [first, second]
    assert snapshots[0].slots["cle_jointure"] == "?"  # the earlier, wronger snapshot survives
    assert snapshots[1].slots["cle_jointure"] == "ID Inter"


def test_abandon_leaves_a_readable_partial_trace(trace: SqliteTraceRepository) -> None:
    session_id = _seeded_session(trace)
    trace.append_dialogue_turn(
        session_id=session_id, role="user", content_raw="automatise ma FAE", created_at=CLOCK
    )
    # The demandeur abandons here: no file, no expression_de_besoin.
    assert trace.read_session(session_id).demandeur == "filipe"
    turns = trace.read_dialogue_turns(session_id)
    assert len(turns) == 1
    assert turns[0].content_raw == "automatise ma FAE"
    assert trace.read_expressions_de_besoin(session_id) == []  # abandon is visible, not an error


def test_coauthorship_chain(trace: SqliteTraceRepository) -> None:
    session_id = _seeded_session(trace)
    expression_de_besoin_id = trace.record_expression_de_besoin(
        session_id=session_id, request_type="croisement_fichiers", slots={}, created_at=CLOCK
    )
    hypothesis_id = trace.pose_hypothesis(
        expression_de_besoin_id=expression_de_besoin_id,
        slot="cle_jointure",
        proposed_value="ID Inter",
        risk_rank=1,
        created_at=CLOCK,
    )
    trace.capture_verdict(
        hypothesis_id=hypothesis_id, human_verdict="confirm", corrected_value=None, created_at=CLOCK
    )
    verdicts = trace.read_verdicts(hypothesis_id)
    assert len(verdicts) == 1
    assert verdicts[0].human_verdict == "confirm"
