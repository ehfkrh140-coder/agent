from __future__ import annotations

from typing import Any


def compute_orderbook_imbalance(
    observation: Any,
    *,
    threshold: float = 1.5,
    target_notional: float | None = None,
    max_data_age_ms: int | float | None = None,
    freshness_pass: bool | None = None,
) -> dict[str, Any]:
    """Compute read-only orderbook depth imbalance metrics from public depth levels."""

    depth_levels = _depth_levels(observation)
    bid_depth_notional = 0.0
    ask_depth_notional = 0.0
    levels_used = 0
    for level in depth_levels:
        if not isinstance(level, dict):
            continue
        bid_depth_notional += _notional(level.get("bid_price"), level.get("bid_size"))
        ask_depth_notional += _notional(level.get("ask_price"), level.get("ask_size"))
        side = level.get("side")
        if side == "bid":
            bid_depth_notional += _notional(level.get("price"), level.get("size"))
        elif side == "ask":
            ask_depth_notional += _notional(level.get("price"), level.get("size"))
        levels_used += 1

    imbalance_ratio = _imbalance_ratio(bid_depth_notional, ask_depth_notional)
    imbalance_side = _imbalance_side(bid_depth_notional, ask_depth_notional, imbalance_ratio, threshold)
    spread_pct = _spread_pct(_value(observation, "bid"), _value(observation, "ask"))
    liquidity_pass = _liquidity_pass(bid_depth_notional, ask_depth_notional, target_notional)
    effective_freshness = freshness_pass if freshness_pass is not None else _freshness_from_observation(observation, max_data_age_ms)
    imbalance_pass = imbalance_side in {"BID_HEAVY", "ASK_HEAVY"}
    direction = {
        "BID_HEAVY": "bid_heavy_orderbook_signal",
        "ASK_HEAVY": "ask_heavy_orderbook_signal",
        "BALANCED": "balanced_orderbook_signal",
    }[imbalance_side]
    return {
        "bid_depth_notional": bid_depth_notional,
        "ask_depth_notional": ask_depth_notional,
        "imbalance_ratio": imbalance_ratio,
        "spread_pct": spread_pct,
        "depth_levels_used": levels_used,
        "target_notional": target_notional,
        "imbalance_side": imbalance_side,
        "direction": direction,
        "freshness_pass": effective_freshness,
        "liquidity_pass": liquidity_pass,
        "imbalance_pass": imbalance_pass,
    }


def _depth_levels(observation: Any) -> list[dict[str, Any]]:
    liquidity = _value(observation, "liquidity")
    if isinstance(liquidity, dict):
        levels = liquidity.get("depth_levels")
    else:
        levels = getattr(liquidity, "depth_levels", None)
    return levels if isinstance(levels, list) else []


def _freshness_from_observation(observation: Any, max_data_age_ms: int | float | None) -> bool | None:
    if max_data_age_ms is None:
        return None
    data_quality = _value(observation, "data_quality")
    age = data_quality.get("max_data_age_ms") if isinstance(data_quality, dict) else getattr(data_quality, "max_data_age_ms", None)
    numeric_age = _float(age)
    return False if numeric_age is None else numeric_age <= float(max_data_age_ms)


def _notional(price: Any, size: Any) -> float:
    numeric_price = _float(price)
    numeric_size = _float(size)
    if numeric_price is None or numeric_size is None:
        return 0.0
    return numeric_price * numeric_size


def _imbalance_ratio(bid_depth_notional: float, ask_depth_notional: float) -> float | None:
    if bid_depth_notional <= 0 and ask_depth_notional <= 0:
        return None
    if bid_depth_notional <= 0 or ask_depth_notional <= 0:
        return float("inf")
    return max(bid_depth_notional, ask_depth_notional) / min(bid_depth_notional, ask_depth_notional)


def _imbalance_side(bid_depth_notional: float, ask_depth_notional: float, imbalance_ratio: float | None, threshold: float) -> str:
    if imbalance_ratio is None or imbalance_ratio < threshold:
        return "BALANCED"
    if bid_depth_notional > ask_depth_notional:
        return "BID_HEAVY"
    if ask_depth_notional > bid_depth_notional:
        return "ASK_HEAVY"
    return "BALANCED"


def _liquidity_pass(bid_depth_notional: float, ask_depth_notional: float, target_notional: float | None) -> bool | None:
    if target_notional is None:
        return None
    return bid_depth_notional >= target_notional and ask_depth_notional >= target_notional


def _spread_pct(bid: Any, ask: Any) -> float | None:
    numeric_bid = _float(bid)
    numeric_ask = _float(ask)
    if numeric_bid is None or numeric_ask in (None, 0):
        return None
    return ((numeric_ask - numeric_bid) / numeric_ask) * 100


def _value(observation: Any, key: str) -> Any:
    if isinstance(observation, dict):
        return observation.get(key)
    return getattr(observation, key, None)


def _float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
