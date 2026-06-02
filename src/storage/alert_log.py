from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_ALERT_LOG_PATH = Path("data/alerts/alert_log.jsonl")


def build_alert_log_record(
    payload: dict[str, Any],
    alert: dict[str, Any],
    message: str,
    *,
    sampling_output: str | None = None,
) -> dict[str, Any]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else payload
    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "alert_level": alert.get("alert_level"),
        "alert_type": alert.get("alert_type"),
        "should_alert": bool(alert.get("should_alert")),
        "sampling_output": sampling_output or payload.get("sampling_output_file") or payload.get("sampling_output"),
        "persistence_status": summary.get("persistence_status"),
        "council_recommended": bool(payload.get("council_recommended")),
        "council_input_file": payload.get("council_input_file"),
        "message": message,
    }


def append_alert_log(
    payload: dict[str, Any],
    alert: dict[str, Any],
    message: str,
    *,
    log_path: str | Path = DEFAULT_ALERT_LOG_PATH,
    sampling_output: str | None = None,
) -> dict[str, Any]:
    record = build_alert_log_record(payload, alert, message, sampling_output=sampling_output)
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record
