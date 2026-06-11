from __future__ import annotations

import ast
import json
import unittest
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.market_data.funding_rate_parser import parse_funding_rate_payload

FIXTURE_DIR = Path("tests/fixtures/market_data/funding_rate")
FORBIDDEN_OUTPUT_KEYS = {
    "order",
    "cancel",
    "withdraw",
    "deposit",
    "transfer",
    "credential",
    "api_key",
    "secret",
    "alert",
    "execution",
}


def load_fixture(name: str) -> Any:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def assert_no_forbidden_output_keys(testcase: unittest.TestCase, result: dict[str, Any]) -> None:
    testcase.assertTrue(FORBIDDEN_OUTPUT_KEYS.isdisjoint(result.keys()))
    for observation in result.get("observations", []):
        testcase.assertTrue(FORBIDDEN_OUTPUT_KEYS.isdisjoint(observation.keys()))


class FundingRateParserTest(unittest.TestCase):
    def assert_decimal_equal(self, actual: Any, expected: str) -> None:
        self.assertIsInstance(actual, Decimal)
        self.assertEqual(actual, Decimal(expected))

    def assert_common_normal_result(self, result: dict[str, Any], semantics: str) -> None:
        self.assertEqual(result["parser_status"], "OK")
        self.assertEqual(result["source_semantics"], semantics)
        self.assertEqual(result["records_seen"], 2)
        self.assertEqual(result["records_parsed"], 2)
        self.assertEqual(len(result["observations"]), 2)
        self.assertIsInstance(result["observations"][0]["funding_rate"], Decimal)
        self.assertIsInstance(result["observations"][0]["funding_rate_timestamp_ms"], int)
        assert_no_forbidden_output_keys(self, result)

    def test_binance_history_normal_fixture_parses_ok(self) -> None:
        result = parse_funding_rate_payload(
            load_fixture("binance_usdm_funding_rate_history_normal.json"),
            venue="binance_usdm",
            source_endpoint="binance_usdm_funding_rate_history",
        )

        self.assert_common_normal_result(result, "historical_funding_charge_record")
        first = result["observations"][0]
        self.assertEqual(first["instrument_id"], "BTCUSDT")
        self.assertEqual(first["instrument_type"], "usdm_perpetual")
        self.assert_decimal_equal(first["funding_rate"], "0.00010000")
        self.assertEqual(first["funding_rate_timestamp_ms"], 1717200000000)
        self.assert_decimal_equal(first["mark_price_reference"], "68000.12500000")

    def test_bybit_linear_history_normal_fixture_parses_ok(self) -> None:
        result = parse_funding_rate_payload(
            load_fixture("bybit_linear_funding_history_normal.json"),
            venue="bybit",
            source_endpoint="bybit_v5_funding_history",
        )

        self.assert_common_normal_result(result, "settled_historical_funding_context")
        self.assertEqual(result["observations"][0]["instrument_type"], "linear")
        self.assert_decimal_equal(result["observations"][0]["funding_rate"], "0.00010000")

    def test_okx_history_normal_fixture_parses_ok(self) -> None:
        result = parse_funding_rate_payload(
            load_fixture("okx_funding_rate_history_normal.json"),
            venue="okx",
            source_endpoint="okx_funding_rate_history",
        )

        self.assert_common_normal_result(result, "historical_funding_context")
        first = result["observations"][0]
        self.assertEqual(first["instrument_id"], "BTC-USDT-SWAP")
        self.assert_decimal_equal(first["funding_rate"], "0.00010000")
        self.assert_decimal_equal(first["realized_funding_rate"], "0.00009500")

    def test_binance_funding_info_parses_interval_cap_floor_context(self) -> None:
        result = parse_funding_rate_payload(
            load_fixture("binance_usdm_funding_info_interval_cap_floor.json"),
            venue="binance_usdm",
            source_endpoint="binance_usdm_funding_info",
        )

        self.assertEqual(result["parser_status"], "OK")
        first = result["observations"][0]
        self.assertEqual(first["source_semantics"], "interval_cap_floor_context")
        self.assertIsNone(first["funding_rate"])
        self.assert_decimal_equal(first["funding_cap"], "0.00300000")
        self.assert_decimal_equal(first["funding_floor"], "-0.00300000")
        self.assert_decimal_equal(first["funding_interval_hours"], "8")

    def test_bybit_instruments_info_parses_minutes_to_hours(self) -> None:
        result = parse_funding_rate_payload(
            load_fixture("bybit_linear_instruments_info_funding_interval.json"),
            venue="bybit",
            source_endpoint="bybit_v5_instruments_info",
        )

        self.assertEqual(result["parser_status"], "OK")
        first = result["observations"][0]
        second = result["observations"][1]
        self.assertEqual(first["instrument_type"], "linear")
        self.assert_decimal_equal(first["funding_interval_hours"], "8")
        self.assert_decimal_equal(second["funding_interval_hours"], "4")
        self.assert_decimal_equal(first["funding_cap"], "0.00300000")
        self.assert_decimal_equal(first["funding_floor"], "-0.00300000")

    def test_bybit_inverse_history_preserves_inverse_category(self) -> None:
        result = parse_funding_rate_payload(
            load_fixture("bybit_inverse_funding_history_normal.json"),
            venue="bybit",
            source_endpoint="bybit_v5_funding_history",
        )

        self.assertEqual(result["parser_status"], "OK")
        self.assertEqual(result["observations"][0]["instrument_type"], "inverse")
        self.assertEqual(result["observations"][0]["instrument_id"], "BTCUSD")

    def test_okx_current_funding_keeps_current_predicted_settled_fields_distinct(self) -> None:
        result = parse_funding_rate_payload(
            load_fixture("okx_current_funding_rate_normal.json"),
            venue="okx",
            source_endpoint="okx_current_funding_rate",
        )

        self.assertEqual(result["parser_status"], "OK")
        first = result["observations"][0]
        self.assertEqual(first["source_semantics"], "current_predicted_funding_context")
        self.assert_decimal_equal(first["funding_rate"], "0.00009000")
        self.assert_decimal_equal(first["predicted_funding_rate"], "0.00007000")
        self.assert_decimal_equal(first["realized_funding_rate"], "0.00008000")
        self.assertEqual(first["next_funding_time_ms"], 1717228800000)
        self.assert_decimal_equal(first["premium_index_reference"], "0.00001200")

    def test_missing_required_funding_rate_reports_need_source_fields(self) -> None:
        result = parse_funding_rate_payload(
            load_fixture("missing_required_funding_rate.json"),
            venue="binance_usdm",
            source_endpoint="binance_usdm_funding_rate_history",
        )

        self.assertEqual(result["parser_status"], "NEED_SOURCE_FIELDS")
        self.assertIn("funding_rate", result["required_missing_fields"])
        self.assertEqual(result["records_parsed"], 0)

    def test_missing_optional_interval_stays_ok_with_optional_missing_field(self) -> None:
        result = parse_funding_rate_payload(
            load_fixture("missing_optional_interval.json"),
            venue="binance_usdm",
            source_endpoint="binance_usdm_funding_info",
        )

        self.assertEqual(result["parser_status"], "OK_WITH_WARNINGS")
        self.assertIn("funding_interval_hours", result["optional_missing_fields"])
        self.assertIn("optional_interval_missing", result["warnings"])
        self.assertEqual(result["records_parsed"], 1)

    def test_string_numeric_parsing_uses_decimal_values(self) -> None:
        result = parse_funding_rate_payload(
            load_fixture("string_numeric_parsing.json"),
            venue="binance_usdm",
            source_endpoint="string_numeric_parsing",
        )

        self.assertEqual(result["parser_status"], "OK_WITH_WARNINGS")
        self.assertIsInstance(result["observations"][0]["funding_rate"], Decimal)
        self.assertIsInstance(result["observations"][1]["funding_rate"], Decimal)
        self.assertIn("numeric_parse_success_is_not_signal", result["warnings"])

    def test_positive_funding_has_no_short_permission_output(self) -> None:
        result = parse_funding_rate_payload(
            load_fixture("positive_funding_rate.json"),
            venue="binance_usdm",
            source_endpoint="binance_usdm_funding_rate_history",
        )

        self.assertEqual(result["parser_status"], "OK")
        assert_no_forbidden_output_keys(self, result)
        self.assertNotIn("short_permission", result)

    def test_negative_funding_has_no_long_permission_output(self) -> None:
        result = parse_funding_rate_payload(
            load_fixture("negative_funding_rate.json"),
            venue="binance_usdm",
            source_endpoint="binance_usdm_funding_rate_history",
        )

        self.assertEqual(result["parser_status"], "OK")
        assert_no_forbidden_output_keys(self, result)
        self.assertNotIn("long_permission", result)

    def test_zero_funding_has_no_trade_conclusion_output(self) -> None:
        result = parse_funding_rate_payload(
            load_fixture("zero_funding_rate.json"),
            venue="bybit",
            source_endpoint="bybit_v5_funding_history",
        )

        self.assertEqual(result["parser_status"], "OK")
        self.assert_decimal_equal(result["observations"][0]["funding_rate"], "0.00000000")
        self.assertNotIn("trade_conclusion", result)

    def test_high_absolute_funding_context_returns_warning_not_enter(self) -> None:
        result = parse_funding_rate_payload(
            load_fixture("high_absolute_funding_context.json"),
            venue="okx",
            source_endpoint="high_abs_funding_context",
        )

        self.assertEqual(result["parser_status"], "OK_WITH_WARNINGS")
        self.assertIn("high_abs_funding_context", result["warnings"])
        self.assertNotIn("enter", result)
        self.assertNotIn("ENTER", result["warnings"])

    def test_timestamp_watch_context_returns_warning_without_skew_calculation(self) -> None:
        result = parse_funding_rate_payload(
            load_fixture("timestamp_data_age_clock_skew_watch.json"),
            venue="bybit",
            source_endpoint="timestamp_watch_context",
        )

        self.assertEqual(result["parser_status"], "OK_WITH_WARNINGS")
        self.assertIn("timestamp_watch_context", result["warnings"])
        for observation in result["observations"]:
            self.assertNotIn("clock_skew_warning", observation)
            self.assertNotIn("data_age_ms", observation)

    def test_varying_interval_does_not_hard_code_eight_hours(self) -> None:
        result = parse_funding_rate_payload(
            load_fixture("varying_funding_interval.json"),
            venue="binance_usdm",
            source_endpoint="varying_funding_interval",
        )

        self.assertEqual(result["parser_status"], "OK_WITH_WARNINGS")
        intervals = {observation["funding_interval_hours"] for observation in result["observations"]}
        self.assertIn(Decimal("8"), intervals)
        self.assertIn(Decimal("4"), intervals)
        self.assertIn("do_not_hard_code_8h_interval", result["warnings"])

    def test_okx_predicted_vs_realized_fields_remain_separate(self) -> None:
        result = parse_funding_rate_payload(
            load_fixture("okx_predicted_vs_realized_semantics.json"),
            venue="okx",
            source_endpoint="okx_predicted_vs_realized_semantics",
        )

        self.assertEqual(result["parser_status"], "OK_WITH_WARNINGS")
        self.assertIn("do_not_collapse_predicted_and_realized", result["warnings"])
        first = result["observations"][0]
        self.assert_decimal_equal(first["funding_rate"], "0.00009000")
        self.assert_decimal_equal(first["predicted_funding_rate"], "0.00007000")
        self.assert_decimal_equal(first["realized_funding_rate"], "0.00008000")

    def test_unsupported_venue_returns_status(self) -> None:
        result = parse_funding_rate_payload([], venue="kraken", source_endpoint="binance_usdm_funding_rate_history")

        self.assertEqual(result["parser_status"], "UNSUPPORTED_VENUE")
        self.assertEqual(result["records_seen"], 0)

    def test_unsupported_source_returns_status(self) -> None:
        result = parse_funding_rate_payload([], venue="binance_usdm", source_endpoint="unknown_source")

        self.assertEqual(result["parser_status"], "UNSUPPORTED_SOURCE")
        self.assertEqual(result["records_seen"], 0)

    def test_invalid_source_shape_returns_status(self) -> None:
        result = parse_funding_rate_payload({}, venue="binance_usdm", source_endpoint="binance_usdm_funding_rate_history")

        self.assertEqual(result["parser_status"], "INVALID_SOURCE_SHAPE")
        self.assertIn("expected_top_level_list", result["warnings"])

    def test_invalid_required_numeric_field_returns_status(self) -> None:
        result = parse_funding_rate_payload(
            [{"symbol": "BTCUSDT", "fundingRate": "not-a-number", "fundingTime": 1717200000000}],
            venue="binance_usdm",
            source_endpoint="binance_usdm_funding_rate_history",
        )

        self.assertEqual(result["parser_status"], "INVALID_NUMERIC_FIELD")
        self.assertIn("invalid_numeric_field:funding_rate", result["warnings"])

    def test_invalid_required_timestamp_field_returns_status(self) -> None:
        result = parse_funding_rate_payload(
            [{"symbol": "BTCUSDT", "fundingRate": "0.0001", "fundingTime": "not-a-timestamp"}],
            venue="binance_usdm",
            source_endpoint="binance_usdm_funding_rate_history",
        )

        self.assertEqual(result["parser_status"], "INVALID_TIMESTAMP_FIELD")
        self.assertIn("invalid_timestamp_field:funding_rate_timestamp_ms", result["warnings"])

    def test_no_file_network_private_credential_execution_imports_or_output_keys(self) -> None:
        source_path = Path("src/market_data/funding_rate_parser.py")
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
        result = parse_funding_rate_payload(
            load_fixture("binance_usdm_funding_rate_history_normal.json"),
            venue="binance_usdm",
            source_endpoint="binance_usdm_funding_rate_history",
        )
        assert_no_forbidden_output_keys(self, result)

    def test_generated_json_path_not_created_or_referenced(self) -> None:
        source = Path("src/market_data/funding_rate_parser.py").read_text(encoding="utf-8")
        self.assertNotIn("data/generated_packets", source)
        self.assertNotIn("data/market_samples", source)
        self.assertFalse(Path("data/generated_packets/funding_rate_parser.json").exists())
        self.assertFalse(Path("data/market_samples/funding_rate_parser.json").exists())


if __name__ == "__main__":
    unittest.main()
