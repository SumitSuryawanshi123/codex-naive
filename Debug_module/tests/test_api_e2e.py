from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from debug_module.database import Base, get_db
from debug_module.main import app


@pytest.fixture()
def client() -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
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
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)


def test_http_investigation_flow_ranks_cited_external_service_cause(client: TestClient) -> None:
    created = client.post(
        "/investigations",
        json={"budget": 3, "summary": "Checkout fails while charging cards"},
    )
    assert created.status_code == 200
    investigation = created.json()
    assert investigation["status"] == "in_progress"
    assert investigation["budget"] == 3

    evidence = client.post(
        f"/investigations/{investigation['id']}/evidence",
        json={
            "type": "log",
            "raw_text": (
                "2026-06-14T08:15:01Z ERROR checkout charge failed: "
                "timeout calling Stripe after 30000ms request_id=ch_123 token=sk_test_supersecret\n"
                "2026-06-14T08:15:02Z WARN retry exhausted for external payment provider"
            ),
            "source_meta": {"fixture": "timeout_stripe"},
        },
    )
    assert evidence.status_code == 200
    assert evidence.json()["artifact_id"] > 0

    stepped = client.post(f"/investigations/{investigation['id']}/step")
    assert stepped.status_code == 200
    assert stepped.json()["step_count"] == 1
    assert stepped.json()["status"] in {"complete", "ranked"}

    report = client.get(f"/investigations/{investigation['id']}/report")
    assert report.status_code == 200
    body = report.json()
    assert body["ranked_causes"][0]["category"] == "EXTERNAL_SERVICE"
    assert body["ranked_causes"][0]["evidence_score"] >= 7
    assert body["ranked_causes"][0]["signals"]
    assert body["ranked_causes"][0]["signals"][0]["verified"] is True
    assert "sk_test_supersecret" not in body["ranked_causes"][0]["signals"][0]["text"]

    feedback = client.post(
        f"/investigations/{investigation['id']}/feedback",
        json={
            "chosen_root_cause": "Stripe calls are timing out",
            "was_correct": True,
            "resolution_note": "Provider latency confirmed.",
        },
    )
    assert feedback.status_code == 200
    assert feedback.json() == {"ok": True}


def test_http_flow_handles_missing_investigations_and_insufficient_evidence(client: TestClient) -> None:
    missing_evidence = client.post(
        "/investigations/404/evidence",
        json={"type": "log", "raw_text": "ERROR no such investigation"},
    )
    assert missing_evidence.status_code == 404

    created = client.post("/investigations", json={"budget": 1, "summary": "empty case"})
    investigation_id = created.json()["id"]

    stepped = client.post(f"/investigations/{investigation_id}/step")
    assert stepped.status_code == 200
    assert stepped.json()["status"] == "evidence_insufficient"

    missing_step = client.post("/investigations/404/step")
    assert missing_step.status_code == 404

    missing_report = client.get("/investigations/404/report")
    assert missing_report.status_code == 404
