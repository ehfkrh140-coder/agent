"""Pure readiness helper for Spot-Futures Basis parser source bundles.

This helper consumes mocked/already-normalized source bundle dictionaries and
returns analysis-only readiness dictionaries. It performs no network I/O, no
file reads, no credential lookup, no adapter/registry integration, no
OpportunityPacket creation, no alerting, no Council calls, and no execution
behavior.
"""

from __future__ import annotations

from typing import Any

READINESS_REJECT = "REJECT"
READINESS_NEED_DATA = "NEED_DATA"
READINESS_WATCH = "WATCH"
NO_TRADE_EXECUTION_POLICY = "NO_TRADE_ONLY"

DIRECTION_LONG_SPOT_SHORT_PERP = "analysis_only_long_spot_short_perp_basis"
DIRECTION_LONG_PERP_SHORT_SPOT = "analysis_only_long_perp_short_spot_basis"
DIRECTION_NO_POSITIVE_BASIS = "analysis_only_no_positive_executable_basis"

READINESS_ASSUMPTIONS = (
    "public no-key endpoints only",
    "analysis-only readiness output",
    "no private API",
    "no trading behavior",
    "mark price is not executable",
    "last price is weak context only if present",
    "WATCH is not ENTER",
    "WATCH does not trigger Council auto-call, alert, or execution",
)

_REQUIRED_EXECUTABLE_FIELDS = (
    ("spot_observation", "best_bid", "spot_bid_missing"),
    ("spot_observation", "best_ask", "spot_ask_missing"),
    ("spot_observation", "best_bid_qty", "spot_bid_qty_missing"),
    ("spot_observation", "best_ask_qty", "spot_ask_qty_missing"),
    ("perp_observation", "best_bid", "perp_bid_missing"),
    ("perp_observation", "best_ask", "perp_ask_missing"),
    ("perp_observation", "best_bid_qty", "perp_bid_qty_missing"),
    ("perp_observation", "best_ask_qty", "perp_ask_qty_missing"),
)


def evaluate_spot_futures_basis_readiness(
    source_bundle: dict[str, Any],
    *,
    fee_slippage_buffer_pct: float = 0.20,
    max_data_age_ms: int | float | None = None,
) -> dict[str, Any]:
    """Evaluate analysis-only readiness for a spot-futures basis source bundle."""

    if not isinstance(source_bundle, dict):
        raise ValueError("source_bundle must be a dict")

    spot = source_bundle.get("spot_observation")
    perp = source_bundle.get("perp_observation")
    if not isinstance(spot, dict):
        spot = {}
    if not isinstance(perp, dict):
        perp = {}

    required_missing_fields: list[str] = []
    warnings: list[str] = [
        "mark_price_not_executable",
        "funding_rate_not_basis",
        "depth_vwap_not_implemented",
    ]
    metrics = _base_metrics(fee_slippage_buffer_pct)

    fee_buffer = _positive_or_zero_float(fee_slippage_buffer_pct)
    if fee_buffer is None:
        _add_missing(required_missing_fields, "fee_slippage_buffer_pct")
        _add_warning(warnings, "fee_slippage_buffer_missing_or_invalid")

    _merge_parser_missing(spot, "spot", required_missing_fields, warnings)
    _merge_parser_missing(perp, "perp", required_missing_fields, warnings)

    values = _extract_executable_values(spot, perp, required_missing_fields, warnings)
    metrics.update({
        "spot_bid": values["spot_bid"],
        "spot_ask": values["spot_ask"],
        "perp_bid": values["perp_bid"],
        "perp_ask": values["perp_ask"],
        "fee_slippage_buffer_pct": fee_buffer,
    })

    comparability_pass = _comparability_pass(spot, perp, required_missing_fields, warnings)
    freshness_pass = _freshness_pass(spot, perp, max_data_age_ms, warnings)
    liquidity_pass = _liquidity_pass(values, required_missing_fields, warnings)
    parser_status = _combined_parser_status(spot, perp)
    metrics.update(
        {
            "parser_normalized_status": parser_status,
            "comparability_pass": comparability_pass,
            "freshness_pass": freshness_pass,
            "liquidity_pass": liquidity_pass,
        }
    )

    if required_missing_fields:
        _add_warning(warnings, "required_fields_missing")
        return _readiness_output(
            status=READINESS_NEED_DATA,
            required_missing_fields=required_missing_fields,
            warnings=warnings,
            metrics=metrics,
        )

    spot_bid = values["spot_bid"]
    spot_ask = values["spot_ask"]
    perp_bid = values["perp_bid"]
    perp_ask = values["perp_ask"]
    assert spot_bid is not None and spot_ask is not None and perp_bid is not None and perp_ask is not None
    assert fee_buffer is not None

    spot_mid = (spot_bid + spot_ask) / 2
    perp_mid = (perp_bid + perp_ask) / 2
    mid_basis_pct = ((perp_mid - spot_mid) / spot_mid) * 100
    long_spot_short_perp_gross_pct = ((perp_bid - spot_ask) / spot_ask) * 100
    long_perp_short_spot_gross_pct = ((spot_bid - perp_ask) / perp_ask) * 100
    selected_direction, selected_gross_basis_pct = _select_direction(
        long_spot_short_perp_gross_pct,
        long_perp_short_spot_gross_pct,
    )
    estimated_net_basis_pct = selected_gross_basis_pct - fee_buffer

    metrics.update(
        {
            "spot_mid": spot_mid,
            "perp_mid": perp_mid,
            "mid_basis_pct": mid_basis_pct,
            "long_spot_short_perp_gross_pct": long_spot_short_perp_gross_pct,
            "long_perp_short_spot_gross_pct": long_perp_short_spot_gross_pct,
            "selected_direction": selected_direction,
            "selected_gross_basis_pct": selected_gross_basis_pct,
            "estimated_net_basis_pct": estimated_net_basis_pct,
        }
    )

    if selected_gross_basis_pct <= 0:
        _add_warning(warnings, "no_positive_gross_basis")
        return _readiness_output(
            status=READINESS_REJECT,
            required_missing_fields=[],
            warnings=warnings,
            metrics=metrics,
        )

    if estimated_net_basis_pct <= 0:
        _add_warning(warnings, "non_positive_estimated_net_basis")
        return _readiness_output(
            status=READINESS_REJECT,
            required_missing_fields=[],
            warnings=warnings,
            metrics=metrics,
        )

    _add_warning(warnings, "positive_net_basis_analysis_only")
    return _readiness_output(
        status=READINESS_WATCH,
        required_missing_fields=[],
        warnings=warnings,
        metrics=metrics,
    )


def _base_metrics(fee_slippage_buffer_pct: Any) -> dict[str, Any]:
    return {
        "spot_bid": None,
        "spot_ask": None,
        "perp_bid": None,
        "perp_ask": None,
        "spot_mid": None,
        "perp_mid": None,
        "mid_basis_pct": None,
        "long_spot_short_perp_gross_pct": None,
        "long_perp_short_spot_gross_pct": None,
        "selected_direction": DIRECTION_NO_POSITIVE_BASIS,
        "selected_gross_basis_pct": 0.0,
        "fee_slippage_buffer_pct": fee_slippage_buffer_pct,
        "estimated_net_basis_pct": None,
        "parser_normalized_status": None,
        "comparability_pass": False,
        "freshness_pass": False,
        "liquidity_pass": False,
    }


def _readiness_output(
    *,
    status: str,
    required_missing_fields: list[str],
    warnings: list[str],
    metrics: dict[str, Any],
) -> dict[str, Any]:
    return {
        "strategy_family": "spot_futures_basis",
        "strategy_id": "spot_futures_basis_v0",
        "readiness_status": status,
        "readiness_pass": status == READINESS_WATCH,
        "recommended_default_decision": status,
        "required_missing_fields": list(dict.fromkeys(required_missing_fields)),
        "warnings": list(dict.fromkeys(warnings)),
        "assumptions": list(READINESS_ASSUMPTIONS),
        "metrics": metrics,
        "no_trade_only": True,
        "execution_policy": NO_TRADE_EXECUTION_POLICY,
    }


def _merge_parser_missing(
    observation: dict[str, Any],
    prefix: str,
    required_missing_fields: list[str],
    warnings: list[str],
) -> None:
    parser_status = observation.get("parser_normalized_status")
    parser_missing = observation.get("required_missing_fields")
    if isinstance(parser_missing, list) and parser_missing:
        _add_warning(warnings, "parser_required_missing_fields_present")
        for field in parser_missing:
            _add_missing(required_missing_fields, _prefix_parser_missing_field(prefix, field))
    if parser_status not in (None, "OK"):
        _add_warning(warnings, "parser_status_not_ok")
        _add_missing(required_missing_fields, f"{prefix}_parser_normalized_status")


def _prefix_parser_missing_field(prefix: str, field: Any) -> str:
    field_text = str(field)
    if field_text.startswith(("spot_", "perp_")):
        return field_text
    return f"{prefix}_{field_text}"


def _extract_executable_values(
    spot: dict[str, Any],
    perp: dict[str, Any],
    required_missing_fields: list[str],
    warnings: list[str],
) -> dict[str, float | None]:
    values = {
        "spot_bid": _positive_float(spot.get("best_bid")),
        "spot_ask": _positive_float(spot.get("best_ask")),
        "spot_bid_qty": _positive_float(spot.get("best_bid_qty")),
        "spot_ask_qty": _positive_float(spot.get("best_ask_qty")),
        "perp_bid": _positive_float(perp.get("best_bid")),
        "perp_ask": _positive_float(perp.get("best_ask")),
        "perp_bid_qty": _positive_float(perp.get("best_bid_qty")),
        "perp_ask_qty": _positive_float(perp.get("best_ask_qty")),
    }
    lookup = {"spot_observation": spot, "perp_observation": perp}
    for observation_key, field_name, missing_name in _REQUIRED_EXECUTABLE_FIELDS:
        if _positive_float(lookup[observation_key].get(field_name)) is None:
            _add_missing(required_missing_fields, missing_name)
            _add_warning(warnings, "required_fields_missing")
    if any(values[key] is None for key in ("spot_bid", "spot_ask", "perp_bid", "perp_ask")):
        if perp.get("mark_price") is not None or perp.get("index_price") is not None:
            _add_warning(warnings, "mark_price_not_executable")
        if spot.get("last_price") is not None or perp.get("last_price") is not None:
            _add_warning(warnings, "last_price_weak_context_only")
    return values


def _comparability_pass(
    spot: dict[str, Any],
    perp: dict[str, Any],
    required_missing_fields: list[str],
    warnings: list[str],
) -> bool:
    spot_symbol = spot.get("symbol")
    perp_symbol = perp.get("symbol")
    spot_base = spot.get("base_asset")
    perp_base = perp.get("base_asset")
    spot_quote = spot.get("quote_asset")
    perp_quote = perp.get("quote_asset")
    settlement_asset = perp.get("settlement_asset")
    margin_asset = perp.get("margin_asset")
    ok = all((spot_symbol, perp_symbol, spot_base, perp_base, spot_quote, perp_quote, settlement_asset or margin_asset))
    ok = bool(ok and spot_base == perp_base and spot_quote == perp_quote and spot_quote in {settlement_asset, margin_asset})
    if not ok:
        _add_missing(required_missing_fields, "quote_settlement_comparability_unresolved")
        _add_warning(warnings, "quote_settlement_comparability_unresolved")
    return ok


def _freshness_pass(
    spot: dict[str, Any],
    perp: dict[str, Any],
    max_data_age_ms: int | float | None,
    warnings: list[str],
) -> bool:
    data_ages = [value for value in (spot.get("data_age_ms"), perp.get("data_age_ms")) if isinstance(value, int | float)]
    for data_age_ms in data_ages:
        if data_age_ms < 0:
            _add_warning(warnings, "negative_data_age_watch")
    if max_data_age_ms is None:
        return True
    if not data_ages:
        _add_warning(warnings, "stale_timestamp")
        return False
    freshness_pass = all(data_age_ms <= max_data_age_ms for data_age_ms in data_ages)
    if not freshness_pass:
        _add_warning(warnings, "stale_timestamp")
    return freshness_pass


def _liquidity_pass(
    values: dict[str, float | None],
    required_missing_fields: list[str],
    warnings: list[str],
) -> bool:
    quantity_keys = ("spot_bid_qty", "spot_ask_qty", "perp_bid_qty", "perp_ask_qty")
    passed = all(values.get(key) is not None and values[key] > 0 for key in quantity_keys)
    if not passed:
        _add_warning(warnings, "low_top_of_book_quantity")
        for key in quantity_keys:
            if values.get(key) is None:
                _add_missing(required_missing_fields, f"{key}_missing")
    return passed


def _combined_parser_status(spot: dict[str, Any], perp: dict[str, Any]) -> str:
    statuses = {spot.get("parser_normalized_status"), perp.get("parser_normalized_status")}
    if statuses <= {"OK", None}:
        return "OK"
    return "NEED_DATA"


def _select_direction(
    long_spot_short_perp_gross_pct: float,
    long_perp_short_spot_gross_pct: float,
) -> tuple[str, float]:
    if long_spot_short_perp_gross_pct <= 0 and long_perp_short_spot_gross_pct <= 0:
        return DIRECTION_NO_POSITIVE_BASIS, 0.0
    if long_spot_short_perp_gross_pct >= long_perp_short_spot_gross_pct:
        return DIRECTION_LONG_SPOT_SHORT_PERP, long_spot_short_perp_gross_pct
    return DIRECTION_LONG_PERP_SHORT_SPOT, long_perp_short_spot_gross_pct


def _positive_float(value: Any) -> float | None:
    number = _float_or_none(value)
    if number is None or number <= 0:
        return None
    return number


def _positive_or_zero_float(value: Any) -> float | None:
    number = _float_or_none(value)
    if number is None or number < 0:
        return None
    return number


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _add_missing(required_missing_fields: list[str], field_name: str) -> None:
    if field_name not in required_missing_fields:
        required_missing_fields.append(field_name)


def _add_warning(warnings: list[str], warning: str) -> None:
    if warning not in warnings:
        warnings.append(warning)
