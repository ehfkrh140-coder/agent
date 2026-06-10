"""Analysis-only Depth/VWAP context builders.

This module is analysis-only. It does not place orders. It does not check
balances. It does not check account-specific fill feasibility. It does not
imply execution permission. VWAP context is not trading signal.
NO_TRADE_ONLY posture must be preserved by callers.

The functions consume caller-provided public/mock observation dictionaries only.
They do not perform network I/O, file I/O, env-var lookup, credential lookup,
config lookup, registry lookup, adapter/parser/readiness integration, sampling,
alerting, Council calls, or execution behavior.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from src.market_data.depth_vwap import calculate_vwap_for_notional, calculate_vwap_for_size

NO_TRADE_EXECUTION_POLICY = "NO_TRADE_ONLY"
_DIAGNOSTICS_ONLY = "diagnostics_only"
_VALID_SIDES = {"ask", "bid"}


def extract_depth_levels_from_observation(observation: dict[str, Any], *, side: str) -> dict[str, Any]:
    """Extract one side of depth levels from a parser-style observation dict.

    Missing levels are reported as warnings rather than exceptions because
    absence of depth means only that VWAP context is unavailable.
    """

    warnings: list[str] = []
    if side not in _VALID_SIDES:
        return {"side": side, "levels": [], "levels_available": 0, "depth_available": False, "warnings": [f"unsupported_side:{side!r}"]}
    if not isinstance(observation, dict):
        return {"side": side, "levels": [], "levels_available": 0, "depth_available": False, "warnings": ["observation_must_be_dict"]}

    levels = _find_side_levels(observation, side=side, warnings=warnings)
    if levels is None:
        warnings.append(f"depth_{side}_levels_not_found")
        levels = []

    levels_available = _levels_available(levels)
    if levels_available == 0:
        warnings.append(f"depth_{side}_levels_empty")

    return {
        "side": side,
        "levels": levels,
        "levels_available": levels_available,
        "depth_available": levels_available > 0,
        "warnings": warnings,
    }


def build_observation_vwap_context(
    observation: dict[str, Any],
    *,
    target_size: Any | None = None,
    target_notional: Any | None = None,
) -> dict[str, Any]:
    """Build ask/bid VWAP diagnostics context for one observation."""

    warnings: list[str] = []
    target_mode = _target_mode(target_size=target_size, target_notional=target_notional, warnings=warnings)
    ask_extraction = extract_depth_levels_from_observation(observation, side="ask")
    bid_extraction = extract_depth_levels_from_observation(observation, side="bid")
    warnings.extend(_prefixed_warnings("ask", ask_extraction["warnings"]))
    warnings.extend(_prefixed_warnings("bid", bid_extraction["warnings"]))

    ask_result = None
    bid_result = None
    if target_mode == "size":
        ask_result = calculate_vwap_for_size(ask_extraction["levels"], target_size, side="ask")
        bid_result = calculate_vwap_for_size(bid_extraction["levels"], target_size, side="bid")
    elif target_mode == "notional":
        ask_result = calculate_vwap_for_notional(ask_extraction["levels"], target_notional, side="ask")
        bid_result = calculate_vwap_for_notional(bid_extraction["levels"], target_notional, side="bid")

    context_warnings = list(warnings)
    for label, result in (("ask", ask_result), ("bid", bid_result)):
        if isinstance(result, dict):
            context_warnings.extend(_prefixed_warnings(label, result.get("warnings", [])))

    return {
        "behavior": _DIAGNOSTICS_ONLY,
        "no_trade_only": True,
        "execution_policy": NO_TRADE_EXECUTION_POLICY,
        "target_size": target_size if target_mode == "size" else None,
        "target_notional": target_notional if target_mode == "notional" else None,
        "ask_vwap_result": ask_result,
        "bid_vwap_result": bid_result,
        "depth_available": bool(ask_extraction["depth_available"] and bid_extraction["depth_available"]),
        "ask_levels_available": ask_extraction["levels_available"],
        "bid_levels_available": bid_extraction["levels_available"],
        "warnings": _dedupe(context_warnings),
    }


def build_spot_futures_basis_vwap_context(
    source_bundle: dict[str, Any],
    *,
    target_size: Any | None = None,
    target_notional: Any | None = None,
) -> dict[str, Any]:
    """Build diagnostics-only VWAP context for spot/perp basis observations."""

    warnings: list[str] = []
    if not isinstance(source_bundle, dict):
        source_bundle = {}
        warnings.append("source_bundle_must_be_dict")
    target_mode = _target_mode(target_size=target_size, target_notional=target_notional, warnings=warnings)

    spot_observation = source_bundle.get("spot_observation")
    perp_observation = source_bundle.get("perp_observation")
    if not isinstance(spot_observation, dict):
        spot_observation = {}
        warnings.append("spot_observation_missing_or_not_dict")
    if not isinstance(perp_observation, dict):
        perp_observation = {}
        warnings.append("perp_observation_missing_or_not_dict")

    spot = build_observation_vwap_context(
        spot_observation,
        target_size=target_size,
        target_notional=target_notional,
    )
    perp = build_observation_vwap_context(
        perp_observation,
        target_size=target_size,
        target_notional=target_notional,
    )
    warnings.extend(_prefixed_warnings("spot", spot.get("warnings", [])))
    warnings.extend(_prefixed_warnings("perp", perp.get("warnings", [])))

    return {
        "behavior": _DIAGNOSTICS_ONLY,
        "no_trade_only": True,
        "execution_policy": NO_TRADE_EXECUTION_POLICY,
        "target_size": target_size if target_mode == "size" else None,
        "target_notional": target_notional if target_mode == "notional" else None,
        "spot": _observation_context_summary(spot),
        "perp": _observation_context_summary(perp),
        "directions": _direction_context(spot, perp),
        "warnings": _dedupe(warnings),
    }


def _find_side_levels(observation: dict[str, Any], *, side: str, warnings: list[str]) -> Any | None:
    plural = "asks" if side == "ask" else "bids"
    explicit_key = "ask_levels" if side == "ask" else "bid_levels"
    depth_key = "depth_asks" if side == "ask" else "depth_bids"

    for container_key in ("depth", "orderbook_depth"):
        container = observation.get(container_key)
        if isinstance(container, dict) and container.get(plural) is not None:
            return container.get(plural)

    if observation.get(explicit_key) is not None:
        return observation.get(explicit_key)
    if observation.get(depth_key) is not None:
        return observation.get(depth_key)

    liquidity = observation.get("liquidity")
    if isinstance(liquidity, dict):
        depth_levels = liquidity.get("depth_levels")
        if isinstance(depth_levels, dict):
            if depth_levels.get(plural) is not None:
                return depth_levels.get(plural)
            warnings.append(f"liquidity_depth_levels_missing_{plural}")
        elif depth_levels is not None:
            warnings.append("liquidity_depth_levels_not_explicit_by_side")

    return None


def _target_mode(*, target_size: Any | None, target_notional: Any | None, warnings: list[str]) -> str | None:
    if target_size is not None:
        if target_notional is not None:
            warnings.append("target_size_preferred_over_target_notional")
        return "size"
    if target_notional is not None:
        return "notional"
    warnings.append("depth_vwap_target_not_provided")
    return None


def _observation_context_summary(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "ask_vwap_result": context.get("ask_vwap_result"),
        "bid_vwap_result": context.get("bid_vwap_result"),
        "depth_available": context.get("depth_available", False),
        "ask_levels_available": context.get("ask_levels_available", 0),
        "bid_levels_available": context.get("bid_levels_available", 0),
        "warnings": context.get("warnings", []),
    }


def _direction_context(spot: dict[str, Any], perp: dict[str, Any]) -> dict[str, Any]:
    spot_ask = _result_or_empty(spot.get("ask_vwap_result"))
    spot_bid = _result_or_empty(spot.get("bid_vwap_result"))
    perp_ask = _result_or_empty(perp.get("ask_vwap_result"))
    perp_bid = _result_or_empty(perp.get("bid_vwap_result"))
    return {
        "long_spot_short_perp": {
            "spot_vwap_ask": spot_ask.get("vwap"),
            "perp_vwap_bid": perp_bid.get("vwap"),
            "depth_coverage_pct": _min_decimal_or_none(spot_ask.get("depth_coverage_pct"), perp_bid.get("depth_coverage_pct")),
            "insufficient_depth": bool(spot_ask.get("insufficient_depth", True) or perp_bid.get("insufficient_depth", True)),
            "context_only": True,
        },
        "long_perp_short_spot": {
            "perp_vwap_ask": perp_ask.get("vwap"),
            "spot_vwap_bid": spot_bid.get("vwap"),
            "depth_coverage_pct": _min_decimal_or_none(perp_ask.get("depth_coverage_pct"), spot_bid.get("depth_coverage_pct")),
            "insufficient_depth": bool(perp_ask.get("insufficient_depth", True) or spot_bid.get("insufficient_depth", True)),
            "context_only": True,
        },
    }


def _result_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _levels_available(levels: Any) -> int:
    if levels is None or isinstance(levels, (str, bytes)):
        return 0
    if hasattr(levels, "__len__"):
        try:
            return len(levels)  # type: ignore[arg-type]
        except TypeError:
            return 0
    return 0


def _min_decimal_or_none(*values: Any) -> Decimal | None:
    decimals: list[Decimal] = []
    for value in values:
        if isinstance(value, Decimal):
            decimals.append(value)
        elif value is not None:
            try:
                decimals.append(Decimal(str(value)))
            except Exception:  # noqa: BLE001 - context warning path must not raise
                continue
    if not decimals:
        return None
    return min(decimals)


def _prefixed_warnings(prefix: str, warnings: Any) -> list[str]:
    if not isinstance(warnings, list):
        return []
    return [f"{prefix}:{warning}" for warning in warnings if isinstance(warning, str)]


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        if value not in deduped:
            deduped.append(value)
    return deduped
