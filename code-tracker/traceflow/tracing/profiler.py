from __future__ import annotations

import sys
import threading
from pathlib import Path
from threading import RLock
from types import FrameType
from typing import Any, Callable

from .context import current_trace_id
from .models import TraceEvent
from .recorder import TraceRecorder


ProfileFunc = Callable[[FrameType, str, Any], object]


class FunctionProfiler:
    def __init__(
        self,
        recorder: TraceRecorder,
        roots: list[Path],
        *,
        max_events: int = 350,
    ) -> None:
        self.recorder = recorder
        self.roots = [root.resolve() for root in roots]
        self.max_events = max_events
        self._events_by_frame: dict[int, tuple[TraceEvent, Any, int | None]] = {}
        self._lock = RLock()
        self._previous_profile: ProfileFunc | None = None
        self._previous_thread_profile: ProfileFunc | None = None
        self._local = threading.local()
        self._event_count = 0
        self._limit_recorded = False

    def __enter__(self) -> "FunctionProfiler":
        self._previous_profile = sys.getprofile()
        self._previous_thread_profile = threading.getprofile()
        sys.setprofile(self._profile)
        threading.setprofile(self._profile)
        if hasattr(threading, "setprofile_all_threads"):
            threading.setprofile_all_threads(self._profile)
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: object) -> bool:
        sys.setprofile(self._previous_profile)
        threading.setprofile(self._previous_thread_profile)
        if hasattr(threading, "setprofile_all_threads"):
            threading.setprofile_all_threads(self._previous_thread_profile)
        self._finish_open_events()
        return False

    def _profile(self, frame: FrameType, event: str, arg: Any) -> None:
        if event not in {"call", "return"}:
            return
        if getattr(self._local, "disabled", False):
            return
        if current_trace_id.get() is None:
            return

        path = self._source_path(frame)
        if path is None:
            return

        self._local.disabled = True
        try:
            if event == "call":
                self._record_call(frame, path)
            elif event == "return":
                self._record_return(frame)
        finally:
            self._local.disabled = False

    def _record_call(self, frame: FrameType, path: Path) -> None:
        with self._lock:
            if self._event_count >= self.max_events:
                self._record_limit_once()
                return

        name = self._function_name(frame)
        event, token = self.recorder.begin_event(
            name,
            kind=self._kind_from_path(path),
            detail=f"{self._relative_path(path)}:{frame.f_code.co_firstlineno}",
        )
        if event is None:
            return
        with self._lock:
            self._events_by_frame[id(frame)] = (event, token, threading.get_ident())
            self._event_count += 1

    def _record_return(self, frame: FrameType) -> None:
        with self._lock:
            item = self._events_by_frame.pop(id(frame), None)
        if item is None:
            return
        event, token, thread_id = item
        if thread_id is not None and thread_id != threading.get_ident():
            token = None
        self.recorder.finish_event(event, token, status="ok")

    def _record_limit_once(self) -> None:
        if self._limit_recorded:
            return
        event, token = self.recorder.begin_event(
            "function trace limit reached",
            kind="profiler",
            detail=f"Stopped after {self.max_events} function calls",
        )
        if event is not None:
            self.recorder.finish_event(event, token, status="ok")
        self._limit_recorded = True

    def _finish_open_events(self) -> None:
        with self._lock:
            open_events = list(self._events_by_frame.values())
            self._events_by_frame.clear()
        for event, _token, _thread_id in reversed(open_events):
            self.recorder.finish_event(event, None, status="ok")

    def _source_path(self, frame: FrameType) -> Path | None:
        filename = frame.f_code.co_filename
        if not filename or filename.startswith("<"):
            return None
        path = Path(filename).resolve()
        for root in self.roots:
            try:
                path.relative_to(root)
                return path
            except ValueError:
                continue
        return None

    def _relative_path(self, path: Path) -> str:
        for root in self.roots:
            try:
                return str(path.relative_to(root))
            except ValueError:
                continue
        return str(path)

    def _function_name(self, frame: FrameType) -> str:
        module = frame.f_globals.get("__name__", "")
        qualname = frame.f_code.co_qualname
        return f"{module}.{qualname}" if module else qualname

    def _kind_from_path(self, path: Path) -> str:
        lowered_parts = {part.lower() for part in path.parts}
        name = path.stem.lower()
        if "routes" in lowered_parts or "api" in lowered_parts:
            return "route"
        if "services" in lowered_parts or "service" in name:
            return "service"
        if "repositories" in lowered_parts or "repository" in name:
            return "repository"
        if "db" in lowered_parts or "database" in lowered_parts or "database" in name:
            return "database"
        if "models" in lowered_parts or "schemas" in lowered_parts:
            return "model"
        return "function"
