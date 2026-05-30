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
    result.update(council_handoff_metadata(summary, output_path=str(output_path) if output_path else None))
    return result


def _sample_record(index: int, collected_at: str, packet: OpportunityPacket, readiness: dict[str, Any]) -> dict[str, Any]:
    return {
        "sample_index": index,
        "collected_at_utc": collected_at,
        "status": "ok",
        "error": None,
        "packet_id": packet.packet_id,
        "candidate_count": len(packet.candidates),
        "readiness_status": readiness.get("status"),
        "readiness_pass": bool(readiness.get("readiness_pass")),
        "recommended_default_decision": readiness.get("recommended_default_decision"),
        "best_candidate": _best_candidate(packet.candidates),
        "latency": _latency_summary(packet),
    }


def _best_candidate(candidates: list[OpportunityCandidate]) -> dict[str, Any] | None:
    if not candidates:
        return None
    candidate = max(candidates, key=lambda item: _candidate_sort_value(item))
    default_vwap = None
    vwap_results = candidate.metrics.get("vwap_results") if isinstance(candidate.metrics, dict) else None
    if isinstance(vwap_results, list) and vwap_results:
        default_vwap = vwap_results[0]
    return {
        "candidate_id": candidate.candidate_id,
        "source_venue_id": candidate.source_venue_id,
        "target_venue_id": candidate.target_venue_id,
        "gross_gap_pct": candidate.gross_gap_pct,
        "estimated_net_gap_pct": candidate.estimated_net_gap_pct,
        "net_gap_pass": _metric_bool(candidate, "net_gap_pass", default_vwap),
        "liquidity_pass": candidate.liquidity_pass,
        "freshness_pass": candidate.freshness_pass,
        "target_notional": (default_vwap or {}).get("target_notional"),
        "source_vwap_ask": (default_vwap or {}).get("source_vwap_ask"),
        "target_vwap_bid": (default_vwap or {}).get("target_vwap_bid"),
        "vwap_result": default_vwap,
    }


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
