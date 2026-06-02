from __future__ import annotations

from typing import Any


def safe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:  # NaN
        return None
    return number


def compute_domestic_spread(source_ask: Any, target_bid: Any) -> float | None:
    ask = safe_float(source_ask)
    bid = safe_float(target_bid)
    if ask is None or bid is None:
        return None
    return bid - ask


def compute_domestic_spread_pct(source_ask: Any, target_bid: Any) -> float | None:
    ask = safe_float(source_ask)
    spread = compute_domestic_spread(source_ask, target_bid)
    if ask is None or ask <= 0 or spread is None:
        return None
    return (spread / ask) * 100


def compute_estimated_net_gap_pct(
    gross_gap_pct: Any,
    source_fee_pct: Any,
    target_fee_pct: Any,
    estimated_slippage_pct: Any,
    safety_buffer_pct: Any,
) -> float | None:
    values = [
        safe_float(gross_gap_pct),
        safe_float(source_fee_pct),
        safe_float(target_fee_pct),
        safe_float(estimated_slippage_pct),
        safe_float(safety_buffer_pct),
    ]
    if any(value is None for value in values):
        return None
    gross, source_fee, target_fee, slippage, buffer = values
    return gross - source_fee - target_fee - slippage - buffer


def compute_domestic_mid(best_bid: Any, best_ask: Any) -> float | None:
    bid = safe_float(best_bid)
    ask = safe_float(best_ask)
    if bid is None or ask is None:
        return None
    return (bid + ask) / 2


def compute_global_usdt_depeg_pct(global_usdt_mid: Any) -> float | None:
    mid = safe_float(global_usdt_mid)
    if mid is None:
        return None
    return (mid - 1.0) * 100


def classify_global_usdt_health(global_usdt_mid: Any, depeg_threshold_pct: Any) -> dict[str, Any]:
    depeg_pct = compute_global_usdt_depeg_pct(global_usdt_mid)
    threshold = safe_float(depeg_threshold_pct)
    if depeg_pct is None or threshold is None or threshold < 0:
        return {"status": "unknown", "global_usdt_depeg_pct": depeg_pct, "global_usdt_depeg_flag": None}
    depeg = abs(depeg_pct) >= threshold
    return {
        "status": "depeg" if depeg else "healthy",
        "global_usdt_depeg_pct": depeg_pct,
        "global_usdt_depeg_flag": depeg,
    }


def classify_domestic_spread_side(source_venue: Any, target_venue: Any) -> str | None:
    source = str(source_venue or "").strip().lower()
    target = str(target_venue or "").strip().lower()
    if not source or not target or source == target:
        return None
    return f"buy_{source}_sell_{target}"
