import copy
import json
import unittest
from pathlib import Path

from src.market_data.parsers.spot_futures_basis import (
    build_spot_futures_basis_source_bundle,
    parse_bybit_perp_observation,
    parse_bybit_spot_observation,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "market_data" / "spot_futures_basis"
PARSER_MODULE = Path("src/market_data/parsers/spot_futures_basis.py")
CREATED_AT_UTC = "2024-06-01T00:00:00Z"

FORBIDDEN_KEY_SUBSTRINGS = (
    "apikey",
    "secret",
    "token",
    "credential",
    "account",
    "balance",
    "position",
    "orderid",
    "clientorderid",
    "cancel",
    "withdraw",
    "deposit",
    "transfer",
    "privatekey",
    "execution_enabled",
    "auto_trade",
    "alert_enabled",
    "council_auto_call",
)


class SpotFuturesBasisBybitMockedParserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payloads = {
            "spot_ticker": cls._load_fixture("bybit_spot_ticker_btcusdt.json"),
            "spot_orderbook": cls._load_fixture("bybit_spot_orderbook_btcusdt.json"),
            "spot_instruments": cls._load_fixture("bybit_spot_instruments_info_btcusdt.json"),
            "linear_ticker": cls._load_fixture("bybit_linear_ticker_btcusdt.json"),
            "linear_orderbook": cls._load_fixture("bybit_linear_orderbook_btcusdt.json"),
            "linear_instruments": cls._load_fixture("bybit_linear_instruments_info_btcusdt.json"),
        }

    @staticmethod
    def _load_fixture(filename):
        with (FIXTURE_DIR / filename).open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _parse_spot(self, **overrides):
        payloads = {
            "ticker_payload": self.payloads["spot_ticker"],
            "orderbook_payload": self.payloads["spot_orderbook"],
            "instruments_info_payload": self.payloads["spot_instruments"],
        }
        payloads.update(overrides)
        return parse_bybit_spot_observation(
            copy.deepcopy(payloads["ticker_payload"]),
            copy.deepcopy(payloads["orderbook_payload"]),
            copy.deepcopy(payloads["instruments_info_payload"]),
            created_at_utc=CREATED_AT_UTC,
            latency_ms=12,
        )

    def _parse_perp(self, **overrides):
        payloads = {
            "ticker_payload": self.payloads["linear_ticker"],
            "orderbook_payload": self.payloads["linear_orderbook"],
            "instruments_info_payload": self.payloads["linear_instruments"],
        }
        payloads.update(overrides)
        return parse_bybit_perp_observation(
            copy.deepcopy(payloads["ticker_payload"]),
            copy.deepcopy(payloads["orderbook_payload"]),
            copy.deepcopy(payloads["instruments_info_payload"]),
            created_at_utc=CREATED_AT_UTC,
            latency_ms=15,
        )

    def test_parse_bybit_spot_observation_from_fixtures(self):
        observation = self._parse_spot()

        self.assertEqual("OK", observation["parser_normalized_status"])
        self.assertEqual([], observation["required_missing_fields"])
        self.assertEqual("bybit", observation["venue_id"])
        self.assertEqual("Bybit Spot", observation["venue_name"])
        self.assertEqual("spot", observation["market_type"])
        self.assertEqual("spot", observation["category"])
        self.assertEqual("BTCUSDT", observation["symbol"])
        self.assertEqual("BTC", observation["base_asset"])
        self.assertEqual("USDT", observation["quote_asset"])
        self.assertGreater(observation["best_bid"], 0)
        self.assertGreater(observation["best_ask"], observation["best_bid"])
        self.assertGreater(observation["best_bid_qty"], 0)
        self.assertGreater(observation["best_ask_qty"], 0)
        self.assertGreaterEqual(len(observation["depth_bids"]), 2)
        self.assertGreaterEqual(len(observation["depth_asks"]), 2)
        self.assertIsNotNone(observation["tick_size"])
        self.assertIsNotNone(observation["min_order_size"])
        self.assertIsNotNone(observation["min_notional"])
        self.assertLess(observation["data_age_ms"], 0)
        self.assertEqual(12, observation["latency_ms"])
        self.assertIn("bybit_v5_market_tickers_spot", observation["raw_endpoint_ids"])
        self.assertIn("bybit_v5_market_orderbook_spot", observation["raw_endpoint_ids"])
        self.assertIn("bybit_v5_market_instruments_info_spot", observation["raw_endpoint_ids"])
        self.assertNotEqual(observation["last_price"], observation["best_bid"])
        self.assertNotEqual(observation["last_price"], observation["best_ask"])
        self.assertEqual("weak_context_only_not_executable", observation["last_price_role"])

    def test_parse_bybit_perp_observation_from_fixtures(self):
        observation = self._parse_perp()

        self.assertEqual("OK", observation["parser_normalized_status"])
        self.assertEqual([], observation["required_missing_fields"])
        self.assertEqual("bybit", observation["venue_id"])
        self.assertEqual("Bybit Derivatives V5", observation["venue_name"])
        self.assertEqual("perp", observation["market_type"])
        self.assertEqual("linear", observation["category"])
        self.assertEqual("LinearPerpetual", observation["contract_type"])
        self.assertEqual("BTCUSDT", observation["symbol"])
        self.assertEqual("BTC", observation["base_asset"])
        self.assertEqual("USDT", observation["quote_asset"])
        self.assertEqual("USDT", observation["settlement_asset"])
        self.assertEqual("USDT", observation["margin_asset"])
        self.assertGreater(observation["best_bid"], 0)
        self.assertGreater(observation["best_ask"], observation["best_bid"])
        self.assertIsNotNone(observation["mark_price"])
        self.assertIsNotNone(observation["index_price"])
        self.assertIsNotNone(observation["funding_rate"])
        self.assertIsNotNone(observation["next_funding_time"])
        self.assertIsNotNone(observation["tick_size"])
        self.assertIsNotNone(observation["step_size"])
        self.assertIsNotNone(observation["min_order_size"])
        self.assertIsNotNone(observation["min_notional"])
        self.assertEqual(480, observation["funding_interval"])
        self.assertIn("funding_interval=480", observation["parser_warnings"])
        self.assertLess(observation["data_age_ms"], 0)
        self.assertEqual(15, observation["latency_ms"])
        self.assertIn("bybit_v5_market_tickers_linear", observation["raw_endpoint_ids"])
        self.assertIn("bybit_v5_market_orderbook_linear", observation["raw_endpoint_ids"])
        self.assertIn("bybit_v5_market_instruments_info_linear", observation["raw_endpoint_ids"])

    def test_bybit_spot_missing_bid_ask_reports_need_data(self):
        ticker = copy.deepcopy(self.payloads["spot_ticker"])
        orderbook = copy.deepcopy(self.payloads["spot_orderbook"])
        ticker_item = ticker["result"]["list"][0]
        for key in ("bid1Price", "bid1Size", "ask1Price", "ask1Size"):
            ticker_item.pop(key, None)
        orderbook["result"].pop("b", None)
        orderbook["result"].pop("a", None)

        observation = self._parse_spot(ticker_payload=ticker, orderbook_payload=orderbook)

        self.assertEqual("NEED_DATA", observation["parser_normalized_status"])
        self.assertIn("spot_bid_missing", observation["required_missing_fields"])
        self.assertIn("spot_ask_missing", observation["required_missing_fields"])

    def test_bybit_spot_missing_min_notional_reports_need_data(self):
        instruments = copy.deepcopy(self.payloads["spot_instruments"])
        lot_size = instruments["result"]["list"][0]["lotSizeFilter"]
        lot_size.pop("minOrderAmt", None)

        observation = self._parse_spot(instruments_info_payload=instruments)

        self.assertEqual("NEED_DATA", observation["parser_normalized_status"])
        self.assertIn("spot_min_notional_missing", observation["required_missing_fields"])

    def test_bybit_perp_mark_index_funding_do_not_replace_executable_bid_ask(self):
        ticker = copy.deepcopy(self.payloads["linear_ticker"])
        orderbook = copy.deepcopy(self.payloads["linear_orderbook"])
        ticker_item = ticker["result"]["list"][0]
        for key in ("bid1Price", "bid1Size", "ask1Price", "ask1Size"):
            ticker_item.pop(key, None)
        orderbook["result"].pop("b", None)
        orderbook["result"].pop("a", None)

        observation = self._parse_perp(ticker_payload=ticker, orderbook_payload=orderbook)

        self.assertEqual("NEED_DATA", observation["parser_normalized_status"])
        self.assertIn("perp_bid_missing", observation["required_missing_fields"])
        self.assertIn("perp_ask_missing", observation["required_missing_fields"])
        self.assertIsNotNone(observation["mark_price"])
        self.assertIsNotNone(observation["index_price"])
        self.assertIsNotNone(observation["funding_rate"])
        self.assertIsNone(observation["best_bid"])
        self.assertIsNone(observation["best_ask"])
        self.assertIn("mark_index_funding_context_only_not_executable", observation["parser_warnings"])

    def test_bybit_source_bundle_no_trade_metadata(self):
        spot = self._parse_spot()
        perp = self._parse_perp()
        bundle = build_spot_futures_basis_source_bundle(spot, perp)

        self.assertEqual("spot_futures_basis", bundle["strategy_family"])
        self.assertEqual("spot_futures_basis_v0", bundle["strategy_id"])
        self.assertEqual("bybit", bundle["source_venue_id"])
        self.assertEqual("same_exchange_spot_perp_basis", bundle["comparison_type"])
        self.assertIs(bundle["no_trade_only"], True)
        self.assertEqual("NO_TRADE_ONLY", bundle["execution_policy"])
        assumptions = bundle["assumptions"]
        self.assertIn("public no-key endpoints only", assumptions)
        self.assertIn("analysis-only parser output", assumptions)
        self.assertIn("no private API", assumptions)
        self.assertIn("no trading behavior", assumptions)
        self.assertIn("mark price is not executable", assumptions)

    def test_bybit_parser_output_has_no_private_or_execution_fields(self):
        spot = self._parse_spot()
        perp = self._parse_perp()
        bundle = build_spot_futures_basis_source_bundle(spot, perp)
        self._assert_no_forbidden_private_or_execution_content(bundle)

    def test_bybit_parser_module_no_file_or_network_behavior(self):
        parser_source = PARSER_MODULE.read_text(encoding="utf-8")
        self.assertNotIn("import requests", parser_source)
        self.assertNotIn("from requests", parser_source)
        self.assertNotIn("data/market_samples", parser_source)
        self.assertNotIn("data/generated_packets", parser_source)
        self.assertNotIn(".write(", parser_source)
        self.assertNotIn("open(", parser_source)

    def _assert_no_forbidden_private_or_execution_content(self, value):
        if isinstance(value, dict):
            for key, nested in value.items():
                normalized_key = key.lower()
                for forbidden in FORBIDDEN_KEY_SUBSTRINGS:
                    self.assertNotIn(forbidden, normalized_key, key)
                self._assert_no_forbidden_private_or_execution_content(nested)
        elif isinstance(value, list):
            for item in value:
                self._assert_no_forbidden_private_or_execution_content(item)
        elif isinstance(value, str):
            normalized_value = value.lower()
            for forbidden in FORBIDDEN_KEY_SUBSTRINGS:
                self.assertNotIn(forbidden, normalized_value, value)


if __name__ == "__main__":
    unittest.main()
