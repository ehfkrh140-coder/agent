from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any

from src.market_data.parsers.mark_orderbook_gap_hunt import parse_mark_orderbook_gap_snapshot

FIXTURE_DIR = Path("tests/fixtures/mark_orderbook_gap_hunt")


def _load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _binance_filter(metadata: dict[str, Any], filter_type: str) -> dict[str, Any]:
    filters = metadata["symbols"][0]["filters"]
    for item in filters:
        if item.get("filterType") == filter_type:
            return item
    raise AssertionError(f"missing Binance filter: {filter_type}")


def _normalize_binance_planning(fixture: dict[str, Any]) -> dict[str, Any]:
    mark = fixture["mark_response"]
    depth = fixture["depth_response"]
    metadata = fixture["metadata_response"]
    symbol = metadata["symbols"][0]
    price_filter = _binance_filter(metadata, "PRICE_FILTER")
    lot_size = _binance_filter(metadata, "LOT_SIZE")
    min_notional = _binance_filter(metadata, "MIN_NOTIONAL")

    same_symbol = mark["symbol"] == symbol["symbol"] == symbol["pair"]
    return {
        "venue_id": "binance",
        "instrument_id": symbol["symbol"],
        "instrument_type": "linear_perpetual",
        "mark_price": mark["markPrice"],
        "index_price": mark["indexPrice"],
        "bid": depth["bids"][0][0],
        "ask": depth["asks"][0][0],
        "bid_size_raw": depth["bids"][0][1],
        "ask_size_raw": depth["asks"][0][1],
        "tick_size": price_filter["tickSize"],
        "quantity_step": lot_size["stepSize"],
        "min_order_size": lot_size["minQty"],
        "min_notional": min_notional["notional"],
        "margin_asset": symbol["marginAsset"],
        "comparability_pass": same_symbol,
        "required_missing_fields": [] if same_symbol else ["instrument_match"],
        "readiness_status": "WATCH" if same_symbol else "NEED_DATA",
        "execution_allowed": False,
    }


def _normalize_bybit_planning(fixture: dict[str, Any]) -> dict[str, Any]:
    ticker = fixture["ticker_response"]
    orderbook = fixture["orderbook_response"]
    metadata = fixture["metadata_response"]
    ticker_item = ticker["result"]["list"][0]
    book = orderbook["result"]
    instrument = metadata["result"]["list"][0]
    lot_size = instrument["lotSizeFilter"]

    same_symbol = ticker_item["symbol"] == book["s"] == instrument["symbol"]
    same_category = ticker["result"]["category"] == metadata["result"]["category"] == "linear"
    comparable = same_symbol and same_category
    return {
        "venue_id": "bybit",
        "instrument_id": instrument["symbol"],
        "instrument_type": "linear_perpetual",
        "mark_price": ticker_item["markPrice"],
        "index_price": ticker_item["indexPrice"],
        "bid": book["b"][0][0],
        "ask": book["a"][0][0],
        "bid_size_raw": book["b"][0][1],
        "ask_size_raw": book["a"][0][1],
        "tick_size": instrument["priceFilter"]["tickSize"],
        "quantity_step": lot_size["qtyStep"],
        "min_order_size": lot_size["minOrderQty"],
        "min_notional": lot_size["minNotionalValue"],
        "settle_coin": instrument["settleCoin"],
        "funding_interval": instrument["fundingInterval"],
        "comparability_pass": comparable,
        "required_missing_fields": [] if comparable else ["instrument_or_category_match"],
        "readiness_status": "WATCH" if comparable else "NEED_DATA",
        "execution_allowed": False,
    }


def _normalize_okx_planning(fixture: dict[str, Any]) -> dict[str, Any]:
    mark = fixture["mark_response"]["data"][0]
    book = fixture["books_response"]["data"][0]
    metadata = fixture["metadata_response"]["data"][0]

    same_inst_id = mark["instId"] == metadata["instId"] == "BTC-USDT-SWAP"
    return {
        "venue_id": "okx",
        "instrument_id": metadata["instId"],
        "instrument_type": "linear_swap",
        "mark_price": mark["markPx"],
        "bid": book["bids"][0][0],
        "ask": book["asks"][0][0],
        "bid_size_raw": book["bids"][0][1],
        "ask_size_raw": book["asks"][0][1],
        "contract_value": metadata["ctVal"],
        "contract_multiplier": metadata["ctMult"],
        "contract_value_currency": metadata["ctValCcy"],
        "settle_currency": metadata["settleCcy"],
        "tick_size": metadata["tickSz"],
        "lot_size": metadata["lotSz"],
        "min_order_size": metadata["minSz"],
        "comparability_pass": same_inst_id,
        "required_missing_fields": [] if same_inst_id else ["inst_id_match"],
        "readiness_status": "WATCH" if same_inst_id else "NEED_DATA",
        "execution_allowed": False,
    }


class MarkOrderbookGapHuntParserFixtureTests(unittest.TestCase):
    def test_binance_valid_btcusdt_fixture_matches_expected_normalized_output(self) -> None:
        fixture = _load_fixture("binance_valid_btcusdt.json")

        self.assertIn("mark_response", fixture)
        self.assertIn("depth_response", fixture)
        self.assertIn("metadata_response", fixture)
        self.assertEqual(_normalize_binance_planning(fixture), fixture["expected_normalized"])
        self.assertEqual(fixture["expected_normalized"]["required_missing_fields"], [])
        self.assertFalse(fixture["expected_normalized"]["execution_allowed"])

    def test_bybit_valid_btcusdt_linear_fixture_matches_expected_normalized_output(self) -> None:
        fixture = _load_fixture("bybit_valid_btcusdt_linear.json")

        self.assertIn("ticker_response", fixture)
        self.assertIn("orderbook_response", fixture)
        self.assertIn("metadata_response", fixture)
        self.assertEqual(_normalize_bybit_planning(fixture), fixture["expected_normalized"])
        self.assertEqual(fixture["expected_normalized"]["required_missing_fields"], [])
        self.assertFalse(fixture["expected_normalized"]["execution_allowed"])

    def test_okx_valid_btc_usdt_swap_fixture_matches_expected_normalized_output(self) -> None:
        fixture = _load_fixture("okx_valid_btc_usdt_swap.json")

        self.assertIn("mark_response", fixture)
        self.assertTrue("books_response" in fixture or "ticker_response" in fixture)
        self.assertIn("metadata_response", fixture)
        self.assertEqual(_normalize_okx_planning(fixture), fixture["expected_normalized"])
        self.assertEqual(fixture["expected_normalized"]["required_missing_fields"], [])
        self.assertFalse(fixture["expected_normalized"]["execution_allowed"])


    def test_valid_fixtures_match_production_parser_core_fields(self) -> None:
        cases = [
            (
                "binance_valid_btcusdt.json",
                {"venue_id": "binance", "parser_mode": "binance_usdm", "mark_key": "mark_response", "book_key": "depth_response"},
            ),
            (
                "bybit_valid_btcusdt_linear.json",
                {"venue_id": "bybit", "parser_mode": "bybit_linear", "ticker_key": "ticker_response", "book_key": "orderbook_response"},
            ),
            (
                "okx_valid_btc_usdt_swap.json",
                {"venue_id": "okx", "parser_mode": "okx_swap", "mark_key": "mark_response", "book_key": "books_response"},
            ),
        ]
        for fixture_name, config in cases:
            with self.subTest(fixture=fixture_name):
                fixture = _load_fixture(fixture_name)
                parsed = parse_mark_orderbook_gap_snapshot(
                    venue_id=config["venue_id"],
                    parser_mode=config["parser_mode"],
                    mark_response=fixture.get(config.get("mark_key", "")),
                    ticker_response=fixture.get(config.get("ticker_key", "")),
                    orderbook_response=fixture[config["book_key"]],
                    metadata_response=fixture["metadata_response"],
                )
                expected = fixture["expected_normalized"]
                self.assertEqual(parsed["normalized_status"], "OK")
                self.assertEqual(parsed["instrument_id"], expected["instrument_id"])
                self.assertEqual(parsed["mark_price"], expected["mark_price"])
                self.assertEqual(parsed["bid"], expected["bid"])
                self.assertEqual(parsed["ask"], expected["ask"])
                self.assertTrue(parsed["comparability_pass"])
                self.assertEqual(parsed["required_missing_fields"], [])

    def test_failure_cases_pin_expected_need_data_or_reject_statuses(self) -> None:
        payload = _load_fixture("failure_cases.json")
        cases = {case["name"]: case for case in payload["cases"]}

        expected_statuses = {
            "missing_mark_response": "NEED_DATA",
            "missing_orderbook_or_bid_ask": "NEED_DATA",
            "missing_metadata": "NEED_DATA",
            "instrument_mismatch_btcusdt_ethusdt": "NEED_DATA",
            "bybit_category_type_mismatch": "NEED_DATA",
            "okx_inst_id_mismatch": "NEED_DATA",
            "unknown_size_unit_missing_ctval_or_lot_size": "NEED_DATA",
            "stale_timestamp_excessive_latency": "NEED_DATA",
            "non_positive_gap_after_fee_slippage_buffer": "REJECT",
            "positive_gap_complete_metadata_watch_only": "WATCH",
        }

        self.assertEqual(set(cases), set(expected_statuses))
        for name, status in expected_statuses.items():
            with self.subTest(name=name):
                case = cases[name]
                self.assertEqual(case["expected_readiness_status"], status)
                self.assertIn("required_missing_fields", case)
                self.assertFalse(case["execution_allowed"])
                self.assertFalse(case["council_auto_call"])

    def test_watch_fixture_is_not_execution_or_council_auto_call(self) -> None:
        payload = _load_fixture("failure_cases.json")
        watch_case = next(case for case in payload["cases"] if case["name"] == "positive_gap_complete_metadata_watch_only")

        self.assertEqual(watch_case["expected_readiness_status"], "WATCH")
        self.assertTrue(watch_case["comparability_pass"])
        self.assertTrue(watch_case["net_gap_pass"])
        self.assertFalse(watch_case["execution_allowed"])
        self.assertFalse(watch_case["council_auto_call"])

    def test_fixtures_contain_no_private_or_execution_material(self) -> None:
        forbidden = [
            "api_key",
            "api_secret",
            "private_key",
            "authorization",
            "bearer",
            "account_id",
            "balance_lookup",
            "withdrawal",
            "deposit_address",
            "transfer_id",
        ]
        for path in FIXTURE_DIR.glob("*.json"):
            text = path.read_text(encoding="utf-8").lower()
            for phrase in forbidden:
                with self.subTest(path=path.name, phrase=phrase):
                    self.assertNotIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
