from __future__ import annotations

from pathlib import Path
from typing import Any


def build_fix_detail(payload: dict[str, Any], source_root: Path | None = None) -> dict[str, Any]:
    from debug_module.integration import analyze_traceflow_payload

    trace = payload.get("trace") or {}
    response = payload.get("response") or {}
    request = payload.get("request") or {}
    analysis = payload.get("analysis") or {}

    report = analyze_traceflow_payload(payload, source_root=source_root)
    ranked = report.get("ranked_causes") or []
    top_cause = ranked[0] if ranked else None
    alternatives = ranked[1:4]

    failure_events = _failure_events(trace)
    evidence_requests = report.get("evidence_requests") or []
    remediation = report.get("remediation_suggestions") or []

    graph_context = None
    if analysis:
        graph_context = {
            "summary": analysis.get("summary"),
            "failure_points": analysis.get("failure_points") or [],
            "llm_used": analysis.get("llm_used", False),
            "model": analysis.get("model"),
            "node_count": len(analysis.get("nodes") or []),
        }

    return {
        "status": report.get("investigation", {}).get("status", "unknown"),
        "failure": {
            "summary": _failure_summary(trace, request, response),
            "method": trace.get("method") or request.get("method"),
            "path": trace.get("path") or request.get("path"),
            "status_code": response.get("status_code") or trace.get("status_code"),
            "trace_id": trace.get("trace_id"),
            "error": trace.get("error") or response.get("body"),
            "events": failure_events,
            "event_count": len(trace.get("events") or []),
        },
        "investigation": report.get("investigation"),
        "top_cause": top_cause,
        "alternatives": alternatives,
        "ranked_causes": ranked,
        "evidence_requests": evidence_requests,
        "remediation": remediation,
        "timeline": report.get("timeline") or [],
        "similar_resolutions": report.get("similar_resolutions") or [],
        "graph_context": graph_context,
        "fix_zip_available": bool(analysis),
        "recommended_next_steps": _recommended_next_steps(
            top_cause=top_cause,
            evidence_requests=evidence_requests,
            remediation=remediation,
            graph_context=graph_context,
        ),
        "query": payload.get("query") or "",
    }


def _failure_events(trace: dict[str, Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if trace.get("error"):
        events.append(
            {
                "kind": "trace",
                "name": trace.get("title") or "request failure",
                "error": trace.get("error"),
                "status": "error",
            }
        )
    for event in trace.get("events") or []:
        if event.get("status") == "error" or event.get("error"):
            events.append(
                {
                    "kind": event.get("kind"),
                    "name": event.get("name"),
                    "error": event.get("error") or event.get("detail"),
                    "status": event.get("status") or "error",
                    "duration_ms": event.get("duration_ms"),
                }
            )
    return events


def _failure_summary(trace: dict[str, Any], request: dict[str, Any], response: dict[str, Any]) -> str:
    method = trace.get("method") or request.get("method") or "REQUEST"
    path = trace.get("path") or request.get("path") or "<unknown>"
    status = response.get("status_code") or trace.get("status_code") or "error"
    error = trace.get("error") or response.get("body") or "unknown failure"
    if isinstance(error, dict):
        error = str(error)
    return f"{method} {path} failed with status {status}: {error}"


def _recommended_next_steps(
    *,
    top_cause: dict[str, Any] | None,
    evidence_requests: list[dict[str, Any]],
    remediation: list[dict[str, str]],
    graph_context: dict[str, Any] | None,
) -> list[dict[str, str]]:
    steps: list[dict[str, str]] = []

    for item in remediation:
        steps.append(
            {
                "type": "remediation",
                "title": f"Fix {item.get('category', 'issue')}",
                "detail": item.get("action", ""),
                "validation": item.get("validation", ""),
            }
        )

    for item in evidence_requests[:3]:
        steps.append(
            {
                "type": "evidence",
                "title": "Collect more evidence",
                "detail": item.get("what", ""),
                "validation": item.get("expected_signal", ""),
            }
        )

    if graph_context:
        for point in (graph_context.get("failure_points") or [])[:2]:
            steps.append(
                {
                    "type": "graph",
                    "title": f"Inspect {point.get('node_id', 'suspect node')}",
                    "detail": point.get("reason", ""),
                    "validation": point.get("confidence", ""),
                }
            )

    if top_cause and top_cause.get("evidence_score", 0) < 7:
        steps.append(
            {
                "type": "investigation",
                "title": "Investigation inconclusive",
                "detail": "Evidence score is still low. Add logs, config, or dependency health checks before changing code.",
                "validation": "Re-run Fix This after attaching new evidence.",
            }
        )

    return steps
