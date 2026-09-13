"""Unit tests for services: SQLite storage, Google Sheets, Email, Telegram adapters."""

import os
import pytest
from src.schemas.lead import NormalizedLead
from src.services.email_service import EmailService
from src.services.google_sheets import GoogleSheetsService
from src.services.storage import LeadStorageService
from src.services.telegram_service import TelegramService


@pytest.fixture
def temp_storage(tmp_path):
    db_file = tmp_path / "test_leads.db"
    return LeadStorageService(db_path=str(db_file))


@pytest.fixture
def sample_lead():
    payload = {
        "form_id": "1",
        "entry_id": "99",
        "first_name": "Farhan",
        "last_name": "Aziz",
        "email": "farhan@apex.com",
        "phone": "+60123334455",
        "company": "Apex Corp",
        "message": "Automate our lead intake",
        "service_interest": "Workflow & API Automation",
        "estimated_budget": "RM 15,000 - RM 30,000",
    }
    return NormalizedLead.from_fluent_forms(payload, lead_id="LD-TEST-100")


def test_storage_save_and_retrieve(temp_storage, sample_lead):
    saved = temp_storage.save_lead(sample_lead, google_sheets_synced=True, email_dispatched=True, telegram_notified=True)
    assert saved is True

    record = temp_storage.get_lead(sample_lead.lead_id)
    assert record is not None
    assert record["email"] == "farhan@apex.com"
    assert record["full_name"] == "Farhan Aziz"
    assert record["google_sheets_synced"] == 1


def test_storage_deduplication(temp_storage, sample_lead):
    temp_storage.save_lead(sample_lead)
    # Same entry_id should trigger duplicate
    is_dup = temp_storage.is_duplicate(email="farhan@apex.com", form_id="1", entry_id="99")
    assert is_dup is True

    # Different form_id and entry_id
    is_diff = temp_storage.is_duplicate(email="other@apex.com", form_id="2", entry_id="101")
    assert is_diff is False


import asyncio

def test_google_sheets_mock_adapter(sample_lead):
    sheets_service = GoogleSheetsService()
    res = asyncio.run(sheets_service.append_lead(sample_lead))
    assert res["status"] == "success"
    assert len(res["appended_row"]) == 10
    assert res["appended_row"][2] == sample_lead.full_name


def test_email_mock_adapter(sample_lead):
    email_service = EmailService()
    res = asyncio.run(email_service.send_team_alert(sample_lead))
    assert res["status"] == "success"
    assert res["simulated"] is True


def test_telegram_mock_adapter(sample_lead):
    tg_service = TelegramService()
    res = asyncio.run(tg_service.send_lead_notification(sample_lead))
    assert res["status"] == "success"
    assert res["simulated"] is True
    assert sample_lead.lead_id in res["message_preview"]
