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


def test_debug_fix_detail_endpoint_returns_rich_payload() -> None:
    client = TestClient(create_app())
    trace = {
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
                "name": "PaymentService.charge",
                "kind": "service",
                "status": "error",
                "error": "TimeoutError: timeout calling Stripe after 30000ms",
                "duration_ms": 30000,
            }
        ],
    }

    response = client.post(
        "/api/debug/fix/detail",
        json={
            "request": {"method": "POST", "path": "/api/payments"},
            "response": {"status_code": 500, "body": "timeout calling Stripe after 30000ms"},
            "trace": trace,
            "query": "why did payment fail",
            "analysis": {
                "summary": "Stripe timeout at payment service",
                "failure_points": [
                    {
                        "node_id": "PaymentService.charge",
                        "confidence": "high",
                        "reason": "External provider call exceeded timeout budget",
                    }
                ],
                "llm_used": False,
                "nodes": [{"id": "PaymentService.charge"}],
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["failure"]["summary"].startswith("POST /api/payments failed")
    assert body["failure"]["events"]
    assert body["top_cause"]["evidence_score"] > 0
    assert body["ranked_causes"]
    assert body["remediation"]
    assert body["recommended_next_steps"]
    assert body["graph_context"]["failure_points"]
    assert body["fix_zip_available"] is True
    assert body["query"] == "why did payment fail"
