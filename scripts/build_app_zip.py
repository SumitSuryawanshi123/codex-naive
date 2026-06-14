"""Build app.zip for TraceFlow upload (CRM-only package)."""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_SRC = ROOT / "app"
STAGING = ROOT / ".build" / "crm-upload"
OUTPUT = ROOT / "app.zip"

CRM_DIRS = ("api", "core", "data", "db", "models", "repositories", "services", "static", "utils")
TRACE_MAIN = '''from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api.error_handlers import register_exception_handlers
from .api.router import api_router
from .core.config import get_settings
from .db.initialization import initialize_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

    register_exception_handlers(app)
    app.include_router(api_router)

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(settings.static_dir / "index.html")

    app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
    return app


app = create_app()
'''

CRM_MODELS_INIT = '"""Pydantic API models."""\n'

CRM_DATABASE = '''"""Backward-compatible imports for older local scripts."""

from .db.connection import create_connection as get_connection
from .db.initialization import initialize_database
from .utils.datetime import utc_now

__all__ = ["get_connection", "initialize_database", "utc_now"]
'''


def build() -> None:
    if STAGING.exists():
        shutil.rmtree(STAGING)
    target = STAGING / "app"
    target.mkdir(parents=True)

    (target / "__init__.py").write_text("", encoding="utf-8")

    for dirname in CRM_DIRS:
        src_dir = APP_SRC / dirname
        if src_dir.exists():
            shutil.copytree(src_dir, target / dirname)

    (target / "main.py").write_text(TRACE_MAIN, encoding="utf-8")
    (target / "models" / "__init__.py").write_text(CRM_MODELS_INIT, encoding="utf-8")
    (target / "database.py").write_text(CRM_DATABASE, encoding="utf-8")

    if OUTPUT.exists():
        OUTPUT.unlink()
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(STAGING.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(STAGING).as_posix())

    shutil.rmtree(STAGING)
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
