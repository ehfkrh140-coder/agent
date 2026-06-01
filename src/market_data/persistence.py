from __future__ import annotations

from statistics import mean
from typing import Any

PERSISTENCE_STATUSES = {
    "NO_CANDIDATE",
    "NO_PERSISTENT_EDGE",
    "PERSISTENT_GROSS_GAP_ONLY",
    "PERSISTENT_NET_GAP",
    "PERSISTENT_READY_EDGE",
    "INSUFFICIENT_DATA",
    "SAMPLE_ERRORS",
}


def summarize_persistence(
    samples: list[dict[str, Any]],
    *,
    adapter_id: str,
    samples_requested: int,
    max_errors: int = 3,
    min_consecutive_ready: int = 2,
) -> dict[str, Any]:
    ok_samples = [sample for sample in samples if sample.get("status") == "ok"]
    error_samples = [sample for sample in samples if sample.get("status") == "error"]
    candidates = [sample.get("best_candidate") for sample in ok_samples if sample.get("best_candidate")]
    net_gaps = [_float(candidate.get("estimated_net_gap_pct")) for candidate in candidates]
    net_gaps = [value for value in net_gaps if value is not None]
    gross_gaps = [_float(candidate.get("gross_gap_pct")) for candidate in candidates]
    gross_gaps = [value for value in gross_gaps if value is not None]
    latencies = [_float((sample.get("latency") or {}).get("max_latency_ms")) for sample in ok_samples]
    latencies = [value for value in latencies if value is not None]
    direction_counts: dict[str, int] = {}
    for candidate in candidates:
        direction = _direction_key(candidate)
        direction_counts[direction] = direction_counts.get(direction, 0) + 1
    positive_net_gap_count = sum(1 for candidate in candidates if _candidate_net_gap_pass(candidate))
    readiness_pass_count = sum(1 for sample in ok_samples if bool(sample.get("readiness_pass")))
    candidate_seen_count = len(candidates)
    too_many_errors = len(error_samples) > max_errors
    if too_many_errors:
        persistence_status = "SAMPLE_ERRORS"
        recommended = "NEED_DATA"
    elif not ok_samples:
        persistence_status = "INSUFFICIENT_DATA" if error_samples else "NO_CANDIDATE"
        recommended = "NEED_DATA"
    elif candidate_seen_count == 0:
        persistence_status = "NO_CANDIDATE"
        recommended = "REJECT"
    elif _max_consecutive_ready(samples) >= min_consecutive_ready:
        persistence_status = "PERSISTENT_READY_EDGE"
        recommended = "WATCH"
    elif positive_net_gap_count > 0:
        persistence_status = "PERSISTENT_NET_GAP"
        recommended = "WATCH"
    elif gross_gaps:
        persistence_status = "NO_PERSISTENT_EDGE"
        recommended = "REJECT"
    else:
        persistence_status = "PERSISTENT_GROSS_GAP_ONLY"
        recommended = "NEED_DATA"
    return {
        "adapter_id": adapter_id,
        "samples_requested": samples_requested,
        "samples_ok": len(ok_samples),
        "samples_error": len(error_samples),
        "candidate_seen_count": candidate_seen_count,
        "positive_net_gap_count": positive_net_gap_count,
        "readiness_pass_count": readiness_pass_count,
        "direction_counts": direction_counts,
        "max_estimated_net_gap_pct": max(net_gaps) if net_gaps else None,
        "avg_estimated_net_gap_pct": mean(net_gaps) if net_gaps else None,
        "max_gross_gap_pct": max(gross_gaps) if gross_gaps else None,
        "avg_latency_ms": mean(latencies) if latencies else None,
        "max_latency_ms": max(latencies) if latencies else None,
        "persistence_status": persistence_status,
        "recommended_default_decision": recommended,
        "min_consecutive_ready": min_consecutive_ready,
    }


def council_handoff_metadata(
    summary: dict[str, Any],
    *,
    sampling_output_file: str | None = None,
    council_input_file: str | None = None,
) -> dict[str, Any]:
    recommended = summary.get("persistence_status") == "PERSISTENT_READY_EDGE" and bool(council_input_file)
    reason = (
        "PERSISTENT_READY_EDGE: handoff OpportunityPacket is available"
        if recommended
        else f"{summary.get('persistence_status')}: persistent ready edge handoff packet not available"
    )
    return {
        "council_recommended": recommended,
        "council_reason": reason,
        "council_input_file": council_input_file if recommended else None,
        "sampling_output_file": sampling_output_file,
    }


def _candidate_net_gap_pass(candidate: dict[str, Any]) -> bool:
    if candidate.get("net_gap_pass") is True:
        return True
    net_gap = _float(candidate.get("estimated_net_gap_pct"))
    return bool(net_gap is not None and net_gap > 0)


def _direction_key(candidate: dict[str, Any]) -> str:
    source = candidate.get("source_venue_id") or "unknown_source"
    target = candidate.get("target_venue_id") or "unknown_target"
    return f"{source}_to_{target}"


def _max_consecutive_ready(samples: list[dict[str, Any]]) -> int:
    best = 0
    current = 0
    for sample in samples:
        if sample.get("status") == "ok" and sample.get("readiness_pass") is True:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def _float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
