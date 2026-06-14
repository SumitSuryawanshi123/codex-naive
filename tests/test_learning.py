from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import ResolvedIncident, RootCausePattern


def test_correct_feedback_records_resolution_and_report_similarity() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)
        created = client.post("/investigations", json={"budget": 2, "summary": "checkout failing"})
        investigation_id = created.json()["id"]
        client.post(
            f"/investigations/{investigation_id}/evidence",
            json={
                "type": "log",
                "raw_text": "2026-06-14T08:15:01Z ERROR checkout timeout calling Stripe after 30000ms",
            },
        )
        client.post(f"/investigations/{investigation_id}/step")

        feedback = client.post(
            f"/investigations/{investigation_id}/feedback",
            json={
                "chosen_root_cause": "Stripe timeout",
                "was_correct": True,
                "resolution_note": "Provider latency confirmed.",
            },
        )
        assert feedback.status_code == 200

        report = client.get(f"/investigations/{investigation_id}/report").json()
        assert report["similar_resolutions"]
        assert report["similar_resolutions"][0]["summary"] == "Stripe timeout"

        with Session() as db:
            assert db.scalar(select(ResolvedIncident)) is not None
            assert db.scalar(select(RootCausePattern)) is not None
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)


def test_incorrect_feedback_does_not_record_resolution() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)

    with Session() as db:
        from app.learning import record_resolution
        from app.models import Feedback, Investigation

        inv = Investigation(summary="unresolved")
        db.add(inv)
        db.flush()
        feedback = Feedback(
            investigation_id=inv.id,
            chosen_root_cause="guess",
            was_correct=False,
            resolution_note="wrong",
        )
        db.add(feedback)
        db.flush()
        record_resolution(db, feedback)
        db.commit()

        assert db.scalar(select(ResolvedIncident)) is None
