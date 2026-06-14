from __future__ import annotations

import json

from app.ingestion.fingerprint import fingerprint
from app.ingestion.logs import EvidenceCandidate


def ingest_har_text(text: str) -> list[EvidenceCandidate]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    entries = data.get("log", {}).get("entries", []) if isinstance(data, dict) else []
    candidates: list[EvidenceCandidate] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        request = entry.get("request", {}) or {}
        response = entry.get("response", {}) or {}
        url = request.get("url", "<unknown>")
        status = int(response.get("status") or 0)
        elapsed = float(entry.get("time") or 0)
        tags = ["external_service"]
        if status >= 500:
            tags.extend(["error", "dependency"])
        if elapsed >= 1000:
            tags.append("timeout")
        if status < 500 and elapsed < 1000:
            continue
        normalized = f"har_entry url={url} status={status} time_ms={elapsed:g}"
        candidates.append(
            EvidenceCandidate(
                type="har",
                span_start=0,
                span_end=len(text),
                normalized_text=normalized,
                signal_tags=sorted(set(tags)),
                fingerprint=fingerprint(f"{index}:{normalized}"),
            )
        )
    return candidates
