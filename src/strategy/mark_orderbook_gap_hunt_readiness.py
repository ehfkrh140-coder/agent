"""Pure readiness helper for Mark-Orderbook Gap Hunt parser output.

The helper consumes normalized parser dictionaries and returns analysis-only
readiness dictionaries. It performs no network I/O, no credential lookup, no
adapter/registry integration, no sampling, no alerting, no Council calls, and no
execution behavior.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

READINESS_NEED_DATA = "NEED_DATA"
READINESS_REJECT = "REJECT"
READINESS_WATCH = "WATCH"


def evaluate_mark_orderbook_gap_readiness(
    parser_output: dict[str, Any],
    *,
    fee_slippage_buffer_pct: float | Decimal | str | None,
    liquidity_pass: bool | None = None,
    require_freshness: bool = True,
    size_or_notional_resolved: bool = False,
    min_net_gap_pct: float | Decimal | str = 0,
) -> dict[str, Any]:
    """Evaluate analysis-only readiness for a normalized parser snapshot.

    ``WATCH`` is not execution. ``readiness_pass`` intentionally remains false
    in this phase, and the output deliberately excludes execution/Council/alert
    trigger fields.
    """

    if not isinstance(parser_output, dict):
        raise ValueError("parser_output must be a dict")

    required_missing_fields = set(_string_items(parser_output.get("required_missing_fields")))
    warnings = list(_string_items(parser_output.get("parser_warnings")))

    mark = _to_decimal(parser_output.get("mark_price"))
    bid = _to_decimal(parser_output.get("bid"))
    ask = _to_decimal(parser_output.get("ask"))
    fee_buffer = _to_decimal(fee_slippage_buffer_pct)
    min_net_gap = _to_decimal(min_net_gap_pct) or Decimal("0")

    normalized_status = parser_output.get("normalized_status")
    comparability_pass = parser_output.get("comparability_pass")
    freshness_pass = parser_output.get("freshness_pass")

    if normalized_status == READINESS_NEED_DATA:
        required_missing_fields.add("parser_normalized_status")
    elif normalized_status not in {"OK", READINESS_REJECT}:
        required_missing_fields.add("parser_normalized_status")

    if comparability_pass is not True:
        required_missing_fields.add("comparability_pass")
    if require_freshness and freshness_pass is not True:
        required_missing_fields.add("freshness_pass")
    for field_name, value in (("mark_price", mark), ("bid", bid), ("ask", ask)):
        if value is None:
            required_missing_fields.add(field_name)
    if not size_or_notional_resolved:
        required_missing_fields.add("size_or_notional_resolved")
    if fee_buffer is None:
        required_missing_fields.add("fee_slippage_buffer_pct")
    if liquidity_pass is None:
        required_missing_fields.add("liquidity_pass")

    metrics: dict[str, Any] = {
        "long_gap_pct": None,
        "short_gap_pct": None,
        "max_observed_gap_pct": None,
        "fee_slippage_buffer_pct": _decimal_to_string(fee_buffer),
        "estimated_net_gap_pct": None,
        "liquidity_pass": liquidity_pass,
        "freshness_pass": freshness_pass,
        "comparability_pass": comparability_pass,
    }

    if required_missing_fields:
        return _readiness_output(
            status=READINESS_NEED_DATA,
            required_missing_fields=sorted(required_missing_fields),
            warnings=warnings,
            metrics=metrics,
        )

    assert mark is not None and bid is not None and ask is not None and fee_buffer is not None
    if mark <= 0:
        required_missing_fields.add("mark_price")
        warnings.append("non_positive_mark_price")
        return _readiness_output(
            status=READINESS_NEED_DATA,
            required_missing_fields=sorted(required_missing_fields),
            warnings=warnings,
            metrics=metrics,
        )

    long_gap = ((mark - ask) / mark) * Decimal("100")
    short_gap = ((bid - mark) / mark) * Decimal("100")
    max_observed_gap = max(long_gap, short_gap)
    estimated_net_gap = max_observed_gap - fee_buffer
    metrics.update(
        {
            "long_gap_pct": _decimal_to_string(long_gap),
            "short_gap_pct": _decimal_to_string(short_gap),
            "max_observed_gap_pct": _decimal_to_string(max_observed_gap),
            "estimated_net_gap_pct": _decimal_to_string(estimated_net_gap),
        }
    )

    if liquidity_pass is False:
        warnings.append("liquidity_insufficient")
        return _readiness_output(
            status=READINESS_REJECT,
            required_missing_fields=[],
            warnings=warnings,
            metrics=metrics,
        )
    if max_observed_gap <= 0:
        warnings.append("no_positive_gross_gap")
        return _readiness_output(
            status=READINESS_REJECT,
            required_missing_fields=[],
            warnings=warnings,
            metrics=metrics,
        )
    if estimated_net_gap <= min_net_gap:
        warnings.append("non_positive_estimated_net_gap")
        return _readiness_output(
            status=READINESS_REJECT,
            required_missing_fields=[],
            warnings=warnings,
            metrics=metrics,
        )

    return _readiness_output(
        status=READINESS_WATCH,
        required_missing_fields=[],
        warnings=warnings,
        metrics=metrics,
    )


def _readiness_output(
    *,
    status: str,
    required_missing_fields: list[str],
    warnings: list[str],
    metrics: dict[str, Any],
) -> dict[str, Any]:
    deduped_warnings = list(dict.fromkeys(warnings))
    return {
        "readiness_status": status,
        "readiness_pass": False,
        "recommended_default_decision": status,
        "required_missing_fields": required_missing_fields,
        "warnings": deduped_warnings,
        "metrics": metrics,
    }


def _to_decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _decimal_to_string(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _string_items(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]
