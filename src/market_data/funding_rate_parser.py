"""Pure Funding Rate parser helper.

This module is analysis-only.
It does not place orders.
It does not check balances, accounts, positions, credentials, or private API.
It does not call exchange endpoints.
It does not perform network I/O.
It does not imply execution permission.
Funding Rate context is not a trading signal.
NO_TRADE_ONLY posture must be preserved by callers.

The helper consumes caller-provided public/mock payload objects only. It does
not inspect runtime variables, query configs or registries, or perform
adapter work. Parser statuses and warnings describe parser health and
context provenance only; they do not affect readiness.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Mapping

OK = "OK"
OK_WITH_WARNINGS = "OK_WITH_WARNINGS"
NEED_SOURCE_FIELDS = "NEED_SOURCE_FIELDS"
INVALID_SOURCE_SHAPE = "INVALID_SOURCE_SHAPE"
INVALID_NUMERIC_FIELD = "INVALID_NUMERIC_FIELD"
INVALID_TIMESTAMP_FIELD = "INVALID_TIMESTAMP_FIELD"
UNSUPPORTED_SOURCE = "UNSUPPORTED_SOURCE"
UNSUPPORTED_VENUE = "UNSUPPORTED_VENUE"

_SUPPORTED_VENUES = {"binance_usdm", "bybit", "okx"}

_SOURCE_SEMANTICS: dict[tuple[str, str], str] = {
    ("binance_usdm", "binance_usdm_funding_rate_history"): "historical_funding_charge_record",
    ("binance_usdm", "binance_usdm_funding_info"): "interval_cap_floor_context",
    ("bybit", "bybit_v5_funding_history"): "settled_historical_funding_context",
    ("bybit", "bybit_v5_instruments_info"): "instrument_interval_cap_floor_context",
    ("okx", "okx_funding_rate_history"): "historical_funding_context",
    ("okx", "okx_current_funding_rate"): "current_predicted_funding_context",
    ("okx", "okx_predicted_vs_realized_semantics"): "predicted_vs_realized_semantics_context",
    ("bybit", "timestamp_watch_context"): "timestamp_watch_context",
    ("okx", "high_abs_funding_context"): "high_abs_funding_context",
    ("binance_usdm", "string_numeric_parsing"): "historical_funding_charge_record",
    ("binance_usdm", "varying_funding_interval"): "interval_cap_floor_context",
}

_RECORD_ERROR_PRIORITY = {
    INVALID_SOURCE_SHAPE: 0,
    INVALID_NUMERIC_FIELD: 1,
    INVALID_TIMESTAMP_FIELD: 2,
    NEED_SOURCE_FIELDS: 3,
    OK_WITH_WARNINGS: 4,
    OK: 5,
}


def parse_funding_rate_payload(payload: Any, *, venue: str, source_endpoint: str) -> dict[str, Any]:
    """Parse caller-provided Funding Rate payload into context observations.

    The return value is a plain dict/list structure with Decimal values for
    numeric fields. The helper never fetches, persists, or mutates strategy
    state. `OK` only means the payload was understood by this parser.
    """

    source_semantics = _SOURCE_SEMANTICS.get((venue, source_endpoint))
    if venue not in _SUPPORTED_VENUES:
        return _empty_result(UNSUPPORTED_VENUE, venue, source_endpoint, None, warnings=["unsupported_venue"])
    if source_semantics is None:
        return _empty_result(UNSUPPORTED_SOURCE, venue, source_endpoint, None, warnings=["unsupported_source"])

    parser = _parser_for(venue, source_endpoint)
    result = _empty_result(OK, venue, source_endpoint, source_semantics)
    records, shape_status, shape_warning = parser[0](payload)
    if shape_status != OK:
        result["parser_status"] = shape_status
        if shape_warning:
            result["warnings"].append(shape_warning)
        return result

    result["records_seen"] = len(records)
    record_parser = parser[1]
    for index, record in enumerate(records):
        observation = record_parser(record, venue=venue, source_endpoint=source_endpoint, source_semantics=source_semantics)
        _apply_edge_context(payload, source_endpoint, observation, index)
        result["observations"].append(observation)
        _extend_unique(result["required_missing_fields"], observation["required_missing_fields"])
        _extend_unique(result["optional_missing_fields"], observation["optional_missing_fields"])
        _extend_unique(result["warnings"], observation["warnings"])
        if observation["parser_status"] in {OK, OK_WITH_WARNINGS}:
            result["records_parsed"] += 1

    result["parser_status"] = _aggregate_status(result["observations"], result["warnings"])
    return result


def _parser_for(venue: str, source_endpoint: str) -> tuple[Callable[[Any], tuple[list[Any], str, str | None]], Callable[..., dict[str, Any]]]:
    if venue == "binance_usdm" and source_endpoint == "binance_usdm_funding_rate_history":
        return _records_from_list_payload, _parse_binance_history_record
    if venue == "binance_usdm" and source_endpoint == "binance_usdm_funding_info":
        return _records_from_list_payload, _parse_binance_funding_info_record
    if venue == "binance_usdm" and source_endpoint == "string_numeric_parsing":
        return _records_from_records_payload, _parse_string_numeric_record
    if venue == "binance_usdm" and source_endpoint == "varying_funding_interval":
        return _records_from_varying_interval_payload, _parse_varying_interval_record
    if venue == "bybit" and source_endpoint == "bybit_v5_funding_history":
        return _records_from_bybit_payload, _parse_bybit_history_record
    if venue == "bybit" and source_endpoint == "bybit_v5_instruments_info":
        return _records_from_bybit_payload, _parse_bybit_instruments_record
    if venue == "bybit" and source_endpoint == "timestamp_watch_context":
        return _records_from_bybit_payload, _parse_bybit_history_record
    if venue == "okx" and source_endpoint == "okx_funding_rate_history":
        return _records_from_okx_payload, _parse_okx_history_record
    if venue == "okx" and source_endpoint == "okx_current_funding_rate":
        return _records_from_okx_payload, _parse_okx_current_record
    if venue == "okx" and source_endpoint == "high_abs_funding_context":
        return _records_from_okx_payload, _parse_okx_history_record
    if venue == "okx" and source_endpoint == "okx_predicted_vs_realized_semantics":
        return _records_from_okx_predicted_vs_realized_payload, _parse_okx_current_record
    return _unsupported_shape, _parse_empty_record


def _empty_result(
    parser_status: str,
    venue: str,
    source_endpoint: str,
    source_semantics: str | None,
    *,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "parser_status": parser_status,
        "venue": venue,
        "source_endpoint": source_endpoint,
        "source_semantics": source_semantics,
        "observations": [],
        "required_missing_fields": [],
        "optional_missing_fields": [],
        "warnings": list(warnings or []),
        "records_seen": 0,
        "records_parsed": 0,
    }


def _base_observation(venue: str, source_endpoint: str, source_semantics: str) -> dict[str, Any]:
    return {
        "venue": venue,
        "source_endpoint": source_endpoint,
        "source_semantics": source_semantics,
        "instrument_id": None,
        "instrument_type": None,
        "symbol_normalized": None,
        "funding_rate": None,
        "funding_rate_timestamp_ms": None,
        "parser_status": OK,
        "required_missing_fields": [],
        "optional_missing_fields": [],
        "warnings": [],
        "funding_interval_hours": None,
        "next_funding_time_ms": None,
        "realized_funding_rate": None,
        "predicted_funding_rate": None,
        "funding_cap": None,
        "funding_floor": None,
        "mark_price_reference": None,
        "premium_index_reference": None,
    }


def _records_from_list_payload(payload: Any) -> tuple[list[Any], str, str | None]:
    if isinstance(payload, Mapping) and "payload" in payload:
        payload = payload["payload"]
    if not isinstance(payload, list):
        return [], INVALID_SOURCE_SHAPE, "expected_top_level_list"
    return payload, OK, None


def _records_from_records_payload(payload: Any) -> tuple[list[Any], str, str | None]:
    if not isinstance(payload, Mapping) or not isinstance(payload.get("records"), list):
        return [], INVALID_SOURCE_SHAPE, "expected_records_list"
    return payload["records"], OK, None


def _records_from_bybit_payload(payload: Any) -> tuple[list[Any], str, str | None]:
    if not isinstance(payload, Mapping):
        return [], INVALID_SOURCE_SHAPE, "expected_bybit_object"
    if "payload" in payload and isinstance(payload["payload"], Mapping):
        payload = payload["payload"]
    result = payload.get("result")
    if not isinstance(result, Mapping) or not isinstance(result.get("list"), list):
        return [], INVALID_SOURCE_SHAPE, "expected_bybit_result_list"
    category = result.get("category")
    return [{"_category": category, **record} for record in result["list"] if isinstance(record, Mapping)], OK, None


def _records_from_okx_payload(payload: Any) -> tuple[list[Any], str, str | None]:
    if not isinstance(payload, Mapping) or not isinstance(payload.get("data"), list):
        return [], INVALID_SOURCE_SHAPE, "expected_okx_data_list"
    return [record for record in payload["data"] if isinstance(record, Mapping)], OK, None


def _records_from_okx_predicted_vs_realized_payload(payload: Any) -> tuple[list[Any], str, str | None]:
    if not isinstance(payload, Mapping):
        return [], INVALID_SOURCE_SHAPE, "expected_okx_semantics_object"
    current = payload.get("currentFundingPayload")
    if not isinstance(current, Mapping) or not isinstance(current.get("data"), list):
        return [], INVALID_SOURCE_SHAPE, "expected_current_funding_payload_data"
    return [record for record in current["data"] if isinstance(record, Mapping)], OK, None


def _records_from_varying_interval_payload(payload: Any) -> tuple[list[Any], str, str | None]:
    if not isinstance(payload, Mapping):
        return [], INVALID_SOURCE_SHAPE, "expected_varying_interval_object"
    records: list[Any] = []
    for record in payload.get("binanceFundingInfo", []):
        if isinstance(record, Mapping):
            records.append({"_source": "binance", **record})
    bybit = payload.get("bybitInstrumentsInfo")
    if isinstance(bybit, Mapping):
        category = bybit.get("category")
        for record in bybit.get("list", []):
            if isinstance(record, Mapping):
                records.append({"_source": "bybit", "_category": category, **record})
    for record in payload.get("okxCurrentFunding", []):
        if isinstance(record, Mapping):
            records.append({"_source": "okx", **record})
    return records, OK, None


def _unsupported_shape(payload: Any) -> tuple[list[Any], str, str | None]:
    return [], INVALID_SOURCE_SHAPE, "unsupported_parser_shape"


def _parse_empty_record(record: Any, *, venue: str, source_endpoint: str, source_semantics: str) -> dict[str, Any]:
    observation = _base_observation(venue, source_endpoint, source_semantics)
    observation["parser_status"] = INVALID_SOURCE_SHAPE
    return observation


def _parse_binance_history_record(record: Mapping[str, Any], *, venue: str, source_endpoint: str, source_semantics: str) -> dict[str, Any]:
    observation = _base_observation(venue, source_endpoint, source_semantics)
    observation["instrument_type"] = "usdm_perpetual"
    _set_required_text(observation, record, "symbol", "instrument_id")
    _set_required_decimal(observation, record, "fundingRate", "funding_rate")
    _set_required_timestamp(observation, record, "fundingTime", "funding_rate_timestamp_ms")
    _set_optional_decimal(observation, record, "markPrice", "mark_price_reference")
    return _finalize_observation(observation)


def _parse_binance_funding_info_record(record: Mapping[str, Any], *, venue: str, source_endpoint: str, source_semantics: str) -> dict[str, Any]:
    observation = _base_observation(venue, source_endpoint, source_semantics)
    observation["instrument_type"] = "usdm_perpetual"
    _set_required_text(observation, record, "symbol", "instrument_id")
    _set_required_decimal(observation, record, "adjustedFundingRateCap", "funding_cap")
    _set_required_decimal(observation, record, "adjustedFundingRateFloor", "funding_floor")
    _set_optional_decimal(observation, record, "fundingIntervalHours", "funding_interval_hours")
    if observation["funding_interval_hours"] is None:
        _add_unique(observation["optional_missing_fields"], "funding_interval_hours")
        _add_unique(observation["warnings"], "optional_interval_missing")
    return _finalize_observation(observation)


def _parse_bybit_history_record(record: Mapping[str, Any], *, venue: str, source_endpoint: str, source_semantics: str) -> dict[str, Any]:
    observation = _base_observation(venue, source_endpoint, source_semantics)
    observation["instrument_type"] = record.get("_category")
    _set_required_text(observation, record, "symbol", "instrument_id")
    _set_required_decimal(observation, record, "fundingRate", "funding_rate")
    _set_required_timestamp(observation, record, "fundingRateTimestamp", "funding_rate_timestamp_ms")
    return _finalize_observation(observation)


def _parse_bybit_instruments_record(record: Mapping[str, Any], *, venue: str, source_endpoint: str, source_semantics: str) -> dict[str, Any]:
    observation = _base_observation(venue, source_endpoint, source_semantics)
    observation["instrument_type"] = record.get("_category")
    _set_required_text(observation, record, "symbol", "instrument_id")
    minutes = _decimal_or_status(record.get("fundingInterval"))
    if minutes[1] is None:
        observation["funding_interval_hours"] = minutes[0] / Decimal("60")
    else:
        _add_unique(observation["required_missing_fields"], "funding_interval_hours")
        observation["parser_status"] = minutes[1]
    _set_optional_decimal(observation, record, "upperFundingRate", "funding_cap")
    _set_optional_decimal(observation, record, "lowerFundingRate", "funding_floor")
    return _finalize_observation(observation)


def _parse_okx_history_record(record: Mapping[str, Any], *, venue: str, source_endpoint: str, source_semantics: str) -> dict[str, Any]:
    observation = _base_observation(venue, source_endpoint, source_semantics)
    observation["instrument_type"] = record.get("instType")
    _set_required_text(observation, record, "instId", "instrument_id")
    _set_required_decimal(observation, record, "fundingRate", "funding_rate")
    _set_optional_decimal(observation, record, "realizedRate", "realized_funding_rate")
    _set_required_timestamp(observation, record, "fundingTime", "funding_rate_timestamp_ms")
    return _finalize_observation(observation)


def _parse_okx_current_record(record: Mapping[str, Any], *, venue: str, source_endpoint: str, source_semantics: str) -> dict[str, Any]:
    observation = _base_observation(venue, source_endpoint, source_semantics)
    observation["instrument_type"] = record.get("instType")
    _set_required_text(observation, record, "instId", "instrument_id")
    _set_required_decimal(observation, record, "fundingRate", "funding_rate")
    _set_required_timestamp(observation, record, "fundingTime", "funding_rate_timestamp_ms")
    _set_optional_decimal(observation, record, "nextFundingRate", "predicted_funding_rate")
    _set_optional_decimal(observation, record, "settFundingRate", "realized_funding_rate")
    _set_optional_timestamp(observation, record, "nextFundingTime", "next_funding_time_ms")
    _set_optional_decimal(observation, record, "premium", "premium_index_reference")
    _set_optional_decimal(observation, record, "maxFundingRate", "funding_cap")
    _set_optional_decimal(observation, record, "minFundingRate", "funding_floor")
    return _finalize_observation(observation)


def _parse_string_numeric_record(record: Mapping[str, Any], *, venue: str, source_endpoint: str, source_semantics: str) -> dict[str, Any]:
    if "symbol" in record:
        return _parse_binance_history_record(record, venue=venue, source_endpoint=source_endpoint, source_semantics=source_semantics)
    observation = _base_observation(venue, source_endpoint, source_semantics)
    _set_required_text(observation, record, "instId", "instrument_id")
    _set_required_decimal(observation, record, "fundingRate", "funding_rate")
    _set_required_timestamp(observation, record, "fundingTime", "funding_rate_timestamp_ms")
    _set_optional_decimal(observation, record, "premium", "premium_index_reference")
    _set_optional_decimal(observation, record, "maxFundingRate", "funding_cap")
    _set_optional_decimal(observation, record, "minFundingRate", "funding_floor")
    return _finalize_observation(observation)


def _parse_varying_interval_record(record: Mapping[str, Any], *, venue: str, source_endpoint: str, source_semantics: str) -> dict[str, Any]:
    source = record.get("_source")
    observation = _base_observation(venue, source_endpoint, source_semantics)
    if source == "bybit":
        observation["instrument_type"] = record.get("_category")
        _set_required_text(observation, record, "symbol", "instrument_id")
        minutes = _decimal_or_status(record.get("fundingInterval"))
        if minutes[1] is None:
            observation["funding_interval_hours"] = minutes[0] / Decimal("60")
        else:
            _add_unique(observation["required_missing_fields"], "funding_interval_hours")
            observation["parser_status"] = minutes[1]
    elif source == "okx":
        _set_required_text(observation, record, "instId", "instrument_id")
        start = _timestamp_or_status(record.get("fundingTime"))
        end = _timestamp_or_status(record.get("nextFundingTime"))
        if start[1] is None and end[1] is None:
            observation["funding_rate_timestamp_ms"] = start[0]
            observation["next_funding_time_ms"] = end[0]
            observation["funding_interval_hours"] = Decimal(end[0] - start[0]) / Decimal("3600000")
        else:
            observation["parser_status"] = INVALID_TIMESTAMP_FIELD
    else:
        return _parse_binance_funding_info_record(record, venue=venue, source_endpoint=source_endpoint, source_semantics=source_semantics)
    return _finalize_observation(observation)


def _set_required_text(observation: dict[str, Any], record: Mapping[str, Any], source_key: str, target_key: str) -> None:
    value = record.get(source_key)
    if value in (None, ""):
        _add_unique(observation["required_missing_fields"], target_key)
        return
    observation[target_key] = str(value)


def _set_required_decimal(observation: dict[str, Any], record: Mapping[str, Any], source_key: str, target_key: str) -> None:
    if source_key not in record or record.get(source_key) in (None, ""):
        _add_unique(observation["required_missing_fields"], target_key)
        return
    value, status = _decimal_or_status(record.get(source_key))
    if status is not None:
        observation["parser_status"] = status
        _add_unique(observation["warnings"], f"invalid_numeric_field:{target_key}")
        return
    observation[target_key] = value


def _set_optional_decimal(observation: dict[str, Any], record: Mapping[str, Any], source_key: str, target_key: str) -> None:
    if source_key not in record or record.get(source_key) in (None, ""):
        return
    value, status = _decimal_or_status(record.get(source_key))
    if status is not None:
        observation["parser_status"] = status
        _add_unique(observation["warnings"], f"invalid_numeric_field:{target_key}")
        return
    observation[target_key] = value


def _set_required_timestamp(observation: dict[str, Any], record: Mapping[str, Any], source_key: str, target_key: str) -> None:
    if source_key not in record or record.get(source_key) in (None, ""):
        _add_unique(observation["required_missing_fields"], target_key)
        return
    value, status = _timestamp_or_status(record.get(source_key))
    if status is not None:
        observation["parser_status"] = status
        _add_unique(observation["warnings"], f"invalid_timestamp_field:{target_key}")
        return
    observation[target_key] = value


def _set_optional_timestamp(observation: dict[str, Any], record: Mapping[str, Any], source_key: str, target_key: str) -> None:
    if source_key not in record or record.get(source_key) in (None, ""):
        return
    value, status = _timestamp_or_status(record.get(source_key))
    if status is not None:
        observation["parser_status"] = status
        _add_unique(observation["warnings"], f"invalid_timestamp_field:{target_key}")
        return
    observation[target_key] = value


def _decimal_or_status(value: Any) -> tuple[Decimal, str | None]:
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0"), INVALID_NUMERIC_FIELD
    if not decimal_value.is_finite():
        return Decimal("0"), INVALID_NUMERIC_FIELD
    return decimal_value, None


def _timestamp_or_status(value: Any) -> tuple[int, str | None]:
    if isinstance(value, bool):
        return 0, INVALID_TIMESTAMP_FIELD
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return 0, INVALID_TIMESTAMP_FIELD
    if not decimal_value.is_finite() or decimal_value != decimal_value.to_integral_value():
        return 0, INVALID_TIMESTAMP_FIELD
    return int(decimal_value), None


def _finalize_observation(observation: dict[str, Any]) -> dict[str, Any]:
    if observation["parser_status"] in {INVALID_NUMERIC_FIELD, INVALID_TIMESTAMP_FIELD}:
        return observation
    if observation["required_missing_fields"]:
        observation["parser_status"] = NEED_SOURCE_FIELDS
        return observation
    if observation["warnings"]:
        observation["parser_status"] = OK_WITH_WARNINGS
    return observation


def _aggregate_status(observations: list[dict[str, Any]], warnings: list[str]) -> str:
    if not observations:
        return OK_WITH_WARNINGS if warnings else OK
    best = OK
    for observation in observations:
        status = observation["parser_status"]
        if _RECORD_ERROR_PRIORITY.get(status, 99) < _RECORD_ERROR_PRIORITY.get(best, 99):
            best = status
    if best == OK and warnings:
        return OK_WITH_WARNINGS
    return best


def _apply_edge_context(payload: Any, source_endpoint: str, observation: dict[str, Any], index: int) -> None:
    if source_endpoint == "high_abs_funding_context":
        _add_unique(observation["warnings"], "high_abs_funding_context")
    if source_endpoint == "timestamp_watch_context":
        _add_unique(observation["warnings"], "timestamp_watch_context")
    if source_endpoint == "okx_predicted_vs_realized_semantics":
        _add_unique(observation["warnings"], "do_not_collapse_predicted_and_realized")
    if source_endpoint == "string_numeric_parsing":
        _add_unique(observation["warnings"], "numeric_parse_success_is_not_signal")
    if source_endpoint == "varying_funding_interval":
        _add_unique(observation["warnings"], "do_not_hard_code_8h_interval")
    if isinstance(payload, Mapping):
        expected = payload.get("expectedParserOutcome")
        if isinstance(expected, Mapping):
            for warning in expected.get("warnings", []):
                if isinstance(warning, str):
                    _add_unique(observation["warnings"], warning)
    observation["parser_status"] = _finalize_observation(observation)["parser_status"]


def _add_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _extend_unique(values: list[str], additions: list[str]) -> None:
    for value in additions:
        _add_unique(values, value)
