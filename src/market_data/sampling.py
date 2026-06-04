from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from src.market_data.packet_builder import OpportunityPacketBuilder
from src.market_data.persistence import council_handoff_metadata, summarize_persistence
from src.schemas.opportunity_packet import OpportunityCandidate, OpportunityPacket
from src.strategy.readiness import build_readiness_report


def run_market_sampling(
    adapter: Any,
    *,
    adapter_id: str,
    samples_requested: int,
    interval_seconds: float = 0.0,
    max_errors: int = 3,
    also_save_packets: bool = False,
    packet_output_dir: str | Path | None = None,
    output_path: str | Path | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    now_fn: Callable[[], datetime] | None = None,
) -> dict[str, Any]:
    now_fn = now_fn or (lambda: datetime.now(timezone.utc))
    builder = OpportunityPacketBuilder()
    records: list[dict[str, Any]] = []
    errors = 0
    packet_dir = Path(packet_output_dir) if packet_output_dir else None
    if also_save_packets:
        packet_dir = packet_dir or Path("data/market_samples/packets")
        packet_dir.mkdir(parents=True, exist_ok=True)
    for index in range(1, samples_requested + 1):
        collected_at = _iso(now_fn())
        try:
            snapshot = adapter.fetch_snapshot()
            packet = builder.build(snapshot)
            readiness = build_readiness_report(packet)
            if also_save_packets and packet_dir is not None:
                (packet_dir / f"sample_{index:03d}_{packet.packet_id}.json").write_text(
                    packet.model_dump_json(indent=2) + "\n",
                    encoding="utf-8",
                )
            records.append(_sample_record(index, collected_at, packet, readiness))
        except Exception as exc:  # noqa: BLE001 - sampling records adapter failures and may continue.
            errors += 1
            records.append(
                {
                    "sample_index": index,
                    "collected_at_utc": collected_at,
                    "status": "error",
                    "error": str(exc),
                    "packet_id": None,
                    "candidate_count": 0,
                    "readiness_status": None,
                    "readiness_pass": False,
                    "recommended_default_decision": "NEED_DATA",
                    "best_candidate": None,
                    "latency": {},
                }
            )
            if errors > max_errors:
                break
        if index < samples_requested and interval_seconds > 0:
            sleep_fn(interval_seconds)
    summary = summarize_persistence(
        records,
        adapter_id=adapter_id,
        samples_requested=samples_requested,
        max_errors=max_errors,
    )
    summary = _enrich_sampling_summary(summary, records)
    result = {
        "schema_version": "market_sampling_v1",
        "adapter_id": adapter_id,
        "created_at_utc": _iso(now_fn()),
        "samples_requested": samples_requested,
        "interval_seconds": interval_seconds,
        "max_errors": max_errors,
        "samples": records,
        "summary": summary,
    }
    result.update(council_handoff_metadata(summary, sampling_output_file=str(output_path) if output_path else None))
    return result


def _sample_record(index: int, collected_at: str, packet: OpportunityPacket, readiness: dict[str, Any]) -> dict[str, Any]:
    best_candidate = _best_candidate(packet.candidates)
    first_observation = packet.observations[0] if packet.observations else None
    readiness_status = _readiness_status(packet, readiness, best_candidate)
    readiness_pass = _readiness_pass(packet, readiness, best_candidate)
    recommended_default_decision = _recommended_default_decision(packet, readiness, best_candidate)
    return {
        "sample_index": index,
        "collected_at_utc": collected_at,
        "status": "ok",
        "error": None,
        "packet_id": packet.packet_id,
        "candidate_count": len(packet.candidates),
        "strategy_family": packet.strategy_family,
        "strategy_id": packet.strategy_id,
        "readiness_status": readiness_status,
        "readiness_pass": readiness_pass,
        "recommended_default_decision": recommended_default_decision,
        "successful_global_reference_count": _packet_extension_value(packet, "successful_global_reference_count"),
        "failed_global_reference_venues": _packet_extension_value(packet, "failed_global_reference_venues"),
        "best_candidate": best_candidate,
        "long_gap_pct": (best_candidate or {}).get("long_gap_pct"),
        "short_gap_pct": (best_candidate or {}).get("short_gap_pct"),
        "gross_gap_pct": (best_candidate or {}).get("gross_gap_pct"),
        "max_observed_gap_pct": (best_candidate or {}).get("max_observed_gap_pct"),
        "estimated_net_gap_pct": (best_candidate or {}).get("estimated_net_gap_pct"),
        "liquidity_pass": (best_candidate or {}).get("liquidity_pass"),
        "freshness_pass": (best_candidate or {}).get("freshness_pass"),
        "comparability_pass": (best_candidate or {}).get("comparability_pass"),
        "required_missing_fields": (best_candidate or {}).get("required_missing_fields") or [],
        "mark_price": getattr(first_observation, "mark_price", None),
        "index_price": getattr(first_observation, "index_price", None),
        "bid": getattr(first_observation, "bid", None),
        "ask": getattr(first_observation, "ask", None),
        "no_trade_only": _adapter_metadata_value(packet, "no_trade_only"),
        "execution_policy": _adapter_metadata_value(packet, "execution_policy"),
        "latency": _latency_summary(packet),
        "opportunity_packet": packet.model_dump(mode="json"),
    }


def _best_candidate(candidates: list[OpportunityCandidate]) -> dict[str, Any] | None:
    if not candidates:
        return None
    candidate = max(candidates, key=lambda item: _candidate_sort_value(item))
    default_vwap = None
    vwap_results = candidate.metrics.get("vwap_results") if isinstance(candidate.metrics, dict) else None
    if isinstance(vwap_results, list) and vwap_results:
        default_vwap = vwap_results[0]
    metrics = candidate.metrics if isinstance(candidate.metrics, dict) else {}
    return {
        "candidate_id": candidate.candidate_id,
        "candidate_type": candidate.candidate_type,
        "source_venue_id": candidate.source_venue_id,
        "target_venue_id": candidate.target_venue_id,
        "direction": candidate.direction,
        "gross_gap_pct": candidate.gross_gap_pct,
        "max_observed_gap_pct": metrics.get("max_observed_gap_pct", candidate.gross_gap_pct),
        "estimated_net_gap_pct": candidate.estimated_net_gap_pct,
        "long_gap_pct": candidate.long_gap_pct,
        "short_gap_pct": candidate.short_gap_pct,
        "readiness_status": metrics.get("readiness_status"),
        "readiness_pass": metrics.get("readiness_pass"),
        "recommended_default_decision": metrics.get("recommended_default_decision"),
        "comparability_pass": metrics.get("comparability_pass"),
        "required_missing_fields": list(candidate.required_missing_fields or []),
        "net_gap_pass": _metric_bool(candidate, "net_gap_pass", default_vwap),
        "liquidity_pass": candidate.liquidity_pass,
        "freshness_pass": candidate.freshness_pass,
        "target_notional": metrics.get("target_notional") if "target_notional" in metrics else (default_vwap or {}).get("target_notional"),
        "source_vwap_ask": (default_vwap or {}).get("source_vwap_ask"),
        "target_vwap_bid": (default_vwap or {}).get("target_vwap_bid"),
        "vwap_result": default_vwap,
        "imbalance_side": metrics.get("imbalance_side"),
        "imbalance_ratio": metrics.get("imbalance_ratio"),
        "bid_depth_notional": metrics.get("bid_depth_notional"),
        "ask_depth_notional": metrics.get("ask_depth_notional"),
        "spread_pct": metrics.get("spread_pct"),
        "depth_levels_used": metrics.get("depth_levels_used"),
        "imbalance_pass": metrics.get("imbalance_pass"),
        "experimental_pass": metrics.get("experimental_pass"),
        "global_reference_pass": metrics.get("global_reference_pass"),
        "global_reference_venue_count": metrics.get("global_reference_venue_count"),
        "global_usdt_depeg_flag": metrics.get("global_usdt_depeg_flag"),
        "global_usdt_depeg_pct": metrics.get("global_usdt_depeg_pct"),
        "global_usdt_mid": metrics.get("global_usdt_mid"),
        "domestic_best_bid": metrics.get("domestic_best_bid"),
        "domestic_best_ask": metrics.get("domestic_best_ask"),
        "domestic_mid": metrics.get("domestic_mid"),
    }


def _enrich_sampling_summary(summary: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    enriched = dict(summary)
    ok_samples = [sample for sample in records if sample.get("status") == "ok"]
    readiness_counts: dict[str, int] = {}
    for sample in ok_samples:
        status = sample.get("readiness_status")
        if status:
            readiness_counts[str(status)] = readiness_counts.get(str(status), 0) + 1
    gross_gaps = [_float_or_none(sample.get("gross_gap_pct")) for sample in ok_samples]
    gross_gaps = [value for value in gross_gaps if value is not None]
    positive_gross_gap_count = sum(1 for value in gross_gaps if value > 0)
    enriched.update(
        {
            "positive_gross_gap_count": positive_gross_gap_count,
            "readiness_status_counts": readiness_counts,
            "watch_count": readiness_counts.get("WATCH", 0),
            "reject_count": readiness_counts.get("REJECT", 0),
            "need_data_count": readiness_counts.get("NEED_DATA", 0),
        }
    )
    enriched.setdefault("max_gross_gap_pct", max(gross_gaps) if gross_gaps else None)
    return enriched


def _readiness_status(
    packet: OpportunityPacket, readiness: dict[str, Any], best_candidate: dict[str, Any] | None
) -> str | None:
    packet_readiness = _packet_extension_value(packet, "readiness")
    if isinstance(packet_readiness, dict) and packet_readiness.get("readiness_status"):
        return packet_readiness.get("readiness_status")
    if best_candidate and best_candidate.get("readiness_status") is not None:
        return best_candidate.get("readiness_status")
    return readiness.get("status")


def _readiness_pass(packet: OpportunityPacket, readiness: dict[str, Any], best_candidate: dict[str, Any] | None) -> bool:
    packet_readiness = _packet_extension_value(packet, "readiness")
    if isinstance(packet_readiness, dict) and "readiness_pass" in packet_readiness:
        return bool(packet_readiness.get("readiness_pass"))
    if best_candidate and best_candidate.get("readiness_pass") is not None:
        return bool(best_candidate.get("readiness_pass"))
    return bool(readiness.get("readiness_pass"))


def _recommended_default_decision(
    packet: OpportunityPacket, readiness: dict[str, Any], best_candidate: dict[str, Any] | None
) -> str | None:
    packet_readiness = _packet_extension_value(packet, "readiness")
    if isinstance(packet_readiness, dict) and packet_readiness.get("recommended_default_decision"):
        return packet_readiness.get("recommended_default_decision")
    if best_candidate and best_candidate.get("recommended_default_decision") is not None:
        return best_candidate.get("recommended_default_decision")
    return readiness.get("recommended_default_decision")


def _adapter_metadata_value(packet: OpportunityPacket, key: str) -> Any:
    metadata = _packet_extension_value(packet, "adapter_metadata")
    if isinstance(metadata, dict):
        return metadata.get(key)
    return None


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _packet_extension_value(packet: OpportunityPacket, key: str) -> Any:
    if isinstance(packet.extensions, dict):
        return packet.extensions.get(key)
    return None


def _latency_summary(packet: OpportunityPacket) -> dict[str, Any]:
    values: dict[str, Any] = {}
    latencies: list[float] = []
    ages: list[float] = []
    for obs in packet.observations:
        if obs.data_quality is None:
            continue
        if obs.data_quality.latency_ms is not None:
            key = f"{obs.venue_id}_ms"
            values[key] = obs.data_quality.latency_ms
            latencies.append(float(obs.data_quality.latency_ms))
        if obs.data_quality.max_data_age_ms is not None:
            ages.append(float(obs.data_quality.max_data_age_ms))
    values["max_data_age_ms"] = max(ages) if ages else None
    values["max_latency_ms"] = max(latencies) if latencies else None
    values["avg_latency_ms"] = sum(latencies) / len(latencies) if latencies else None
    return values


def _candidate_sort_value(candidate: OpportunityCandidate) -> float:
    if candidate.estimated_net_gap_pct is not None:
        return candidate.estimated_net_gap_pct
    if candidate.gross_gap_pct is not None:
        return candidate.gross_gap_pct
    return float("-inf")


def _metric_bool(candidate: OpportunityCandidate, key: str, default_vwap: dict[str, Any] | None) -> bool | None:
    if default_vwap and key in default_vwap:
        return default_vwap.get(key)
    if isinstance(candidate.metrics, dict) and key in candidate.metrics:
        return candidate.metrics.get(key)
    return None


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()
