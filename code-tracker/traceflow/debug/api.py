from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from traceflow.projects.manager import ProjectError, project_manager

from .service import build_fix_detail


REPO_ROOT = Path(__file__).resolve().parents[3]
DEBUG_MODULE_PATH = REPO_ROOT / "Debug_module"
if str(DEBUG_MODULE_PATH) not in sys.path:
    sys.path.insert(0, str(DEBUG_MODULE_PATH))

from debug_module.integration import analyze_traceflow_payload  # noqa: E402


router = APIRouter(prefix="/debug", tags=["debug"])


class DebugFixRequest(BaseModel):
    project_id: str | None = None
    request: dict[str, Any] = Field(default_factory=dict)
    response: dict[str, Any] = Field(default_factory=dict)
    trace: dict[str, Any] = Field(default_factory=dict)


class DebugFixDetailRequest(DebugFixRequest):
    query: str | None = None
    analysis: dict[str, Any] | None = None


def _enrich_payload(payload: DebugFixRequest | DebugFixDetailRequest) -> tuple[dict[str, Any], Path | None]:
    data = payload.model_dump()
    source_root: Path | None = None
    if payload.project_id:
        try:
            session = project_manager.get_project(payload.project_id)
        except ProjectError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        source_root = session.source_dir
        data["log_tail"] = session.read_log_tail()
    return data, source_root


@router.post("/fix")
async def fix_trace(payload: DebugFixRequest) -> dict[str, Any]:
    data, source_root = _enrich_payload(payload)
    try:
        return analyze_traceflow_payload(data, source_root=source_root or REPO_ROOT)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/fix/detail")
async def fix_trace_detail(payload: DebugFixDetailRequest) -> dict[str, Any]:
    """Run a full Fix This investigation and return a detailed, UI-ready payload."""
    data, source_root = _enrich_payload(payload)
    try:
        return build_fix_detail(data, source_root=source_root or REPO_ROOT)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
