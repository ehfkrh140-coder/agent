from __future__ import annotations

from typing import Any


def format_console_alert(payload: dict[str, Any], alert: dict[str, Any]) -> str:
    """Render a human-readable, no-network alert summary for console/file use."""

    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else payload
    adapter_or_strategy = _adapter_or_strategy(payload, summary)
    asset_quote = _asset_quote(payload)
    header_label = "Council handoff ready" if alert.get("alert_type") == "persistent_ready_edge" else adapter_or_strategy
    lines = [f"[{alert.get('alert_level')}] {header_label}{asset_quote}"]
    lines.extend(
        [
            f"status={summary.get('persistence_status')}",
            f"samples_ok={summary.get('samples_ok')}/{summary.get('samples_requested') or payload.get('samples_requested')}",
            f"candidate_seen={summary.get('candidate_seen_count')}",
            f"positive_net_gap_count={summary.get('positive_net_gap_count')}",
            f"readiness_pass_count={summary.get('readiness_pass_count')}",
            f"max_net_gap={_fmt_pct(summary.get('max_estimated_net_gap_pct'))}",
            f"council_recommended={str(bool(payload.get('council_recommended'))).lower()}",
        ]
    )
    if payload.get("council_input_file"):
        lines.append(f"council_input_file={payload.get('council_input_file')}")
    if payload.get("sampling_output_file") or payload.get("sampling_output"):
        lines.append(f"sampling_output={payload.get('sampling_output_file') or payload.get('sampling_output')}")
    lines.append(f"reason={alert.get('reason')}")
    lines.append(f"recommended_action={alert.get('recommended_action')}")
    return "\n".join(lines)


def _adapter_or_strategy(payload: dict[str, Any], summary: dict[str, Any]) -> str:
    if payload.get("strategy_family"):
        return str(payload["strategy_family"])
    return str(payload.get("adapter_id") or summary.get("adapter_id") or "market_sampling")


def _asset_quote(payload: dict[str, Any]) -> str:
    if payload.get("asset") and payload.get("quote"):
        return f" {payload['asset']}/{payload['quote']}"
    samples = payload.get("samples") if isinstance(payload.get("samples"), list) else []
    for sample in samples:
        packet = sample.get("opportunity_packet") if isinstance(sample, dict) else None
        if isinstance(packet, dict) and packet.get("asset") and packet.get("quote"):
            return f" {packet['asset']}/{packet['quote']}"
    return ""


def _fmt_pct(value: Any) -> str:
    if value is None:
        return "null"
    try:
        return f"{float(value):.4f}%"
    except (TypeError, ValueError):
        return str(value)
