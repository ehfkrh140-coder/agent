from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path
from typing import Any

from src.market_data import funding_rate_wrappers
from src.market_data.funding_rate_wrappers import (
    parse_binance_usdm_funding_info,
    parse_binance_usdm_funding_rate_history,
    parse_bybit_v5_funding_history,
    parse_bybit_v5_instruments_info,
    parse_okx_current_funding_rate,
    parse_okx_funding_rate_history,
)

FIXTURE_DIR = Path("tests/fixtures/market_data/funding_rate")
WRAPPER_SOURCE_PATH = Path("src/market_data/funding_rate_wrappers.py")

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
    "WATCH",
    "ENTER",
    "recommended_default_decision",
}

FORBIDDEN_IMPORTS = {
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


def load_fixture(name: str) -> Any:
    with (FIXTURE_DIR / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def assert_no_forbidden_output_keys(testcase: unittest.TestCase, result: dict[str, Any]) -> None:
    testcase.assertTrue(FORBIDDEN_OUTPUT_KEYS.isdisjoint(result.keys()))
    parser_result = result.get("parser_result", {})
    if isinstance(parser_result, dict):
        testcase.assertTrue(FORBIDDEN_OUTPUT_KEYS.isdisjoint(parser_result.keys()))
        for observation in parser_result.get("observations", []):
            testcase.assertTrue(FORBIDDEN_OUTPUT_KEYS.isdisjoint(observation.keys()))


class FundingRateWrapperTests(unittest.TestCase):
    def assert_common_envelope(self, result: dict[str, Any], *, input_record_count: int) -> None:
        self.assertTrue(result["context_only"])
        self.assertEqual(result["readiness_effect"], "unchanged")
        self.assertIn("parser_result", result)
        self.assertEqual(result["parsed_record_count"], result["parser_result"]["records_parsed"])
        self.assertEqual(result["input_record_count"], input_record_count)
        assert_no_forbidden_output_keys(self, result)

    def test_binance_history_wrapper_calls_pure_helper_with_correct_source(self) -> None:
        result = parse_binance_usdm_funding_rate_history(
            load_fixture("binance_usdm_funding_rate_history_normal.json")
        )

        self.assertEqual(result["wrapper_status"], "OK")
        self.assertEqual(result["venue"], "binance_usdm")
        self.assertEqual(result["source_endpoint"], "binance_usdm_funding_rate_history")
        self.assertEqual(result["source_semantics"], "historical_funding_charge_record")
        self.assertEqual(result["parser_result"]["source_endpoint"], "binance_usdm_funding_rate_history")
        self.assert_common_envelope(result, input_record_count=2)

    def test_binance_funding_info_wrapper_returns_interval_cap_floor_context(self) -> None:
        result = parse_binance_usdm_funding_info(
            load_fixture("binance_usdm_funding_info_interval_cap_floor.json")
        )

        self.assertEqual(result["wrapper_status"], "OK")
        self.assertEqual(result["source_endpoint"], "binance_usdm_funding_info")
        self.assertEqual(result["source_semantics"], "interval_cap_floor_context")
        self.assert_common_envelope(result, input_record_count=2)

    def test_bybit_funding_history_wrapper_returns_settled_historical_context(self) -> None:
        result = parse_bybit_v5_funding_history(
            load_fixture("bybit_linear_funding_history_normal.json")
        )

        self.assertEqual(result["wrapper_status"], "OK")
        self.assertEqual(result["source_endpoint"], "bybit_v5_funding_history")
        self.assertEqual(result["source_semantics"], "settled_historical_funding_context")
        self.assert_common_envelope(result, input_record_count=2)

    def test_bybit_instruments_info_wrapper_returns_instrument_interval_context(self) -> None:
        result = parse_bybit_v5_instruments_info(
            load_fixture("bybit_linear_instruments_info_funding_interval.json")
        )

        self.assertEqual(result["wrapper_status"], "OK")
        self.assertEqual(result["source_endpoint"], "bybit_v5_instruments_info")
        self.assertEqual(result["source_semantics"], "instrument_interval_cap_floor_context")
        self.assert_common_envelope(result, input_record_count=2)

    def test_okx_history_wrapper_returns_historical_funding_context(self) -> None:
        result = parse_okx_funding_rate_history(
            load_fixture("okx_funding_rate_history_normal.json")
        )

        self.assertEqual(result["wrapper_status"], "OK")
        self.assertEqual(result["source_endpoint"], "okx_funding_rate_history")
        self.assertEqual(result["source_semantics"], "historical_funding_context")
        self.assert_common_envelope(result, input_record_count=2)

    def test_okx_current_wrapper_returns_current_predicted_context(self) -> None:
        result = parse_okx_current_funding_rate(
            load_fixture("okx_current_funding_rate_normal.json")
        )

        self.assertEqual(result["wrapper_status"], "OK")
        self.assertEqual(result["source_endpoint"], "okx_current_funding_rate")
        self.assertEqual(result["source_semantics"], "current_predicted_funding_context")
        self.assert_common_envelope(result, input_record_count=2)

    def test_provenance_is_shallow_copied_and_not_mutated(self) -> None:
        provenance = {"adapter": "fixture", "request_symbol": "BTCUSDT"}
        result = parse_binance_usdm_funding_rate_history(
            load_fixture("binance_usdm_funding_rate_history_normal.json"),
            provenance=provenance,
        )

        self.assertEqual(result["provenance"], provenance)
        self.assertIsNot(result["provenance"], provenance)
        result["provenance"]["adapter"] = "changed"
        self.assertEqual(provenance["adapter"], "fixture")
        self.assertNotIn("adapter", result["parser_result"])

    def test_bybit_matching_category_hint_produces_no_mismatch_warning(self) -> None:
        result = parse_bybit_v5_funding_history(
            load_fixture("bybit_linear_funding_history_normal.json"),
            category_hint="linear",
        )

        self.assertEqual(result["wrapper_status"], "OK")
        self.assertNotIn("category_hint_mismatch", result["wrapper_warnings"])
        assert_no_forbidden_output_keys(self, result)

    def test_bybit_mismatching_category_hint_produces_diagnostic_warning_only(self) -> None:
        result = parse_bybit_v5_funding_history(
            load_fixture("bybit_inverse_funding_history_normal.json"),
            category_hint="linear",
        )

        self.assertEqual(result["wrapper_status"], "OK_WITH_WARNINGS")
        self.assertIn("category_hint_mismatch", result["wrapper_warnings"])
        self.assertEqual(result["parser_result"]["parser_status"], "OK")
        assert_no_forbidden_output_keys(self, result)

    def test_empty_binance_list_produces_empty_payload_warning(self) -> None:
        result = parse_binance_usdm_funding_rate_history([])

        self.assertEqual(result["wrapper_status"], "WRAPPER_INPUT_EMPTY")
        self.assertIn("empty_payload", result["wrapper_warnings"])
        self.assertEqual(result["input_record_count"], 0)
        self.assertEqual(result["readiness_effect"], "unchanged")
        assert_no_forbidden_output_keys(self, result)

    def test_empty_bybit_result_list_produces_empty_payload_warning(self) -> None:
        payload = {"retCode": 0, "retMsg": "OK", "result": {"category": "linear", "list": []}, "time": 1}
        result = parse_bybit_v5_funding_history(payload)

        self.assertEqual(result["wrapper_status"], "WRAPPER_INPUT_EMPTY")
        self.assertIn("empty_payload", result["wrapper_warnings"])
        self.assertEqual(result["input_record_count"], 0)
        self.assertEqual(result["readiness_effect"], "unchanged")
        assert_no_forbidden_output_keys(self, result)

    def test_empty_okx_data_produces_empty_payload_warning(self) -> None:
        result = parse_okx_funding_rate_history({"code": "0", "msg": "", "data": []})

        self.assertEqual(result["wrapper_status"], "WRAPPER_INPUT_EMPTY")
        self.assertIn("empty_payload", result["wrapper_warnings"])
        self.assertEqual(result["input_record_count"], 0)
        self.assertEqual(result["readiness_effect"], "unchanged")
        assert_no_forbidden_output_keys(self, result)

    def test_invalid_wrapper_input_returns_wrapper_invalid_input(self) -> None:
        result = parse_okx_funding_rate_history({"unexpected": []})

        self.assertEqual(result["wrapper_status"], "WRAPPER_INVALID_INPUT")
        self.assertIsNone(result["input_record_count"])
        self.assertEqual(result["readiness_effect"], "unchanged")
        assert_no_forbidden_output_keys(self, result)

    def test_wrapper_source_does_not_import_network_private_or_io_modules(self) -> None:
        tree = ast.parse(WRAPPER_SOURCE_PATH.read_text(encoding="utf-8"))
        imported_roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_roots.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])

        self.assertTrue(FORBIDDEN_IMPORTS.isdisjoint(imported_roots))

    def test_wrapper_output_keys_exclude_execution_alert_order_fields(self) -> None:
        result = parse_okx_current_funding_rate(
            load_fixture("okx_current_funding_rate_normal.json")
        )

        assert_no_forbidden_output_keys(self, result)

    def test_generated_artifacts_are_not_created_or_referenced(self) -> None:
        self.assertFalse(Path("data/generated_packets/funding_rate_wrappers.json").exists())
        self.assertFalse(Path("data/market_samples/funding_rate_wrappers.json").exists())
        source = WRAPPER_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("data/generated_packets", source)
        self.assertNotIn("data/market_samples", source)

    def test_status_constants_include_source_mismatch_candidate(self) -> None:
        self.assertEqual(funding_rate_wrappers.WRAPPER_SOURCE_MISMATCH, "WRAPPER_SOURCE_MISMATCH")


if __name__ == "__main__":
    unittest.main()
