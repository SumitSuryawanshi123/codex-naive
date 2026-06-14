from __future__ import annotations

from fastapi.testclient import TestClient

from traceflow.app import create_app


def test_debug_fix_endpoint_analyzes_failed_trace() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/debug/fix",
        json={
            "request": {"method": "POST", "path": "/api/payments"},
            "response": {"status_code": 500, "body": "timeout calling Stripe after 30000ms"},
            "trace": {
                "trace_id": "failed-payment",
                "method": "POST",
                "path": "/api/payments",
                "title": "POST /api/payments",
                "status_code": 500,
                "outcome": "error",
                "error": "TimeoutError: timeout calling Stripe after 30000ms",
                "events": [
                    {
                        "event_id": "event-1",
                        "trace_id": "failed-payment",
                        "parent_id": None,
                        "name": "PaymentService.charge",
                        "kind": "service",
                        "detail": "calling Stripe",
                        "depth": 0,
                        "started_at": "2026-06-14T08:15:01Z",
                        "ended_at": "2026-06-14T08:15:31Z",
                        "duration_ms": 30000,
                        "status": "error",
                        "error": "TimeoutError: timeout calling Stripe after 30000ms",
                    }
                ],
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ranked_causes"]
    assert body["remediation_suggestions"]
    assert body["ranked_causes"][0]["evidence_score"] > 0


def test_debug_fix_endpoint_rejects_successful_trace() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/debug/fix",
        json={
            "response": {"status_code": 200, "body": "{}"},
            "trace": {
                "trace_id": "ok",
                "method": "GET",
                "path": "/health",
                "status_code": 200,
                "outcome": "ok",
                "events": [],
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "No failed trace to analyze"
