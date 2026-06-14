from __future__ import annotations

import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from debug_module.database import Base
from debug_module.evidence.store import append_artifact
from debug_module.ingestion.configs import ingest_config_text
from debug_module.ingestion.har import ingest_har_text
from debug_module.ingestion.otel import ingest_otel_text
from debug_module.orchestrator import create_investigation, step_investigation
from debug_module.report import investigation_report


def test_config_ingestion_marks_configuration_signal() -> None:
    candidates = ingest_config_text("DATABASE_URL=null\nFEATURE_FLAG=true")

    assert candidates[0].type == "config"
    assert "configuration" in candidates[0].signal_tags
    assert "error" in candidates[0].signal_tags


def test_har_ingestion_marks_slow_external_service() -> None:
    raw = json.dumps(
        {
            "log": {
                "entries": [
                    {
                        "request": {"url": "https://api.stripe.com/v1/charges"},
                        "response": {"status": 504},
                        "time": 3200,
                    }
                ]
            }
        }
    )

    candidates = ingest_har_text(raw)

    assert candidates[0].type == "har"
    assert {"external_service", "timeout", "dependency"} <= set(candidates[0].signal_tags)


def test_otel_ingestion_marks_error_span() -> None:
    raw = json.dumps({"spans": [{"trace_id": "abc", "name": "checkout.charge", "status": {"code": "ERROR"}}]})

    candidates = ingest_otel_text(raw)

    assert candidates[0].type == "otel_trace"
    assert "trace_id=abc" in candidates[0].normalized_text


def test_report_includes_timeline_and_har_classifies_external_service() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    har = json.dumps(
        {
            "log": {
                "entries": [
                    {
                        "request": {"url": "https://api.stripe.com/v1/charges"},
                        "response": {"status": 504},
                        "time": 3200,
                    }
                ]
            }
        }
    )

    with Session() as db:
        inv = create_investigation(db, budget=2, summary="checkout external call failed")
        append_artifact(db, inv.id, "log", "2026-06-14T08:15:00Z INFO checkout started", {"test": True})
        append_artifact(db, inv.id, "har", har, {"test": True})
        step_investigation(db, inv.id)
        report = investigation_report(db, inv.id)

    assert report["timeline"]
    assert report["timeline"][0]["timestamp"] == "2026-06-14T08:15:00Z"
    assert report["ranked_causes"][0]["category"] == "EXTERNAL_SERVICE"
