from __future__ import annotations

from typing import Any, Literal

Side = Literal["buy", "sell"]


def compute_buy_vwap_from_asks(depth_levels: list[dict[str, Any]], target_notional: float) -> dict[str, Any]:
    """Compute quote-notional buy VWAP by consuming ask_price/ask_size levels."""

    return _compute_vwap(depth_levels, target_notional, side="buy")


def compute_sell_vwap_from_bids(depth_levels: list[dict[str, Any]], target_notional: float) -> dict[str, Any]:
    """Compute quote-notional sell VWAP by consuming bid_price/bid_size levels."""

    return _compute_vwap(depth_levels, target_notional, side="sell")


def compute_executable_notional(depth_levels: list[dict[str, Any]], side: Side) -> float:
    """Return the quote notional available on one side of compact depth levels."""

    price_key, size_key = _side_keys(side)
    total = 0.0
    for level in depth_levels or []:
        price = _safe_float(level.get(price_key))
        size = _safe_float(level.get(size_key))
        if price is None or size is None or price <= 0 or size <= 0:
            continue
        total += price * size
    return total


def compute_slippage_pct(top_price: float | None, vwap_price: float | None, side: Side) -> float | None:
    """Compute top-of-book to VWAP degradation percentage for buy or sell."""

    if top_price is None or vwap_price is None or top_price <= 0:
        return None
    if side == "buy":
        return max(0.0, ((vwap_price - top_price) / top_price) * 100)
    return max(0.0, ((top_price - vwap_price) / top_price) * 100)


def _compute_vwap(depth_levels: list[dict[str, Any]], target_notional: float, *, side: Side) -> dict[str, Any]:
    price_key, size_key = _side_keys(side)
    target = float(target_notional or 0)
    filled_notional = 0.0
    filled_base_size = 0.0
    levels_consumed = 0
    top_price: float | None = None
    if target <= 0:
        return {
            "target_notional": target,
            "filled_notional": 0.0,
            "vwap_price": None,
            "top_price": None,
            "slippage_pct": None,
            "levels_consumed": 0,
            "fully_filled": False,
        }
    for level in depth_levels or []:
        price = _safe_float(level.get(price_key))
        size = _safe_float(level.get(size_key))
        if price is None or size is None or price <= 0 or size <= 0:
            continue
        if top_price is None:
            top_price = price
        remaining = target - filled_notional
        if remaining <= 0:
            break
        available_notional = price * size
        fill_notional = min(available_notional, remaining)
        filled_notional += fill_notional
        filled_base_size += fill_notional / price
        levels_consumed += 1
        if filled_notional >= target:
            break
    vwap_price = filled_notional / filled_base_size if filled_base_size > 0 else None
    return {
        "target_notional": target,
        "filled_notional": filled_notional,
        "vwap_price": vwap_price,
        "top_price": top_price,
        "slippage_pct": compute_slippage_pct(top_price, vwap_price, side),
        "levels_consumed": levels_consumed,
        "fully_filled": filled_notional >= target,
    }


def _side_keys(side: Side) -> tuple[str, str]:
    if side == "buy":
        return "ask_price", "ask_size"
    if side == "sell":
        return "bid_price", "bid_size"
    raise ValueError(f"Unsupported VWAP side: {side!r}")


def _safe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
