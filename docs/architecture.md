# System Architecture

## Overview
The **Lead Processing & Notification Automation System** is an event-driven webhook processing service designed to decouple public lead-capture forms from internal operations tooling (CRM, spreadsheets, and notification bots).

By routing inbound webhook traffic through this specialized processing service, businesses achieve:
1. **Resilience & Reliability:** If Google Sheets API or Telegram rate-limits temporarily, lead submissions are safely captured in SQLite database first and never lost.
2. **Data Cleansing & Normalization:** Irregular input fields from web forms are cleansed, deduplicated, and mapped to standardized schema models before reaching sales databases.
3. **Multi-Channel Distribution:** A single form submission fans out simultaneously to spreadsheets, email recipients, and real-time messaging channels (Telegram).

---

## Architectural Diagram

```mermaid
flowchart TD
    subgraph ClientLayer["1. Inbound Ingestion Layer"]
        FF["WordPress Fluent Forms Pro Webhook"] -->|HTTP POST JSON| EP["Webhook Receiver (/api/v1/webhook/fluent-forms)"]
        UI["Interactive Demo Web Form"] -->|HTTP POST JSON| EP
        CLI["CLI Simulation Tool"] -->|HTTP POST JSON| EP
    end

    subgraph SecurityLayer["2. Validation & Security"]
        EP --> SEC{"Secret Header & Rate Check"}
        SEC -->|Valid| VAL["Schema Parser & Normalizer (Pydantic)"]
        SEC -->|Invalid| REJ["401 Unauthorized Response"]
    end

    subgraph CoreEngine["3. Automation Pipeline Orchestrator"]
        VAL --> DEDUP{"Deduplication Guard"}
        DEDUP -->|Duplicate| SUPP["Suppression Handler"]
        DEDUP -->|New Lead| PIPE["LeadPipeline Dispatcher"]
    end

    subgraph OutputAdapters["4. Storage & Integrations Layer"]
        PIPE --> DB[("SQLite Database<br/>Audit Trail & Persistence")]
        PIPE --> GS["Google Sheets Adapter<br/>(Live API / Mock Mode)"]
        PIPE --> EM["Email Service<br/>(HTML Alerts / Mock Mode)"]
        PIPE --> TG["Telegram Bot Adapter<br/>(Markdown Channel Alerts)"]
    end
```

---

## Component Responsibilities

| Component | Technology | Primary Function |
| :--- | :--- | :--- |
| **FastAPI Ingestion** | Python / FastAPI / Uvicorn | Receives asynchronous webhook requests, authenticates header tokens, and returns structured execution metrics. |
| **Schema Validation** | Pydantic v2 | Standardizes messy form data, sanitizes phone numbers, normalizes emails, and maps UTM campaign tags. |
| **Deduplication Engine** | SQLite3 / SQL Index | Detects duplicate rapid re-submissions or matching entry IDs to prevent spamming sales channels. |
| **Local Lead Store** | SQLite3 | Stores durable lead records with complete payload metadata, processing status, and channel delivery flags. |
| **Google Sheets Adapter** | Google Sheets API v4 / Mock | Appends structured row records to the target spreadsheet for marketing and sales analysis. |
| **Email Adapter** | SMTP / Python `email` / Mock | Renders a clean responsive HTML email summary for internal team notification. |
| **Telegram Bot Adapter** | Telegram Bot API / `httpx` / Mock | Dispatches rich markdown-formatted instant alerts to team operations chats or channels. |

---

## Data Schema & Transformation

```mermaid
classDiagram
    class FluentFormsRaw {
        +String form_id
        +String entry_id
        +String first_name
        +String last_name
        +String email
        +String phone
        +String company
        +String message
        +String utm_source
        +String utm_campaign
    }

    class NormalizedLead {
        +String lead_id
        +String form_id
        +String form_title
        +String full_name
        +EmailStr email
        +String phone
        +String company
        +String service_interest
        +String estimated_budget
        +String utm_source
        +String utm_campaign
        +DateTime created_at
        +Dict raw_metadata
    }

    FluentFormsRaw ..> NormalizedLead : Normalized & Cleaned via Pydantic
```
