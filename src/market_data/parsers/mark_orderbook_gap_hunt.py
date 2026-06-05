"""Pure parser for Mark-Orderbook Gap Hunt planning snapshots.

This module intentionally accepts already-fetched public response dictionaries. It
performs no network I/O, no credential lookup, no runtime adapter registration,
and no readiness/execution/Council/alert side effects.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

PARSER_MODE_BINANCE_USDM = "binance_usdm"
PARSER_MODE_BYBIT_LINEAR = "bybit_linear"
PARSER_MODE_OKX_SWAP = "okx_swap"

STATUS_OK = "OK"
STATUS_NEED_DATA = "NEED_DATA"
STATUS_REJECT = "REJECT"

SUPPORTED_PARSER_MODES = {PARSER_MODE_BINANCE_USDM, PARSER_MODE_BYBIT_LINEAR, PARSER_MODE_OKX_SWAP}

_OUTPUT_FIELDS = (
    "venue_id",
    "parser_mode",
    "instrument_id",
    "instrument_type",
    "mark_price",
    "index_price",
    "bid",
    "ask",
    "bid_size_raw",
    "ask_size_raw",
    "bid_size_unit",
    "ask_size_unit",
    "tick_size",
    "quantity_step",
    "lot_size",
    "min_order_size",
    "min_notional",
    "contract_value",
    "contract_multiplier",
    "contract_value_currency",
    "settle_currency",
    "margin_asset",
    "funding_rate",
    "next_funding_time",
    "timestamp",
    "data_age_ms",
    "comparability_pass",
    "freshness_pass",
    "required_missing_fields",
    "parser_warnings",
    "normalized_status",
)


class MarkOrderbookGapParserError(ValueError):
    """Raised for malformed parser inputs or unsupported parser modes."""


def parse_mark_orderbook_gap_snapshot(
    *,
    venue_id: str,
    parser_mode: str,
    mark_response: dict[str, Any] | None,
    orderbook_response: dict[str, Any] | None,
    metadata_response: dict[str, Any] | None,
    ticker_response: dict[str, Any] | None = None,
    collected_at_utc: str | None = None,
    latency_ms: float | None = None,
    max_data_age_ms: float | None = None,
) -> dict[str, Any]:
    """Parse already-fetched public market responses into a normalized snapshot.

    Expected missing-data cases return ``normalized_status=NEED_DATA`` with
    ``required_missing_fields`` populated. Malformed non-dict payloads and
    unsupported parser modes raise :class:`MarkOrderbookGapParserError`.
    """

    del latency_ms  # latency is an input contract field; freshness uses timestamps here.
    if parser_mode not in SUPPORTED_PARSER_MODES:
        raise MarkOrderbookGapParserError(f"unsupported parser_mode: {parser_mode}")

    if parser_mode == PARSER_MODE_BINANCE_USDM:
        return _parse_binance_usdm(
            venue_id=venue_id,
            parser_mode=parser_mode,
            mark_response=mark_response,
            orderbook_response=orderbook_response,
            metadata_response=metadata_response,
            collected_at_utc=collected_at_utc,
            max_data_age_ms=max_data_age_ms,
        )
    if parser_mode == PARSER_MODE_BYBIT_LINEAR:
        return _parse_bybit_linear(
            venue_id=venue_id,
            parser_mode=parser_mode,
            ticker_response=ticker_response if ticker_response is not None else mark_response,
            orderbook_response=orderbook_response,
            metadata_response=metadata_response,
            collected_at_utc=collected_at_utc,
            max_data_age_ms=max_data_age_ms,
        )
    return _parse_okx_swap(
        venue_id=venue_id,
        parser_mode=parser_mode,
        mark_response=mark_response,
        orderbook_response=orderbook_response,
        metadata_response=metadata_response,
        ticker_response=ticker_response,
        collected_at_utc=collected_at_utc,
        max_data_age_ms=max_data_age_ms,
    )


def _parse_binance_usdm(
    *,
    venue_id: str,
    parser_mode: str,
    mark_response: dict[str, Any] | None,
    orderbook_response: dict[str, Any] | None,
    metadata_response: dict[str, Any] | None,
    collected_at_utc: str | None,
    max_data_age_ms: float | None,
) -> dict[str, Any]:
    missing = _missing_payloads(
        ("mark_response", mark_response),
        ("orderbook_response", orderbook_response),
        ("metadata_response", metadata_response),
    )
    if missing:
        return _need_data(venue_id, parser_mode, missing)
    mark = _require_dict(mark_response, "mark_response")
    orderbook = _require_dict(orderbook_response, "orderbook_response")
    metadata = _require_dict(metadata_response, "metadata_response")
    symbol = _first_item(metadata.get("symbols"), "metadata_response.symbols")

    price_filter = _binance_filter(symbol, "PRICE_FILTER")
    lot_size = _binance_filter(symbol, "LOT_SIZE")
    min_notional = _binance_filter(symbol, "MIN_NOTIONAL")
    best_bid, best_bid_size = _first_level(orderbook.get("bids"), "bid")
    best_ask, best_ask_size = _first_level(orderbook.get("asks"), "ask")

    mark_symbol = _as_str(mark.get("symbol"))
    metadata_symbol = _as_str(symbol.get("symbol"))
    metadata_pair = _as_str(symbol.get("pair"))
    comparability_pass = bool(mark_symbol and mark_symbol == metadata_symbol == metadata_pair)
    timestamp = mark.get("time") or orderbook.get("T") or orderbook.get("E")
    freshness_pass, data_age_ms = _freshness(timestamp, collected_at_utc, max_data_age_ms)

    output = _base_output(venue_id, parser_mode)
    output.update(
        {
            "instrument_id": metadata_symbol or mark_symbol,
            "instrument_type": "linear_perpetual",
            "mark_price": _as_str(mark.get("markPrice")),
            "index_price": _as_str(mark.get("indexPrice")),
            "bid": best_bid,
            "ask": best_ask,
            "bid_size_raw": best_bid_size,
            "ask_size_raw": best_ask_size,
            "bid_size_unit": "base_asset",
            "ask_size_unit": "base_asset",
            "tick_size": _as_str(price_filter.get("tickSize")),
            "quantity_step": _as_str(lot_size.get("stepSize")),
            "min_order_size": _as_str(lot_size.get("minQty")),
            "min_notional": _as_str(min_notional.get("notional")),
            "margin_asset": _as_str(symbol.get("marginAsset")),
            "funding_rate": _as_str(mark.get("lastFundingRate")),
            "next_funding_time": _as_str(mark.get("nextFundingTime")),
            "timestamp": _as_str(timestamp),
            "data_age_ms": data_age_ms,
            "comparability_pass": comparability_pass,
            "freshness_pass": freshness_pass,
        }
    )
    return _finalize(output)


def _parse_bybit_linear(
    *,
    venue_id: str,
    parser_mode: str,
    ticker_response: dict[str, Any] | None,
    orderbook_response: dict[str, Any] | None,
    metadata_response: dict[str, Any] | None,
    collected_at_utc: str | None,
    max_data_age_ms: float | None,
) -> dict[str, Any]:
    missing = _missing_payloads(
        ("ticker_response", ticker_response),
        ("orderbook_response", orderbook_response),
        ("metadata_response", metadata_response),
    )
    if missing:
        return _need_data(venue_id, parser_mode, missing)
    ticker = _require_dict(ticker_response, "ticker_response")
    orderbook = _require_dict(orderbook_response, "orderbook_response")
    metadata = _require_dict(metadata_response, "metadata_response")
    ticker_result = _require_dict(ticker.get("result"), "ticker_response.result")
    ticker_item = _first_item(ticker_result.get("list"), "ticker_response.result.list")
    book = _require_dict(orderbook.get("result"), "orderbook_response.result")
    metadata_result = _require_dict(metadata.get("result"), "metadata_response.result")
    instrument = _first_item(metadata_result.get("list"), "metadata_response.result.list")
    price_filter = _require_dict(instrument.get("priceFilter"), "metadata_response.priceFilter")
    lot_size = _require_dict(instrument.get("lotSizeFilter"), "metadata_response.lotSizeFilter")
    best_bid, best_bid_size = _first_level(book.get("b"), "bid")
    best_ask, best_ask_size = _first_level(book.get("a"), "ask")

    ticker_category = _as_str(ticker_result.get("category"))
    metadata_category = _as_str(metadata_result.get("category"))
    ticker_symbol = _as_str(ticker_item.get("symbol"))
    book_symbol = _as_str(book.get("s"))
    metadata_symbol = _as_str(instrument.get("symbol"))
    comparability_pass = (
        ticker_category == metadata_category == "linear" and ticker_symbol == book_symbol == metadata_symbol
    )
    timestamp = book.get("ts") or book.get("cts") or ticker.get("time")
    freshness_pass, data_age_ms = _freshness(timestamp, collected_at_utc, max_data_age_ms)

    output = _base_output(venue_id, parser_mode)
    output.update(
        {
            "instrument_id": metadata_symbol or ticker_symbol,
            "instrument_type": "linear_perpetual",
            "mark_price": _as_str(ticker_item.get("markPrice")),
            "index_price": _as_str(ticker_item.get("indexPrice")),
            "bid": best_bid,
            "ask": best_ask,
            "bid_size_raw": best_bid_size,
            "ask_size_raw": best_ask_size,
            "bid_size_unit": "base_asset",
            "ask_size_unit": "base_asset",
            "tick_size": _as_str(price_filter.get("tickSize")),
            "quantity_step": _as_str(lot_size.get("qtyStep")),
            "min_order_size": _as_str(lot_size.get("minOrderQty")),
            "min_notional": _as_str(lot_size.get("minNotionalValue")),
            "settle_currency": _as_str(instrument.get("settleCoin")),
            "funding_rate": _as_str(ticker_item.get("fundingRate")),
            "next_funding_time": _as_str(ticker_item.get("nextFundingTime")),
            "timestamp": _as_str(timestamp),
            "data_age_ms": data_age_ms,
            "comparability_pass": comparability_pass,
            "freshness_pass": freshness_pass,
        }
    )
    if instrument.get("fundingInterval") is not None:
        output["parser_warnings"].append(f"funding_interval={instrument['fundingInterval']}")
    return _finalize(output)


def _parse_okx_swap(
    *,
    venue_id: str,
    parser_mode: str,
    mark_response: dict[str, Any] | None,
    orderbook_response: dict[str, Any] | None,
    metadata_response: dict[str, Any] | None,
    ticker_response: dict[str, Any] | None,
    collected_at_utc: str | None,
    max_data_age_ms: float | None,
) -> dict[str, Any]:
    book_or_ticker = orderbook_response if orderbook_response is not None else ticker_response
    missing = _missing_payloads(
        ("mark_response", mark_response),
        ("orderbook_response", book_or_ticker),
        ("metadata_response", metadata_response),
    )
    if missing:
        return _need_data(venue_id, parser_mode, missing)
    mark_payload = _require_dict(mark_response, "mark_response")
    market_payload = _require_dict(book_or_ticker, "orderbook_response")
    metadata_payload = _require_dict(metadata_response, "metadata_response")
    mark = _first_item(mark_payload.get("data"), "mark_response.data")
    market = _first_item(market_payload.get("data"), "orderbook_response.data")
    metadata = _first_item(metadata_payload.get("data"), "metadata_response.data")

    bid, bid_size, ask, ask_size = _okx_top_of_book(market)
    mark_inst = _as_str(mark.get("instId"))
    market_inst = _as_str(market.get("instId")) if market.get("instId") is not None else mark_inst
    metadata_inst = _as_str(metadata.get("instId"))
    comparability_pass = bool(mark_inst and mark_inst == market_inst == metadata_inst)
    timestamp = mark.get("ts") or market.get("ts")
    freshness_pass, data_age_ms = _freshness(timestamp, collected_at_utc, max_data_age_ms)

    output = _base_output(venue_id, parser_mode)
    output.update(
        {
            "instrument_id": metadata_inst or mark_inst,
            "instrument_type": "linear_swap" if _as_str(metadata.get("ctType")) == "linear" else _as_str(metadata.get("instType")),
            "mark_price": _as_str(mark.get("markPx")),
            "bid": bid,
            "ask": ask,
            "bid_size_raw": bid_size,
            "ask_size_raw": ask_size,
            "bid_size_unit": "contracts",
            "ask_size_unit": "contracts",
            "tick_size": _as_str(metadata.get("tickSz")),
            "lot_size": _as_str(metadata.get("lotSz")),
            "min_order_size": _as_str(metadata.get("minSz")),
            "contract_value": _as_str(metadata.get("ctVal")),
            "contract_multiplier": _as_str(metadata.get("ctMult")),
            "contract_value_currency": _as_str(metadata.get("ctValCcy")),
            "settle_currency": _as_str(metadata.get("settleCcy")),
            "timestamp": _as_str(timestamp),
            "data_age_ms": data_age_ms,
            "comparability_pass": comparability_pass,
            "freshness_pass": freshness_pass,
        }
    )
    return _finalize(output)


def _base_output(venue_id: str, parser_mode: str) -> dict[str, Any]:
    output = {field: None for field in _OUTPUT_FIELDS}
    output.update(
        {
            "venue_id": venue_id,
            "parser_mode": parser_mode,
            "comparability_pass": False,
            "freshness_pass": None,
            "required_missing_fields": [],
            "parser_warnings": [],
            "normalized_status": STATUS_OK,
        }
    )
    return output


def _need_data(venue_id: str, parser_mode: str, missing_fields: Iterable[str]) -> dict[str, Any]:
    output = _base_output(venue_id, parser_mode)
    output["required_missing_fields"] = sorted(set(missing_fields))
    output["normalized_status"] = STATUS_NEED_DATA
    output["comparability_pass"] = False
    output["freshness_pass"] = False
    return output


def _finalize(output: dict[str, Any]) -> dict[str, Any]:
    missing = set(output["required_missing_fields"])
    for field in ("mark_price", "bid", "ask"):
        if output.get(field) in (None, ""):
            missing.add(field)
    if not output.get("instrument_id"):
        missing.add("instrument_id")
    if not output.get("comparability_pass"):
        missing.add("instrument_match")
    if output.get("freshness_pass") is False:
        missing.add("fresh_timestamp")

    mode = output.get("parser_mode")
    if mode == PARSER_MODE_BINANCE_USDM:
        for field in ("tick_size", "quantity_step", "min_order_size", "min_notional", "margin_asset"):
            if output.get(field) in (None, ""):
                missing.add(field)
    elif mode == PARSER_MODE_BYBIT_LINEAR:
        for field in ("tick_size", "quantity_step", "min_order_size", "min_notional", "settle_currency"):
            if output.get(field) in (None, ""):
                missing.add(field)
    elif mode == PARSER_MODE_OKX_SWAP:
        for field in ("contract_value", "contract_multiplier", "contract_value_currency", "settle_currency", "tick_size", "lot_size", "min_order_size"):
            if output.get(field) in (None, ""):
                missing.add(field)

    output["required_missing_fields"] = sorted(missing)
    output["normalized_status"] = STATUS_NEED_DATA if missing else STATUS_OK
    return output


def _missing_payloads(*items: tuple[str, dict[str, Any] | None]) -> list[str]:
    return [name for name, payload in items if payload is None]


def _require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MarkOrderbookGapParserError(f"{label} must be a dict")
    return value


def _first_item(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, list) or not value:
        raise MarkOrderbookGapParserError(f"{label} must be a non-empty list")
    return _require_dict(value[0], f"{label}[0]")


def _first_level(value: Any, side: str) -> tuple[str | None, str | None]:
    if not isinstance(value, list) or not value or not isinstance(value[0], list) or len(value[0]) < 2:
        return None, None
    return _as_str(value[0][0]), _as_str(value[0][1])


def _binance_filter(symbol: dict[str, Any], filter_type: str) -> dict[str, Any]:
    filters = symbol.get("filters")
    if not isinstance(filters, list):
        raise MarkOrderbookGapParserError("metadata_response.symbols[0].filters must be a list")
    for item in filters:
        if isinstance(item, dict) and item.get("filterType") == filter_type:
            return item
    return {}


def _okx_top_of_book(market: dict[str, Any]) -> tuple[str | None, str | None, str | None, str | None]:
    if "bids" in market or "asks" in market:
        bid, bid_size = _first_level(market.get("bids"), "bid")
        ask, ask_size = _first_level(market.get("asks"), "ask")
        return bid, bid_size, ask, ask_size
    return _as_str(market.get("bidPx")), _as_str(market.get("bidSz")), _as_str(market.get("askPx")), _as_str(market.get("askSz"))


def _freshness(
    timestamp: Any,
    collected_at_utc: str | None,
    max_data_age_ms: float | None,
) -> tuple[bool | None, float | None]:
    if timestamp is None or collected_at_utc is None or max_data_age_ms is None:
        return None, None
    try:
        ts_ms = float(timestamp)
        collected = datetime.fromisoformat(collected_at_utc.replace("Z", "+00:00"))
        if collected.tzinfo is None:
            collected = collected.replace(tzinfo=timezone.utc)
        data_age_ms = collected.timestamp() * 1000 - ts_ms
    except (TypeError, ValueError):
        return False, None
    return data_age_ms <= max_data_age_ms, data_age_ms


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
