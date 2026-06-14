from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.initialization import initialize_database
from app.main import app


@pytest.fixture()
def crm_client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "crm_test.db"
    monkeypatch.setenv("CRM_DATABASE_PATH", str(db_path))
    get_settings.cache_clear()
    initialize_database()
    with TestClient(app) as client:
        yield client
    get_settings.cache_clear()


def test_export_invoice_demo_fails_without_auth(crm_client: TestClient) -> None:
    response = crm_client.post("/api/tickets/1/export-invoice", json={})
    assert response.status_code == 400
    assert "missing bearer token" in response.json()["detail"]


def test_export_invoice_demo_fails_without_scope(crm_client: TestClient) -> None:
    response = crm_client.post(
        "/api/tickets/1/export-invoice",
        json={"authorization": "bearer demo-token-without-scope"},
    )
    assert response.status_code == 400
    assert "missing scope export:admin" in response.json()["detail"]


def test_export_invoice_demo_fails_on_missing_billing_profile(crm_client: TestClient) -> None:
    response = crm_client.post(
        "/api/tickets/1/export-invoice",
        json={"authorization": "bearer export:admin demo-token"},
    )
    assert response.status_code == 500
    assert "billing_profile" in response.text


def test_export_invoice_demo_missing_config_scenario(crm_client: TestClient) -> None:
    response = crm_client.post(
        "/api/tickets/1/export-invoice?scenario=missing_config",
        json={"authorization": "bearer export:admin demo-token"},
    )
    assert response.status_code == 500
    assert "BILLING_EXPORT_SECRET" in response.text


def test_export_invoice_demo_billing_timeout_scenario(crm_client: TestClient) -> None:
    response = crm_client.post(
        "/api/tickets/1/export-invoice?scenario=billing_timeout",
        json={"authorization": "bearer export:admin demo-token"},
    )
    assert response.status_code == 500
    assert "timeout calling Stripe" in response.text
