"""Pure OpportunityPacket builder for Spot-Futures Basis mocked source bundles.

The builder consumes already-normalized parser source bundles and readiness
results, then returns an ``opportunity_packet_v0`` compatible dictionary. It is
intentionally pure: no network I/O, no file reads/writes, no adapter or registry
wiring, no alerting, no Council calls, and no execution behavior.
"""

from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "opportunity_packet_v0"
STRATEGY_FAMILY = "spot_futures_basis"
STRATEGY_ID = "spot_futures_basis_v0"
SIGNAL_TYPE = "spot_futures_basis"
ASSET = "BTC"
QUOTE = "USDT"
SOURCE_VENUE_ID = "binance"
COMPARISON_TYPE = "same_exchange_spot_perp_basis"
NO_TRADE_EXECUTION_POLICY = "NO_TRADE_ONLY"
STATUS = "experimental_non_active_no_trade_only"

SPOT_OBSERVATION_ID = "binance_spot_btcusdt_spot_futures_basis"
PERP_OBSERVATION_ID = "binance_usdm_btcusdt_perp_spot_futures_basis"
CANDIDATE_ID = "binance_btcusdt_spot_futures_basis_candidate"

REQUIRED_PACKET_ASSUMPTIONS = (
    "public no-key endpoints only",
    "analysis-only packet",
    "no private API",
    "no trading behavior",
    "mark price is not executable",
    "last price is weak context only if present",
    "WATCH is not ENTER",
    "WATCH does not trigger Council auto-call, alert, or execution",
    "spot/perp symbol string equality does not imply product equivalence",
    "funding rate is context, not basis decision alone",
)

REQUIRED_METRIC_FIELDS = (
    "readiness_status",
    "recommended_default_decision",
    "readiness_pass",
    "spot_bid",
    "spot_ask",
    "perp_bid",
    "perp_ask",
    "spot_mid",
    "perp_mid",
    "mid_basis_pct",
    "long_spot_short_perp_gross_pct",
    "long_perp_short_spot_gross_pct",
    "selected_direction",
    "selected_gross_basis_pct",
    "fee_slippage_buffer_pct",
    "estimated_net_basis_pct",
    "parser_normalized_status",
    "comparability_pass",
    "freshness_pass",
    "liquidity_pass",
)


def build_spot_futures_basis_opportunity_packet(
    source_bundle: dict[str, Any],
    readiness_result: dict[str, Any],
    *,
    created_at_utc: str,
    packet_id: str | None = None,
) -> dict[str, Any]:
    """Build a pure analysis-only Spot-Futures Basis OpportunityPacket dict."""

    _require_mapping(source_bundle, "source_bundle")
    _require_mapping(readiness_result, "readiness_result")
    if not isinstance(created_at_utc, str) or not created_at_utc:
        raise ValueError("created_at_utc must be a non-empty string")

    spot_observation = source_bundle.get("spot_observation")
    perp_observation = source_bundle.get("perp_observation")
    if not isinstance(spot_observation, dict):
        spot_observation = {}
    if not isinstance(perp_observation, dict):
        perp_observation = {}

    effective_packet_id = packet_id or _deterministic_packet_id(source_bundle, created_at_utc)
    packet_assumptions = _merged_assumptions(
        source_bundle.get("assumptions"),
        readiness_result.get("assumptions"),
        REQUIRED_PACKET_ASSUMPTIONS,
    )
    readiness_summary = _readiness_summary(readiness_result)

    identity = _packet_identity(source_bundle, spot_observation, perp_observation)
    spot_packet_observation = _spot_packet_observation(spot_observation, identity["spot_observation_id"])
    perp_packet_observation = _perp_packet_observation(perp_observation, identity["perp_observation_id"])
    candidate = _basis_candidate(readiness_result, packet_assumptions, identity)

    return {
        "schema_version": SCHEMA_VERSION,
        "packet_id": effective_packet_id,
        "created_at_utc": created_at_utc,
        "asset": ASSET,
        "quote": QUOTE,
        "signal_type": SIGNAL_TYPE,
        "strategy_family": STRATEGY_FAMILY,
        "strategy_id": STRATEGY_ID,
        "observations": [spot_packet_observation, perp_packet_observation],
        "candidates": [candidate],
        "detector_metadata": {
            "detector_name": "spot_futures_basis_packet_builder",
            "detector_version": "v0",
            "generated_from": identity["generated_from"],
            "source_files": [
                "src/market_data/parsers/spot_futures_basis.py",
                "src/strategy/spot_futures_basis_readiness.py",
                "src/market_data/spot_futures_basis_packet_builder.py",
            ],
        },
        "human_context": None,
        "expected_behavior": None,
        "extensions": {
            "no_trade_only": True,
            "execution_policy": NO_TRADE_EXECUTION_POLICY,
            "status": STATUS,
            "source_venue_id": identity["source_venue_id"],
            "comparison_type": source_bundle.get("comparison_type", COMPARISON_TYPE),
            "assumptions": packet_assumptions,
            "readiness": readiness_summary,
            "parser_source_bundle_summary": _source_bundle_summary(source_bundle),
        },
    }


def _spot_packet_observation(observation: dict[str, Any], observation_id: str) -> dict[str, Any]:
    depth_available = _has_depth(observation)
    data_age_ms = observation.get("data_age_ms")
    latency_ms = observation.get("latency_ms")
    return {
        "observation_id": observation_id,
        "venue_id": observation.get("venue_id", SOURCE_VENUE_ID),
        "venue_name": observation.get("venue_name", "Binance Spot"),
        "market_symbol": observation.get("symbol", "BTCUSDT"),
        "instrument_type": "spot",
        "region": "GLOBAL",
        "bid": observation.get("best_bid"),
        "ask": observation.get("best_ask"),
        "bid_size": observation.get("best_bid_qty"),
        "ask_size": observation.get("best_ask_qty"),
        "tick": observation.get("tick_size"),
        "step": observation.get("step_size"),
        "timestamp_utc": None,
        "liquidity": {"orderbook_depth_available": depth_available},
        "data_quality": {
            "latency_ms": _coerce_optional_int_ms(latency_ms),
            "data_age_ms": _coerce_optional_int_ms(data_age_ms),
            "max_data_age_ms": _coerce_optional_int_ms(data_age_ms),
        },
        "health": {"api_status_known": True, "api_ok": True},
        "extensions": {
            "market_type": "spot",
            "category": observation.get("category", "spot"),
            "base_asset": observation.get("base_asset", ASSET),
            "quote_asset": observation.get("quote_asset", QUOTE),
            "bid_qty_unit": observation.get("bid_qty_unit", "base_asset"),
            "ask_qty_unit": observation.get("ask_qty_unit", "base_asset"),
            "parser_normalized_status": observation.get("parser_normalized_status"),
            "required_missing_fields": _list_or_empty(observation.get("required_missing_fields")),
            "raw_endpoint_ids": _list_or_empty(observation.get("raw_endpoint_ids")),
            "book_update_id": observation.get("book_update_id"),
            "min_notional": observation.get("min_notional"),
            "raw_data_age_ms": _raw_optional_number(data_age_ms),
            "raw_latency_ms": _raw_optional_number(latency_ms),
        },
    }


def _perp_packet_observation(observation: dict[str, Any], observation_id: str) -> dict[str, Any]:
    depth_available = _has_depth(observation)
    data_age_ms = observation.get("data_age_ms")
    latency_ms = observation.get("latency_ms")
    return {
        "observation_id": observation_id,
        "venue_id": observation.get("venue_id", SOURCE_VENUE_ID),
        "venue_name": observation.get("venue_name", "Binance USDⓈ-M Futures"),
        "market_symbol": observation.get("symbol", "BTCUSDT"),
        "instrument_type": "linear_perpetual",
        "region": "GLOBAL",
        "bid": observation.get("best_bid"),
        "ask": observation.get("best_ask"),
        "bid_size": observation.get("best_bid_qty"),
        "ask_size": observation.get("best_ask_qty"),
        "mark_price": observation.get("mark_price"),
        "index_price": observation.get("index_price"),
        "tick": observation.get("tick_size"),
        "step": observation.get("step_size"),
        "timestamp_utc": observation.get("book_timestamp"),
        "liquidity": {"orderbook_depth_available": depth_available},
        "derivatives": {
            "funding_rate_pct": observation.get("funding_rate"),
            "next_funding_time_utc": observation.get("next_funding_time"),
            "mark_price": observation.get("mark_price"),
            "index_price": observation.get("index_price"),
        },
        "data_quality": {
            "latency_ms": _coerce_optional_int_ms(latency_ms),
            "data_age_ms": _coerce_optional_int_ms(data_age_ms),
            "max_data_age_ms": _coerce_optional_int_ms(data_age_ms),
        },
        "health": {"api_status_known": True, "api_ok": True},
        "extensions": {
            "market_type": "perp",
            "category": observation.get("category"),
            "base_asset": observation.get("base_asset", ASSET),
            "quote_asset": observation.get("quote_asset", QUOTE),
            "settlement_asset": observation.get("settlement_asset", QUOTE),
            "margin_asset": observation.get("margin_asset", QUOTE),
            "contract_type": observation.get("contract_type", "PERPETUAL"),
            "funding_interval": observation.get("funding_interval"),
            "bid_qty_unit": observation.get("bid_qty_unit"),
            "ask_qty_unit": observation.get("ask_qty_unit"),
            "parser_normalized_status": observation.get("parser_normalized_status"),
            "required_missing_fields": _list_or_empty(observation.get("required_missing_fields")),
            "raw_endpoint_ids": _list_or_empty(observation.get("raw_endpoint_ids")),
            "book_timestamp": observation.get("book_timestamp"),
            "interest_rate": observation.get("interest_rate"),
            "min_notional": observation.get("min_notional"),
            "raw_data_age_ms": _raw_optional_number(data_age_ms),
            "raw_latency_ms": _raw_optional_number(latency_ms),
        },
    }


def _basis_candidate(
    readiness_result: dict[str, Any],
    assumptions: list[str],
    identity: dict[str, str],
) -> dict[str, Any]:
    metrics = _candidate_metrics(readiness_result)
    warnings = _list_or_empty(readiness_result.get("warnings"))
    required_missing_fields = _list_or_empty(readiness_result.get("required_missing_fields"))
    return {
        "candidate_id": identity["candidate_id"],
        "candidate_type": "spot_futures_basis_observation",
        "strategy_family": STRATEGY_FAMILY,
        "strategy_id": STRATEGY_ID,
        "source_observation_id": identity["spot_observation_id"],
        "target_observation_id": identity["perp_observation_id"],
        "source_venue_id": identity["source_venue_id"],
        "target_venue_id": identity["source_venue_id"],
        "direction": metrics.get("selected_direction"),
        "gross_gap_absolute": None,
        "gross_gap_pct": metrics.get("selected_gross_basis_pct"),
        "estimated_net_gap_pct": metrics.get("estimated_net_basis_pct"),
        "liquidity_pass": metrics.get("liquidity_pass"),
        "freshness_pass": metrics.get("freshness_pass"),
        "guard_pass": _guard_pass(readiness_result, assumptions),
        "metrics": metrics,
        "required_missing_fields": required_missing_fields,
        "assumptions": assumptions,
        "extensions": {
            "warnings": warnings,
            "comparability_pass": metrics.get("comparability_pass"),
            "no_trade_only": True,
            "execution_policy": NO_TRADE_EXECUTION_POLICY,
        },
    }



def _packet_identity(
    source_bundle: dict[str, Any],
    spot_observation: dict[str, Any],
    perp_observation: dict[str, Any],
) -> dict[str, str]:
    source_venue_id = _safe_identifier(
        source_bundle.get("source_venue_id")
        or spot_observation.get("venue_id")
        or perp_observation.get("venue_id")
        or SOURCE_VENUE_ID
    )
    symbol = _safe_identifier(
        spot_observation.get("symbol") or perp_observation.get("symbol") or "BTCUSDT"
    )

    if source_venue_id == SOURCE_VENUE_ID:
        return {
            "source_venue_id": SOURCE_VENUE_ID,
            "spot_observation_id": SPOT_OBSERVATION_ID,
            "perp_observation_id": PERP_OBSERVATION_ID,
            "candidate_id": CANDIDATE_ID,
            "generated_from": "mocked_binance_spot_and_usdm_futures_source_bundle",
        }

    perp_market_label = _perp_market_label(source_venue_id, perp_observation)
    return {
        "source_venue_id": source_venue_id,
        "spot_observation_id": f"{source_venue_id}_spot_{symbol}_spot_futures_basis",
        "perp_observation_id": f"{source_venue_id}_{perp_market_label}_{symbol}_perp_spot_futures_basis",
        "candidate_id": f"{source_venue_id}_{symbol}_spot_futures_basis_candidate",
        "generated_from": f"mocked_{source_venue_id}_spot_and_{perp_market_label}_source_bundle",
    }


def _perp_market_label(source_venue_id: str, perp_observation: dict[str, Any]) -> str:
    category = _safe_identifier(perp_observation.get("category"))
    if source_venue_id == "bybit" and category == "linear":
        return "linear"
    if category:
        return category
    contract_type = _safe_identifier(perp_observation.get("contract_type"))
    if contract_type:
        return contract_type
    return "perp"


def _safe_identifier(value: Any) -> str:
    text = str(value or "").strip().lower()
    safe = []
    previous_underscore = False
    for char in text:
        if char.isalnum():
            safe.append(char)
            previous_underscore = False
        elif not previous_underscore:
            safe.append("_")
            previous_underscore = True
    return "".join(safe).strip("_")


def _candidate_metrics(readiness_result: dict[str, Any]) -> dict[str, Any]:
    source_metrics = readiness_result.get("metrics")
    if not isinstance(source_metrics, dict):
        source_metrics = {}
    metrics = {field: source_metrics.get(field) for field in REQUIRED_METRIC_FIELDS}
    metrics["readiness_status"] = readiness_result.get("readiness_status")
    metrics["recommended_default_decision"] = readiness_result.get("recommended_default_decision")
    metrics["readiness_pass"] = readiness_result.get("readiness_pass")
    return metrics


def _readiness_summary(readiness_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "readiness_status": readiness_result.get("readiness_status"),
        "recommended_default_decision": readiness_result.get("recommended_default_decision"),
        "readiness_pass": readiness_result.get("readiness_pass"),
        "required_missing_fields": _list_or_empty(readiness_result.get("required_missing_fields")),
        "warnings": _list_or_empty(readiness_result.get("warnings")),
    }


def _source_bundle_summary(source_bundle: dict[str, Any]) -> dict[str, Any]:
    spot = source_bundle.get("spot_observation")
    perp = source_bundle.get("perp_observation")
    if not isinstance(spot, dict):
        spot = {}
    if not isinstance(perp, dict):
        perp = {}
    return {
        "strategy_family": source_bundle.get("strategy_family", STRATEGY_FAMILY),
        "strategy_id": source_bundle.get("strategy_id", STRATEGY_ID),
        "status": source_bundle.get("status", STATUS),
        "source_venue_id": source_bundle.get("source_venue_id", SOURCE_VENUE_ID),
        "comparison_type": source_bundle.get("comparison_type", COMPARISON_TYPE),
        "spot_parser_normalized_status": spot.get("parser_normalized_status"),
        "perp_parser_normalized_status": perp.get("parser_normalized_status"),
    }


def _deterministic_packet_id(source_bundle: dict[str, Any], created_at_utc: str) -> str:
    strategy_id = source_bundle.get("strategy_id", STRATEGY_ID)
    source_venue_id = source_bundle.get("source_venue_id", SOURCE_VENUE_ID)
    safe_created_at = (
        created_at_utc.replace(":", "").replace("-", "").replace(".", "").replace("+", "").replace("Z", "z")
    )
    return f"{source_venue_id}_{strategy_id}_{safe_created_at}"


def _merged_assumptions(*assumption_groups: Any) -> list[str]:
    merged: list[str] = []
    for group in assumption_groups:
        if isinstance(group, str):
            candidates = [group]
        elif isinstance(group, (list, tuple, set)):
            candidates = list(group)
        else:
            candidates = []
        for assumption in candidates:
            if isinstance(assumption, str) and assumption not in merged:
                merged.append(assumption)
    return merged


def _guard_pass(readiness_result: dict[str, Any], assumptions: list[str]) -> bool:
    return (
        readiness_result.get("execution_policy") == NO_TRADE_EXECUTION_POLICY
        and readiness_result.get("no_trade_only") is True
        and "no trading behavior" in assumptions
        and "WATCH is not ENTER" in assumptions
    )


def _has_depth(observation: dict[str, Any]) -> bool:
    return bool(observation.get("depth_bids")) and bool(observation.get("depth_asks"))


def _list_or_empty(value: Any) -> list[Any]:
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    return []


def _coerce_optional_int_ms(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        try:
            return int(value)
        except (OverflowError, ValueError):
            return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(float(text))
        except (OverflowError, ValueError):
            return None
    return None


def _raw_optional_number(value: Any) -> int | float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            parsed = float(text)
        except ValueError:
            return None
        if parsed.is_integer():
            return int(parsed)
        return parsed
    return None


def _require_mapping(payload: dict[str, Any], name: str) -> None:
    if not isinstance(payload, dict):
        raise ValueError(f"{name} must be a dict")
