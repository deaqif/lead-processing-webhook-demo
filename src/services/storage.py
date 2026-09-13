"""SQLite storage repository for persisting and tracking processed leads."""

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
from ..core.logger import logger
from ..schemas.lead import NormalizedLead


class LeadStorageService:
    """Handles local SQLite database persistence, deduplication, and lead retrieval."""

    def __init__(self, db_path: str = "leads.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Creates the leads table and indexes if not already present."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    lead_id TEXT PRIMARY KEY,
                    form_id TEXT NOT NULL,
                    entry_id TEXT,
                    form_title TEXT,
                    full_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT,
                    company TEXT,
                    message TEXT,
                    service_interest TEXT,
                    estimated_budget TEXT,
                    utm_source TEXT,
                    utm_medium TEXT,
                    utm_campaign TEXT,
                    source_url TEXT,
                    ip_address TEXT,
                    raw_metadata TEXT,
                    status TEXT DEFAULT 'PROCESSED',
                    google_sheets_synced INTEGER DEFAULT 0,
                    email_dispatched INTEGER DEFAULT 0,
                    telegram_notified INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at);")
            conn.commit()
            logger.info("Database initialized successfully at %s", self.db_path)

    def is_duplicate(self, email: str, form_id: str, entry_id: Optional[str] = None) -> bool:
        """Detects if an entry was already captured recently or has an identical entry_id."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if entry_id:
                cursor.execute(
                    "SELECT lead_id FROM leads WHERE form_id = ? AND entry_id = ?",
                    (form_id, entry_id),
                )
                if cursor.fetchone():
                    return True
            # Check duplicate email in same form submitted within last 60 seconds
            cursor.execute(
                """
                SELECT lead_id FROM leads
                WHERE email = ? AND form_id = ?
                AND datetime(created_at) >= datetime('now', '-60 seconds')
                """,
                (email, form_id),
            )
            return cursor.fetchone() is not None

    def save_lead(
        self,
        lead: NormalizedLead,
        google_sheets_synced: bool = False,
        email_dispatched: bool = False,
        telegram_notified: bool = False,
    ) -> bool:
        """Inserts a new normalized lead record into SQLite."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO leads (
                        lead_id, form_id, entry_id, form_title, full_name,
                        email, phone, company, message, service_interest,
                        estimated_budget, utm_source, utm_medium, utm_campaign,
                        source_url, ip_address, raw_metadata, status,
                        google_sheets_synced, email_dispatched, telegram_notified, created_at
                    ) VALUES (
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?
                    )
                    """,
                    (
                        lead.lead_id,
                        lead.form_id,
                        lead.entry_id,
                        lead.form_title,
                        lead.full_name,
                        lead.email,
                        lead.phone,
                        lead.company,
                        lead.message,
                        lead.service_interest,
                        lead.estimated_budget,
                        lead.utm_source,
                        lead.utm_medium,
                        lead.utm_campaign,
                        lead.source_url,
                        lead.ip_address,
                        json.dumps(lead.raw_metadata),
                        "PROCESSED",
                        1 if google_sheets_synced else 0,
                        1 if email_dispatched else 0,
                        1 if telegram_notified else 0,
                        lead.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                )
                conn.commit()
                logger.info("Lead %s persisted to SQLite database", lead.lead_id)
                return True
        except Exception as e:
            logger.error("Failed to save lead %s to database: %s", lead.lead_id, e)
            return False

    def get_lead(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single lead by its lead_id."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM leads WHERE lead_id = ?", (lead_id,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                if data.get("raw_metadata"):
                    try:
                        data["raw_metadata"] = json.loads(data["raw_metadata"])
                    except Exception:
                        pass
                return data
            return None

    def list_leads(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns the most recent leads ordered by creation date."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM leads ORDER BY created_at DESC LIMIT ?", (limit,)
            )
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                if item.get("raw_metadata"):
                    try:
                        item["raw_metadata"] = json.loads(item["raw_metadata"])
                    except Exception:
                        pass
                results.append(item)
            return results
