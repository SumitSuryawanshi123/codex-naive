from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import perf_counter
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class TraceEvent:
    event_id: str
    trace_id: str
    parent_id: str | None
    name: str
    kind: str
    detail: str | None
    depth: int
    started_at: datetime = field(default_factory=utc_now)
    ended_at: datetime | None = None
    duration_ms: float | None = None
    status: str = "running"
    error: str | None = None
    started_perf: float = field(default_factory=perf_counter, repr=False)

    def finish(self, *, status: str = "ok", error: str | None = None) -> None:
        self.ended_at = utc_now()
        self.duration_ms = round((perf_counter() - self.started_perf) * 1000, 3)
        self.status = status
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "kind": self.kind,
            "detail": self.detail,
            "depth": self.depth,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "error": self.error,
        }


@dataclass
class Trace:
    trace_id: str
    method: str
    path: str
    title: str
    started_at: datetime = field(default_factory=utc_now)
    ended_at: datetime | None = None
    duration_ms: float | None = None
    status_code: int | None = None
    outcome: str = "running"
    error: str | None = None
    events: list[TraceEvent] = field(default_factory=list)
    started_perf: float = field(default_factory=perf_counter, repr=False)

    def finish(
        self,
        *,
        status_code: int | None,
        outcome: str,
        error: str | None = None,
    ) -> None:
        self.ended_at = utc_now()
        self.duration_ms = round((perf_counter() - self.started_perf) * 1000, 3)
        self.status_code = status_code
        self.outcome = outcome
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "method": self.method,
            "path": self.path,
            "title": self.title,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_ms": self.duration_ms,
            "status_code": self.status_code,
            "outcome": self.outcome,
            "error": self.error,
            "events": [event.to_dict() for event in self.events],
        }
