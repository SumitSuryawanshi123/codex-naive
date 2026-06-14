from __future__ import annotations

from collections import OrderedDict
from contextlib import AbstractContextManager
from threading import RLock
from types import TracebackType
from typing import Any
from uuid import uuid4

from .context import current_span_stack, current_trace_id
from .models import Trace, TraceEvent


class _RecordedSpan(AbstractContextManager["_RecordedSpan"]):
    def __init__(
        self,
        recorder: "TraceRecorder",
        *,
        name: str,
        kind: str,
        detail: str | None = None,
    ) -> None:
        self.recorder = recorder
        self.name = name
        self.kind = kind
        self.detail = detail
        self.event: TraceEvent | None = None
        self.stack_token: Any = None

    def __enter__(self) -> "_RecordedSpan":
        self.event, self.stack_token = self.recorder.begin_event(
            self.name,
            kind=self.kind,
            detail=self.detail,
        )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        if self.event is not None:
            status = "error" if exc else "ok"
            error = f"{type(exc).__name__}: {exc}" if exc else None
            self.recorder.finish_event(self.event, self.stack_token, status=status, error=error)
        return False


class TraceRecorder:
    def __init__(self, *, max_traces: int = 100) -> None:
        self.max_traces = max_traces
        self._lock = RLock()
        self._traces: OrderedDict[str, Trace] = OrderedDict()

    def start_trace(
        self,
        *,
        trace_id: str | None,
        method: str,
        path: str,
        title: str | None = None,
    ) -> Trace:
        trace = Trace(
            trace_id=trace_id or uuid4().hex,
            method=method,
            path=path,
            title=title or f"{method} {path}",
        )
        with self._lock:
            self._traces[trace.trace_id] = trace
            self._traces.move_to_end(trace.trace_id)
            while len(self._traces) > self.max_traces:
                self._traces.popitem(last=False)
        return trace

    def finish_trace(
        self,
        trace_id: str,
        *,
        status_code: int | None,
        outcome: str,
        error: str | None = None,
    ) -> None:
        with self._lock:
            trace = self._traces.get(trace_id)
            if trace is not None:
                trace.finish(status_code=status_code, outcome=outcome, error=error)

    def begin_event(
        self,
        name: str,
        *,
        kind: str,
        detail: str | None = None,
    ) -> tuple[TraceEvent | None, Any]:
        trace_id = current_trace_id.get()
        if trace_id is None:
            return None, None

        stack = current_span_stack.get()
        parent_id = stack[-1] if stack else None
        event = TraceEvent(
            event_id=uuid4().hex,
            trace_id=trace_id,
            parent_id=parent_id,
            name=name,
            kind=kind,
            detail=detail,
            depth=len(stack),
        )

        with self._lock:
            trace = self._traces.get(trace_id)
            if trace is None:
                return None, None
            trace.events.append(event)

        token = current_span_stack.set((*stack, event.event_id))
        return event, token

    def finish_event(
        self,
        event: TraceEvent,
        stack_token: Any,
        *,
        status: str,
        error: str | None = None,
    ) -> None:
        event.finish(status=status, error=error)
        if stack_token is not None:
            current_span_stack.reset(stack_token)

    def span(
        self,
        name: str,
        *,
        kind: str = "function",
        detail: str | None = None,
    ) -> _RecordedSpan:
        return _RecordedSpan(self, name=name, kind=kind, detail=detail)

    def latest_trace(self) -> dict[str, Any] | None:
        with self._lock:
            if not self._traces:
                return None
            trace = next(reversed(self._traces.values()))
            return trace.to_dict()

    def get_trace(self, trace_id: str) -> dict[str, Any] | None:
        with self._lock:
            trace = self._traces.get(trace_id)
            if trace is None:
                return None
            return trace.to_dict()

    def list_traces(self) -> list[dict[str, Any]]:
        with self._lock:
            return [trace.to_dict() for trace in reversed(self._traces.values())]


trace_recorder = TraceRecorder()


def trace_step(name: str, *, kind: str = "function", detail: str | None = None) -> _RecordedSpan:
    return trace_recorder.span(name, kind=kind, detail=detail)
