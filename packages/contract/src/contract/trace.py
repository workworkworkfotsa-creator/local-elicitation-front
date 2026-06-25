"""Trace — the append-only governance log (brique 1).

The boundary the IT team reintegrates: the engine talks ONLY to the ``TraceRepository`` ABC
(dependency injection); ``SqliteTraceRepository`` is a jettable POC adapter that the IT swaps
for a MariaDB one. Append-only is part of the contract — the ABC exposes append + read,
never update/delete.

The schema is version-portable across the planned MariaDB migration (see ``sqlite_trace``): JSON
lives in TEXT columns (parsed app-side, as the IT already does on MariaDB 5), timestamps are
app-supplied (deterministic, no ``CURRENT_TIMESTAMP`` default), keys stay bounded.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Session:
    """Provenance of one elicitation session (immutable once started)."""

    session_id: str
    demandeur: str
    created_at: datetime
    model_name: str
    model_config: dict[str, Any]


@dataclass(frozen=True)
class DialogueTurn:
    """One verbatim turn of the raw dialogue, captured as it happens."""

    turn_id: int
    session_id: str
    created_at: datetime
    role: str
    content_raw: str


@dataclass(frozen=True)
class DeclaredFile:
    """A file the demandeur declared, with its read schema (names + types, values synthesised)."""

    file_id: int
    session_id: str
    created_at: datetime
    filename: str
    role: str
    schema: dict[str, Any]


@dataclass(frozen=True)
class ExpressionDeBesoin:
    """One snapshot of the normalised spec. A later snapshot is a new row, never an update."""

    expression_de_besoin_id: int
    session_id: str
    created_at: datetime
    request_type: str
    slots: dict[str, Any]


@dataclass(frozen=True)
class Hypothesis:
    """A pre-filled assumption surfaced to the human, ranked by risk-if-wrong."""

    hypothesis_id: int
    expression_de_besoin_id: int
    created_at: datetime
    slot: str
    proposed_value: str
    risk_rank: int


@dataclass(frozen=True)
class Verdict:
    """The human verdict on a hypothesis — the proof of co-authorship."""

    verdict_id: int
    hypothesis_id: int
    created_at: datetime
    human_verdict: str
    corrected_value: str | None


class TraceRepository(abc.ABC):
    """Append-only governance log. Implementations expose append + read, never mutate.

    Every method takes ``created_at`` explicitly (the app owns time — MariaDB 5.5 has no usable
    ``CURRENT_TIMESTAMP`` default), which also makes the Tier A tests deterministic.
    """

    # --- append: provenance + the four primitives ---

    @abc.abstractmethod
    def start_session(
        self,
        *,
        session_id: str,
        demandeur: str,
        model_name: str,
        model_config: dict[str, Any],
        created_at: datetime,
    ) -> str: ...

    @abc.abstractmethod
    def append_dialogue_turn(
        self,
        *,
        session_id: str,
        role: str,
        content_raw: str,
        created_at: datetime,
    ) -> int: ...

    @abc.abstractmethod
    def declare_file(
        self,
        *,
        session_id: str,
        filename: str,
        role: str,
        schema: dict[str, Any],
        created_at: datetime,
    ) -> int: ...

    @abc.abstractmethod
    def record_expression_de_besoin(
        self,
        *,
        session_id: str,
        request_type: str,
        slots: dict[str, Any],
        created_at: datetime,
    ) -> int: ...

    @abc.abstractmethod
    def pose_hypothesis(
        self,
        *,
        expression_de_besoin_id: int,
        slot: str,
        proposed_value: str,
        risk_rank: int,
        created_at: datetime,
    ) -> int: ...

    @abc.abstractmethod
    def capture_verdict(
        self,
        *,
        hypothesis_id: int,
        human_verdict: str,
        corrected_value: str | None,
        created_at: datetime,
    ) -> int: ...

    # --- read ---

    @abc.abstractmethod
    def read_session(self, session_id: str) -> Session: ...

    @abc.abstractmethod
    def read_dialogue_turns(self, session_id: str) -> list[DialogueTurn]: ...

    @abc.abstractmethod
    def read_declared_files(self, session_id: str) -> list[DeclaredFile]: ...

    @abc.abstractmethod
    def read_expressions_de_besoin(self, session_id: str) -> list[ExpressionDeBesoin]: ...

    @abc.abstractmethod
    def read_hypotheses(self, expression_de_besoin_id: int) -> list[Hypothesis]: ...

    @abc.abstractmethod
    def read_verdicts(self, hypothesis_id: int) -> list[Verdict]: ...
