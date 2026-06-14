from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.evidence.retrieval import ranked_evidence
from app.models import EvidenceLink, EvidenceRequest, Hypothesis, Investigation
from app.reasoning.hypotheses import generate_hypotheses
from app.reasoning.linking import link_evidence
from app.reasoning.requests import build_evidence_request
from app.scoring import margin, rescore_all
from app.verifier import verify_links


def create_investigation(db: Session, budget: int | None = None, summary: str | None = None) -> Investigation:
    settings = get_settings()
    investigation = Investigation(budget=budget or settings.default_budget, summary=summary)
    db.add(investigation)
    db.commit()
    db.refresh(investigation)
    return investigation


def step_investigation(db: Session, investigation_id: int) -> Investigation:
    settings = get_settings()
    investigation = db.get(Investigation, investigation_id)
    if not investigation:
        raise ValueError(f"Investigation {investigation_id} not found")
    evidence = ranked_evidence(db, investigation_id, query=investigation.summary or "")
    if not evidence:
        investigation.status = "evidence_insufficient"
        db.commit()
        return investigation

    db.execute(delete(EvidenceRequest).where(EvidenceRequest.investigation_id == investigation_id))
    hypotheses = list(db.scalars(select(Hypothesis).where(Hypothesis.investigation_id == investigation_id)))
    if not hypotheses:
        for candidate in generate_hypotheses(evidence):
            db.add(Hypothesis(investigation_id=investigation_id, **candidate))
        db.commit()
        hypotheses = list(db.scalars(select(Hypothesis).where(Hypothesis.investigation_id == investigation_id)))

    for hypothesis in hypotheses:
        existing = {link.evidence_id for link in hypothesis.links}
        new_links = []
        for proposal in link_evidence(hypothesis, evidence):
            if proposal["evidence_id"] in existing:
                continue
            link = EvidenceLink(hypothesis_id=hypothesis.id, **proposal)
            db.add(link)
            new_links.append(link)
        db.flush()
        verify_links(db, new_links)

    db.expire_all()
    hypotheses = list(db.scalars(select(Hypothesis).where(Hypothesis.investigation_id == investigation_id)))
    rescore_all(db, hypotheses)
    investigation.step_count += 1
    ranked = sorted(hypotheses, key=lambda item: item.evidence_score, reverse=True)
    top_score = ranked[0].evidence_score if ranked else 0
    top_margin = margin(ranked)

    if top_score >= settings.high_threshold and top_margin >= settings.margin_threshold:
        investigation.status = "complete"
    elif investigation.step_count >= investigation.budget:
        investigation.status = "ranked"
    elif top_score < settings.low_threshold:
        investigation.status = "unknown"
    else:
        investigation.status = "ranked"
        for hypothesis in ranked[:3]:
            req = build_evidence_request(hypothesis)
            db.add(EvidenceRequest(investigation_id=investigation_id, hypothesis_id=hypothesis.id, **req))
    db.commit()
    db.refresh(investigation)
    return investigation
