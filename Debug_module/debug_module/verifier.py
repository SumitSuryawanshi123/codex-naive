from __future__ import annotations

from sqlalchemy.orm import Session

from debug_module.models import Evidence, EvidenceLink


def verify_link(db: Session, link: EvidenceLink) -> bool:
    evidence = db.get(Evidence, link.evidence_id)
    if not evidence:
        return False
    artifact = evidence.artifact
    if evidence.span_start < 0 or evidence.span_end > len(artifact.raw_text):
        return False
    if evidence.span_start >= evidence.span_end:
        return False
    span_text = artifact.raw_text[evidence.span_start : evidence.span_end]
    if artifact.type in {"config", "har", "otel", "otel_trace", "trace"}:
        return bool(span_text.strip())
    return bool(span_text.strip()) and any(token in span_text for token in evidence.normalized_text.split()[:3])


def verify_links(db: Session, links: list[EvidenceLink]) -> None:
    for link in links:
        link.verified = verify_link(db, link)
    db.commit()
