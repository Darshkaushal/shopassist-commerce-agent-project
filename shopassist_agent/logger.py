"""Small JSONL logger for tool calls and admin actions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "activity.jsonl"


def log_event(event_type: str, payload: dict[str, Any]) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "payload": payload,
    }
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_logs(limit: int = 50) -> list[dict[str, Any]]:
    if not LOG_FILE.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in LOG_FILE.read_text(encoding="utf-8").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows
