from __future__ import annotations

from typing import Any

DEFAULT_ALERT_CONFIG: dict[str, Any] = {
    "alerts": {
        "emit_info_for_no_candidate": False,
        "alert_on_persistent_net_gap": True,
        "alert_on_sample_errors": True,
        "alert_on_persistent_ready_edge": True,
        "alert_on_orderbook_imbalance": True,
        "alert_on_mixed_orderbook_imbalance": True,
    }
}

ORDERBOOK_IMBALANCE_STATUSES = {
    "NO_IMBALANCE",
    "NO_PERSISTENT_IMBALANCE",
    "PERSISTENT_BID_HEAVY",
    "PERSISTENT_ASK_HEAVY",
    "MIXED_IMBALANCE",
}


def evaluate_alert(payload: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Classify a sampling result or opportunity-journal record into an alert decision."""

    config = config or DEFAULT_ALERT_CONFIG
    alert_config = config.get("alerts") or {}
    summary = _summary(payload)
    status = summary.get("persistence_status")
    strategy_family = summary.get("strategy_family") or payload.get("strategy_family")
    council_recommended = bool(payload.get("council_recommended"))
    samples_error = int(summary.get("samples_error") or 0)

    if strategy_family == "orderbook_imbalance" or status in ORDERBOOK_IMBALANCE_STATUSES:
        return _orderbook_imbalance_alert(status, alert_config, samples_error)

    if status == "PERSISTENT_READY_EDGE" and council_recommended:
        enabled = alert_config.get("alert_on_persistent_ready_edge", True)
        return _decision(
            enabled,
            "CRITICAL",
            "persistent_ready_edge",
            "PERSISTENT_READY_EDGE with Council handoff OpportunityPacket available.",
            "REVIEW_COUNCIL_HANDOFF",
        )
    if status == "PERSISTENT_NET_GAP":
        enabled = alert_config.get("alert_on_persistent_net_gap", True)
        return _decision(
            enabled,
            "WATCH",
            "persistent_net_gap",
            "Persistent positive net gap observed, but readiness/council handoff is not confirmed.",
            "REVIEW_JOURNAL",
        )
    if status == "SAMPLE_ERRORS":
        enabled = alert_config.get("alert_on_sample_errors", True)
        return _decision(
            enabled,
            "ERROR",
            "sample_errors",
            "Sampling exceeded the configured error threshold.",
            "REVIEW_JOURNAL",
        )
    if status == "INSUFFICIENT_DATA":
        level = "WATCH" if samples_error else "INFO"
        return _decision(
            bool(samples_error),
            level,
            "insufficient_data",
            "Sampling did not collect enough usable data." if samples_error else "No alert: insufficient data without sample errors.",
            "REVIEW_JOURNAL" if samples_error else "NO_ACTION",
        )
    if status == "NO_CANDIDATE":
        emit = bool(alert_config.get("emit_info_for_no_candidate", False))
        return _decision(
            emit,
            "INFO",
            "no_candidate",
            "No candidate was observed; default policy suppresses this alert.",
            "NO_ACTION",
        )
    if status == "NO_PERSISTENT_EDGE":
        return _decision(
            False,
            "INFO",
            "no_persistent_edge",
            "No persistent edge was observed; alert suppressed by default.",
            "NO_ACTION",
        )
    return _decision(
        False,
        "INFO",
        "sampling_status",
        f"No alert rule matched persistence_status={status!r}.",
        "NO_ACTION",
    )


def _orderbook_imbalance_alert(status: Any, alert_config: dict[str, Any], samples_error: int) -> dict[str, Any]:
    if status == "SAMPLE_ERRORS":
        enabled = alert_config.get("alert_on_sample_errors", True)
        return _decision(enabled, "ERROR", "sample_errors", "Experimental orderbook imbalance sampling exceeded the error threshold.", "REVIEW_JOURNAL")
    if status == "PERSISTENT_BID_HEAVY":
        enabled = alert_config.get("alert_on_orderbook_imbalance", True)
        return _decision(enabled, "WATCH", "persistent_bid_heavy", "Experimental non-active orderbook imbalance persisted on the bid side. Review journal only.", "REVIEW_JOURNAL")
    if status == "PERSISTENT_ASK_HEAVY":
        enabled = alert_config.get("alert_on_orderbook_imbalance", True)
        return _decision(enabled, "WATCH", "persistent_ask_heavy", "Experimental non-active orderbook imbalance persisted on the ask side. Review journal only.", "REVIEW_JOURNAL")
    if status == "MIXED_IMBALANCE":
        enabled = alert_config.get("alert_on_mixed_orderbook_imbalance", True)
        return _decision(enabled, "WATCH", "mixed_orderbook_imbalance", "Experimental non-active orderbook imbalance alternated between bid and ask sides. Review journal only.", "REVIEW_JOURNAL")
    if status == "INSUFFICIENT_DATA":
        return _decision(bool(samples_error), "WATCH" if samples_error else "INFO", "insufficient_data", "Experimental orderbook imbalance sampling did not collect enough usable data.", "REVIEW_JOURNAL" if samples_error else "NO_ACTION")
    if status == "NO_IMBALANCE":
        return _decision(False, "INFO", "no_orderbook_imbalance", "No orderbook imbalance observed; alert suppressed by default.", "NO_ACTION")
    if status == "NO_PERSISTENT_IMBALANCE":
        return _decision(False, "INFO", "no_persistent_orderbook_imbalance", "No persistent orderbook imbalance observed; alert suppressed by default.", "NO_ACTION")
    return _decision(False, "INFO", "orderbook_imbalance_status", f"No orderbook imbalance alert rule matched persistence_status={status!r}.", "NO_ACTION")


def _summary(payload: dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload.get("summary"), dict):
        return payload["summary"]
    return {
        "adapter_id": payload.get("adapter_id"),
        "strategy_family": payload.get("strategy_family"),
        "samples_requested": payload.get("samples_requested"),
        "samples_ok": payload.get("samples_ok"),
        "samples_error": payload.get("samples_error"),
        "candidate_seen_count": payload.get("candidate_seen_count"),
        "positive_net_gap_count": payload.get("positive_net_gap_count"),
        "readiness_pass_count": payload.get("readiness_pass_count"),
        "max_estimated_net_gap_pct": payload.get("max_estimated_net_gap_pct"),
        "avg_estimated_net_gap_pct": payload.get("avg_estimated_net_gap_pct"),
        "imbalance_seen_count": payload.get("imbalance_seen_count"),
        "bid_heavy_count": payload.get("bid_heavy_count"),
        "ask_heavy_count": payload.get("ask_heavy_count"),
        "balanced_count": payload.get("balanced_count"),
        "max_imbalance_ratio": payload.get("max_imbalance_ratio"),
        "avg_imbalance_ratio": payload.get("avg_imbalance_ratio"),
        "persistence_status": payload.get("persistence_status"),
        "recommended_default_decision": payload.get("recommended_default_decision"),
        "direction_counts": payload.get("direction_counts") or {},
    }


def _decision(should_alert: bool, level: str, alert_type: str, reason: str, action: str) -> dict[str, Any]:
    return {
        "alert_level": level,
        "alert_type": alert_type,
        "should_alert": should_alert,
        "reason": reason,
        "recommended_action": action,
    }
