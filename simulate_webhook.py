#!/usr/bin/env python3
"""CLI Webhook Simulator.

Sends test payloads to the running webhook receiver to demonstrate
data validation, SQLite persistence, Google Sheets sync, and Telegram alerts.
"""

import json
import sys
import time
from pathlib import Path
import httpx

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SAMPLE_DIR = Path(__file__).parent / "sample"
DEFAULT_PAYLOAD_FILE = SAMPLE_DIR / "fluent_forms_payload.json"
WEBHOOK_URL = "http://127.0.0.1:8000/api/v1/webhook/fluent-forms"
SECRET_HEADER = "demo_secret_token_12345"


def run_simulation(payload_path: Path = DEFAULT_PAYLOAD_FILE):
    print("=" * 70)
    print("🚀 FLUENT FORMS WEBHOOK PIPELINE SIMULATOR")
    print("=" * 70)

    if not payload_path.exists():
        print(f"❌ Error: Payload file not found at {payload_path}")
        sys.exit(1)

    with open(payload_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    # Randomize entry ID to avoid duplicate rejection when testing multiple times
    payload["entry_id"] = str(int(time.time()) % 100000)

    print(f"📦 Target Endpoint : {WEBHOOK_URL}")
    print(f"📄 Payload Source  : {payload_path.name}")
    print(f"👤 Lead Name       : {payload.get('first_name', '')} {payload.get('last_name', '')}")
    print(f"📧 Lead Email      : {payload.get('email', '')}")
    print(f"🏢 Company         : {payload.get('company', '')}")
    print("-" * 70)
    print("⏳ Dispatching HTTP POST request...")

    try:
        start = time.perf_counter()
        response = httpx.post(
            WEBHOOK_URL,
            json=payload,
            headers={"X-Webhook-Secret": SECRET_HEADER, "Content-Type": "application/json"},
            timeout=10.0,
        )
        elapsed = round((time.perf_counter() - start) * 1000, 2)

        print(f"⚡ Response Status : {response.status_code} ({response.reason_phrase}) in {elapsed}ms")
        print("-" * 70)

        if response.status_code == 200:
            data = response.json()
            print("✅ PIPELINE EXECUTION SUCCESSFUL!")
            print(f"   • Lead Tracking ID : {data.get('lead_id')}")
            print(f"   • SQLite DB Saved  : {data.get('database_saved')}")
            print(f"   • Google Sheets    : {data.get('google_sheets_synced')}")
            print(f"   • Email Dispatched : {data.get('email_dispatched')}")
            print(f"   • Telegram Alerted : {data.get('telegram_notified')}")
            print(f"   • Execution Time   : {data.get('execution_time_ms')} ms")
            print("\n📋 Full Response Data:")
            print(json.dumps(data, indent=2))
        else:
            print("❌ Pipeline failed or rejected:")
            print(response.text)

    except httpx.ConnectError:
        print("❌ Could not connect to webhook server!")
        print("💡 Make sure the application is running first:")
        print("   python src/main.py")
        sys.exit(1)
    except Exception as exc:
        print(f"❌ Error occurred during request: {exc}")
        sys.exit(1)

    print("=" * 70)


if __name__ == "__main__":
    target = DEFAULT_PAYLOAD_FILE
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
    run_simulation(target)
