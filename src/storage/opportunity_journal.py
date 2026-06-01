from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_JOURNAL_PATH = Path("data/opportunity_journal/opportunity_journal.jsonl")


def build_journal_record(result: dict[str, Any], *, sampling_output: str | None = None) -> dict[str, Any]:
    summary = result.get("summary") or {}
    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "adapter_id": result.get("adapter_id") or summary.get("adapter_id"),
        "sampling_output": sampling_output or result.get("sampling_output_file"),
        "persistence_status": summary.get("persistence_status"),
        "recommended_default_decision": summary.get("recommended_default_decision"),
        "council_recommended": result.get("council_recommended", False),
        "council_input_file": result.get("council_input_file"),
        "samples_requested": summary.get("samples_requested") or result.get("samples_requested"),
        "samples_ok": summary.get("samples_ok"),
        "samples_error": summary.get("samples_error"),
        "candidate_seen_count": summary.get("candidate_seen_count"),
        "positive_net_gap_count": summary.get("positive_net_gap_count"),
        "readiness_pass_count": summary.get("readiness_pass_count"),
        "max_estimated_net_gap_pct": summary.get("max_estimated_net_gap_pct"),
        "avg_estimated_net_gap_pct": summary.get("avg_estimated_net_gap_pct"),
        "direction_counts": summary.get("direction_counts") or {},
    }


def append_journal_record(result: dict[str, Any], *, journal_path: str | Path = DEFAULT_JOURNAL_PATH, sampling_output: str | None = None) -> dict[str, Any]:
    record = build_journal_record(result, sampling_output=sampling_output)
    path = Path(journal_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record
