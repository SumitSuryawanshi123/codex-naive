from __future__ import annotations

import importlib
import os
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from starlette.types import ASGIApp, Receive, Scope, Send

from .tracing import TraceMiddleware, trace_recorder


CONTROL_PREFIX = "/__traceflow"
FASTAPI_SYSTEM_ROUTES = {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}


class RuntimeApp:
    def __init__(self, control_app: ASGIApp, target_app: ASGIApp) -> None:
        self.control_app = control_app
        self.target_app = target_app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = str(scope.get("path") or "")
        if path.startswith(CONTROL_PREFIX):
            await self.control_app(scope, receive, send)
            return
        await self.target_app(scope, receive, send)


def load_target_app(target: str) -> ASGIApp:
    if ":" not in target:
        raise RuntimeError("TRACEFLOW_TARGET_APP must look like module:app or module:create_app()")

    module_name, attr_name = target.split(":", 1)
    module = importlib.import_module(module_name)
    if attr_name.endswith("()"):
        factory_name = attr_name[:-2]
        factory = getattr(module, factory_name)
        loaded = factory()
    else:
        loaded = getattr(module, attr_name)

    if not callable(loaded):
        raise RuntimeError(f"Target '{target}' did not resolve to an ASGI callable")
    return loaded


def patch_sqlite_thread_check() -> None:
    original_connect = sqlite3.connect

    def connect(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        kwargs.setdefault("check_same_thread", False)
        return original_connect(*args, **kwargs)

    sqlite3.connect = connect


def route_snapshot(target_app: ASGIApp) -> list[dict[str, Any]]:
    routes = []
    for route in getattr(target_app, "routes", []):
        path = getattr(route, "path", None)
        if not path:
            continue
        if path in FASTAPI_SYSTEM_ROUTES:
            continue
        methods = sorted((getattr(route, "methods", None) or {"GET"}) - {"HEAD", "OPTIONS"})
        if not methods:
            methods = ["GET"]
        routes.append(
            {
                "path": path,
                "methods": methods,
                "name": getattr(route, "name", path),
            }
        )
    return routes


def create_control_app(target_app: ASGIApp, app_target: str, project_root: Path) -> FastAPI:
    control_app = FastAPI(title="TraceFlow Runtime Control", docs_url=None, redoc_url=None)

    @control_app.get(f"{CONTROL_PREFIX}/health")
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "app_target": app_target,
            "project_root": str(project_root),
        }

    @control_app.get(f"{CONTROL_PREFIX}/routes")
    async def routes() -> list[dict[str, Any]]:
        return route_snapshot(target_app)

    @control_app.get(f"{CONTROL_PREFIX}/traces")
    async def traces() -> list[dict[str, Any]]:
        return trace_recorder.list_traces()

    @control_app.get(f"{CONTROL_PREFIX}/traces/latest")
    async def latest_trace() -> dict[str, Any]:
        trace = trace_recorder.latest_trace()
        if trace is None:
            raise HTTPException(status_code=404, detail="No traces recorded yet")
        return trace

    @control_app.get(f"{CONTROL_PREFIX}/traces/{{trace_id}}")
    async def get_trace(trace_id: str) -> dict[str, Any]:
        trace = trace_recorder.get_trace(trace_id)
        if trace is None:
            raise HTTPException(status_code=404, detail="Trace not found")
        return trace

    return control_app


def create_runtime_app() -> RuntimeApp:
    app_target = os.environ["TRACEFLOW_TARGET_APP"]
    project_root = Path(os.environ["TRACEFLOW_PROJECT_ROOT"]).resolve()
    profile_roots = [
        Path(item).resolve()
        for item in os.environ.get("TRACEFLOW_PROFILE_ROOTS", str(project_root)).split(os.pathsep)
        if item
    ]

    patch_sqlite_thread_check()
    target_app = load_target_app(app_target)
    traced_target = TraceMiddleware(
        target_app,
        ignored_paths={"/favicon.ico"},
        ignored_path_prefixes=(CONTROL_PREFIX,),
        profile_roots=profile_roots,
    )
    control_app = create_control_app(target_app, app_target, project_root)
    return RuntimeApp(control_app=control_app, target_app=traced_target)


app = create_runtime_app()
