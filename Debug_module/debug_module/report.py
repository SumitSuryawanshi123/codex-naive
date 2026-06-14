from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from debug_module.learning import similar_resolutions
from debug_module.models import EvidenceRequest, Hypothesis, Investigation
from debug_module.remediation import remediation_suggestions
from debug_module.scoring import score_hypothesis
from debug_module.temporal import investigation_timeline


def investigation_report(db: Session, investigation_id: int) -> dict:
    investigation = db.get(Investigation, investigation_id)
    if not investigation:
        raise ValueError(f"Investigation {investigation_id} not found")
    hypotheses = list(db.scalars(select(Hypothesis).where(Hypothesis.investigation_id == investigation_id)))
    ranked = sorted(hypotheses, key=lambda item: item.evidence_score, reverse=True)
    requests = list(db.scalars(select(EvidenceRequest).where(EvidenceRequest.investigation_id == investigation_id)))
    return {
        "investigation": {
            "id": investigation.id,
            "status": investigation.status,
            "step_count": investigation.step_count,
            "budget": investigation.budget,
            "summary": investigation.summary,
        },
        "ranked_causes": [
            {
                "id": h.id,
                "category": h.category,
                "statement": h.statement,
                "novelty_score": h.novelty_score,
                "evidence_score": h.evidence_score,
                "breakdown": score_hypothesis(h)[1],
                "signals": [
                    {
                        "evidence_id": link.evidence_id,
                        "relation": link.relation,
                        "strength": link.strength,
                        "verified": link.verified,
                        "tags": json.loads(link.evidence.signal_tags),
                        "text": link.evidence.normalized_text,
                        "span": [link.evidence.span_start, link.evidence.span_end],
                    }
                    for link in h.links
                    if link.verified
                ],
            }
            for h in ranked
        ],
        "evidence_requests": [
            {
                "id": r.id,
                "hypothesis_id": r.hypothesis_id,
                "what": r.what,
                "why": r.why,
                "expected_signal": r.expected_signal,
                "format": r.format,
            }
            for r in requests
        ],
        "timeline": investigation_timeline(db, investigation_id),
        "similar_resolutions": similar_resolutions(db, investigation_id),
        "remediation_suggestions": remediation_suggestions(db, investigation_id),
    }
