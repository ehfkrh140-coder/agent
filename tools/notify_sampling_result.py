#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.notifications.alert_rules import DEFAULT_ALERT_CONFIG, evaluate_alert
from src.notifications.formatters import format_console_alert
from src.storage.alert_log import DEFAULT_ALERT_LOG_PATH, append_alert_log


def main() -> None:
    parser = argparse.ArgumentParser(description="Render read-only alerts for market sampling results")
    parser.add_argument("--sampling-output", required=True, help="Path to market_sampling_v1 JSON output")
    parser.add_argument("--config", default="configs/alerts.yaml")
    parser.add_argument("--log", action="store_true", help="Append the rendered alert decision to the file alert log")
    parser.add_argument("--log-path", default=None)
    args = parser.parse_args()

    sampling_path = Path(args.sampling_output)
    payload = json.loads(sampling_path.read_text(encoding="utf-8"))
    config = _load_config(args.config)
    alert = evaluate_alert(payload, config=config)
    message = format_console_alert(payload, alert)
    print(message)
    if args.log:
        log_path = args.log_path or _configured_log_path(config)
        append_alert_log(payload, alert, message, log_path=log_path, sampling_output=str(sampling_path))


def _load_config(path: str | Path) -> dict:
    config_path = Path(path)
    if not config_path.exists():
        return DEFAULT_ALERT_CONFIG
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else DEFAULT_ALERT_CONFIG


def _configured_log_path(config: dict) -> str:
    channels = config.get("channels") if isinstance(config, dict) else None
    file_channel = (channels or {}).get("file") if isinstance(channels, dict) else None
    path = (file_channel or {}).get("path") if isinstance(file_channel, dict) else None
    return str(path or DEFAULT_ALERT_LOG_PATH)


if __name__ == "__main__":
    main()
