from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ...tracing import trace_recorder


router = APIRouter(prefix="/traces", tags=["traces"])


@router.get("")
async def list_traces() -> list[dict]:
    return trace_recorder.list_traces()


@router.get("/latest")
async def latest_trace() -> dict:
    trace = trace_recorder.latest_trace()
    if trace is None:
        raise HTTPException(status_code=404, detail="No traces recorded yet")
    return trace


@router.get("/{trace_id}")
async def get_trace(trace_id: str) -> dict:
    trace = trace_recorder.get_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace
