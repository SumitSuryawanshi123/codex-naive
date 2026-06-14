from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from debug_module.database import Base
from debug_module.evidence.store import append_artifact
from debug_module.orchestrator import create_investigation, step_investigation
from debug_module.report import investigation_report


def analyze_traceflow_payload(payload: dict[str, Any], source_root: Path | None = None) -> dict[str, Any]:
    trace = payload.get("trace") or {}
    response = payload.get("response") or {}
    request = payload.get("request") or {}

    if not _is_failure(trace, response):
        raise ValueError("No failed trace to analyze")

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    summary = _summary(trace, request, response)
    with Session() as db:
        investigation = create_investigation(db, budget=3, summary=summary)
        append_artifact(
            db,
            investigation.id,
            "trace",
            _trace_text(trace),
            {"source": "traceflow", "trace_id": trace.get("trace_id")},
            repo_root=source_root,
        )
        append_artifact(
            db,
            investigation.id,
            "log",
            _response_text(response),
            {"source": "traceflow_response"},
            repo_root=source_root,
        )
        log_tail = payload.get("log_tail")
        if log_tail:
            append_artifact(
                db,
                investigation.id,
                "log",
                str(log_tail),
                {"source": "traceflow_runtime_log"},
                repo_root=source_root,
            )
        step_investigation(db, investigation.id)
        return investigation_report(db, investigation.id)


def _is_failure(trace: dict[str, Any], response: dict[str, Any]) -> bool:
    status_code = response.get("status_code") or trace.get("status_code")
    try:
        if status_code is not None and int(status_code) >= 400:
            return True
    except (TypeError, ValueError):
        pass
    if trace.get("outcome") == "error" or trace.get("error"):
        return True
    return any(event.get("status") == "error" or event.get("error") for event in trace.get("events") or [])


def _summary(trace: dict[str, Any], request: dict[str, Any], response: dict[str, Any]) -> str:
    method = trace.get("method") or request.get("method") or "REQUEST"
    path = trace.get("path") or request.get("path") or "<unknown>"
    status = response.get("status_code") or trace.get("status_code") or "error"
    return f"{method} {path} failed with status {status}"


def _trace_text(trace: dict[str, Any]) -> str:
    lines = [
        f"{trace.get('started_at', '')} ERROR trace_id={trace.get('trace_id')} "
        f"{trace.get('method')} {trace.get('path')} status={trace.get('status_code')} outcome={trace.get('outcome')}"
    ]
    if trace.get("error"):
        lines.append(f"trace error {trace['error']}")
    for event in trace.get("events") or []:
        status = str(event.get("status") or "ok").upper()
        level = "ERROR" if status == "ERROR" or event.get("error") else "INFO"
        bits = [
            str(event.get("started_at") or ""),
            level,
            f"kind={event.get('kind')}",
            f"name={event.get('name')}",
        ]
        if event.get("detail"):
            bits.append(f"detail={event.get('detail')}")
        if event.get("error"):
            bits.append(f"error={event.get('error')}")
        lines.append(" ".join(bits))
    return "\n".join(line for line in lines if line.strip())


def _response_text(response: dict[str, Any]) -> str:
    body = response.get("json")
    if body is None:
        body = response.get("body")
    if not isinstance(body, str):
        body = json.dumps(body, sort_keys=True)
    return f"ERROR response status={response.get('status_code')} body={body}"
