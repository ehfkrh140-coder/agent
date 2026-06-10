"""Pure strategy-common Depth/VWAP helpers.

This module is analysis-only. It does not place orders. It does not check
balances. It does not check account-specific fill feasibility. It does not
imply execution permission. VWAP context is not trading signal.
NO_TRADE_ONLY posture must be preserved by callers.

The helpers consume caller-provided public/mock depth levels only. They do not
perform network I/O, file I/O, env-var lookup, credential lookup, config
lookup, registry lookup, or strategy-specific integration.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping

_VALID_SIDES = {"ask", "bid"}
_HUNDRED = Decimal("100")
_ZERO = Decimal("0")


def calculate_vwap_for_size(levels: Any, target_size: Any, *, side: str) -> dict[str, Any]:
    """Calculate VWAP by consuming depth until ``target_size`` is filled.

    Input levels are assumed to arrive best-to-worse for the given side. The
    helper validates monotonic price ordering and records warnings, but it does
    not sort, fetch, persist, or change any strategy behavior.
    """

    return _calculate_vwap(levels, target_size=target_size, target_notional=None, side=side)


def calculate_vwap_for_notional(levels: Any, target_notional: Any, *, side: str) -> dict[str, Any]:
    """Calculate VWAP by consuming depth until ``target_notional`` is filled."""

    return _calculate_vwap(levels, target_size=None, target_notional=target_notional, side=side)


def summarize_depth_vwap(
    levels: Any,
    *,
    target_size: Any | None = None,
    target_notional: Any | None = None,
    side: str,
) -> dict[str, Any]:
    """Return a plain dict Depth/VWAP summary for one side of an orderbook.

    If both ``target_size`` and ``target_notional`` are provided, size-based
    simulation is used and a warning records that ``target_notional`` was
    ignored. If neither target is provided, the result is insufficient with a
    warning rather than an exception.
    """

    warnings: list[str] = []
    if target_size is not None:
        result = calculate_vwap_for_size(levels, target_size, side=side)
        if target_notional is not None:
            result["warnings"].append("target_notional_ignored_when_target_size_is_provided")
        return result
    if target_notional is not None:
        return calculate_vwap_for_notional(levels, target_notional, side=side)
    result = _empty_result(side=side, levels_available=_levels_available(levels))
    result["warnings"].append("missing_target_size_or_target_notional")
    return result


def _calculate_vwap(levels: Any, *, target_size: Any | None, target_notional: Any | None, side: str) -> dict[str, Any]:
    warnings: list[str] = []
    levels_available = _levels_available(levels)
    result = _empty_result(side=side, levels_available=levels_available)

    if side not in _VALID_SIDES:
        result["warnings"].append(f"unsupported_side:{side!r}")
        return result

    parsed_levels = _parse_levels(levels, warnings)
    _add_price_sequence_warnings(parsed_levels, side=side, warnings=warnings)
    result["warnings"].extend(warnings)

    if not parsed_levels:
        result["warnings"].append("empty_or_no_valid_levels")
        return result

    best_price = parsed_levels[0][0]
    result["best_price"] = best_price

    if target_size is not None:
        target = _to_decimal(target_size)
        result["target_size"] = target
        if target is None or target <= _ZERO:
            result["warnings"].append("target_size_must_be_positive")
            return result
        _fill_for_size(result, parsed_levels, target)
        return _finalize_result(result)

    target = _to_decimal(target_notional)
    result["target_notional"] = target
    if target is None or target <= _ZERO:
        result["warnings"].append("target_notional_must_be_positive")
        return result
    _fill_for_notional(result, parsed_levels, target)
    return _finalize_result(result)


def _fill_for_size(result: dict[str, Any], parsed_levels: list[tuple[Decimal, Decimal]], target_size: Decimal) -> None:
    filled_size = _ZERO
    filled_notional = _ZERO
    levels_consumed = 0

    for price, quantity in parsed_levels:
        remaining_size = target_size - filled_size
        if remaining_size <= _ZERO:
            break
        fill_size = min(quantity, remaining_size)
        if fill_size <= _ZERO:
            continue
        filled_size += fill_size
        filled_notional += fill_size * price
        levels_consumed += 1
        if filled_size >= target_size:
            break

    result["filled_size"] = filled_size
    result["filled_notional"] = filled_notional
    result["levels_consumed"] = levels_consumed
    result["depth_coverage_pct"] = _percent(filled_size, target_size)
    result["insufficient_depth"] = filled_size < target_size


def _fill_for_notional(result: dict[str, Any], parsed_levels: list[tuple[Decimal, Decimal]], target_notional: Decimal) -> None:
    filled_size = _ZERO
    filled_notional = _ZERO
    levels_consumed = 0

    for price, quantity in parsed_levels:
        remaining_notional = target_notional - filled_notional
        if remaining_notional <= _ZERO:
            break
        available_notional = price * quantity
        fill_notional = min(available_notional, remaining_notional)
        if fill_notional <= _ZERO:
            continue
        filled_notional += fill_notional
        filled_size += fill_notional / price
        levels_consumed += 1
        if filled_notional >= target_notional:
            break

    result["filled_size"] = filled_size
    result["filled_notional"] = filled_notional
    result["levels_consumed"] = levels_consumed
    result["depth_coverage_pct"] = _percent(filled_notional, target_notional)
    result["insufficient_depth"] = filled_notional < target_notional


def _finalize_result(result: dict[str, Any]) -> dict[str, Any]:
    filled_size = result["filled_size"]
    filled_notional = result["filled_notional"]
    best_price = result["best_price"]
    if filled_size and filled_size > _ZERO:
        vwap = filled_notional / filled_size
        result["vwap"] = vwap
        result["slippage_pct"] = _slippage_pct(best_price, vwap, result["side"])
    else:
        result["warnings"].append("no_fill_possible")
        result["insufficient_depth"] = True
    return result


def _parse_levels(levels: Any, warnings: list[str]) -> list[tuple[Decimal, Decimal]]:
    parsed: list[tuple[Decimal, Decimal]] = []
    if levels is None:
        warnings.append("empty_levels")
        return parsed
    if isinstance(levels, (str, bytes)):
        warnings.append("levels_must_be_iterable_depth_rows")
        return parsed
    try:
        iterator = iter(levels)
    except TypeError:
        warnings.append("levels_must_be_iterable_depth_rows")
        return parsed

    for index, level in enumerate(iterator):
        price_raw, quantity_raw = _extract_level_values(level)
        price = _to_decimal(price_raw)
        quantity = _to_decimal(quantity_raw)
        if price is None:
            warnings.append(f"invalid_price_at_level:{index}")
            continue
        if quantity is None:
            warnings.append(f"invalid_quantity_at_level:{index}")
            continue
        if price <= _ZERO:
            warnings.append(f"non_positive_price_at_level:{index}")
            continue
        if quantity <= _ZERO:
            warnings.append(f"non_positive_quantity_at_level:{index}")
            continue
        parsed.append((price, quantity))
    return parsed


def _extract_level_values(level: Any) -> tuple[Any, Any]:
    if isinstance(level, Mapping):
        price = level.get("price")
        quantity = level.get("quantity", level.get("qty", level.get("size")))
        return price, quantity
    if isinstance(level, (list, tuple)) and len(level) >= 2:
        return level[0], level[1]
    return None, None


def _add_price_sequence_warnings(parsed_levels: list[tuple[Decimal, Decimal]], *, side: str, warnings: list[str]) -> None:
    if len(parsed_levels) < 2:
        return
    prices = [price for price, _quantity in parsed_levels]
    if side == "ask":
        for previous, current in zip(prices, prices[1:]):
            if current < previous:
                warnings.append("ask_levels_not_best_to_worse")
                return
    if side == "bid":
        for previous, current in zip(prices, prices[1:]):
            if current > previous:
                warnings.append("bid_levels_not_best_to_worse")
                return


def _empty_result(*, side: str, levels_available: int) -> dict[str, Any]:
    return {
        "side": side,
        "target_size": None,
        "target_notional": None,
        "filled_size": _ZERO,
        "filled_notional": _ZERO,
        "vwap": None,
        "best_price": None,
        "slippage_pct": None,
        "depth_coverage_pct": _ZERO,
        "insufficient_depth": True,
        "levels_consumed": 0,
        "levels_available": levels_available,
        "level_sort_assumption": "best_to_worse",
        "warnings": [],
    }


def _levels_available(levels: Any) -> int:
    if levels is None or isinstance(levels, (str, bytes)):
        return 0
    if hasattr(levels, "__len__"):
        return len(levels)  # type: ignore[arg-type]
    if isinstance(levels, Iterable):
        return 0
    return 0


def _to_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value if value.is_finite() else None
    try:
        value_text = str(value).strip()
        if not value_text:
            return None
        decimal_value = Decimal(value_text)
    except (InvalidOperation, ValueError):
        return None
    if not decimal_value.is_finite():
        return None
    return decimal_value


def _percent(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator <= _ZERO:
        return None
    return (numerator / denominator) * _HUNDRED


def _slippage_pct(best_price: Decimal | None, vwap: Decimal | None, side: str) -> Decimal | None:
    if best_price is None or vwap is None or best_price <= _ZERO:
        return None
    if side == "ask":
        return max(_ZERO, ((vwap - best_price) / best_price) * _HUNDRED)
    if side == "bid":
        return max(_ZERO, ((best_price - vwap) / best_price) * _HUNDRED)
    return None
