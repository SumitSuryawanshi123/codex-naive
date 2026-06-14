from __future__ import annotations

import json
import re

from debug_module.ingestion.fingerprint import fingerprint
from debug_module.ingestion.logs import EvidenceCandidate


def ingest_config_text(text: str) -> list[EvidenceCandidate]:
    candidates: list[EvidenceCandidate] = []
    lowered = text.lower()
    tags = ["configuration"]
    if any(term in lowered for term in ["missing", "invalid", "unset", "null", "none"]):
        tags.append("error")

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            body = ", ".join(f"{key}={_summarize_value(value)}" for key, value in sorted(parsed.items()))
        else:
            body = str(parsed)
    except json.JSONDecodeError:
        pairs = re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*[:=]\s*(.+?)\s*$", text, flags=re.MULTILINE)
        body = ", ".join(f"{key}={value}" for key, value in pairs) if pairs else text.strip()

    if not body:
        return []
    normalized = f"config_snapshot {body}"
    candidates.append(
        EvidenceCandidate(
            type="config",
            span_start=0,
            span_end=len(text),
            normalized_text=normalized,
            signal_tags=sorted(set(tags)),
            fingerprint=fingerprint(normalized),
        )
    )
    return candidates


def _summarize_value(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool | int | float):
        return str(value)
    if isinstance(value, str):
        return value[:80]
    return type(value).__name__
