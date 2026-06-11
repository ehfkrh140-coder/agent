"""Thin venue-specific Funding Rate parser wrappers.

This module is analysis-only.
It does not place orders.
It does not check balances, accounts, positions, credentials, or private API.
It does not call exchange endpoints.
It does not perform network I/O.
It does not read files, env vars, config, or registry.
It does not imply execution permission.
Funding Rate wrapper output is not a trading signal.
NO_TRADE_ONLY posture must be preserved by callers.

The wrappers accept caller-provided raw Funding Rate payload objects, select
fixed venue/source labels, delegate parsing to the pure helper, and return a
context-only envelope. Wrapper status and warnings describe orchestration
health only; they do not affect readiness and must not be interpreted as
WATCH, ENTER, alert, order, or execution permission.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.market_data.funding_rate_parser import parse_funding_rate_payload

OK = "OK"
OK_WITH_WARNINGS = "OK_WITH_WARNINGS"
WRAPPER_INPUT_EMPTY = "WRAPPER_INPUT_EMPTY"
WRAPPER_SOURCE_MISMATCH = "WRAPPER_SOURCE_MISMATCH"
WRAPPER_INVALID_INPUT = "WRAPPER_INVALID_INPUT"

_SOURCE_SEMANTICS: dict[tuple[str, str], str] = {
    ("binance_usdm", "binance_usdm_funding_rate_history"): "historical_funding_charge_record",
    ("binance_usdm", "binance_usdm_funding_info"): "interval_cap_floor_context",
    ("bybit", "bybit_v5_funding_history"): "settled_historical_funding_context",
    ("bybit", "bybit_v5_instruments_info"): "instrument_interval_cap_floor_context",
    ("okx", "okx_funding_rate_history"): "historical_funding_context",
    ("okx", "okx_current_funding_rate"): "current_predicted_funding_context",
}


def parse_binance_usdm_funding_rate_history(
    payload: Any,
    *,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Parse caller-provided Binance USD-M funding history payload context."""

    return _wrap_payload(
        payload,
        venue="binance_usdm",
        source_endpoint="binance_usdm_funding_rate_history",
        provenance=provenance,
    )


def parse_binance_usdm_funding_info(
    payload: Any,
    *,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Parse caller-provided Binance USD-M funding info payload context."""

    return _wrap_payload(
        payload,
        venue="binance_usdm",
        source_endpoint="binance_usdm_funding_info",
        provenance=provenance,
    )


def parse_bybit_v5_funding_history(
    payload: Any,
    *,
    category_hint: str | None = None,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Parse caller-provided Bybit V5 funding history payload context."""

    return _wrap_payload(
        payload,
        venue="bybit",
        source_endpoint="bybit_v5_funding_history",
        category_hint=category_hint,
        provenance=provenance,
    )


def parse_bybit_v5_instruments_info(
    payload: Any,
    *,
    category_hint: str | None = None,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Parse caller-provided Bybit V5 instruments-info funding context."""

    return _wrap_payload(
        payload,
        venue="bybit",
        source_endpoint="bybit_v5_instruments_info",
        category_hint=category_hint,
        provenance=provenance,
    )


def parse_okx_funding_rate_history(
    payload: Any,
    *,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Parse caller-provided OKX funding-rate-history payload context."""

    return _wrap_payload(
        payload,
        venue="okx",
        source_endpoint="okx_funding_rate_history",
        provenance=provenance,
    )


def parse_okx_current_funding_rate(
    payload: Any,
    *,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Parse caller-provided OKX current funding-rate payload context."""

    return _wrap_payload(
        payload,
        venue="okx",
        source_endpoint="okx_current_funding_rate",
        provenance=provenance,
    )


def _wrap_payload(
    payload: Any,
    *,
    venue: str,
    source_endpoint: str,
    category_hint: str | None = None,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_semantics = _SOURCE_SEMANTICS[(venue, source_endpoint)]
    wrapper_warnings: list[str] = []
    input_record_count = _input_record_count(payload, venue=venue)
    payload_category = _bybit_payload_category(payload) if venue == "bybit" else None

    if input_record_count == 0:
        wrapper_warnings.append("empty_payload")
    if category_hint is not None and payload_category is not None and category_hint != payload_category:
        wrapper_warnings.append("category_hint_mismatch")

    parser_result = parse_funding_rate_payload(
        payload,
        venue=venue,
        source_endpoint=source_endpoint,
    )

    return {
        "wrapper_status": _wrapper_status(input_record_count, wrapper_warnings),
        "venue": venue,
        "source_endpoint": source_endpoint,
        "source_semantics": source_semantics,
        "parser_result": parser_result,
        "wrapper_warnings": wrapper_warnings,
        "provenance": dict(provenance or {}),
        "input_record_count": input_record_count,
        "parsed_record_count": parser_result.get("records_parsed", 0),
        "context_only": True,
        "readiness_effect": "unchanged",
    }


def _wrapper_status(input_record_count: int | None, wrapper_warnings: list[str]) -> str:
    if input_record_count is None:
        return WRAPPER_INVALID_INPUT
    if input_record_count == 0:
        return WRAPPER_INPUT_EMPTY
    if wrapper_warnings:
        return OK_WITH_WARNINGS
    return OK


def _input_record_count(payload: Any, *, venue: str) -> int | None:
    if venue == "binance_usdm":
        list_payload = _payload_list(payload)
        return len(list_payload) if list_payload is not None else None
    if venue == "bybit":
        records = _bybit_record_list(payload)
        return len(records) if records is not None else None
    if venue == "okx":
        records = _okx_data_list(payload)
        return len(records) if records is not None else None
    return None


def _payload_list(payload: Any) -> list[Any] | None:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, Mapping) and isinstance(payload.get("payload"), list):
        return payload["payload"]
    return None


def _bybit_record_list(payload: Any) -> list[Any] | None:
    bybit_payload = _mapping_payload(payload)
    if bybit_payload is None:
        return None
    result = bybit_payload.get("result")
    if not isinstance(result, Mapping) or not isinstance(result.get("list"), list):
        return None
    return result["list"]


def _bybit_payload_category(payload: Any) -> str | None:
    bybit_payload = _mapping_payload(payload)
    if bybit_payload is None:
        return None
    result = bybit_payload.get("result")
    if not isinstance(result, Mapping):
        return None
    category = result.get("category")
    return category if isinstance(category, str) else None


def _okx_data_list(payload: Any) -> list[Any] | None:
    if not isinstance(payload, Mapping) or not isinstance(payload.get("data"), list):
        return None
    return payload["data"]


def _mapping_payload(payload: Any) -> Mapping[str, Any] | None:
    if not isinstance(payload, Mapping):
        return None
    nested_payload = payload.get("payload")
    if isinstance(nested_payload, Mapping):
        return nested_payload
    return payload
