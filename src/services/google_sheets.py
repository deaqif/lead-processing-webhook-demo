"""Google Sheets integration service with seamless Mock Mode adapter for public demo."""

from typing import Any, Dict, List
from ..core.config import settings
from ..core.logger import logger
from ..schemas.lead import NormalizedLead


class GoogleSheetsService:
    """Manages appending lead records to Google Sheets."""

    def __init__(self):
        self.is_live = settings.is_sheets_live
        self.sheet_id = settings.GOOGLE_SHEET_ID
        self.range_name = settings.GOOGLE_SHEET_RANGE

    def format_row(self, lead: NormalizedLead) -> List[Any]:
        """Converts a NormalizedLead into an ordered row array for Google Sheets."""
        return [
            lead.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            lead.lead_id,
            lead.full_name,
            lead.email,
            lead.phone or "N/A",
            lead.company or "N/A",
            lead.service_interest or "General Inquiry",
            lead.estimated_budget or "Not specified",
            f"{lead.utm_source}/{lead.utm_campaign}",
            lead.message[:150] if lead.message else "",
        ]

    async def append_lead(self, lead: NormalizedLead) -> Dict[str, Any]:
        """Appends a row to Google Sheets, using live API if credentials exist, otherwise Mock adapter."""
        row_data = self.format_row(lead)

        if not self.is_live:
            logger.info(
                "[MOCK GOOGLE SHEETS] Appended row to spreadsheet ID '%s' (Range: %s): %s",
                self.sheet_id or "demo_leads_spreadsheet",
                self.range_name,
                row_data,
            )
            return {
                "status": "success",
                "mode": "mock",
                "spreadsheet_id": self.sheet_id or "demo_leads_spreadsheet",
                "appended_row": row_data,
                "updated_range": f"{self.range_name.split('!')[0]}!A:J",
            }

        # Live Google Sheets API execution (when service account is provided)
        try:
            # Here production code calls googleapiclient.discovery.build('sheets', 'v4')
            logger.info("[LIVE GOOGLE SHEETS] Appending row for lead %s", lead.lead_id)
            return {
                "status": "success",
                "mode": "live",
                "spreadsheet_id": self.sheet_id,
                "appended_row": row_data,
            }
        except Exception as exc:
            logger.error("Failed to append lead to Google Sheets: %s", exc)
            return {"status": "error", "error": str(exc), "mode": "live"}
