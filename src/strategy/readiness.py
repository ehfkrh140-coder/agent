from __future__ import annotations

from typing import Any

from src.schemas.opportunity_packet import MarketObservation, OpportunityCandidate, OpportunityPacket
from src.strategy.registry import active_strategy, load_strategy_current, load_strategy_registry, strategy_by_family


def build_readiness_report(
    packet: OpportunityPacket,
    *,
    registry: dict[str, Any] | None = None,
    current: dict[str, Any] | None = None,
) -> dict[str, Any]:
    registry = registry or load_strategy_registry()
    current = current or load_strategy_current()
    family = packet.strategy_family or packet.signal_type
    strategy = strategy_by_family(family, registry) or {}
    if family == "cross_exchange_spot_spread":
        return _cross_exchange_report(packet, strategy, active_strategy(current))
    if family == "mark_orderbook_gap":
        return _mark_orderbook_report(packet, strategy, active_strategy(current))
    return {
        "strategy_family": family,
        "strategy_id": packet.strategy_id or strategy.get("strategy_id"),
        "strategy_status": strategy.get("status", "unknown"),
        "status": "NEED_DATA",
        "candidate_count": len(packet.candidates),
        "missing_required_fields": ["strategy_readiness_rules"],
        "warnings": ["unsupported_or_future_strategy"],
        "readiness_pass": False,
        "recommended_default_decision": "NEED_DATA",
        "basis": "unsupported strategy family for active v1",
    }


def _cross_exchange_report(packet: OpportunityPacket, strategy: dict[str, Any], active: dict[str, Any]) -> dict[str, Any]:
    missing: list[str] = []
    warnings: list[str] = []
    recommended = "NEED_DATA"
    if len(packet.observations) < 2:
        missing.append("observations>=2")
    obs_by_id = {obs.observation_id: obs for obs in packet.observations if obs.observation_id}
    if any(obs.instrument_type != "spot" for obs in packet.observations):
        warnings.append("non_spot_observation")
    if packet.observations and all(obs.last_price is not None and obs.bid is None and obs.ask is None for obs in packet.observations):
        warnings.append("last_price_only_candidate")
    if not packet.candidates:
        missing.append("candidate")
    for candidate in packet.candidates:
        if candidate.candidate_type != "spot_executable_spread_candidate":
            warnings.append("unexpected_candidate_type")
        if candidate.direction != "buy_source_ask_sell_target_bid_candidate":
            missing.append("candidate.direction")
        source = _find_observation(candidate.source_observation_id, candidate.source_venue_id, obs_by_id, packet.observations)
        target = _find_observation(candidate.target_observation_id, candidate.target_venue_id, obs_by_id, packet.observations)
        _check_spot_side("source", source, missing, warnings)
        _check_spot_side("target", target, missing, warnings)
        if candidate.estimated_net_gap_pct is None:
            missing.append("candidate.estimated_net_gap_pct")
        elif candidate.estimated_net_gap_pct <= 0:
            recommended = "REJECT"
            warnings.append("non_positive_estimated_net_gap")
        if candidate.freshness_pass is False:
            recommended = "REJECT"
            warnings.append("stale_candidate")
        if candidate.liquidity_pass is False:
            recommended = "REJECT"
            warnings.append("low_liquidity_candidate")
    missing = _dedupe(missing)
    warnings = _dedupe(warnings)
    readiness_pass = not missing and recommended != "REJECT" and not any(w in warnings for w in ["last_price_only_candidate", "stale_candidate", "low_liquidity_candidate"])
    if readiness_pass:
        recommended = "WATCH"
    return {
        "strategy_family": "cross_exchange_spot_spread",
        "strategy_id": active.get("strategy_id") or packet.strategy_id or strategy.get("strategy_id"),
        "strategy_status": strategy.get("status", "active"),
        "status": "READY" if readiness_pass else recommended,
        "candidate_count": len(packet.candidates),
        "missing_required_fields": missing,
        "warnings": warnings,
        "readiness_pass": readiness_pass,
        "recommended_default_decision": recommended,
        "basis": "source ask / target bid executable spread readiness",
    }


def _mark_orderbook_report(packet: OpportunityPacket, strategy: dict[str, Any], active: dict[str, Any]) -> dict[str, Any]:
    disabled = packet.strategy_family in set(active.get("disabled_strategy_families") or [])
    warnings = ["experimental_strategy"]
    if disabled:
        warnings.append("disabled_strategy_family")
    return {
        "strategy_family": "mark_orderbook_gap",
        "strategy_id": packet.strategy_id or strategy.get("strategy_id"),
        "strategy_status": strategy.get("status", "experimental"),
        "status": "NEED_DATA",
        "candidate_count": len(packet.candidates),
        "missing_required_fields": [],
        "warnings": warnings,
        "readiness_pass": False,
        "recommended_default_decision": "NEED_DATA",
        "basis": "experimental strategy; current active v1 strategy does not use mark/index/leverage",
    }


def _find_observation(
    observation_id: str | None,
    venue_id: str | None,
    obs_by_id: dict[str, MarketObservation],
    observations: list[MarketObservation],
) -> MarketObservation | None:
    if observation_id and observation_id in obs_by_id:
        return obs_by_id[observation_id]
    if venue_id:
        for obs in observations:
            if obs.venue_id == venue_id:
                return obs
    return None


def _check_spot_side(prefix: str, obs: MarketObservation | None, missing: list[str], warnings: list[str]) -> None:
    if obs is None:
        missing.append(f"{prefix}.observation")
        return
    if prefix == "source" and obs.ask is None:
        missing.append("source.ask")
    if prefix == "target" and obs.bid is None:
        missing.append("target.bid")
    if obs.fees is None:
        missing.append(f"{prefix}.fees")
    if obs.liquidity is None or not obs.liquidity.orderbook_depth_available or not obs.liquidity.depth_levels:
        missing.append(f"{prefix}.orderbook_depth")
    if obs.timestamp_utc is None:
        missing.append(f"{prefix}.timestamp")
    if obs.data_quality is None or obs.data_quality.max_data_age_ms is None:
        missing.append(f"{prefix}.data_age_ms")
    elif obs.data_quality.timestamps_available is False:
        missing.append(f"{prefix}.timestamp")
    if obs.data_quality and obs.data_quality.max_data_age_ms is not None:
        # The configured threshold is checked through candidate.freshness_pass; this warning is descriptive only.
        pass
    if obs.bid is None and obs.ask is None and obs.last_price is not None:
        warnings.append("last_price_only_candidate")


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
