from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.evidence.store import append_artifact
from app.orchestrator import create_investigation, step_investigation
from app.report import investigation_report


def test_report_includes_proposed_remediation_with_validation_plan() -> None:
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

    suggestion = report["remediation_suggestions"][0]
    assert suggestion["category"] == "EXTERNAL_SERVICE"
    assert suggestion["status"] == "proposed"
    assert suggestion["validation"]
