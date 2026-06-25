"""SQLite adapter for the append-only ``TraceRepository`` — a jettable POC proxy of MariaDB.

The IT team swaps this for a MariaDB adapter; the engine, talking only to the ABC, is unchanged.
Schema choices are version-portable across the planned MariaDB migration: JSON in TEXT columns
(parsed app-side, as the IT already does on MariaDB 5 — the engine passes/returns dicts, so a prod
column may stay TEXT or become native JSON without touching the contract), app-supplied
``created_at`` (deterministic, no ``CURRENT_TIMESTAMP`` default), bounded keys, raw SQL (no ORM).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any

from contract.trace import (
    DeclaredFile,
    DialogueTurn,
    ExpressionDeBesoin,
    Hypothesis,
    Session,
    TraceRepository,
    Verdict,
)

# All trace tables, used to generate the append-only triggers uniformly.
_TABLES = (
    "session",
    "dialogue_turn",
    "declared_file",
    "expression_de_besoin",
    "hypothesis",
    "verdict",
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS session (
    session_id   TEXT PRIMARY KEY,
    demandeur    TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    model_name   TEXT NOT NULL,
    model_config TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS dialogue_turn (
    turn_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL REFERENCES session(session_id),
    created_at  TEXT NOT NULL,
    role        TEXT NOT NULL,
    content_raw TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS declared_file (
    file_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL REFERENCES session(session_id),
    created_at  TEXT NOT NULL,
    filename    TEXT NOT NULL,
    role        TEXT NOT NULL,
    schema_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS expression_de_besoin (
    expression_de_besoin_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id              TEXT NOT NULL REFERENCES session(session_id),
    created_at              TEXT NOT NULL,
    request_type            TEXT NOT NULL,
    slots_json              TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS hypothesis (
    hypothesis_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    expression_de_besoin_id INTEGER NOT NULL REFERENCES expression_de_besoin(expression_de_besoin_id),
    created_at              TEXT NOT NULL,
    slot                    TEXT NOT NULL,
    proposed_value          TEXT NOT NULL,
    risk_rank               INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS verdict (
    verdict_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    hypothesis_id   INTEGER NOT NULL REFERENCES hypothesis(hypothesis_id),
    created_at      TEXT NOT NULL,
    human_verdict   TEXT NOT NULL,
    corrected_value TEXT
);
"""


def _append_only_triggers() -> str:
    """One BEFORE UPDATE and one BEFORE DELETE trigger per table, each aborting the statement."""
    statements: list[str] = []
    for table in _TABLES:
        for operation in ("UPDATE", "DELETE"):
            message = f"trace is append-only: {operation} forbidden"
            statements.append(
                f"CREATE TRIGGER IF NOT EXISTS {table}_no_{operation.lower()} "
                f"BEFORE {operation} ON {table} "
                f"BEGIN SELECT RAISE(ABORT, '{message}'); END;"
            )
    return "\n".join(statements)


class SqliteTraceRepository(TraceRepository):
    """Append-only trace backed by SQLite. Pass a connection (DI); ``:memory:`` for tests."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.executescript(_SCHEMA)
        self._connection.executescript(_append_only_triggers())
        self._connection.commit()

    @classmethod
    def in_memory(cls) -> SqliteTraceRepository:
        return cls(sqlite3.connect(":memory:"))

    def _insert(self, sql: str, parameters: tuple[Any, ...]) -> int:
        cursor = self._connection.execute(sql, parameters)
        self._connection.commit()
        return int(cursor.lastrowid)

    # --- append ---

    def start_session(
        self,
        *,
        session_id: str,
        demandeur: str,
        model_name: str,
        model_config: dict[str, Any],
        created_at: datetime,
    ) -> str:
        self._connection.execute(
            "INSERT INTO session (session_id, demandeur, created_at, model_name, model_config) "
            "VALUES (?, ?, ?, ?, ?)",
            (session_id, demandeur, created_at.isoformat(), model_name, json.dumps(model_config)),
        )
        self._connection.commit()
        return session_id

    def append_dialogue_turn(
        self,
        *,
        session_id: str,
        role: str,
        content_raw: str,
        created_at: datetime,
    ) -> int:
        return self._insert(
            "INSERT INTO dialogue_turn (session_id, created_at, role, content_raw) VALUES (?, ?, ?, ?)",
            (session_id, created_at.isoformat(), role, content_raw),
        )

    def declare_file(
        self,
        *,
        session_id: str,
        filename: str,
        role: str,
        schema: dict[str, Any],
        created_at: datetime,
    ) -> int:
        return self._insert(
            "INSERT INTO declared_file (session_id, created_at, filename, role, schema_json) "
            "VALUES (?, ?, ?, ?, ?)",
            (session_id, created_at.isoformat(), filename, role, json.dumps(schema)),
        )

    def record_expression_de_besoin(
        self,
        *,
        session_id: str,
        request_type: str,
        slots: dict[str, Any],
        created_at: datetime,
    ) -> int:
        return self._insert(
            "INSERT INTO expression_de_besoin (session_id, created_at, request_type, slots_json) "
            "VALUES (?, ?, ?, ?)",
            (session_id, created_at.isoformat(), request_type, json.dumps(slots)),
        )

    def pose_hypothesis(
        self,
        *,
        expression_de_besoin_id: int,
        slot: str,
        proposed_value: str,
        risk_rank: int,
        created_at: datetime,
    ) -> int:
        return self._insert(
            "INSERT INTO hypothesis "
            "(expression_de_besoin_id, created_at, slot, proposed_value, risk_rank) "
            "VALUES (?, ?, ?, ?, ?)",
            (expression_de_besoin_id, created_at.isoformat(), slot, proposed_value, risk_rank),
        )

    def capture_verdict(
        self,
        *,
        hypothesis_id: int,
        human_verdict: str,
        corrected_value: str | None,
        created_at: datetime,
    ) -> int:
        return self._insert(
            "INSERT INTO verdict (hypothesis_id, created_at, human_verdict, corrected_value) "
            "VALUES (?, ?, ?, ?)",
            (hypothesis_id, created_at.isoformat(), human_verdict, corrected_value),
        )

    # --- read ---

    def read_session(self, session_id: str) -> Session:
        row = self._connection.execute("SELECT * FROM session WHERE session_id = ?", (session_id,)).fetchone()
        if row is None:
            raise KeyError(session_id)
        return Session(
            session_id=row["session_id"],
            demandeur=row["demandeur"],
            created_at=datetime.fromisoformat(row["created_at"]),
            model_name=row["model_name"],
            model_config=json.loads(row["model_config"]),
        )

    def read_dialogue_turns(self, session_id: str) -> list[DialogueTurn]:
        rows = self._connection.execute(
            "SELECT * FROM dialogue_turn WHERE session_id = ? ORDER BY turn_id", (session_id,)
        ).fetchall()
        return [
            DialogueTurn(
                turn_id=row["turn_id"],
                session_id=row["session_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                role=row["role"],
                content_raw=row["content_raw"],
            )
            for row in rows
        ]

    def read_declared_files(self, session_id: str) -> list[DeclaredFile]:
        rows = self._connection.execute(
            "SELECT * FROM declared_file WHERE session_id = ? ORDER BY file_id", (session_id,)
        ).fetchall()
        return [
            DeclaredFile(
                file_id=row["file_id"],
                session_id=row["session_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                filename=row["filename"],
                role=row["role"],
                schema=json.loads(row["schema_json"]),
            )
            for row in rows
        ]

    def read_expressions_de_besoin(self, session_id: str) -> list[ExpressionDeBesoin]:
        rows = self._connection.execute(
            "SELECT * FROM expression_de_besoin WHERE session_id = ? ORDER BY expression_de_besoin_id",
            (session_id,),
        ).fetchall()
        return [
            ExpressionDeBesoin(
                expression_de_besoin_id=row["expression_de_besoin_id"],
                session_id=row["session_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                request_type=row["request_type"],
                slots=json.loads(row["slots_json"]),
            )
            for row in rows
        ]

    def read_hypotheses(self, expression_de_besoin_id: int) -> list[Hypothesis]:
        rows = self._connection.execute(
            "SELECT * FROM hypothesis WHERE expression_de_besoin_id = ? ORDER BY hypothesis_id",
            (expression_de_besoin_id,),
        ).fetchall()
        return [
            Hypothesis(
                hypothesis_id=row["hypothesis_id"],
                expression_de_besoin_id=row["expression_de_besoin_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                slot=row["slot"],
                proposed_value=row["proposed_value"],
                risk_rank=row["risk_rank"],
            )
            for row in rows
        ]

    def read_verdicts(self, hypothesis_id: int) -> list[Verdict]:
        rows = self._connection.execute(
            "SELECT * FROM verdict WHERE hypothesis_id = ? ORDER BY verdict_id", (hypothesis_id,)
        ).fetchall()
        return [
            Verdict(
                verdict_id=row["verdict_id"],
                hypothesis_id=row["hypothesis_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                human_verdict=row["human_verdict"],
                corrected_value=row["corrected_value"],
            )
            for row in rows
        ]
