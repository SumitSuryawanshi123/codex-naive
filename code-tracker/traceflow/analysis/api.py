from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .service import AnalysisError, analyze_trace, create_fix_zip, elaborate_node


router = APIRouter(prefix="/analysis", tags=["analysis"])


class TraceAnalysisRequest(BaseModel):
    trace: dict[str, Any]
    query: str | None = None
    project_id: str | None = None


class TraceFixRequest(BaseModel):
    trace: dict[str, Any]
    query: str | None = None
    project_id: str | None = None
    analysis: dict[str, Any] | None = None


class NodeElaborationRequest(BaseModel):
    trace: dict[str, Any]
    node: dict[str, Any]
    query: str | None = None
    project_id: str | None = None


@router.post("/trace")
async def analyze_trace_request(request: TraceAnalysisRequest) -> dict[str, Any]:
    try:
        return analyze_trace(trace=request.trace, query=request.query, project_id=request.project_id)
    except AnalysisError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/elaborate")
async def elaborate_node_request(request: NodeElaborationRequest) -> dict[str, Any]:
    try:
        return elaborate_node(
            trace=request.trace,
            node=request.node,
            query=request.query,
            project_id=request.project_id,
        )
    except AnalysisError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/fix")
async def create_fix_request(request: TraceFixRequest) -> FileResponse:
    try:
        zip_path = create_fix_zip(
            trace=request.trace,
            query=request.query,
            project_id=request.project_id,
            analysis=request.analysis,
        )
    except AnalysisError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename="traceflow-fix.zip",
    )
