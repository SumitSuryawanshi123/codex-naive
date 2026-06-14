from __future__ import annotations

from contextvars import ContextVar


current_span_stack: ContextVar[tuple[str, ...]] = ContextVar(
    "traceflow_current_span_stack",
    default=(),
)
current_trace_id: ContextVar[str | None] = ContextVar(
    "traceflow_current_trace_id",
    default=None,
)
