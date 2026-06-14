from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from debug_module.database import Base
from debug_module.evidence.store import append_artifact
from debug_module.orchestrator import create_investigation, step_investigation
from debug_module.report import investigation_report
from debug_module.reasoning.patterns import pattern_evidence_from_text


def test_failure_pattern_detects_external_service_timeout() -> None:
    candidates = pattern_evidence_from_text("ERROR checkout timeout calling Stripe after 30000ms")

    assert candidates
    assert candidates[0].type == "failure_pattern"
    assert "known_pattern" in candidates[0].signal_tags
    assert "pattern_external_service" in candidates[0].signal_tags


def test_known_pattern_reduces_matching_hypothesis_novelty_without_overriding_score() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    with Session() as db:
        inv = create_investigation(db, budget=2, summary="checkout failing")
        append_artifact(
            db,
            inv.id,
            "log",
            "2026-06-14T08:15:01Z ERROR checkout timeout calling Stripe after 30000ms",
            {"test": True},
        )
        step_investigation(db, inv.id)
        report = investigation_report(db, inv.id)

    top = report["ranked_causes"][0]
    assert top["category"] == "EXTERNAL_SERVICE"
    assert top["novelty_score"] == 0.2
    assert top["evidence_score"] > 0
