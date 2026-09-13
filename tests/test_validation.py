"""Unit tests for payload validation and lead normalization schemas."""

import pytest
from src.schemas.lead import NormalizedLead


def test_normalized_lead_standard_fields():
    payload = {
        "form_id": "5",
        "entry_id": "100",
        "first_name": "Azman",
        "last_name": "Hashim",
        "email": "AZMAN.HASHIM@EXAMPLE.COM ",
        "phone": "+6012-345 6789",
        "company": "Hashim Holdings",
        "message": "Interested in workflow automation.",
        "utm_source": "google",
        "utm_campaign": "search_q3"
    }
    lead = NormalizedLead.from_fluent_forms(payload, lead_id="LD-TEST-001")

    assert lead.lead_id == "LD-TEST-001"
    assert lead.full_name == "Azman Hashim"
    assert lead.email == "azman.hashim@example.com"
    assert lead.phone == "+60123456789"
    assert lead.company == "Hashim Holdings"
    assert lead.utm_source == "google"
    assert lead.utm_campaign == "search_q3"


def test_normalized_lead_nested_names_and_alternate_keys():
    payload = {
        "form_id": "8",
        "names": {"first_name": "Siti", "last_name": "Aishah"},
        "user_email": "siti@creative.my",
        "contact_number": "(019) 876-5432",
        "company_name": "Creative Pixel Studio",
        "inquiry": "Need lead integration pipeline.",
    }
    lead = NormalizedLead.from_fluent_forms(payload, lead_id="LD-TEST-002")

    assert lead.full_name == "Siti Aishah"
    assert lead.email == "siti@creative.my"
    assert lead.company == "Creative Pixel Studio"
    assert lead.message == "Need lead integration pipeline."
    assert lead.phone == "0198765432"


def test_normalized_lead_defaults_and_extras():
    payload = {
        "email": "test.user@company.com",
        "custom_field_budget": "RM 20k",
        "industry": "FinTech"
    }
    lead = NormalizedLead.from_fluent_forms(payload, lead_id="LD-TEST-003")

    assert lead.full_name == "Anonymous Lead"
    assert lead.email == "test.user@company.com"
    assert lead.company == "N/A"
    assert lead.utm_source == "direct"
    assert "custom_field_budget" in lead.raw_metadata
    assert lead.raw_metadata["industry"] == "FinTech"
