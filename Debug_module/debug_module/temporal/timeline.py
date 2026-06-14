from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from debug_module.models import Evidence

ISO_TS_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}Z?\b")
SYSLOG_TS_RE = re.compile(r"\b[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\b")


def investigation_timeline(db: Session, investigation_id: int) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    evidence = list(db.scalars(select(Evidence).where(Evidence.investigation_id == investigation_id)))
    for item in evidence:
        timestamp = _extract_timestamp(item.normalized_text)
        if not timestamp:
            continue
        events.append(
            {
                "timestamp": timestamp,
                "evidence_id": item.id,
                "type": item.type,
                "text": item.normalized_text,
            }
        )
    return sorted(events, key=lambda event: str(event["timestamp"]))


def _extract_timestamp(text: str) -> str | None:
    match = ISO_TS_RE.search(text) or SYSLOG_TS_RE.search(text)
    return match.group(0) if match else None
