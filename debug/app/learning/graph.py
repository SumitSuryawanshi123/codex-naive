from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.fingerprint import fingerprint
from app.models import Feedback, Hypothesis, Investigation, ResolvedIncident, RootCausePattern


def record_resolution(db: Session, feedback: Feedback) -> None:
    if not feedback.was_correct:
        return
    investigation = db.get(Investigation, feedback.investigation_id)
    if not investigation:
        return
    top = _top_hypothesis(db, feedback.investigation_id)
    category = top.category if top else "UNKNOWN"
    symptom_fingerprint = fingerprint(f"{category}:{investigation.summary or ''}:{feedback.chosen_root_cause}")

    db.add(
        ResolvedIncident(
            investigation_id=feedback.investigation_id,
            category=category,
            chosen_root_cause=feedback.chosen_root_cause,
            resolution_note=feedback.resolution_note,
            symptom_fingerprint=symptom_fingerprint,
        )
    )

    pattern = db.scalar(
        select(RootCausePattern).where(
            RootCausePattern.category == category,
            RootCausePattern.symptom_fingerprint == symptom_fingerprint,
        )
    )
    if pattern:
        pattern.weight += 1
        if feedback.resolution_note:
            pattern.resolution_note = feedback.resolution_note
    else:
        db.add(
            RootCausePattern(
                category=category,
                symptom_fingerprint=symptom_fingerprint,
                summary=feedback.chosen_root_cause,
                resolution_note=feedback.resolution_note,
                weight=1,
            )
        )


def similar_resolutions(db: Session, investigation_id: int, limit: int = 5) -> list[dict[str, object]]:
    top = _top_hypothesis(db, investigation_id)
    if not top:
        return []
    rows = list(
        db.scalars(
            select(RootCausePattern)
            .where(RootCausePattern.category == top.category)
            .order_by(RootCausePattern.weight.desc(), RootCausePattern.id.desc())
            .limit(limit)
        )
    )
    return [
        {
            "category": row.category,
            "summary": row.summary,
            "resolution_note": row.resolution_note,
            "weight": row.weight,
        }
        for row in rows
    ]


def _top_hypothesis(db: Session, investigation_id: int) -> Hypothesis | None:
    return db.scalar(
        select(Hypothesis)
        .where(Hypothesis.investigation_id == investigation_id)
        .order_by(Hypothesis.evidence_score.desc(), Hypothesis.id.asc())
        .limit(1)
    )
