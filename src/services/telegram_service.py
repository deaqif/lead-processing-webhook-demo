"""Telegram Bot notification service with live Bot API dispatch and mock fallback."""

from typing import Any, Dict
import httpx
from ..core.config import settings
from ..core.logger import logger
from ..schemas.lead import NormalizedLead


class TelegramService:
    """Dispatches instant structured lead notifications to a Telegram chat or channel."""

    def __init__(self):
        self.is_live = settings.is_telegram_live
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.thread_id = settings.TELEGRAM_THREAD_ID

    def format_lead_message(self, lead: NormalizedLead) -> str:
        """Formats the lead data into an aesthetic Telegram Markdown notification."""
        phone_display = lead.phone if lead.phone else "Not provided"
        company_display = lead.company if lead.company else "N/A"
        budget_display = lead.estimated_budget if lead.estimated_budget else "Not specified"
        message_display = lead.message[:250] + ("..." if len(lead.message) > 250 else "")

        return (
            f"🚀 *NEW INBOUND LEAD RECEIVED*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 *Form:* `{lead.form_title}`\n"
            f"🆔 *Lead ID:* `{lead.lead_id}`\n"
            f"👤 *Name:* {lead.full_name}\n"
            f"📧 *Email:* {lead.email}\n"
            f"📱 *Phone:* {phone_display}\n"
            f"🏢 *Company:* {company_display}\n"
            f"🎯 *Interest:* {lead.service_interest}\n"
            f"💰 *Budget:* {budget_display}\n"
            f"📊 *Campaign:* `{lead.utm_source}` / `{lead.utm_campaign}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💬 *Inquiry Message:*\n_{message_display}_\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🕒 _{lead.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}_"
        )

    async def send_lead_notification(self, lead: NormalizedLead) -> Dict[str, Any]:
        """Dispatches notification via Telegram Bot API or outputs formatted mock message."""
        text_message = self.format_lead_message(lead)

        if not self.is_live:
            logger.info(
                "\n==================== [MOCK TELEGRAM NOTIFICATION] ====================\n"
                "%s\n"
                "=======================================================================",
                text_message,
            )
            return {
                "status": "success",
                "mode": "mock",
                "chat_id": self.chat_id or "mock_chat_id",
                "message_preview": text_message,
                "simulated": True,
            }

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload: Dict[str, Any] = {
            "chat_id": self.chat_id,
            "text": text_message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        if self.thread_id:
            payload["message_thread_id"] = self.thread_id

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                resp_data = response.json()
                if response.status_code == 200 and resp_data.get("ok"):
                    logger.info("[LIVE TELEGRAM] Successfully alerted Telegram chat %s", self.chat_id)
                    return {"status": "success", "mode": "live", "telegram_response": resp_data}
                else:
                    logger.warning("[LIVE TELEGRAM] Telegram API error: %s", resp_data)
                    return {"status": "error", "mode": "live", "error": resp_data}
        except Exception as err:
            logger.error("Failed to dispatch Telegram message: %s", err)
            return {"status": "error", "mode": "live", "error": str(err)}
