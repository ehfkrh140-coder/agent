"""Pure mocked-source parser helpers for Spot-Futures Basis planning.

This module accepts already-fetched or mocked public response dictionaries and
normalizes them into venue-neutral observation dictionaries. It intentionally
performs no network I/O, no credential lookup, no adapter/registry wiring, no
OpportunityPacket creation, and no readiness/Council/alert/execution decisions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

STATUS_OK = "OK"
STATUS_NEED_DATA = "NEED_DATA"

BINANCE_VENUE_ID = "binance"
BINANCE_SPOT_VENUE_NAME = "Binance Spot"
BINANCE_USDM_VENUE_NAME = "Binance USDⓈ-M Futures"
NO_TRADE_EXECUTION_POLICY = "NO_TRADE_ONLY"
SPOT_FUTURES_BASIS_STATUS = "experimental_non_active_no_trade_only"

SPOT_ENDPOINT_IDS = (
    "binance_spot_book_ticker",
    "binance_spot_depth",
    "binance_spot_exchange_info",
)
PERP_ENDPOINT_IDS = (
    "binance_futures_book_ticker",
    "binance_futures_depth",
    "binance_futures_premium_index",
    "binance_futures_exchange_info",
)

BYBIT_VENUE_ID = "bybit"
BYBIT_SPOT_VENUE_NAME = "Bybit Spot"
BYBIT_DERIVATIVES_VENUE_NAME = "Bybit Derivatives V5"
BYBIT_SPOT_ENDPOINT_IDS = (
    "bybit_v5_market_tickers_spot",
    "bybit_v5_market_orderbook_spot",
    "bybit_v5_market_instruments_info_spot",
)
BYBIT_LINEAR_ENDPOINT_IDS = (
    "bybit_v5_market_tickers_linear",
    "bybit_v5_market_orderbook_linear",
    "bybit_v5_market_instruments_info_linear",
)

SOURCE_BUNDLE_ASSUMPTIONS = (
    "public no-key endpoints only",
    "analysis-only parser output",
    "no private API",
    "no trading behavior",
    "mark price is not executable",
    "last price is weak context only if present",
)


class SpotFuturesBasisParserError(ValueError):
    """Raised for malformed top-level parser inputs."""


def parse_binance_spot_observation(
    book_ticker: dict[str, Any],
    depth: dict[str, Any],
    exchange_info: dict[str, Any],
    *,
    fetched_at_utc: str | None = None,
    latency_ms: int | float | None = None,
) -> dict[str, Any]:
    """Normalize Binance Spot mocked public source payloads.

    Missing or invalid executable fields are represented in
    ``required_missing_fields`` and ``parser_warnings`` instead of raising,
    allowing future tests to assert parser behavior before readiness policy is
    implemented.
    """

    _require_mapping(book_ticker, "book_ticker")
    _require_mapping(depth, "depth")
    _require_mapping(exchange_info, "exchange_info")

    required_missing_fields: list[str] = []
    parser_warnings: list[str] = []

    symbol_info = _first_symbol(exchange_info, required_missing_fields, parser_warnings, "spot_exchange_info")
    price_filter = _find_filter(symbol_info, "PRICE_FILTER")
    lot_size = _find_filter(symbol_info, "LOT_SIZE")
    min_notional_filter = _find_first_filter(symbol_info, ("MIN_NOTIONAL", "NOTIONAL"))

    best_bid = _positive_float_field(book_ticker, "bidPrice", "spot_bid_missing", required_missing_fields, parser_warnings)
    best_bid_qty = _positive_float_field(
        book_ticker, "bidQty", "spot_bid_qty_missing", required_missing_fields, parser_warnings
    )
    best_ask = _positive_float_field(book_ticker, "askPrice", "spot_ask_missing", required_missing_fields, parser_warnings)
    best_ask_qty = _positive_float_field(
        book_ticker, "askQty", "spot_ask_qty_missing", required_missing_fields, parser_warnings
    )

    symbol = _string_field(book_ticker, "symbol") or _string_field(symbol_info, "symbol")
    base_asset = _string_field(symbol_info, "baseAsset")
    quote_asset = _string_field(symbol_info, "quoteAsset")
    if not symbol:
        _add_missing(required_missing_fields, "spot_symbol_missing")
    if not base_asset:
        _add_missing(required_missing_fields, "base_asset_missing")
    if not quote_asset:
        _add_missing(required_missing_fields, "quote_asset_missing")

    depth_bids = _parse_depth_levels(depth.get("bids"), "spot_depth_bids", required_missing_fields, parser_warnings)
    depth_asks = _parse_depth_levels(depth.get("asks"), "spot_depth_asks", required_missing_fields, parser_warnings)

    tick_size = _float_or_none(price_filter.get("tickSize")) if price_filter else None
    step_size = _float_or_none(lot_size.get("stepSize")) if lot_size else None
    min_notional = _extract_min_notional(min_notional_filter)
    if tick_size is None:
        _add_missing(required_missing_fields, "spot_tick_size_missing")
    if step_size is None:
        _add_missing(required_missing_fields, "spot_step_size_missing")
    if min_notional is None:
        _add_missing(required_missing_fields, "spot_min_notional_missing")

    return _finalize_observation(
        {
            "venue_id": BINANCE_VENUE_ID,
            "venue_name": BINANCE_SPOT_VENUE_NAME,
            "market_type": "spot",
            "symbol": symbol,
            "base_asset": base_asset,
            "quote_asset": quote_asset,
            "best_bid": best_bid,
            "best_bid_qty": best_bid_qty,
            "best_ask": best_ask,
            "best_ask_qty": best_ask_qty,
            "bid_qty_unit": "base_asset",
            "ask_qty_unit": "base_asset",
            "book_update_id": depth.get("lastUpdateId"),
            "depth_bids": depth_bids,
            "depth_asks": depth_asks,
            "tick_size": tick_size,
            "step_size": step_size,
            "min_notional": min_notional,
            "raw_endpoint_ids": list(SPOT_ENDPOINT_IDS),
            "data_age_ms": _data_age_ms(None, fetched_at_utc),
            "latency_ms": latency_ms,
            "required_missing_fields": required_missing_fields,
            "parser_warnings": parser_warnings,
        }
    )



def parse_bybit_spot_observation(
    ticker_payload: dict[str, Any],
    orderbook_payload: dict[str, Any],
    instruments_info_payload: dict[str, Any],
    *,
    created_at_utc: str | None = None,
    latency_ms: int | float | None = None,
) -> dict[str, Any]:
    """Normalize Bybit Spot mocked public source payloads.

    The helper is a pure dict parser. It preserves Bybit category/envelope
    context and records missing executable or metadata fields in
    ``required_missing_fields`` instead of raising.
    """

    _require_mapping(ticker_payload, "ticker_payload")
    _require_mapping(orderbook_payload, "orderbook_payload")
    _require_mapping(instruments_info_payload, "instruments_info_payload")

    required_missing_fields: list[str] = []
    parser_warnings: list[str] = [
        "last_price_weak_context_only",
        "same_symbol_does_not_imply_same_product_semantics",
    ]

    ticker_result = _mapping_field(ticker_payload, "result")
    orderbook_result = _mapping_field(orderbook_payload, "result")
    instruments_result = _mapping_field(instruments_info_payload, "result")
    ticker = _first_result_list_item(ticker_result, "spot_ticker", required_missing_fields, parser_warnings)
    instrument = _first_result_list_item(
        instruments_result, "spot_instruments_info", required_missing_fields, parser_warnings
    )

    _validate_bybit_category(ticker_result, "spot", "spot_ticker", required_missing_fields, parser_warnings)
    _validate_bybit_category(
        orderbook_result,
        "spot",
        "spot_orderbook",
        required_missing_fields,
        parser_warnings,
        allow_missing=True,
    )
    _validate_bybit_category(instruments_result, "spot", "spot_instruments_info", required_missing_fields, parser_warnings)

    depth_bids = _parse_depth_levels(orderbook_result.get("b"), "spot_depth_bids", required_missing_fields, parser_warnings)
    depth_asks = _parse_depth_levels(orderbook_result.get("a"), "spot_depth_asks", required_missing_fields, parser_warnings)

    best_bid, best_bid_qty = _top_of_book_or_ticker(
        depth_bids,
        ticker,
        "bid1Price",
        "bid1Size",
        "spot_bid_missing",
        "spot_bid_qty_missing",
        required_missing_fields,
        parser_warnings,
    )
    best_ask, best_ask_qty = _top_of_book_or_ticker(
        depth_asks,
        ticker,
        "ask1Price",
        "ask1Size",
        "spot_ask_missing",
        "spot_ask_qty_missing",
        required_missing_fields,
        parser_warnings,
    )

    symbol = _string_field(orderbook_result, "s") or _string_field(ticker, "symbol") or _string_field(instrument, "symbol")
    base_asset = _string_field(instrument, "baseCoin")
    quote_asset = _string_field(instrument, "quoteCoin")
    if not symbol:
        _add_missing(required_missing_fields, "spot_symbol_missing")
    if not base_asset:
        _add_missing(required_missing_fields, "base_asset_missing")
    if not quote_asset:
        _add_missing(required_missing_fields, "quote_asset_missing")

    price_filter = _mapping_field(instrument, "priceFilter")
    lot_size_filter = _mapping_field(instrument, "lotSizeFilter")
    tick_size = _float_or_none(price_filter.get("tickSize"))
    step_size = _float_or_none(_first_present(lot_size_filter, ("basePrecision", "qtyStep", "stepSize")))
    min_order_size = _float_or_none(_first_present(lot_size_filter, ("minOrderQty", "minOrderSize")))
    min_notional = _float_or_none(_first_present(lot_size_filter, ("minOrderAmt", "minNotionalValue", "minNotional")))
    if tick_size is None:
        _add_missing(required_missing_fields, "spot_tick_size_missing")
    if step_size is None:
        _add_missing(required_missing_fields, "spot_step_size_missing")
    if min_order_size is None:
        _add_missing(required_missing_fields, "spot_min_order_size_missing")
    if min_notional is None:
        _add_missing(required_missing_fields, "spot_min_notional_missing")

    timestamp = orderbook_result.get("ts") or ticker_payload.get("time") or instruments_info_payload.get("time")

    return _finalize_observation(
        {
            "venue_id": BYBIT_VENUE_ID,
            "venue_name": BYBIT_SPOT_VENUE_NAME,
            "market_type": "spot",
            "category": "spot",
            "symbol": symbol,
            "base_asset": base_asset,
            "quote_asset": quote_asset,
            "best_bid": best_bid,
            "best_bid_qty": best_bid_qty,
            "best_ask": best_ask,
            "best_ask_qty": best_ask_qty,
            "bid_qty_unit": "base_asset",
            "ask_qty_unit": "base_asset",
            "book_timestamp": timestamp,
            "book_update_id": orderbook_result.get("u"),
            "book_sequence": orderbook_result.get("seq"),
            "depth_bids": depth_bids,
            "depth_asks": depth_asks,
            "last_price": _float_or_none(ticker.get("lastPrice")),
            "last_price_role": "weak_context_only_not_executable",
            "tick_size": tick_size,
            "step_size": step_size,
            "min_order_size": min_order_size,
            "min_notional": min_notional,
            "raw_endpoint_ids": list(BYBIT_SPOT_ENDPOINT_IDS),
            "source_envelope": _bybit_source_envelope(
                ticker_payload, orderbook_payload, instruments_info_payload
            ),
            "data_age_ms": _data_age_ms(timestamp, created_at_utc),
            "latency_ms": latency_ms,
            "required_missing_fields": required_missing_fields,
            "parser_warnings": parser_warnings,
        }
    )


def parse_bybit_perp_observation(
    ticker_payload: dict[str, Any],
    orderbook_payload: dict[str, Any],
    instruments_info_payload: dict[str, Any],
    *,
    created_at_utc: str | None = None,
    latency_ms: int | float | None = None,
) -> dict[str, Any]:
    """Normalize Bybit USDT linear perpetual mocked public source payloads."""

    _require_mapping(ticker_payload, "ticker_payload")
    _require_mapping(orderbook_payload, "orderbook_payload")
    _require_mapping(instruments_info_payload, "instruments_info_payload")

    required_missing_fields: list[str] = []
    parser_warnings: list[str] = [
        "mark_index_funding_context_only_not_executable",
        "last_price_weak_context_only",
        "same_symbol_does_not_imply_same_product_semantics",
    ]

    ticker_result = _mapping_field(ticker_payload, "result")
    orderbook_result = _mapping_field(orderbook_payload, "result")
    instruments_result = _mapping_field(instruments_info_payload, "result")
    ticker = _first_result_list_item(ticker_result, "linear_ticker", required_missing_fields, parser_warnings)
    instrument = _first_result_list_item(
        instruments_result, "linear_instruments_info", required_missing_fields, parser_warnings
    )

    _validate_bybit_category(ticker_result, "linear", "linear_ticker", required_missing_fields, parser_warnings)
    _validate_bybit_category(
        orderbook_result,
        "linear",
        "linear_orderbook",
        required_missing_fields,
        parser_warnings,
        allow_missing=True,
    )
    _validate_bybit_category(instruments_result, "linear", "linear_instruments_info", required_missing_fields, parser_warnings)

    depth_bids = _parse_depth_levels(orderbook_result.get("b"), "perp_depth_bids", required_missing_fields, parser_warnings)
    depth_asks = _parse_depth_levels(orderbook_result.get("a"), "perp_depth_asks", required_missing_fields, parser_warnings)

    best_bid, best_bid_qty = _top_of_book_or_ticker(
        depth_bids,
        ticker,
        "bid1Price",
        "bid1Size",
        "perp_bid_missing",
        "perp_bid_qty_missing",
        required_missing_fields,
        parser_warnings,
    )
    best_ask, best_ask_qty = _top_of_book_or_ticker(
        depth_asks,
        ticker,
        "ask1Price",
        "ask1Size",
        "perp_ask_missing",
        "perp_ask_qty_missing",
        required_missing_fields,
        parser_warnings,
    )

    symbol = _string_field(orderbook_result, "s") or _string_field(ticker, "symbol") or _string_field(instrument, "symbol")
    base_asset = _string_field(instrument, "baseCoin")
    quote_asset = _string_field(instrument, "quoteCoin")
    settlement_asset = _string_field(instrument, "settleCoin")
    contract_type = _string_field(instrument, "contractType")
    if not symbol:
        _add_missing(required_missing_fields, "perp_symbol_missing")
    if not base_asset:
        _add_missing(required_missing_fields, "base_asset_missing")
    if not quote_asset:
        _add_missing(required_missing_fields, "quote_asset_missing")
    if not settlement_asset:
        _add_missing(required_missing_fields, "settlement_asset_missing")
    if not contract_type:
        _add_missing(required_missing_fields, "contract_type_missing")

    price_filter = _mapping_field(instrument, "priceFilter")
    lot_size_filter = _mapping_field(instrument, "lotSizeFilter")
    tick_size = _float_or_none(price_filter.get("tickSize"))
    step_size = _float_or_none(_first_present(lot_size_filter, ("qtyStep", "stepSize")))
    min_order_size = _float_or_none(_first_present(lot_size_filter, ("minOrderQty", "minOrderSize")))
    min_notional = _float_or_none(_first_present(lot_size_filter, ("minNotionalValue", "minNotional")))
    if tick_size is None:
        _add_missing(required_missing_fields, "perp_tick_size_missing")
    if step_size is None:
        _add_missing(required_missing_fields, "perp_step_size_missing")
    if min_order_size is None:
        _add_missing(required_missing_fields, "perp_min_order_size_missing")
    if min_notional is None:
        _add_missing(required_missing_fields, "perp_min_notional_missing")

    mark_price = _float_or_none(ticker.get("markPrice"))
    index_price = _float_or_none(ticker.get("indexPrice"))
    funding_rate = _float_or_none(ticker.get("fundingRate"))
    next_funding_time = ticker.get("nextFundingTime")
    funding_interval = instrument.get("fundingInterval")
    if mark_price is None:
        _add_missing(required_missing_fields, "mark_price_missing")
    if index_price is None:
        _add_missing(required_missing_fields, "index_price_missing")
    if funding_rate is None:
        _add_missing(required_missing_fields, "funding_rate_missing")
    if next_funding_time in (None, ""):
        _add_missing(required_missing_fields, "next_funding_time_missing")
    if funding_interval is not None:
        parser_warnings.append(f"funding_interval={funding_interval}")

    timestamp = orderbook_result.get("ts") or ticker_payload.get("time") or instruments_info_payload.get("time")

    return _finalize_observation(
        {
            "venue_id": BYBIT_VENUE_ID,
            "venue_name": BYBIT_DERIVATIVES_VENUE_NAME,
            "market_type": "perp",
            "category": "linear",
            "symbol": symbol,
            "base_asset": base_asset,
            "quote_asset": quote_asset,
            "settlement_asset": settlement_asset,
            "margin_asset": settlement_asset,
            "contract_type": contract_type,
            "best_bid": best_bid,
            "best_bid_qty": best_bid_qty,
            "best_ask": best_ask,
            "best_ask_qty": best_ask_qty,
            "bid_qty_unit": "base_or_contract_quantity",
            "ask_qty_unit": "base_or_contract_quantity",
            "book_timestamp": timestamp,
            "book_update_id": orderbook_result.get("u"),
            "book_sequence": orderbook_result.get("seq"),
            "matching_engine_timestamp": orderbook_result.get("cts"),
            "depth_bids": depth_bids,
            "depth_asks": depth_asks,
            "last_price": _float_or_none(ticker.get("lastPrice")),
            "last_price_role": "weak_context_only_not_executable",
            "mark_price": mark_price,
            "index_price": index_price,
            "funding_rate": funding_rate,
            "next_funding_time": next_funding_time,
            "funding_interval": funding_interval,
            "tick_size": tick_size,
            "step_size": step_size,
            "min_order_size": min_order_size,
            "min_notional": min_notional,
            "raw_endpoint_ids": list(BYBIT_LINEAR_ENDPOINT_IDS),
            "source_envelope": _bybit_source_envelope(
                ticker_payload, orderbook_payload, instruments_info_payload
            ),
            "data_age_ms": _data_age_ms(timestamp, created_at_utc),
            "latency_ms": latency_ms,
            "required_missing_fields": required_missing_fields,
            "parser_warnings": parser_warnings,
        }
    )


def parse_binance_perp_observation(
    book_ticker: dict[str, Any],
    depth: dict[str, Any],
    premium_index: dict[str, Any],
    exchange_info: dict[str, Any],
    *,
    fetched_at_utc: str | None = None,
    latency_ms: int | float | None = None,
) -> dict[str, Any]:
    """Normalize Binance USDⓈ-M Futures mocked public source payloads."""

    _require_mapping(book_ticker, "book_ticker")
    _require_mapping(depth, "depth")
    _require_mapping(premium_index, "premium_index")
    _require_mapping(exchange_info, "exchange_info")

    required_missing_fields: list[str] = []
    parser_warnings: list[str] = []

    symbol_info = _first_symbol(exchange_info, required_missing_fields, parser_warnings, "futures_exchange_info")
    price_filter = _find_filter(symbol_info, "PRICE_FILTER")
    lot_size = _find_filter(symbol_info, "LOT_SIZE")
    min_notional_filter = _find_filter(symbol_info, "MIN_NOTIONAL")

    best_bid = _positive_float_field(book_ticker, "bidPrice", "perp_bid_missing", required_missing_fields, parser_warnings)
    best_bid_qty = _positive_float_field(
        book_ticker, "bidQty", "perp_bid_qty_missing", required_missing_fields, parser_warnings
    )
    best_ask = _positive_float_field(book_ticker, "askPrice", "perp_ask_missing", required_missing_fields, parser_warnings)
    best_ask_qty = _positive_float_field(
        book_ticker, "askQty", "perp_ask_qty_missing", required_missing_fields, parser_warnings
    )

    symbol = _string_field(book_ticker, "symbol") or _string_field(symbol_info, "symbol")
    base_asset = _string_field(symbol_info, "baseAsset")
    quote_asset = _string_field(symbol_info, "quoteAsset")
    margin_asset = _string_field(symbol_info, "marginAsset")
    contract_type = _string_field(symbol_info, "contractType")
    if not symbol:
        _add_missing(required_missing_fields, "perp_symbol_missing")
    if not base_asset:
        _add_missing(required_missing_fields, "base_asset_missing")
    if not quote_asset:
        _add_missing(required_missing_fields, "quote_asset_missing")
    if not margin_asset:
        _add_missing(required_missing_fields, "margin_asset_missing")
    if not contract_type:
        _add_missing(required_missing_fields, "contract_type_missing")

    depth_bids = _parse_depth_levels(depth.get("bids"), "perp_depth_bids", required_missing_fields, parser_warnings)
    depth_asks = _parse_depth_levels(depth.get("asks"), "perp_depth_asks", required_missing_fields, parser_warnings)

    tick_size = _float_or_none(price_filter.get("tickSize")) if price_filter else None
    step_size = _float_or_none(lot_size.get("stepSize")) if lot_size else None
    min_notional = _extract_min_notional(min_notional_filter)
    if tick_size is None:
        _add_missing(required_missing_fields, "perp_tick_size_missing")
    if step_size is None:
        _add_missing(required_missing_fields, "perp_step_size_missing")
    if min_notional is None:
        _add_missing(required_missing_fields, "perp_min_notional_missing")

    mark_price = _float_or_none(premium_index.get("markPrice"))
    index_price = _float_or_none(premium_index.get("indexPrice"))
    funding_rate = _float_or_none(premium_index.get("lastFundingRate"))
    interest_rate = _float_or_none(premium_index.get("interestRate"))
    if mark_price is None:
        _add_missing(required_missing_fields, "mark_price_missing")
    if index_price is None:
        _add_missing(required_missing_fields, "index_price_missing")
    if funding_rate is None:
        _add_missing(required_missing_fields, "funding_rate_missing")

    timestamp = depth.get("T") or depth.get("E") or book_ticker.get("time") or premium_index.get("time")

    return _finalize_observation(
        {
            "venue_id": BINANCE_VENUE_ID,
            "venue_name": BINANCE_USDM_VENUE_NAME,
            "market_type": "perp",
            "symbol": symbol,
            "base_asset": base_asset,
            "quote_asset": quote_asset,
            "settlement_asset": margin_asset,
            "margin_asset": margin_asset,
            "contract_type": contract_type,
            "best_bid": best_bid,
            "best_bid_qty": best_bid_qty,
            "best_ask": best_ask,
            "best_ask_qty": best_ask_qty,
            "bid_qty_unit": "base_asset",
            "ask_qty_unit": "base_asset",
            "book_timestamp": timestamp,
            "depth_bids": depth_bids,
            "depth_asks": depth_asks,
            "mark_price": mark_price,
            "index_price": index_price,
            "funding_rate": funding_rate,
            "interest_rate": interest_rate,
            "next_funding_time": premium_index.get("nextFundingTime"),
            "tick_size": tick_size,
            "step_size": step_size,
            "min_notional": min_notional,
            "raw_endpoint_ids": list(PERP_ENDPOINT_IDS),
            "data_age_ms": _data_age_ms(timestamp, fetched_at_utc),
            "latency_ms": latency_ms,
            "required_missing_fields": required_missing_fields,
            "parser_warnings": parser_warnings,
        }
    )


def build_spot_futures_basis_source_bundle(
    spot_observation: dict[str, Any],
    perp_observation: dict[str, Any],
) -> dict[str, Any]:
    """Bundle normalized spot/perp observations without readiness decisions."""

    _require_mapping(spot_observation, "spot_observation")
    _require_mapping(perp_observation, "perp_observation")
    return {
        "strategy_family": "spot_futures_basis",
        "strategy_id": "spot_futures_basis_v0",
        "status": SPOT_FUTURES_BASIS_STATUS,
        "spot_observation": spot_observation,
        "perp_observation": perp_observation,
        "source_venue_id": _source_venue_id(spot_observation, perp_observation),
        "comparison_type": "same_exchange_spot_perp_basis",
        "assumptions": list(SOURCE_BUNDLE_ASSUMPTIONS),
        "no_trade_only": True,
        "execution_policy": NO_TRADE_EXECUTION_POLICY,
    }


def _source_venue_id(spot_observation: dict[str, Any], perp_observation: dict[str, Any]) -> str:
    spot_venue = _string_field(spot_observation, "venue_id")
    perp_venue = _string_field(perp_observation, "venue_id")
    if spot_venue and spot_venue == perp_venue:
        return spot_venue
    return spot_venue or perp_venue or BINANCE_VENUE_ID


def _mapping_field(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_result_list_item(
    result: dict[str, Any],
    source_name: str,
    required_missing_fields: list[str],
    parser_warnings: list[str],
) -> dict[str, Any]:
    items = result.get("list")
    if not isinstance(items, list) or not items or not isinstance(items[0], dict):
        _add_missing(required_missing_fields, f"{source_name}_list_missing")
        parser_warnings.append(f"{source_name}_list_missing")
        return {}
    return items[0]


def _validate_bybit_category(
    result: dict[str, Any],
    expected_category: str,
    source_name: str,
    required_missing_fields: list[str],
    parser_warnings: list[str],
    *,
    allow_missing: bool = False,
) -> None:
    category = _string_field(result, "category")
    if not category and allow_missing:
        parser_warnings.append(f"{source_name}_category_missing_echo_accepted_expected_{expected_category}")
        return
    if category != expected_category:
        _add_missing(required_missing_fields, f"{source_name}_category_mismatch")
        parser_warnings.append(f"{source_name}_category={category}_expected_{expected_category}")


def _top_of_book_or_ticker(
    depth_levels: list[dict[str, float]],
    ticker: dict[str, Any],
    price_key: str,
    qty_key: str,
    missing_price_field: str,
    missing_qty_field: str,
    required_missing_fields: list[str],
    parser_warnings: list[str],
) -> tuple[float | None, float | None]:
    if depth_levels:
        top = depth_levels[0]
        return top["price"], top["qty"]
    price = _float_or_none(ticker.get(price_key))
    qty = _float_or_none(ticker.get(qty_key))
    if price is None or price <= 0:
        _add_missing(required_missing_fields, missing_price_field)
        parser_warnings.append(f"{missing_price_field}_invalid")
        price = None
    if qty is None or qty <= 0:
        _add_missing(required_missing_fields, missing_qty_field)
        parser_warnings.append(f"{missing_qty_field}_invalid")
        qty = None
    return price, qty


def _bybit_source_envelope(*payloads: dict[str, Any]) -> list[dict[str, Any]]:
    endpoint_ids = (
        "ticker",
        "orderbook",
        "instruments_info",
    )
    envelopes: list[dict[str, Any]] = []
    for endpoint_id, payload in zip(endpoint_ids, payloads, strict=False):
        envelopes.append(
            {
                "endpoint_id": endpoint_id,
                "retCode": payload.get("retCode"),
                "retMsg": payload.get("retMsg"),
                "time": payload.get("time"),
            }
        )
    return envelopes


def _finalize_observation(observation: dict[str, Any]) -> dict[str, Any]:
    required_missing_fields = observation["required_missing_fields"]
    observation["parser_normalized_status"] = STATUS_OK if not required_missing_fields else STATUS_NEED_DATA
    return observation


def _require_mapping(payload: dict[str, Any], name: str) -> None:
    if not isinstance(payload, dict):
        raise SpotFuturesBasisParserError(f"{name} must be a dict")


def _first_symbol(
    exchange_info: dict[str, Any],
    required_missing_fields: list[str],
    parser_warnings: list[str],
    source_name: str,
) -> dict[str, Any]:
    symbols = exchange_info.get("symbols")
    if not isinstance(symbols, list) or not symbols or not isinstance(symbols[0], dict):
        _add_missing(required_missing_fields, f"{source_name}_symbols_missing")
        parser_warnings.append(f"{source_name}_symbols_missing")
        return {}
    return symbols[0]


def _find_filter(symbol_info: dict[str, Any], filter_type: str) -> dict[str, Any] | None:
    return _find_first_filter(symbol_info, (filter_type,))


def _find_first_filter(symbol_info: dict[str, Any], filter_types: tuple[str, ...]) -> dict[str, Any] | None:
    filters = symbol_info.get("filters")
    if not isinstance(filters, list):
        return None
    for item in filters:
        if isinstance(item, dict) and item.get("filterType") in filter_types:
            return item
    return None


def _extract_min_notional(filter_payload: dict[str, Any] | None) -> float | None:
    if not filter_payload:
        return None
    return _float_or_none(_first_present(filter_payload, ("minNotional", "notional")))


def _parse_depth_levels(
    levels: Any,
    field_name: str,
    required_missing_fields: list[str],
    parser_warnings: list[str],
) -> list[dict[str, float]]:
    if not isinstance(levels, list) or not levels:
        _add_missing(required_missing_fields, f"{field_name}_missing")
        parser_warnings.append(f"{field_name}_missing")
        return []
    parsed: list[dict[str, float]] = []
    for index, level in enumerate(levels):
        if not isinstance(level, list | tuple) or len(level) < 2:
            parser_warnings.append(f"{field_name}_{index}_invalid")
            continue
        price = _float_or_none(level[0])
        qty = _float_or_none(level[1])
        if price is None or qty is None or price <= 0 or qty <= 0:
            parser_warnings.append(f"{field_name}_{index}_invalid")
            continue
        parsed.append({"price": price, "qty": qty})
    if not parsed:
        _add_missing(required_missing_fields, f"{field_name}_valid_levels_missing")
    return parsed


def _positive_float_field(
    payload: dict[str, Any],
    key: str,
    missing_field: str,
    required_missing_fields: list[str],
    parser_warnings: list[str],
) -> float | None:
    value = _float_or_none(payload.get(key))
    if value is None or value <= 0:
        _add_missing(required_missing_fields, missing_field)
        parser_warnings.append(f"{missing_field}_invalid")
        return None
    return value


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _string_field(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _first_present(payload: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in payload:
            return payload[key]
    return None


def _add_missing(required_missing_fields: list[str], field_name: str) -> None:
    if field_name not in required_missing_fields:
        required_missing_fields.append(field_name)


def _data_age_ms(source_timestamp_ms: Any, fetched_at_utc: str | None) -> float | None:
    if source_timestamp_ms is None or fetched_at_utc is None:
        return None
    source_timestamp = _float_or_none(source_timestamp_ms)
    if source_timestamp is None:
        return None
    fetched_at = _parse_datetime(fetched_at_utc)
    if fetched_at is None:
        return None
    return (fetched_at.timestamp() * 1000.0) - source_timestamp


def _parse_datetime(value: str) -> datetime | None:
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
