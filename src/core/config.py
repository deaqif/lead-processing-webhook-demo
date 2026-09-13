"""Configuration management for Lead Processing Webhook Demo.

Handles environment variables, default settings, and detects live vs mock mode
for outbound adapters (Google Sheets, Email, Telegram).
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Lead Processing & Notification Automation Demo"
    APP_ENV: str = "demo"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    DEBUG: bool = True

    # Webhook Security
    WEBHOOK_SECRET_KEY: Optional[str] = None

    # SQLite Database
    DATABASE_PATH: str = "leads.db"

    # Telegram Bot Settings
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    TELEGRAM_THREAD_ID: Optional[str] = None

    # Google Sheets Settings
    GOOGLE_SERVICE_ACCOUNT_FILE: Optional[str] = None
    GOOGLE_SHEET_ID: Optional[str] = None
    GOOGLE_SHEET_RANGE: str = "Leads!A:H"

    # Email / SMTP Settings
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "notifications@demo.local"
    NOTIFICATION_RECIPIENT_EMAIL: str = "sales-team@demo.local"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def is_telegram_live(self) -> bool:
        """Returns True only if valid non-placeholder Telegram credentials are set."""
        if not self.TELEGRAM_BOT_TOKEN or not self.TELEGRAM_CHAT_ID:
            return False
        placeholders = {"your_token_here", "your_chat_id_here", "xxx", "none", ""}
        return (
            self.TELEGRAM_BOT_TOKEN.lower() not in placeholders
            and self.TELEGRAM_CHAT_ID.lower() not in placeholders
        )

    @property
    def is_sheets_live(self) -> bool:
        """Returns True if Google Sheet ID and service account file are set."""
        if not self.GOOGLE_SHEET_ID or not self.GOOGLE_SERVICE_ACCOUNT_FILE:
            return False
        placeholders = {"your_google_sheet_id_here", "xxx", "none", ""}
        return self.GOOGLE_SHEET_ID.lower() not in placeholders

    @property
    def is_smtp_live(self) -> bool:
        """Returns True if SMTP host and user are set."""
        return bool(self.SMTP_HOST and self.SMTP_HOST.strip())


settings = Settings()
