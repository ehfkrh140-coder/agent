import json
import unittest
from pathlib import Path

from src.market_data.parsers.spot_futures_basis import (
    build_spot_futures_basis_source_bundle,
    parse_binance_perp_observation,
    parse_binance_spot_observation,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "market_data" / "spot_futures_basis"
FORBIDDEN_FIELD_SUBSTRINGS = (
    "apiKey",
    "secret",
    "token",
    "account",
    "balance",
    "position",
    "orderId",
    "clientOrderId",
    "order",
    "cancel",
    "withdraw",
    "deposit",
    "transfer",
    "privateKey",
)


def _load_fixture(filename):
    with (FIXTURE_DIR / filename).open("r", encoding="utf-8") as handle:
        return json.load(handle)


class SpotFuturesBasisMockedParserTest(unittest.TestCase):
    def setUp(self):
        self.spot_book_ticker = _load_fixture("binance_spot_book_ticker_btcusdt.json")
        self.spot_depth = _load_fixture("binance_spot_depth_btcusdt.json")
        self.spot_exchange_info = _load_fixture("binance_spot_exchange_info_btcusdt.json")
        self.futures_book_ticker = _load_fixture("binance_futures_book_ticker_btcusdt.json")
        self.futures_depth = _load_fixture("binance_futures_depth_btcusdt.json")
        self.futures_premium_index = _load_fixture("binance_futures_premium_index_btcusdt.json")
        self.futures_exchange_info = _load_fixture("binance_futures_exchange_info_btcusdt.json")

    def test_parse_binance_spot_observation_from_mocked_fixtures(self):
        spot = parse_binance_spot_observation(
            self.spot_book_ticker,
            self.spot_depth,
            self.spot_exchange_info,
            fetched_at_utc="2026-01-01T00:00:02Z",
            latency_ms=12.5,
        )

        self.assertEqual("binance", spot["venue_id"])
        self.assertEqual("Binance Spot", spot["venue_name"])
        self.assertEqual("spot", spot["market_type"])
        self.assertEqual("BTCUSDT", spot["symbol"])
        self.assertEqual("BTC", spot["base_asset"])
        self.assertEqual("USDT", spot["quote_asset"])
        self.assertGreater(spot["best_bid"], 0)
        self.assertGreater(spot["best_ask"], 0)
        self.assertGreater(spot["best_bid_qty"], 0)
        self.assertGreater(spot["best_ask_qty"], 0)
        self.assertEqual("base_asset", spot["bid_qty_unit"])
        self.assertEqual("base_asset", spot["ask_qty_unit"])
        self.assertGreaterEqual(len(spot["depth_bids"]), 2)
        self.assertGreaterEqual(len(spot["depth_asks"]), 2)
        self.assertAlmostEqual(0.01, spot["tick_size"])
        self.assertAlmostEqual(0.00001, spot["step_size"])
        self.assertAlmostEqual(5.0, spot["min_notional"])
        self.assertEqual(["binance_spot_book_ticker", "binance_spot_depth", "binance_spot_exchange_info"], spot["raw_endpoint_ids"])
        self.assertIsNone(spot["data_age_ms"])
        self.assertEqual(12.5, spot["latency_ms"])
        self.assertEqual("OK", spot["parser_normalized_status"])
        self.assertEqual([], spot["required_missing_fields"])
        self.assertEqual([], spot["parser_warnings"])
        self.assertNotIn("readiness_status", spot)
        self.assertNotIn("recommended_default_decision", spot)
        self.assertNotIn("schema_version", spot)
        self._assert_no_forbidden_fields(spot)

    def test_parse_binance_perp_observation_from_mocked_fixtures(self):
        perp = parse_binance_perp_observation(
            self.futures_book_ticker,
            self.futures_depth,
            self.futures_premium_index,
            self.futures_exchange_info,
            fetched_at_utc="2026-01-01T00:00:02Z",
            latency_ms=14,
        )

        self.assertEqual("binance", perp["venue_id"])
        self.assertEqual("Binance USDⓈ-M Futures", perp["venue_name"])
        self.assertEqual("perp", perp["market_type"])
        self.assertEqual("BTCUSDT", perp["symbol"])
        self.assertEqual("BTC", perp["base_asset"])
        self.assertEqual("USDT", perp["quote_asset"])
        self.assertEqual("USDT", perp["settlement_asset"])
        self.assertEqual("USDT", perp["margin_asset"])
        self.assertEqual("PERPETUAL", perp["contract_type"])
        self.assertGreater(perp["best_bid"], 0)
        self.assertGreater(perp["best_ask"], 0)
        self.assertGreater(perp["best_bid_qty"], 0)
        self.assertGreater(perp["best_ask_qty"], 0)
        self.assertEqual("base_asset", perp["bid_qty_unit"])
        self.assertEqual("base_asset", perp["ask_qty_unit"])
        self.assertEqual(1767225601050, perp["book_timestamp"])
        self.assertGreaterEqual(len(perp["depth_bids"]), 2)
        self.assertGreaterEqual(len(perp["depth_asks"]), 2)
        self.assertAlmostEqual(65003.85, perp["mark_price"])
        self.assertAlmostEqual(65002.75, perp["index_price"])
        self.assertAlmostEqual(0.0001, perp["funding_rate"])
        self.assertAlmostEqual(0.0001, perp["interest_rate"])
        self.assertEqual(1767254400000, perp["next_funding_time"])
        self.assertAlmostEqual(0.1, perp["tick_size"])
        self.assertAlmostEqual(0.001, perp["step_size"])
        self.assertAlmostEqual(5.0, perp["min_notional"])
        self.assertEqual("OK", perp["parser_normalized_status"])
        self.assertEqual([], perp["required_missing_fields"])
        self.assertEqual([], perp["parser_warnings"])
        self.assertNotIn("readiness_status", perp)
        self.assertNotIn("recommended_default_decision", perp)
        self.assertNotIn("schema_version", perp)
        self._assert_no_forbidden_fields(perp)

    def test_build_spot_futures_basis_source_bundle_is_no_trade_only(self):
        spot = parse_binance_spot_observation(
            self.spot_book_ticker,
            self.spot_depth,
            self.spot_exchange_info,
        )
        perp = parse_binance_perp_observation(
            self.futures_book_ticker,
            self.futures_depth,
            self.futures_premium_index,
            self.futures_exchange_info,
        )
        bundle = build_spot_futures_basis_source_bundle(spot, perp)

        self.assertEqual("spot_futures_basis", bundle["strategy_family"])
        self.assertEqual("spot_futures_basis_v0", bundle["strategy_id"])
        self.assertEqual("experimental_non_active_no_trade_only", bundle["status"])
        self.assertTrue(bundle["no_trade_only"])
        self.assertEqual("NO_TRADE_ONLY", bundle["execution_policy"])
        self.assertEqual("binance", bundle["source_venue_id"])
        self.assertEqual("same_exchange_spot_perp_basis", bundle["comparison_type"])
        self.assertIs(bundle["spot_observation"], spot)
        self.assertIs(bundle["perp_observation"], perp)
        assumptions = bundle["assumptions"]
        for expected in (
            "public no-key endpoints only",
            "analysis-only parser output",
            "no private API",
            "no trading behavior",
            "mark price is not executable",
        ):
            self.assertIn(expected, assumptions)
        self.assertNotIn("readiness_status", bundle)
        self.assertNotIn("recommended_default_decision", bundle)
        self.assertNotIn("schema_version", bundle)
        self._assert_no_forbidden_fields(bundle)

    def test_invalid_spot_best_bid_is_reported_without_readiness_decision(self):
        invalid_book_ticker = dict(self.spot_book_ticker)
        invalid_book_ticker["bidPrice"] = "0"

        spot = parse_binance_spot_observation(
            invalid_book_ticker,
            self.spot_depth,
            self.spot_exchange_info,
        )

        self.assertEqual("NEED_DATA", spot["parser_normalized_status"])
        self.assertIn("spot_bid_missing", spot["required_missing_fields"])
        self.assertIn("spot_bid_missing_invalid", spot["parser_warnings"])
        self.assertNotIn("readiness_status", spot)
        self.assertNotIn("recommended_default_decision", spot)

    def _assert_no_forbidden_fields(self, value):
        if isinstance(value, dict):
            for key, nested in value.items():
                normalized_key = key.lower()
                for forbidden in FORBIDDEN_FIELD_SUBSTRINGS:
                    self.assertNotIn(forbidden.lower(), normalized_key, key)
                self._assert_no_forbidden_fields(nested)
        elif isinstance(value, list):
            for item in value:
                self._assert_no_forbidden_fields(item)


if __name__ == "__main__":
    unittest.main()
