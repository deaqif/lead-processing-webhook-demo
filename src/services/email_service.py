"""Email notification adapter for team alerts and lead confirmation."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict
from ..core.config import settings
from ..core.logger import logger
from ..schemas.lead import NormalizedLead


class EmailService:
    """Dispatches email notifications to internal teams and auto-responder confirmations."""

    def __init__(self):
        self.is_live = settings.is_smtp_live
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.recipient_email = settings.NOTIFICATION_RECIPIENT_EMAIL

    def build_team_alert_html(self, lead: NormalizedLead) -> str:
        """Constructs a responsive HTML notification for internal sales / support teams."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1e293b; background-color: #f8fafc; padding: 24px;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden;">
                <div style="background: #0f172a; padding: 20px 24px; color: #ffffff;">
                    <h2 style="margin: 0; font-size: 18px; font-weight: 600;">⚡ New Inbound Lead Captured</h2>
                    <p style="margin: 4px 0 0 0; font-size: 13px; color: #94a3b8;">Source: {lead.form_title} | ID: {lead.lead_id}</p>
                </div>
                <div style="padding: 24px;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                        <tr><td style="padding: 8px 0; color: #64748b; width: 140px;">Full Name:</td><td style="font-weight: 600;">{lead.full_name}</td></tr>
                        <tr><td style="padding: 8px 0; color: #64748b;">Email:</td><td><a href="mailto:{lead.email}" style="color: #2563eb;">{lead.email}</a></td></tr>
                        <tr><td style="padding: 8px 0; color: #64748b;">Phone:</td><td>{lead.phone or 'N/A'}</td></tr>
                        <tr><td style="padding: 8px 0; color: #64748b;">Company:</td><td>{lead.company or 'N/A'}</td></tr>
                        <tr><td style="padding: 8px 0; color: #64748b;">Service Interest:</td><td><span style="background: #eff6ff; color: #1d4ed8; padding: 2px 8px; border-radius: 4px;">{lead.service_interest}</span></td></tr>
                        <tr><td style="padding: 8px 0; color: #64748b;">Budget:</td><td>{lead.estimated_budget}</td></tr>
                        <tr><td style="padding: 8px 0; color: #64748b;">Attribution:</td><td><code>{lead.utm_source} / {lead.utm_campaign}</code></td></tr>
                    </table>
                    <div style="margin-top: 16px; padding: 14px; background: #f1f5f9; border-radius: 6px;">
                        <div style="font-size: 12px; font-weight: 600; color: #475569; text-transform: uppercase; margin-bottom: 6px;">Message / Requirement:</div>
                        <p style="margin: 0; font-size: 14px; color: #334155;">{lead.message}</p>
                    </div>
                </div>
                <div style="background: #f8fafc; padding: 12px 24px; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; text-align: center;">
                    Lead Processing & Notification Automation System
                </div>
            </div>
        </body>
        </html>
        """

    async def send_team_alert(self, lead: NormalizedLead) -> Dict[str, Any]:
        """Dispatches email alert to team via SMTP or simulated Mock output."""
        subject = f"🎯 New Lead: {lead.full_name} ({lead.company or 'Direct Inquiry'})"
        html_content = self.build_team_alert_html(lead)

        if not self.is_live:
            logger.info(
                "[MOCK EMAIL] Team alert rendered successfully. To: %s | Subject: %s",
                self.recipient_email,
                subject,
            )
            return {
                "status": "success",
                "mode": "mock",
                "recipient": self.recipient_email,
                "subject": subject,
                "simulated": True,
            }

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = self.recipient_email
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, [self.recipient_email], msg.as_string())

            logger.info("[LIVE EMAIL] Successfully sent alert email to %s", self.recipient_email)
            return {"status": "success", "mode": "live", "recipient": self.recipient_email}
        except Exception as e:
            logger.error("Failed to send alert email: %s", e)
            return {"status": "error", "error": str(e), "mode": "live"}
