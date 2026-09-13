"""Main FastAPI Application and Webhook Endpoint."""

from contextlib import asynccontextmanager
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from .core.config import settings
from .core.logger import logger
from .schemas.lead import PipelineResult
from .services.pipeline import LeadPipeline
from .services.storage import LeadStorageService

pipeline = LeadPipeline()
storage = LeadStorageService()

DEMO_HTML_PATH = Path(__file__).parent / "static" / "demo_form.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=================================================================")
    logger.info("⚡ Starting: %s", settings.APP_NAME)
    logger.info("⚡ Environment: %s", settings.APP_ENV)
    logger.info(
        "⚡ Mode Status: Telegram Live: %s | Sheets Live: %s | SMTP Live: %s",
        settings.is_telegram_live,
        settings.is_sheets_live,
        settings.is_smtp_live,
    )
    logger.info("⚡ Interactive UI: http://%s:%s", settings.APP_HOST, settings.APP_PORT)
    logger.info("⚡ Swagger Docs:   http://%s:%s/docs", settings.APP_HOST, settings.APP_PORT)
    logger.info("=================================================================")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Production-inspired Lead Processing & Notification Automation Webhook Service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse, tags=["Demo Interface"])
async def serve_demo_form():
    """Serves the interactive demo web form to test webhook submissions."""
    if DEMO_HTML_PATH.exists():
        return HTMLResponse(content=DEMO_HTML_PATH.read_text(encoding="utf-8"))
    return HTMLResponse("<h2>Demo form HTML not found</h2>", status_code=404)


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for container / server monitoring."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
        "adapters": {
            "telegram": "live" if settings.is_telegram_live else "mock",
            "google_sheets": "live" if settings.is_sheets_live else "mock",
            "email": "live" if settings.is_smtp_live else "mock",
        },
    }


@app.post(
    "/api/v1/webhook/fluent-forms",
    response_model=PipelineResult,
    status_code=status.HTTP_200_OK,
    tags=["Webhooks"],
)
async def handle_fluent_forms_webhook(
    request: Request,
    x_webhook_secret: Optional[str] = Header(default=None, alias="X-Webhook-Secret"),
):
    """Primary webhook receiver for incoming Fluent Forms Pro submissions.

    Accepts raw JSON, validates and normalizes lead data, saves to SQLite,
    appends to Google Sheets, and dispatches Email & Telegram alerts.
    """
    # 1. Verify Secret Key if configured and not running in pure demo mode
    if settings.WEBHOOK_SECRET_KEY and settings.APP_ENV == "production":
        if x_webhook_secret != settings.WEBHOOK_SECRET_KEY:
            logger.warning("Rejected webhook submission: Invalid or missing X-Webhook-Secret")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized: Invalid webhook secret token.",
            )

    # 2. Parse JSON payload
    try:
        payload = await request.json()
    except Exception as parse_err:
        logger.error("Failed to parse incoming webhook JSON: %s", parse_err)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed JSON payload: {str(parse_err)}",
        )

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Payload must be a JSON object",
        )

    # 3. Process via lead pipeline
    result = await pipeline.process_lead(payload)
    return result


@app.get("/api/v1/leads", response_model=List[Dict[str, Any]], tags=["Leads Repository"])
async def list_stored_leads(limit: int = 50):
    """Returns stored leads from the SQLite database."""
    return storage.list_leads(limit=limit)


@app.get("/api/v1/leads/{lead_id}", tags=["Leads Repository"])
async def get_lead_details(lead_id: str):
    """Retrieves details of a specific processed lead."""
    lead = storage.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead with ID {lead_id} not found")
    return lead


def start():
    """CLI launcher for local development."""
    uvicorn.run(
        "src.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    start()
