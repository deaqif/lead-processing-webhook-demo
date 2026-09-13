"""End-to-end integration tests for FastAPI Webhook endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "adapters" in data


def test_demo_ui_serves_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "Lead Processing &amp; Notification Automation" in response.text or "Lead Processing & Notification Automation" in response.text


import uuid

def test_webhook_pipeline_success():
    unique_id = uuid.uuid4().hex[:6]
    payload = {
        "form_id": "4",
        "entry_id": f"entry_{unique_id}",
        "form_title": "Enterprise Inquiry",
        "first_name": "Najib",
        "last_name": "Razak",
        "email": f"lead_{unique_id}@example.com",
        "phone": "+60189912345",
        "company": "Puncak Jaya",
        "service_interest": "Workflow & API Automation",
        "message": "Testing webhook integration pipeline.",
        "utm_source": "unit_test"
    }
    response = client.post(
        "/api/v1/webhook/fluent-forms",
        json=payload,
        headers={"X-Webhook-Secret": "demo_secret_token_12345"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["database_saved"] is True
    assert data["google_sheets_synced"] is True
    assert data["email_dispatched"] is True
    assert data["telegram_notified"] is True
    assert data["lead_id"].startswith("LD-")


def test_leads_list_endpoint():
    response = client.get("/api/v1/leads")
    assert response.status_code == 200
    leads = response.json()
    assert isinstance(leads, list)
    assert len(leads) >= 1
    assert "email" in leads[0]


def test_webhook_duplicate_suppression():
    unique_id = uuid.uuid4().hex[:6]
    payload = {
        "form_id": f"form_{unique_id}",
        "entry_id": f"entry_{unique_id}",
        "first_name": "Duplicate",
        "last_name": "User",
        "email": f"dup_{unique_id}@example.com",
        "phone": "+60129998877",
    }
    # First post succeeds
    res1 = client.post("/api/v1/webhook/fluent-forms", json=payload)
    assert res1.status_code == 200
    assert res1.json()["success"] is True

    # Immediate second post with identical form_id & entry_id gets suppressed
    res2 = client.post("/api/v1/webhook/fluent-forms", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["success"] is False
    assert "Duplicate submission suppressed" in data2["message"]


def test_webhook_malformed_payload():
    response = client.post(
        "/api/v1/webhook/fluent-forms",
        content="not a json string",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 400
