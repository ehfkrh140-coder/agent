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
    latency = _latency_summary(packet)
    data_age_ms = latency.get("max_data_age_ms")
    negative_data_age_observed = _is_negative_number(data_age_ms)
    index_price_null_observed = first_observation is not None and getattr(first_observation, "index_price", None) is None
    stale_assumption_wording_observed = _stale_assumption_wording_observed(packet)
    depth_vwap_summary = _depth_vwap_sample_summary(best_candidate, packet)
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
        "venue_id": getattr(first_observation, "venue_id", None),
        "market_symbol": getattr(first_observation, "market_symbol", None),
        "parser_normalized_status": _parser_normalized_status(packet, first_observation, best_candidate),
        "diagnostics_count": _diagnostics_count(packet),
        "data_age_ms": data_age_ms,
        "timestamp_data_age_watch": negative_data_age_observed,
        "negative_data_age_observed": negative_data_age_observed,
        "mark_price": getattr(first_observation, "mark_price", None),
        "index_price": getattr(first_observation, "index_price", None),
        "index_price_null_observed": index_price_null_observed,
        "bid": getattr(first_observation, "bid", None),
        "ask": getattr(first_observation, "ask", None),
        "no_trade_only": _adapter_metadata_value(packet, "no_trade_only"),
        "execution_policy": _adapter_metadata_value(packet, "execution_policy"),
        "stale_assumption_wording_observed": stale_assumption_wording_observed,
        "depth_vwap_context_seen": depth_vwap_summary["depth_vwap_context_seen"],
        "depth_vwap_insufficient_depth": depth_vwap_summary["depth_vwap_insufficient_depth"],
        "depth_vwap_context_behavior": depth_vwap_summary["depth_vwap_context_behavior"],
        "depth_vwap_warnings": depth_vwap_summary["depth_vwap_warnings"],
        "depth_vwap_target_size": depth_vwap_summary["depth_vwap_target_size"],
        "depth_vwap_target_notional": depth_vwap_summary["depth_vwap_target_notional"],
        "_depth_vwap_ask_slippage_values": depth_vwap_summary["_depth_vwap_ask_slippage_values"],
        "_depth_vwap_bid_slippage_values": depth_vwap_summary["_depth_vwap_bid_slippage_values"],
        "_depth_vwap_context_only": depth_vwap_summary["_depth_vwap_context_only"],
        "latency": latency,
        "opportunity_packet": packet.model_dump(mode="json", exclude_none=True),
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
        "parser_normalized_status": metrics.get("parser_normalized_status"),
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
        "extensions": dict(candidate.extensions or {}),
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
    data_ages = [_float_or_none(sample.get("data_age_ms")) for sample in ok_samples]
    data_ages = [value for value in data_ages if value is not None]
    timestamp_data_age_watch_count = sum(1 for value in data_ages if value < 0)
    index_price_null_count = sum(1 for sample in ok_samples if sample.get("index_price_null_observed"))
    stale_assumption_wording_count = sum(1 for sample in ok_samples if sample.get("stale_assumption_wording_observed"))
    depth_vwap_summary = _depth_vwap_summary_fields(ok_samples)
    enriched.update(
        {
            "positive_gross_gap_count": positive_gross_gap_count,
            "timestamp_data_age_watch_count": timestamp_data_age_watch_count,
            "negative_data_age_observed": timestamp_data_age_watch_count > 0,
            "index_price_null_count": index_price_null_count,
            "index_price_null_observed": index_price_null_count > 0,
            "stale_assumption_wording_count": stale_assumption_wording_count,
            "stale_assumption_wording_observed": stale_assumption_wording_count > 0,
            "readiness_status_counts": readiness_counts,
            "watch_count": readiness_counts.get("WATCH", 0),
            "reject_count": readiness_counts.get("REJECT", 0),
            "need_data_count": readiness_counts.get("NEED_DATA", 0),
            **depth_vwap_summary,
        }
    )
    enriched.setdefault("max_gross_gap_pct", max(gross_gaps) if gross_gaps else None)
    return enriched



def _depth_vwap_sample_summary(best_candidate: dict[str, Any] | None, packet: OpportunityPacket) -> dict[str, Any]:
    context, lookup_warnings = _lookup_depth_vwap_context(best_candidate, packet)
    if not isinstance(context, dict):
        return {
            "depth_vwap_context_seen": False,
            "depth_vwap_insufficient_depth": False,
            "depth_vwap_context_behavior": None,
            "depth_vwap_warnings": lookup_warnings,
            "depth_vwap_target_size": None,
            "depth_vwap_target_notional": None,
            "_depth_vwap_ask_slippage_values": [],
            "_depth_vwap_bid_slippage_values": [],
            "_depth_vwap_context_only": False,
        }
    warnings = _collect_depth_vwap_warnings(context) + lookup_warnings
    ask_slippage_values, ask_slippage_warnings = _collect_depth_vwap_slippage_values(context, side="ask")
    bid_slippage_values, bid_slippage_warnings = _collect_depth_vwap_slippage_values(context, side="bid")
    warnings.extend(ask_slippage_warnings)
    warnings.extend(bid_slippage_warnings)
    return {
        "depth_vwap_context_seen": True,
        "depth_vwap_insufficient_depth": _depth_vwap_insufficient_depth(context),
        "depth_vwap_context_behavior": context.get("behavior"),
        "depth_vwap_warnings": warnings,
        "depth_vwap_target_size": context.get("target_size"),
        "depth_vwap_target_notional": context.get("target_notional"),
        "_depth_vwap_ask_slippage_values": ask_slippage_values,
        "_depth_vwap_bid_slippage_values": bid_slippage_values,
        "_depth_vwap_context_only": _depth_vwap_context_only(context),
    }


def _lookup_depth_vwap_context(best_candidate: dict[str, Any] | None, packet: OpportunityPacket) -> tuple[dict[str, Any] | None, list[str]]:
    candidate_extensions = (best_candidate or {}).get("extensions")
    candidate_context = _extension_context(candidate_extensions)
    if candidate_context is not None:
        if isinstance(candidate_context, dict):
            return candidate_context, []
        return None, ["depth_vwap_context_malformed"]

    if packet.candidates:
        packet_candidate_context = _extension_context(getattr(packet.candidates[0], "extensions", None))
        if packet_candidate_context is not None:
            if isinstance(packet_candidate_context, dict):
                return packet_candidate_context, []
            return None, ["depth_vwap_context_malformed"]

    packet_context = _extension_context(getattr(packet, "extensions", None))
    if packet_context is not None:
        if isinstance(packet_context, dict):
            return packet_context, []
        return None, ["depth_vwap_context_malformed"]
    return None, []


def _extension_context(extensions: Any) -> Any:
    if isinstance(extensions, dict) and "depth_vwap_context" in extensions:
        return extensions.get("depth_vwap_context")
    return None


def _depth_vwap_summary_fields(ok_samples: list[dict[str, Any]]) -> dict[str, Any]:
    seen_samples = [sample for sample in ok_samples if sample.get("depth_vwap_context_seen")]
    behavior_counts: dict[str, int] = {}
    warning_counts: dict[str, int] = {}
    ask_slippage_values: list[float] = []
    bid_slippage_values: list[float] = []
    for sample in ok_samples:
        behavior = sample.get("depth_vwap_context_behavior")
        if behavior:
            behavior_counts[str(behavior)] = behavior_counts.get(str(behavior), 0) + 1
        for warning in sample.get("depth_vwap_warnings") or []:
            if isinstance(warning, str):
                warning_counts[warning] = warning_counts.get(warning, 0) + 1
        ask_slippage_values.extend(sample.get("_depth_vwap_ask_slippage_values") or [])
        bid_slippage_values.extend(sample.get("_depth_vwap_bid_slippage_values") or [])
    return {
        "depth_vwap_context_seen_count": len(seen_samples),
        "depth_vwap_context_missing_count": len(ok_samples) - len(seen_samples),
        "depth_vwap_context_behavior_counts": behavior_counts,
        "depth_vwap_insufficient_depth_count": sum(1 for sample in ok_samples if sample.get("depth_vwap_insufficient_depth")),
        "depth_vwap_target_size_seen_count": sum(1 for sample in ok_samples if sample.get("depth_vwap_target_size") is not None),
        "depth_vwap_target_notional_seen_count": sum(1 for sample in ok_samples if sample.get("depth_vwap_target_notional") is not None),
        "depth_vwap_context_only_count": sum(1 for sample in ok_samples if sample.get("_depth_vwap_context_only")),
        "depth_vwap_warning_counts": warning_counts,
        "max_depth_vwap_ask_slippage_pct": max(ask_slippage_values) if ask_slippage_values else None,
        "max_depth_vwap_bid_slippage_pct": max(bid_slippage_values) if bid_slippage_values else None,
        "avg_depth_vwap_ask_slippage_pct": (sum(ask_slippage_values) / len(ask_slippage_values)) if ask_slippage_values else None,
        "avg_depth_vwap_bid_slippage_pct": (sum(bid_slippage_values) / len(bid_slippage_values)) if bid_slippage_values else None,
    }


def _collect_depth_vwap_warnings(context: Any) -> list[str]:
    warnings: list[str] = []
    if isinstance(context, dict):
        for key, value in context.items():
            if key == "warnings":
                if isinstance(value, list):
                    warnings.extend(str(item) for item in value if isinstance(item, str))
                elif isinstance(value, str):
                    warnings.append(value)
            else:
                warnings.extend(_collect_depth_vwap_warnings(value))
    elif isinstance(context, list):
        for item in context:
            warnings.extend(_collect_depth_vwap_warnings(item))
    return warnings


def _collect_depth_vwap_slippage_values(context: dict[str, Any], *, side: str) -> tuple[list[float], list[str]]:
    values: list[float] = []
    warnings: list[str] = []
    for container_name in ("spot", "perp"):
        container = context.get(container_name)
        if not isinstance(container, dict):
            continue
        result = container.get(f"{side}_vwap_result")
        if isinstance(result, dict) and "slippage_pct" in result:
            number = _float_or_none(result.get("slippage_pct"))
            if number is None:
                warnings.append(f"depth_vwap_{side}_slippage_parse_failed")
            else:
                values.append(number)
    recursive_key = f"{side}_slippage_pct"
    for raw_value in _collect_values_by_key(context, recursive_key):
        number = _float_or_none(raw_value)
        if number is None:
            warnings.append(f"depth_vwap_{side}_slippage_parse_failed")
        else:
            values.append(number)
    return values, warnings


def _collect_values_by_key(value: Any, key: str) -> list[Any]:
    values: list[Any] = []
    if isinstance(value, dict):
        for nested_key, nested_value in value.items():
            if nested_key == key:
                values.append(nested_value)
            values.extend(_collect_values_by_key(nested_value, key))
    elif isinstance(value, list):
        for item in value:
            values.extend(_collect_values_by_key(item, key))
    return values


def _depth_vwap_insufficient_depth(context: Any) -> bool:
    if isinstance(context, dict):
        for key, value in context.items():
            if key == "insufficient_depth" and value is True:
                return True
            if isinstance(value, (dict, list)) and _depth_vwap_insufficient_depth(value):
                return True
    elif isinstance(context, list):
        return any(_depth_vwap_insufficient_depth(item) for item in context)
    return False


def _depth_vwap_context_only(context: Any) -> bool:
    if isinstance(context, dict):
        for key, value in context.items():
            if key == "context_only" and value is True:
                return True
            if isinstance(value, (dict, list)) and _depth_vwap_context_only(value):
                return True
    elif isinstance(context, list):
        return any(_depth_vwap_context_only(item) for item in context)
    return False

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


def _stale_assumption_wording_observed(packet: OpportunityPacket) -> bool:
    stale_phrases = (
        "no config registration in this pr",
        "no registry integration in this pr",
        "no sampling integration in this pr",
    )
    for candidate in packet.candidates:
        for assumption in candidate.assumptions or []:
            text = str(assumption).casefold()
            if any(phrase in text for phrase in stale_phrases):
                return True
    return False


def _adapter_metadata_value(packet: OpportunityPacket, key: str) -> Any:
    metadata = _packet_extension_value(packet, "adapter_metadata")
    if isinstance(metadata, dict):
        return metadata.get(key)
    return None


def _diagnostics_count(packet: OpportunityPacket) -> int | None:
    diagnostics = _packet_extension_value(packet, "diagnostics")
    if isinstance(diagnostics, list):
        return len(diagnostics)
    return None


def _parser_normalized_status(
    packet: OpportunityPacket, first_observation: Any | None, best_candidate: dict[str, Any] | None
) -> Any:
    if best_candidate and best_candidate.get("parser_normalized_status") is not None:
        return best_candidate.get("parser_normalized_status")
    if first_observation is not None and isinstance(getattr(first_observation, "extensions", None), dict):
        observation_status = first_observation.extensions.get("parser_normalized_status")
        if observation_status is not None:
            return observation_status
    parser_output = _packet_extension_value(packet, "parser_output")
    if isinstance(parser_output, dict):
        return parser_output.get("normalized_status")
    return None


def _is_negative_number(value: Any) -> bool:
    number = _float_or_none(value)
    return bool(number is not None and number < 0)


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
