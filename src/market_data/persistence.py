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
    "NO_IMBALANCE",
    "NO_PERSISTENT_IMBALANCE",
    "PERSISTENT_BID_HEAVY",
    "PERSISTENT_ASK_HEAVY",
    "MIXED_IMBALANCE",
}

ORDERBOOK_IMBALANCE_STATUSES = {
    "NO_IMBALANCE",
    "NO_PERSISTENT_IMBALANCE",
    "PERSISTENT_BID_HEAVY",
    "PERSISTENT_ASK_HEAVY",
    "MIXED_IMBALANCE",
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
    if _strategy_family(samples) == "orderbook_imbalance":
        return _summarize_orderbook_imbalance(
            samples,
            adapter_id=adapter_id,
            samples_requested=samples_requested,
            max_errors=max_errors,
            min_consecutive_imbalance=min_consecutive_ready,
        )
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
        "strategy_family": _strategy_family(samples),
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
    if summary.get("strategy_family") == "orderbook_imbalance":
        return {
            "council_recommended": False,
            "council_reason": f"{summary.get('persistence_status')}: experimental non-active orderbook imbalance has no Council handoff",
            "council_input_file": None,
            "sampling_output_file": sampling_output_file,
        }
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


def _summarize_orderbook_imbalance(
    samples: list[dict[str, Any]],
    *,
    adapter_id: str,
    samples_requested: int,
    max_errors: int,
    min_consecutive_imbalance: int,
) -> dict[str, Any]:
    ok_samples = [sample for sample in samples if sample.get("status") == "ok"]
    error_samples = [sample for sample in samples if sample.get("status") == "error"]
    candidates = [sample.get("best_candidate") for sample in ok_samples if sample.get("best_candidate")]
    ratios = [_float(candidate.get("imbalance_ratio")) for candidate in candidates]
    ratios = [value for value in ratios if value is not None]
    bid_notionals = [_float(candidate.get("bid_depth_notional")) for candidate in candidates]
    bid_notionals = [value for value in bid_notionals if value is not None]
    ask_notionals = [_float(candidate.get("ask_depth_notional")) for candidate in candidates]
    ask_notionals = [value for value in ask_notionals if value is not None]
    latencies = [_float((sample.get("latency") or {}).get("max_latency_ms")) for sample in ok_samples]
    latencies = [value for value in latencies if value is not None]
    direction_counts: dict[str, int] = {}
    for candidate in candidates:
        direction = str(candidate.get("direction") or candidate.get("imbalance_side") or "unknown")
        direction_counts[direction] = direction_counts.get(direction, 0) + 1
    bid_heavy_count = sum(1 for candidate in candidates if candidate.get("imbalance_side") == "BID_HEAVY")
    ask_heavy_count = sum(1 for candidate in candidates if candidate.get("imbalance_side") == "ASK_HEAVY")
    balanced_count = sum(1 for candidate in candidates if candidate.get("imbalance_side") == "BALANCED")
    imbalance_pass_count = sum(1 for candidate in candidates if candidate.get("imbalance_pass") is True)
    experimental_watch_count = sum(1 for sample in ok_samples if sample.get("readiness_status") == "WATCH")
    too_many_errors = len(error_samples) > max_errors
    if too_many_errors:
        persistence_status = "SAMPLE_ERRORS"
        recommended = "NEED_DATA"
    elif not ok_samples:
        persistence_status = "INSUFFICIENT_DATA" if error_samples else "NO_IMBALANCE"
        recommended = "NEED_DATA"
    elif imbalance_pass_count == 0:
        persistence_status = "NO_IMBALANCE"
        recommended = "REJECT"
    elif bid_heavy_count and ask_heavy_count and _mixed_imbalance(candidates, bid_heavy_count, ask_heavy_count):
        persistence_status = "MIXED_IMBALANCE"
        recommended = "WATCH"
    elif _max_consecutive_side(samples, "BID_HEAVY") >= min_consecutive_imbalance or _dominates(bid_heavy_count, imbalance_pass_count):
        persistence_status = "PERSISTENT_BID_HEAVY"
        recommended = "WATCH"
    elif _max_consecutive_side(samples, "ASK_HEAVY") >= min_consecutive_imbalance or _dominates(ask_heavy_count, imbalance_pass_count):
        persistence_status = "PERSISTENT_ASK_HEAVY"
        recommended = "WATCH"
    else:
        persistence_status = "NO_PERSISTENT_IMBALANCE"
        recommended = "REJECT"
    return {
        "adapter_id": adapter_id,
        "strategy_family": "orderbook_imbalance",
        "samples_requested": samples_requested,
        "samples_ok": len(ok_samples),
        "samples_error": len(error_samples),
        "candidate_seen_count": len(candidates),
        "imbalance_seen_count": imbalance_pass_count,
        "bid_heavy_count": bid_heavy_count,
        "ask_heavy_count": ask_heavy_count,
        "balanced_count": balanced_count,
        "imbalance_pass_count": imbalance_pass_count,
        "experimental_watch_count": experimental_watch_count,
        "readiness_pass_count": sum(1 for sample in ok_samples if bool(sample.get("readiness_pass"))),
        "direction_counts": direction_counts,
        "max_imbalance_ratio": max(ratios) if ratios else None,
        "avg_imbalance_ratio": mean(ratios) if ratios else None,
        "max_bid_depth_notional": max(bid_notionals) if bid_notionals else None,
        "max_ask_depth_notional": max(ask_notionals) if ask_notionals else None,
        "avg_latency_ms": mean(latencies) if latencies else None,
        "max_latency_ms": max(latencies) if latencies else None,
        "persistence_status": persistence_status,
        "recommended_default_decision": recommended,
        "council_recommended": False,
        "council_input_file": None,
        "min_consecutive_imbalance": min_consecutive_imbalance,
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


def _max_consecutive_side(samples: list[dict[str, Any]], side: str) -> int:
    best = 0
    current = 0
    for sample in samples:
        candidate = sample.get("best_candidate") if sample.get("status") == "ok" else None
        if isinstance(candidate, dict) and candidate.get("imbalance_side") == side and candidate.get("imbalance_pass") is True:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def _dominates(side_count: int, imbalance_pass_count: int) -> bool:
    return imbalance_pass_count >= 2 and side_count >= 2 and (side_count / imbalance_pass_count) >= 0.67


def _mixed_imbalance(candidates: list[dict[str, Any]], bid_heavy_count: int, ask_heavy_count: int) -> bool:
    if min(bid_heavy_count, ask_heavy_count) >= 2:
        return True
    sides = [candidate.get("imbalance_side") for candidate in candidates if candidate.get("imbalance_side") in {"BID_HEAVY", "ASK_HEAVY"}]
    return any(left != right for left, right in zip(sides, sides[1:])) and min(bid_heavy_count, ask_heavy_count) >= 1


def _strategy_family(samples: list[dict[str, Any]]) -> str | None:
    for sample in samples:
        if sample.get("strategy_family"):
            return sample.get("strategy_family")
        packet = sample.get("opportunity_packet")
        if isinstance(packet, dict) and packet.get("strategy_family"):
            return packet.get("strategy_family")
        candidate = sample.get("best_candidate")
        if isinstance(candidate, dict) and candidate.get("candidate_type") == "orderbook_imbalance_signal":
            return "orderbook_imbalance"
    return None


def _float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
