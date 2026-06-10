from __future__ import annotations

import ast
import unittest
from decimal import Decimal
from pathlib import Path

from src.market_data.depth_vwap import (
    calculate_vwap_for_notional,
    calculate_vwap_for_size,
    summarize_depth_vwap,
)


class DepthVwapHelperTests(unittest.TestCase):
    def assert_decimal_equal(self, actual, expected: str) -> None:
        self.assertEqual(actual, Decimal(expected))

    def test_ask_vwap_fully_filled_at_first_level(self) -> None:
        result = calculate_vwap_for_size([["100", "5"], ["101", "2"]], "3", side="ask")

        self.assert_decimal_equal(result["vwap"], "100")
        self.assertEqual(result["levels_consumed"], 1)
        self.assertFalse(result["insufficient_depth"])

    def test_ask_vwap_consumes_multiple_levels(self) -> None:
        result = calculate_vwap_for_size([["100", "1"], ["101", "2"]], "3", side="ask")

        self.assert_decimal_equal(result["vwap"], "100.6666666666666666666666667")
        self.assertEqual(result["levels_consumed"], 2)
        self.assertFalse(result["insufficient_depth"])

    def test_ask_vwap_partial_fill_on_last_level(self) -> None:
        result = calculate_vwap_for_size([["100", "1"], ["102", "10"]], "2", side="ask")

        self.assert_decimal_equal(result["filled_size"], "2")
        self.assert_decimal_equal(result["filled_notional"], "202")
        self.assert_decimal_equal(result["vwap"], "101")
        self.assertEqual(result["levels_consumed"], 2)

    def test_bid_vwap_consumes_multiple_levels(self) -> None:
        result = calculate_vwap_for_size([["100", "1"], ["99", "2"]], "3", side="bid")

        self.assert_decimal_equal(result["vwap"], "99.33333333333333333333333333")
        self.assertEqual(result["levels_consumed"], 2)
        self.assertFalse(result["insufficient_depth"])

    def test_bid_vwap_partial_fill_on_last_level(self) -> None:
        result = calculate_vwap_for_size([["100", "1"], ["98", "10"]], "2", side="bid")

        self.assert_decimal_equal(result["filled_size"], "2")
        self.assert_decimal_equal(result["filled_notional"], "198")
        self.assert_decimal_equal(result["vwap"], "99")
        self.assertEqual(result["levels_consumed"], 2)

    def test_insufficient_ask_depth(self) -> None:
        result = calculate_vwap_for_size([["100", "1"]], "3", side="ask")

        self.assertTrue(result["insufficient_depth"])
        self.assert_decimal_equal(result["depth_coverage_pct"], "33.33333333333333333333333333")
        self.assert_decimal_equal(result["vwap"], "100")

    def test_insufficient_bid_depth(self) -> None:
        result = calculate_vwap_for_size([["100", "1"]], "4", side="bid")

        self.assertTrue(result["insufficient_depth"])
        self.assert_decimal_equal(result["depth_coverage_pct"], "25.00")
        self.assert_decimal_equal(result["vwap"], "100")

    def test_target_notional_ask_calculation(self) -> None:
        result = calculate_vwap_for_notional([["100", "1"], ["102", "2"]], "151", side="ask")

        self.assert_decimal_equal(result["filled_notional"], "151")
        self.assert_decimal_equal(result["filled_size"], "1.5")
        self.assert_decimal_equal(result["vwap"], "100.6666666666666666666666667")
        self.assertFalse(result["insufficient_depth"])

    def test_target_notional_bid_calculation(self) -> None:
        result = calculate_vwap_for_notional([["100", "1"], ["98", "2"]], "149", side="bid")

        self.assert_decimal_equal(result["filled_notional"], "149")
        self.assert_decimal_equal(result["filled_size"], "1.5")
        self.assert_decimal_equal(result["vwap"], "99.33333333333333333333333333")
        self.assertFalse(result["insufficient_depth"])

    def test_empty_levels_returns_warning_no_exception(self) -> None:
        result = calculate_vwap_for_size([], "1", side="ask")

        self.assertIsNone(result["vwap"])
        self.assertTrue(result["insufficient_depth"])
        self.assertIn("empty_or_no_valid_levels", result["warnings"])

    def test_invalid_price_quantity_returns_warning_no_exception(self) -> None:
        result = calculate_vwap_for_size([["not-price", "1"], ["101", "bad"]], "1", side="ask")

        self.assertIsNone(result["vwap"])
        self.assertTrue(result["insufficient_depth"])
        self.assertIn("invalid_price_at_level:0", result["warnings"])
        self.assertIn("invalid_quantity_at_level:1", result["warnings"])

    def test_zero_negative_price_quantity_returns_warning_no_exception(self) -> None:
        result = calculate_vwap_for_size([["0", "1"], ["101", "-2"]], "1", side="ask")

        self.assertIsNone(result["vwap"])
        self.assertTrue(result["insufficient_depth"])
        self.assertIn("non_positive_price_at_level:0", result["warnings"])
        self.assertIn("non_positive_quantity_at_level:1", result["warnings"])

    def test_dict_input_shape_works(self) -> None:
        result = calculate_vwap_for_size(
            [{"price": "100", "quantity": "1"}, {"price": "101", "quantity": "1"}],
            "2",
            side="ask",
        )

        self.assert_decimal_equal(result["vwap"], "100.5")
        self.assertEqual(result["levels_available"], 2)

    def test_string_decimal_input_works(self) -> None:
        result = calculate_vwap_for_size([["100.10", "0.5"], ["100.30", "0.5"]], "1.0", side="ask")

        self.assert_decimal_equal(result["vwap"], "100.20")
        self.assertEqual(result["warnings"], [])

    def test_unsupported_side_returns_warning_no_exception(self) -> None:
        result = calculate_vwap_for_size([["100", "1"]], "1", side="middle")

        self.assertIsNone(result["vwap"])
        self.assertTrue(result["insufficient_depth"])
        self.assertIn("unsupported_side:'middle'", result["warnings"])

    def test_slippage_pct_ask_is_non_negative(self) -> None:
        result = calculate_vwap_for_size([["100", "1"], ["102", "1"]], "2", side="ask")

        self.assertGreaterEqual(result["slippage_pct"], Decimal("0"))
        self.assert_decimal_equal(result["slippage_pct"], "1.00")

    def test_slippage_pct_bid_is_non_negative(self) -> None:
        result = calculate_vwap_for_size([["100", "1"], ["98", "1"]], "2", side="bid")

        self.assertGreaterEqual(result["slippage_pct"], Decimal("0"))
        self.assert_decimal_equal(result["slippage_pct"], "1.00")

    def test_no_file_network_private_credential_execution_imports_or_behavior(self) -> None:
        source_path = Path("src/market_data/depth_vwap.py")
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])

        forbidden_imports = {
            "requests",
            "aiohttp",
            "httpx",
            "os",
            "pathlib",
            "subprocess",
            "socket",
            "urllib",
            "pydantic",
        }
        self.assertTrue(forbidden_imports.isdisjoint(imported_roots))
        self.assertNotIn("open(", source)
        self.assertNotIn("getenv", source)
        self.assertNotIn("environ", source)
        result = calculate_vwap_for_size([["100", "1"]], "1", side="ask")
        forbidden_output_keys = {"order", "cancel", "withdraw", "deposit", "transfer", "credential", "api_key"}
        self.assertTrue(forbidden_output_keys.isdisjoint(result.keys()))

    def test_generated_json_path_not_created_or_referenced(self) -> None:
        source = Path("src/market_data/depth_vwap.py").read_text(encoding="utf-8")
        self.assertNotIn("data/generated_packets", source)
        self.assertNotIn("data/market_samples", source)
        self.assertFalse(Path("data/generated_packets/depth_vwap.json").exists())
        self.assertFalse(Path("data/market_samples/depth_vwap.json").exists())

    def test_top_of_book_example_vwap_101_2(self) -> None:
        result = calculate_vwap_for_size([["100", "1"], ["101", "2"], ["102", "2"]], "5", side="ask")

        self.assert_decimal_equal(result["vwap"], "101.2")
        self.assert_decimal_equal(result["filled_size"], "5")
        self.assert_decimal_equal(result["filled_notional"], "506")

    def test_summarize_depth_vwap_size_path_and_warning_for_ignored_notional(self) -> None:
        result = summarize_depth_vwap([[100, 1], [101, 1]], target_size=1, target_notional=100, side="ask")

        self.assert_decimal_equal(result["vwap"], "100")
        self.assertIn("target_notional_ignored_when_target_size_is_provided", result["warnings"])

    def test_summarize_depth_vwap_missing_target_warning(self) -> None:
        result = summarize_depth_vwap([[100, 1]], side="ask")

        self.assertIsNone(result["vwap"])
        self.assertTrue(result["insufficient_depth"])
        self.assertIn("missing_target_size_or_target_notional", result["warnings"])


if __name__ == "__main__":
    unittest.main()
