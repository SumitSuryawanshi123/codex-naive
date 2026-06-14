from __future__ import annotations

from contextlib import nullcontext
from collections.abc import Awaitable, Callable, Iterable
from pathlib import Path
from typing import Any
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .context import current_span_stack, current_trace_id
from .profiler import FunctionProfiler
from .recorder import TraceRecorder, trace_recorder


class TraceMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        recorder: TraceRecorder = trace_recorder,
        ignored_paths: Iterable[str] | None = None,
        ignored_path_prefixes: Iterable[str] | None = None,
        profile_roots: Iterable[Path | str] | None = None,
    ) -> None:
        self.app = app
        self.recorder = recorder
        self.ignored_paths = set(ignored_paths or {"/", "/favicon.ico"})
        self.ignored_path_prefixes = tuple(ignored_path_prefixes or ("/static", "/api/traces"))
        self.profile_roots = [Path(root).resolve() for root in (profile_roots or [])]

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = str(scope.get("path") or "")
        if self._should_ignore(path):
            await self.app(scope, receive, send)
            return

        method = str(scope.get("method") or "GET")
        trace_id = self._header(scope, b"x-trace-id") or uuid4().hex
        trace = self.recorder.start_trace(
            trace_id=trace_id,
            method=method,
            path=path,
            title=f"{method} {path}",
        )

        trace_token = current_trace_id.set(trace.trace_id)
        stack_token = current_span_stack.set(())
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message.get("status", 200))
                headers = list(message.get("headers", []))
                headers.append((b"x-trace-id", trace.trace_id.encode("utf-8")))
                message = {**message, "headers": headers}
            await send(message)

        try:
            with self.recorder.span("api call", kind="http", detail=f"{method} {path}"):
                profiler = (
                    FunctionProfiler(self.recorder, self.profile_roots)
                    if self.profile_roots
                    else nullcontext()
                )
                with profiler:
                    await self.app(scope, receive, send_wrapper)
            outcome = "ok" if status_code < 500 else "error"
            self.recorder.finish_trace(trace.trace_id, status_code=status_code, outcome=outcome)
        except Exception as exc:
            self.recorder.finish_trace(
                trace.trace_id,
                status_code=status_code,
                outcome="error",
                error=f"{type(exc).__name__}: {exc}",
            )
            raise
        finally:
            current_span_stack.reset(stack_token)
            current_trace_id.reset(trace_token)

    def _should_ignore(self, path: str) -> bool:
        return path in self.ignored_paths or path.startswith(self.ignored_path_prefixes)

    @staticmethod
    def _header(scope: Scope, header_name: bytes) -> str | None:
        for name, value in scope.get("headers", []):
            if name.lower() == header_name:
                return value.decode("utf-8")
        return None
