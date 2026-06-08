import copy
import json
import unittest
from pathlib import Path

from src.market_data.parsers.spot_futures_basis import (
    build_spot_futures_basis_source_bundle,
    parse_binance_perp_observation,
    parse_binance_spot_observation,
)
from src.strategy.spot_futures_basis_readiness import evaluate_spot_futures_basis_readiness


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


class SpotFuturesBasisMockedReadinessTest(unittest.TestCase):
    def setUp(self):
        spot = parse_binance_spot_observation(
            _load_fixture("binance_spot_book_ticker_btcusdt.json"),
            _load_fixture("binance_spot_depth_btcusdt.json"),
            _load_fixture("binance_spot_exchange_info_btcusdt.json"),
        )
        perp = parse_binance_perp_observation(
            _load_fixture("binance_futures_book_ticker_btcusdt.json"),
            _load_fixture("binance_futures_depth_btcusdt.json"),
            _load_fixture("binance_futures_premium_index_btcusdt.json"),
            _load_fixture("binance_futures_exchange_info_btcusdt.json"),
        )
        self.bundle = build_spot_futures_basis_source_bundle(spot, perp)

    def test_default_fixture_returns_reject_or_watch_no_trade_only(self):
        readiness = evaluate_spot_futures_basis_readiness(self.bundle)

        self.assertIn(readiness["readiness_status"], {"REJECT", "WATCH"})
        self.assertEqual(readiness["readiness_status"], readiness["recommended_default_decision"])
        for field in (
            "spot_bid",
            "spot_ask",
            "perp_bid",
            "perp_ask",
            "spot_mid",
            "perp_mid",
            "mid_basis_pct",
            "long_spot_short_perp_gross_pct",
            "long_perp_short_spot_gross_pct",
            "selected_direction",
            "selected_gross_basis_pct",
            "fee_slippage_buffer_pct",
            "estimated_net_basis_pct",
            "parser_normalized_status",
            "comparability_pass",
            "freshness_pass",
            "liquidity_pass",
        ):
            self.assertIn(field, readiness["metrics"])
        for assumption in (
            "public no-key endpoints only",
            "analysis-only readiness output",
            "no private API",
            "no trading behavior",
            "WATCH is not ENTER",
        ):
            self.assertIn(assumption, readiness["assumptions"])
        self.assertTrue(readiness["no_trade_only"])
        self.assertEqual("NO_TRADE_ONLY", readiness["execution_policy"])
        self.assertNotIn("schema_version", readiness)

    def test_no_positive_gross_basis_reject(self):
        bundle = copy.deepcopy(self.bundle)
        spot = bundle["spot_observation"]
        perp = bundle["perp_observation"]
        spot["best_bid"] = 100.0
        spot["best_ask"] = 101.0
        perp["best_bid"] = 100.5
        perp["best_ask"] = 101.5

        readiness = evaluate_spot_futures_basis_readiness(bundle)

        self.assertEqual("REJECT", readiness["readiness_status"])
        self.assertEqual("REJECT", readiness["recommended_default_decision"])
        self.assertFalse(readiness["readiness_pass"])
        self.assertIn("no_positive_gross_basis", readiness["warnings"])
        self.assertLessEqual(readiness["metrics"]["estimated_net_basis_pct"], 0)

    def test_positive_gross_negative_net_reject(self):
        bundle = copy.deepcopy(self.bundle)
        spot = bundle["spot_observation"]
        perp = bundle["perp_observation"]
        spot["best_ask"] = 100.0
        spot["best_bid"] = 99.9
        perp["best_bid"] = 100.1
        perp["best_ask"] = 100.2

        readiness = evaluate_spot_futures_basis_readiness(bundle, fee_slippage_buffer_pct=0.20)

        self.assertEqual("REJECT", readiness["readiness_status"])
        self.assertGreater(readiness["metrics"]["selected_gross_basis_pct"], 0)
        self.assertLessEqual(readiness["metrics"]["estimated_net_basis_pct"], 0)
        self.assertIn("non_positive_estimated_net_basis", readiness["warnings"])

    def test_positive_net_basis_watch_no_trade_only(self):
        bundle = copy.deepcopy(self.bundle)
        spot = bundle["spot_observation"]
        perp = bundle["perp_observation"]
        spot["best_ask"] = 100.0
        spot["best_bid"] = 99.9
        perp["best_bid"] = 101.0
        perp["best_ask"] = 101.1

        readiness = evaluate_spot_futures_basis_readiness(bundle, fee_slippage_buffer_pct=0.20)

        self.assertEqual("WATCH", readiness["readiness_status"])
        self.assertEqual("WATCH", readiness["recommended_default_decision"])
        self.assertTrue(readiness["readiness_pass"])
        self.assertIn("positive_net_basis_analysis_only", readiness["warnings"])
        self.assertIn("no trading behavior", readiness["assumptions"])
        self.assertIn("WATCH is not ENTER", readiness["assumptions"])
        self.assertTrue(readiness["no_trade_only"])
        self.assertEqual("NO_TRADE_ONLY", readiness["execution_policy"])

    def test_missing_executable_fields_need_data(self):
        bundle = copy.deepcopy(self.bundle)
        del bundle["spot_observation"]["best_ask"]

        readiness = evaluate_spot_futures_basis_readiness(bundle)

        self.assertEqual("NEED_DATA", readiness["readiness_status"])
        self.assertEqual("NEED_DATA", readiness["recommended_default_decision"])
        self.assertFalse(readiness["readiness_pass"])
        self.assertIn("spot_ask_missing", readiness["required_missing_fields"])
        self.assertIn("required_fields_missing", readiness["warnings"])

    def test_parser_missing_fields_need_data(self):
        bundle = copy.deepcopy(self.bundle)
        bundle["spot_observation"]["parser_normalized_status"] = "NEED_DATA"
        bundle["spot_observation"]["required_missing_fields"] = ["spot_ask_missing"]

        readiness = evaluate_spot_futures_basis_readiness(bundle)

        self.assertEqual("NEED_DATA", readiness["readiness_status"])
        self.assertIn("spot_spot_ask_missing", readiness["required_missing_fields"])
        self.assertIn("parser_required_missing_fields_present", readiness["warnings"])
        self.assertIn("parser_status_not_ok", readiness["warnings"])

    def test_mark_or_last_price_not_executable(self):
        bundle = copy.deepcopy(self.bundle)
        bundle["spot_observation"].pop("best_bid")
        bundle["spot_observation"].pop("best_ask")
        bundle["perp_observation"].pop("best_bid")
        bundle["perp_observation"].pop("best_ask")

        readiness = evaluate_spot_futures_basis_readiness(bundle)

        self.assertIn(readiness["readiness_status"], {"NEED_DATA", "REJECT"})
        self.assertNotEqual("WATCH", readiness["readiness_status"])
        self.assertIn("mark_price_not_executable", readiness["warnings"])

    def test_no_private_or_execution_fields(self):
        readiness = evaluate_spot_futures_basis_readiness(self.bundle)
        self._assert_no_forbidden_fields(readiness)

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
