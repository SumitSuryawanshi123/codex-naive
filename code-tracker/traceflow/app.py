from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .analysis.api import router as analysis_router
from .demo.api import tickets, traces
from .debug.api import router as debug_router
from .projects.api import router as projects_router
from .tracing import TraceMiddleware


STATIC_DIR = Path(__file__).parent / "static"


def create_app() -> FastAPI:
    app = FastAPI(
        title="TraceFlow",
        version="0.1.0",
        description="Visual FastAPI request and function-flow tracker.",
    )

    app.add_middleware(
        TraceMiddleware,
        ignored_paths={"/", "/monitor", "/favicon.ico"},
        ignored_path_prefixes=("/static", "/api/traces", "/api/projects", "/api/analysis"),
    )

    app.include_router(tickets.router, prefix="/api")
    app.include_router(traces.router, prefix="/api")
    app.include_router(projects_router, prefix="/api")
    app.include_router(analysis_router, prefix="/api")
    app.include_router(debug_router, prefix="/api")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/monitor", include_in_schema=False)
    def monitor() -> FileResponse:
        return FileResponse(STATIC_DIR / "monitor.html")

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


app = create_app()
