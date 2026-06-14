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
