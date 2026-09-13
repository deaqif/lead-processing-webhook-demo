"""Data models and normalization logic for incoming Fluent Forms Pro payloads."""

import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class FluentFormsPayload(BaseModel):
    """Raw or flexible input payload structure sent by Fluent Forms Pro webhook."""

    form_id: Optional[Any] = None
    entry_id: Optional[Any] = None
    form_title: Optional[str] = None

    # Name fields (can be split or combined)
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    names: Optional[Dict[str, Any]] = None

    # Contact fields
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    message: Optional[str] = None

    # Business qualification / Custom attributes
    service_interest: Optional[str] = None
    estimated_budget: Optional[str] = None

    # Campaign / Tracking metadata
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    source_url: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Optional[str] = None

    # Allow arbitrary extra fields from custom forms
    model_config = ConfigDict(extra="allow")


class NormalizedLead(BaseModel):
    """Clean, strongly-typed internal representation of a validated lead."""

    lead_id: str = Field(description="Unique internal lead identifier (UUID or FormEntry key)")
    form_id: str = Field(default="generic_form")
    entry_id: Optional[str] = None
    form_title: str = Field(default="Inbound Lead Form")

    # Normalized personal / company information
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = "N/A"
    message: Optional[str] = "No message provided"

    # Business attributes
    service_interest: Optional[str] = "General Inquiry"
    estimated_budget: Optional[str] = "Not specified"

    # Marketing Attribution
    utm_source: Optional[str] = "direct"
    utm_medium: Optional[str] = "none"
    utm_campaign: Optional[str] = "organic"
    source_url: Optional[str] = None

    # Timestamps & metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: Optional[str] = None
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("phone", mode="before")
    @classmethod
    def clean_phone(cls, v: Any) -> Optional[str]:
        if not v:
            return None
        s = str(v).strip()
        # Clean unwanted characters but preserve leading +
        cleaned = re.sub(r"[^\d+]", "", s)
        return cleaned if cleaned else None

    @classmethod
    def from_fluent_forms(cls, payload: Dict[str, Any], lead_id: str) -> "NormalizedLead":
        """Transforms variable Fluent Forms raw webhook dictionaries into a NormalizedLead."""

        # 1. Resolve Name
        full_name = "Anonymous Lead"
        if payload.get("full_name"):
            full_name = str(payload["full_name"]).strip()
        elif payload.get("name"):
            full_name = str(payload["name"]).strip()
        else:
            first = payload.get("first_name", "")
            last = payload.get("last_name", "")
            if isinstance(payload.get("names"), dict):
                first = payload["names"].get("first_name", first)
                last = payload["names"].get("last_name", last)
            combined = f"{first} {last}".strip()
            if combined:
                full_name = combined

        # 2. Resolve Email
        raw_email = (
            payload.get("email")
            or payload.get("user_email")
            or payload.get("contact_email")
            or "unspecified@example.com"
        )
        email = str(raw_email).strip().lower()

        # 3. Resolve Phone
        raw_phone = (
            payload.get("phone")
            or payload.get("telephone")
            or payload.get("mobile")
            or payload.get("contact_number")
        )

        # 4. Resolve Company & Message
        company = payload.get("company") or payload.get("company_name") or "N/A"
        message = payload.get("message") or payload.get("inquiry") or payload.get("description") or "No message provided"

        # 5. Form & Entry identifiers
        form_id = str(payload.get("form_id") or "1")
        entry_id = str(payload.get("entry_id")) if payload.get("entry_id") is not None else None
        form_title = payload.get("form_title") or f"Form #{form_id}"

        # 6. Marketing Attribution
        utm_source = payload.get("utm_source") or "direct"
        utm_medium = payload.get("utm_medium") or "none"
        utm_campaign = payload.get("utm_campaign") or "organic"

        # 7. Collect raw metadata excluding common top-level fields
        known_keys = {
            "form_id", "entry_id", "form_title", "name", "full_name",
            "first_name", "last_name", "names", "email", "user_email",
            "phone", "telephone", "mobile", "company", "company_name",
            "message", "inquiry", "description", "service_interest",
            "estimated_budget", "utm_source", "utm_medium", "utm_campaign",
            "source_url", "ip_address", "created_at"
        }
        extra_meta = {k: v for k, v in payload.items() if k not in known_keys}

        return cls(
            lead_id=lead_id,
            form_id=form_id,
            entry_id=entry_id,
            form_title=form_title,
            full_name=full_name,
            email=email,
            phone=str(raw_phone) if raw_phone else None,
            company=str(company),
            message=str(message),
            service_interest=payload.get("service_interest") or "General Inquiry",
            estimated_budget=payload.get("estimated_budget") or "Not specified",
            utm_source=str(utm_source),
            utm_medium=str(utm_medium),
            utm_campaign=str(utm_campaign),
            source_url=payload.get("source_url"),
            ip_address=payload.get("ip_address"),
            raw_metadata=extra_meta,
        )


class PipelineResult(BaseModel):
    """Result status of the lead processing automation pipeline."""

    success: bool
    lead_id: str
    message: str
    database_saved: bool
    google_sheets_synced: bool
    email_dispatched: bool
    telegram_notified: bool
    execution_time_ms: float
    details: Dict[str, Any] = Field(default_factory=dict)
