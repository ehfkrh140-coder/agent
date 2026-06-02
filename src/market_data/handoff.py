from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.schemas.opportunity_packet import DetectorMetadata, OpportunityCandidate, OpportunityPacket


def build_handoff_packet_from_sampling_result(result: dict[str, Any]) -> OpportunityPacket | None:
    """Build an OpportunityPacket handoff only for persistent ready sampling results."""

    summary = result.get("summary") or {}
    if summary.get("persistence_status") != "PERSISTENT_READY_EDGE":
        return None
    sample = _best_ready_sample(result.get("samples") or [])
    if sample is None:
        return None
    packet_payload = sample.get("opportunity_packet")
    if not isinstance(packet_payload, dict):
        return None
    source_packet = OpportunityPacket.model_validate(packet_payload)
    candidate = _matching_candidate(source_packet.candidates, sample.get("best_candidate") or {})
    if candidate is None:
        return None
    adapter_id = result.get("adapter_id") or summary.get("adapter_id") or "unknown_adapter"
    created_at = datetime.now(timezone.utc)
    source_files = []
    sampling_output_file = result.get("sampling_output_file")
    if sampling_output_file:
        source_files.append(str(sampling_output_file))
    return OpportunityPacket(
        packet_id=f"handoff_{adapter_id}_{created_at.strftime('%Y%m%d_%H%M%S')}",
        created_at_utc=created_at,
        asset=source_packet.asset,
        quote=source_packet.quote,
        signal_type=source_packet.signal_type or "cross_exchange_spot_spread",
        strategy_family=source_packet.strategy_family,
        strategy_id=source_packet.strategy_id,
        observations=source_packet.observations,
        candidates=[candidate],
        human_context=None,
        detector_metadata=DetectorMetadata(
            detector_name="market_sampling_handoff_builder",
            detector_version="v1",
            generated_from="sampling_persistence",
            source_files=source_files,
        ),
        extensions={
            "sampling_summary": summary,
            "sample_count": summary.get("samples_ok"),
            "persistence_status": summary.get("persistence_status"),
            "best_sample_indices": [sample.get("sample_index")],
            "source_packet_id": source_packet.packet_id,
        },
    )


def write_handoff_packet(packet: OpportunityPacket, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(packet.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return path


def _best_ready_sample(samples: list[dict[str, Any]]) -> dict[str, Any] | None:
    ready = [sample for sample in samples if sample.get("status") == "ok" and sample.get("readiness_pass") is True]
    if not ready:
        return None
    return max(ready, key=lambda sample: _net_gap(sample.get("best_candidate") or {}))


def _matching_candidate(candidates: list[OpportunityCandidate], best_candidate: dict[str, Any]) -> OpportunityCandidate | None:
    candidate_id = best_candidate.get("candidate_id")
    if candidate_id:
        for candidate in candidates:
            if candidate.candidate_id == candidate_id:
                return candidate
    if candidates:
        return max(candidates, key=lambda candidate: candidate.estimated_net_gap_pct if candidate.estimated_net_gap_pct is not None else float("-inf"))
    return None


def _net_gap(candidate: dict[str, Any]) -> float:
    value = candidate.get("estimated_net_gap_pct")
    if value in (None, ""):
        return float("-inf")
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("-inf")
