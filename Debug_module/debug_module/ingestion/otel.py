from __future__ import annotations

import json

from debug_module.ingestion.fingerprint import fingerprint
from debug_module.ingestion.logs import EvidenceCandidate


def ingest_otel_text(text: str) -> list[EvidenceCandidate]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    spans = data.get("spans", data if isinstance(data, list) else []) if isinstance(data, dict | list) else []
    candidates: list[EvidenceCandidate] = []
    for index, span in enumerate(spans):
        if not isinstance(span, dict):
            continue
        status = span.get("status", {})
        status_code = status.get("code") if isinstance(status, dict) else status
        if str(status_code).upper() not in {"ERROR", "STATUS_CODE_ERROR", "2"}:
            continue
        name = span.get("name", "<unknown>")
        trace_id = span.get("trace_id") or span.get("traceId") or "<unknown>"
        normalized = f"otel_span trace_id={trace_id} name={name} status={status_code}"
        candidates.append(
            EvidenceCandidate(
                type="otel_trace",
                span_start=0,
                span_end=len(text),
                normalized_text=normalized,
                signal_tags=["error", "trace"],
                fingerprint=fingerprint(f"{index}:{normalized}"),
            )
        )
    return candidates
