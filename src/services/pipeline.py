"""Lead processing pipeline orchestrator."""

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from ..core.logger import logger
from ..schemas.lead import NormalizedLead, PipelineResult
from .email_service import EmailService
from .google_sheets import GoogleSheetsService
from .storage import LeadStorageService
from .telegram_service import TelegramService


class LeadPipeline:
    """Coordinates validation, deduplication, storage, and outbound notification integrations."""

    def __init__(
        self,
        storage: Optional[LeadStorageService] = None,
        sheets: Optional[GoogleSheetsService] = None,
        email: Optional[EmailService] = None,
        telegram: Optional[TelegramService] = None,
    ):
        self.storage = storage or LeadStorageService()
        self.sheets = sheets or GoogleSheetsService()
        self.email = email or EmailService()
        self.telegram = telegram or TelegramService()

    def generate_lead_id(self, form_id: Any, entry_id: Optional[Any] = None) -> str:
        """Generates a business-readable tracking lead identifier."""
        today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        if entry_id:
            return f"LD-{today_str}-F{form_id}-E{entry_id}"
        random_suffix = uuid.uuid4().hex[:6].upper()
        return f"LD-{today_str}-{random_suffix}"

    async def process_lead(self, raw_payload: Dict[str, Any]) -> PipelineResult:
        """Executes the complete lead automation flow."""
        start_time = time.perf_counter()
        logger.info("Pipeline triggered with payload keys: %s", list(raw_payload.keys()))

        # 1. Generate unique lead ID
        form_id = raw_payload.get("form_id") or "1"
        entry_id = raw_payload.get("entry_id")
        lead_id = self.generate_lead_id(form_id, entry_id)

        # 2. Normalize and validate data
        try:
            lead = NormalizedLead.from_fluent_forms(raw_payload, lead_id=lead_id)
        except Exception as val_err:
            logger.error("Validation error normalizing lead: %s", val_err)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return PipelineResult(
                success=False,
                lead_id=lead_id,
                message=f"Validation failed: {str(val_err)}",
                database_saved=False,
                google_sheets_synced=False,
                email_dispatched=False,
                telegram_notified=False,
                execution_time_ms=elapsed_ms,
            )

        # 3. Deduplication check
        if self.storage.is_duplicate(
            email=lead.email, form_id=lead.form_id, entry_id=lead.entry_id
        ):
            logger.warning("Duplicate lead detected for email: %s, form: %s", lead.email, lead.form_id)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return PipelineResult(
                success=False,
                lead_id=lead_id,
                message="Duplicate submission suppressed (rate limit / duplicate entry)",
                database_saved=False,
                google_sheets_synced=False,
                email_dispatched=False,
                telegram_notified=False,
                execution_time_ms=elapsed_ms,
                details={"duplicate": True, "email": lead.email},
            )

        # 4. Outbound Integrations
        # Google Sheets
        sheets_res = await self.sheets.append_lead(lead)
        sheets_ok = sheets_res.get("status") == "success"

        # Email
        email_res = await self.email.send_team_alert(lead)
        email_ok = email_res.get("status") == "success"

        # Telegram
        telegram_res = await self.telegram.send_lead_notification(lead)
        telegram_ok = telegram_res.get("status") == "success"

        # 5. SQLite Persistence
        db_saved = self.storage.save_lead(
            lead=lead,
            google_sheets_synced=sheets_ok,
            email_dispatched=email_ok,
            telegram_notified=telegram_ok,
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            "Pipeline completed for lead %s in %s ms (DB: %s, Sheets: %s, Email: %s, Telegram: %s)",
            lead_id, elapsed_ms, db_saved, sheets_ok, email_ok, telegram_ok
        )

        return PipelineResult(
            success=True,
            lead_id=lead.lead_id,
            message="Lead processed and dispatched across all channels successfully.",
            database_saved=db_saved,
            google_sheets_synced=sheets_ok,
            email_dispatched=email_ok,
            telegram_notified=telegram_ok,
            execution_time_ms=elapsed_ms,
            details={
                "lead_summary": {
                    "name": lead.full_name,
                    "email": lead.email,
                    "company": lead.company,
                    "service_interest": lead.service_interest,
                },
                "integrations": {
                    "google_sheets": sheets_res,
                    "email": email_res,
                    "telegram": telegram_res,
                },
            },
        )
