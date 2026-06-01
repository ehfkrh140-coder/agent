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
    if family == "orderbook_imbalance":
        return _orderbook_imbalance_report(packet, strategy, active_strategy(current))
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
        vwap_results = candidate.metrics.get("vwap_results") if isinstance(candidate.metrics, dict) else None
        default_vwap = vwap_results[0] if isinstance(vwap_results, list) and vwap_results else None
        if not default_vwap:
            missing.append("candidate.metrics.vwap_results")
            warnings.append("vwap_results_missing")
        else:
            if default_vwap.get("fully_filled_source") is False or default_vwap.get("fully_filled_target") is False:
                recommended = "REJECT"
                warnings.append("low_liquidity_candidate")
            if default_vwap.get("net_gap_pass") is False:
                recommended = "REJECT"
                warnings.append("vwap_net_gap_below_threshold")
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
    readiness_pass = not missing and recommended != "REJECT" and not any(w in warnings for w in ["last_price_only_candidate", "stale_candidate", "low_liquidity_candidate", "vwap_results_missing", "vwap_net_gap_below_threshold"])
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
        "basis": "source ask / target bid VWAP executable spread readiness",
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



def _orderbook_imbalance_report(packet: OpportunityPacket, strategy: dict[str, Any], active: dict[str, Any]) -> dict[str, Any]:
    missing: list[str] = []
    warnings: list[str] = ["experimental_strategy", "non_active_strategy"]
    threshold = _packet_threshold(packet, "imbalance_ratio_threshold", 1.5)
    max_data_age_ms = _packet_threshold(packet, "max_data_age_ms", 3000)
    target_notional = _packet_threshold(packet, "target_notional", None)
    best_signal: dict[str, Any] | None = None
    stale = False

    if not packet.observations:
        missing.append("observations")
    for index, obs in enumerate(packet.observations):
        prefix = obs.observation_id or obs.venue_id or f"observation_{index}"
        if obs.instrument_type != "spot":
            missing.append(f"{prefix}.instrument_type=spot")
        for field_name in ["bid", "ask", "bid_size", "ask_size"]:
            if getattr(obs, field_name) is None:
                missing.append(f"{prefix}.{field_name}")
        if obs.liquidity is None or not obs.liquidity.depth_levels:
            missing.append(f"{prefix}.liquidity.depth_levels")
        if obs.timestamp_utc is None and (obs.data_quality is None or not obs.data_quality.timestamps_available):
            missing.append(f"{prefix}.timestamp")
        if obs.data_quality is None or obs.data_quality.max_data_age_ms is None:
            missing.append(f"{prefix}.data_quality.max_data_age_ms")
        elif obs.data_quality.max_data_age_ms > max_data_age_ms:
            stale = True
            warnings.append("stale_orderbook_data")
        if obs.data_quality is None or obs.data_quality.latency_ms is None:
            missing.append(f"{prefix}.data_quality.latency_ms")
        signal = _orderbook_signal(obs, threshold=threshold, target_notional=target_notional)
        if signal and (best_signal is None or signal["imbalance_ratio"] > best_signal["imbalance_ratio"]):
            best_signal = signal

    if missing:
        recommended = "NEED_DATA"
        status = "NEED_DATA"
    elif stale:
        recommended = "REJECT"
        status = "REJECT"
    elif best_signal and best_signal.get("imbalance_pass"):
        recommended = "WATCH"
        status = "WATCH"
        warnings.append("experimental_watch_only")
    else:
        recommended = "REJECT"
        status = "REJECT"
        warnings.append("balanced_orderbook")

    return {
        "strategy_family": "orderbook_imbalance",
        "strategy_id": packet.strategy_id or strategy.get("strategy_id"),
        "strategy_status": strategy.get("status", "experimental"),
        "status": status,
        "candidate_count": len(packet.candidates),
        "missing_required_fields": _dedupe(missing),
        "warnings": _dedupe(warnings),
        "readiness_pass": False,
        "experimental_pass": bool(status == "WATCH" and best_signal and best_signal.get("imbalance_pass")),
        "recommended_default_decision": recommended,
        "basis": "experimental orderbook depth imbalance readiness; non-active and no Council handoff",
        "computed_metrics": best_signal or {},
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



def _packet_threshold(packet: OpportunityPacket, key: str, default: float | None) -> float | None:
    thresholds = getattr(packet, "thresholds", None)
    if isinstance(thresholds, dict) and thresholds.get(key) is not None:
        try:
            return float(thresholds[key])
        except (TypeError, ValueError):
            return default
    return default


def _orderbook_signal(obs: MarketObservation, *, threshold: float | None, target_notional: float | None) -> dict[str, Any] | None:
    if obs.liquidity is None or not obs.liquidity.depth_levels:
        return None
    bid_depth = 0.0
    ask_depth = 0.0
    levels_used = 0
    for level in obs.liquidity.depth_levels:
        bid_price = _float(level.get("bid_price"))
        bid_size = _float(level.get("bid_size"))
        ask_price = _float(level.get("ask_price"))
        ask_size = _float(level.get("ask_size"))
        side = level.get("side")
        price = _float(level.get("price"))
        size = _float(level.get("size"))
        if bid_price is not None and bid_size is not None:
            bid_depth += bid_price * bid_size
        if ask_price is not None and ask_size is not None:
            ask_depth += ask_price * ask_size
        if side == "bid" and price is not None and size is not None:
            bid_depth += price * size
        if side == "ask" and price is not None and size is not None:
            ask_depth += price * size
        levels_used += 1
    if bid_depth <= 0 and ask_depth <= 0:
        return None
    smaller = min(value for value in [bid_depth, ask_depth] if value > 0) if bid_depth > 0 and ask_depth > 0 else 0
    larger = max(bid_depth, ask_depth)
    ratio = larger / smaller if smaller > 0 else float("inf")
    if bid_depth > ask_depth and ratio >= (threshold or 1.5):
        side = "BID_HEAVY"
        direction = "bid_heavy_orderbook_signal"
        imbalance_pass = True
    elif ask_depth > bid_depth and ratio >= (threshold or 1.5):
        side = "ASK_HEAVY"
        direction = "ask_heavy_orderbook_signal"
        imbalance_pass = True
    else:
        side = "BALANCED"
        direction = "balanced_orderbook_signal"
        imbalance_pass = False
    spread_pct = None
    if obs.bid is not None and obs.ask is not None and obs.ask:
        spread_pct = ((obs.ask - obs.bid) / obs.ask) * 100
    liquidity_pass = True if target_notional is None else bid_depth >= target_notional and ask_depth >= target_notional
    return {
        "observation_id": obs.observation_id,
        "venue_id": obs.venue_id,
        "bid_depth_notional": bid_depth,
        "ask_depth_notional": ask_depth,
        "imbalance_ratio": ratio,
        "spread_pct": spread_pct,
        "depth_levels_used": levels_used,
        "target_notional": target_notional,
        "imbalance_side": side,
        "direction": direction,
        "freshness_pass": not (obs.data_quality and obs.data_quality.max_data_age_ms is not None and obs.data_quality.max_data_age_ms > 3000),
        "liquidity_pass": liquidity_pass,
        "imbalance_pass": imbalance_pass,
    }


def _float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
