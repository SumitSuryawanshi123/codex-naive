from __future__ import annotations

from fastapi.testclient import TestClient

from traceflow.app import create_app


def test_create_ticket_records_service_and_database_spans() -> None:
    client = TestClient(create_app())
    trace_id = "test-create-ticket"

    response = client.post(
        "/api/tickets",
        headers={"X-Trace-Id": trace_id},
        json={
            "subject": "Cannot login",
            "description": "The customer sees an invalid token message.",
            "customer": "Northwind Support",
            "priority": "urgent",
        },
    )

    assert response.status_code == 201
    trace = client.get(f"/api/traces/{trace_id}").json()
    names = {event["name"] for event in trace["events"]}
    kinds = {event["kind"] for event in trace["events"]}

    assert "TicketService.create_ticket" in names
    assert "TicketRepository.create" in names
    assert "db connection" in names
    assert "database" in kinds
    assert trace["status_code"] == 201


def test_trace_analysis_builds_graph_without_openai_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = TestClient(create_app())
    trace_id = "test-analysis-graph"

    response = client.get("/api/tickets", headers={"X-Trace-Id": trace_id})
    assert response.status_code == 200
    trace = client.get(f"/api/traces/{trace_id}").json()

    analysis = client.post(
        "/api/analysis/trace",
        json={
            "trace": trace,
            "query": "why it does not work",
        },
    ).json()

    assert analysis["llm_used"] is False
    assert analysis["nodes"][0]["kind"] == "request"
    assert any(node["kind"] == "service" for node in analysis["nodes"])
    assert analysis["edges"]
    assert analysis["failure_points"]
