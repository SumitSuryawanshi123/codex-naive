from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from debug_module.database import Base
from debug_module.evidence.store import append_artifact
from debug_module.orchestrator import create_investigation, step_investigation
from debug_module.report import investigation_report


def test_investigation_scores_grounded_hypothesis() -> None:
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
    assert report["ranked_causes"]
    assert report["ranked_causes"][0]["evidence_score"] > 0
    assert report["ranked_causes"][0]["signals"][0]["verified"] is True
