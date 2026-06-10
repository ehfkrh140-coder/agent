from __future__ import annotations

import ast
import json
import unittest
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.market_data.depth_vwap import calculate_vwap_for_size

FIXTURE_DIR = Path("tests/fixtures/market_data/depth_vwap")
FIXTURE_FILES = {
    "binance_spot": FIXTURE_DIR / "binance_spot_depth_btcusdt.json",
    "binance_usdm": FIXTURE_DIR / "binance_usdm_depth_btcusdt.json",
    "bybit_spot": FIXTURE_DIR / "bybit_spot_orderbook_btcusdt.json",
    "bybit_linear": FIXTURE_DIR / "bybit_linear_orderbook_btcusdt.json",
    "okx_swap": FIXTURE_DIR / "okx_swap_books_btc_usdt_swap.json",
}
FORBIDDEN_FIELD_SUBSTRINGS = (
    "apiKey",
    "secret",
    "token",
    "account",
    "balance",
    "position",
    "orderId",
    "clientOrderId",
    "cancel",
    "withdraw",
    "deposit",
    "transfer",
    "privateKey",
    "execution_enabled",
    "auto_trade",
)


def _load_fixture(name: str) -> dict[str, Any]:
    path = FIXTURE_FILES[name]
    return json.loads(path.read_text(encoding="utf-8"))


def _walk_values(value: Any) -> list[str]:
    values: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            values.append(str(key))
            values.extend(_walk_values(child))
    elif isinstance(value, list):
        for child in value:
            values.extend(_walk_values(child))
    else:
        values.append(str(value))
    return values


def _assert_positive_decimal_pair(testcase: unittest.TestCase, level: list[Any]) -> None:
    testcase.assertIsInstance(level, list)
    testcase.assertGreaterEqual(len(level), 2)
    testcase.assertGreater(Decimal(str(level[0])), Decimal("0"))
    testcase.assertGreater(Decimal(str(level[1])), Decimal("0"))


def _binance_levels(name: str) -> tuple[list[list[Any]], list[list[Any]]]:
    data = _load_fixture(name)
    return data["asks"], data["bids"]


def _bybit_levels(name: str) -> tuple[list[list[Any]], list[list[Any]]]:
    data = _load_fixture(name)
    return data["result"]["a"], data["result"]["b"]


def _okx_levels() -> tuple[list[list[Any]], list[list[Any]]]:
    data = _load_fixture("okx_swap")
    book = data["data"][0]
    asks = [level[:2] for level in book["asks"]]
    bids = [level[:2] for level in book["bids"]]
    return asks, bids


class DepthVwapMockedFixtureTests(unittest.TestCase):
    def test_all_fixture_files_exist_parse_and_stay_under_fixture_dir(self) -> None:
        for path in FIXTURE_FILES.values():
            with self.subTest(path=path):
                self.assertTrue(path.exists())
                self.assertTrue(path.is_file())
                self.assertEqual(path.parent, FIXTURE_DIR)
                self.assertNotIn("data/generated_packets", path.as_posix())
                self.assertNotIn("data/market_samples", path.as_posix())
                parsed = json.loads(path.read_text(encoding="utf-8"))
                self.assertIsInstance(parsed, dict)

    def test_fixture_forbidden_field_scan_allows_public_orderbook_word(self) -> None:
        for name, path in FIXTURE_FILES.items():
            text = path.read_text(encoding="utf-8")
            values = _walk_values(json.loads(text))
            with self.subTest(name=name):
                self.assertIn("orderbook", text + " public orderbook allowed marker")
                for forbidden in FORBIDDEN_FIELD_SUBSTRINGS:
                    self.assertFalse(any(forbidden in value for value in values), forbidden)

    def test_binance_spot_shape_and_helper_compatibility(self) -> None:
        data = _load_fixture("binance_spot")
        self.assertEqual(data["symbol"], "BTCUSDT")
        asks, bids = data["asks"], data["bids"]
        self.assertGreaterEqual(len(asks), 5)
        self.assertGreaterEqual(len(bids), 5)
        for level in asks + bids:
            self.assertEqual(len(level), 2)
            _assert_positive_decimal_pair(self, level)
        self.assertIsNotNone(calculate_vwap_for_size(asks, "1.0", side="ask")["vwap"])
        self.assertIsNotNone(calculate_vwap_for_size(bids, "1.0", side="bid")["vwap"])

    def test_binance_usdm_shape_and_helper_compatibility(self) -> None:
        data = _load_fixture("binance_usdm")
        self.assertEqual(data["marketType"], "usdm_futures")
        self.assertIn("E", data)
        self.assertIn("T", data)
        asks, bids = data["asks"], data["bids"]
        self.assertGreaterEqual(len(asks), 5)
        self.assertGreaterEqual(len(bids), 5)
        for level in asks + bids:
            self.assertEqual(len(level), 2)
            _assert_positive_decimal_pair(self, level)
        self.assertFalse(calculate_vwap_for_size(asks, "1.0", side="ask")["insufficient_depth"])
        self.assertFalse(calculate_vwap_for_size(bids, "1.0", side="bid")["insufficient_depth"])

    def test_bybit_spot_shape_category_absent_and_helper_compatibility(self) -> None:
        data = _load_fixture("bybit_spot")
        self.assertEqual(data["retCode"], 0)
        self.assertEqual(data["retMsg"], "OK")
        result = data["result"]
        self.assertNotIn("category", result)
        self.assertGreaterEqual(len(result["a"]), 5)
        self.assertGreaterEqual(len(result["b"]), 5)
        self.assertIsNotNone(calculate_vwap_for_size(result["a"], "1.0", side="ask")["vwap"])
        self.assertIsNotNone(calculate_vwap_for_size(result["b"], "1.0", side="bid")["vwap"])

    def test_bybit_linear_shape_category_absent_cts_and_helper_compatibility(self) -> None:
        data = _load_fixture("bybit_linear")
        self.assertEqual(data["retCode"], 0)
        self.assertEqual(data["retMsg"], "OK")
        result = data["result"]
        self.assertNotIn("category", result)
        self.assertIn("cts", result)
        self.assertGreaterEqual(len(result["a"]), 5)
        self.assertGreaterEqual(len(result["b"]), 5)
        self.assertFalse(calculate_vwap_for_size(result["a"], "1.0", side="ask")["insufficient_depth"])
        self.assertFalse(calculate_vwap_for_size(result["b"], "1.0", side="bid")["insufficient_depth"])

    def test_okx_swap_shape_contract_caveat_and_first_two_helper_compatibility(self) -> None:
        data = _load_fixture("okx_swap")
        self.assertEqual(data["code"], "0")
        book = data["data"][0]
        self.assertEqual(book["instId"], "BTC-USDT-SWAP")
        self.assertEqual(book["instType"], "SWAP")
        self.assertEqual(book["ctVal"], "0.01")
        self.assertEqual(book["ctValCcy"], "BTC")
        self.assertEqual(book["lotSz"], "0.01")
        self.assertGreaterEqual(len(book["asks"]), 5)
        self.assertGreaterEqual(len(book["bids"]), 5)
        self.assertTrue(all(len(level) == 4 for level in book["asks"] + book["bids"]))
        asks, bids = _okx_levels()
        self.assertFalse(calculate_vwap_for_size(asks, "10", side="ask")["insufficient_depth"])
        self.assertFalse(calculate_vwap_for_size(bids, "10", side="bid")["insufficient_depth"])

    def test_okx_contract_conversion_is_not_claimed(self) -> None:
        data = _load_fixture("okx_swap")
        book = data["data"][0]
        asks, _bids = _okx_levels()
        result = calculate_vwap_for_size(asks, "10", side="ask")
        self.assertIsNotNone(result["vwap"])
        self.assertEqual(book["ctVal"], "0.01")
        self.assertNotIn("contract_converted", result)
        self.assertNotIn("base_size_converted", result)

    def test_cross_fixture_ask_vwap_consumes_multiple_levels_and_differs_from_top(self) -> None:
        for name, loader in {
            "binance_spot": lambda: _binance_levels("binance_spot"),
            "binance_usdm": lambda: _binance_levels("binance_usdm"),
            "bybit_spot": lambda: _bybit_levels("bybit_spot"),
            "bybit_linear": lambda: _bybit_levels("bybit_linear"),
            "okx_swap": _okx_levels,
        }.items():
            asks, _bids = loader()
            target = Decimal(str(asks[0][1])) + (Decimal(str(asks[1][1])) / Decimal("2"))
            result = calculate_vwap_for_size(asks, str(target), side="ask")
            with self.subTest(name=name):
                self.assertGreater(result["levels_consumed"], 1)
                self.assertNotEqual(result["vwap"], result["best_price"])
                self.assertGreaterEqual(result["slippage_pct"], Decimal("0"))

    def test_cross_fixture_bid_vwap_consumes_multiple_levels_and_differs_from_top(self) -> None:
        for name, loader in {
            "binance_spot": lambda: _binance_levels("binance_spot"),
            "binance_usdm": lambda: _binance_levels("binance_usdm"),
            "bybit_spot": lambda: _bybit_levels("bybit_spot"),
            "bybit_linear": lambda: _bybit_levels("bybit_linear"),
            "okx_swap": _okx_levels,
        }.items():
            _asks, bids = loader()
            target = Decimal(str(bids[0][1])) + (Decimal(str(bids[1][1])) / Decimal("2"))
            result = calculate_vwap_for_size(bids, str(target), side="bid")
            with self.subTest(name=name):
                self.assertGreater(result["levels_consumed"], 1)
                self.assertNotEqual(result["vwap"], result["best_price"])
                self.assertGreaterEqual(result["slippage_pct"], Decimal("0"))

    def test_cross_fixture_insufficient_depth_for_large_target(self) -> None:
        for name, loader in {
            "binance_spot": lambda: _binance_levels("binance_spot"),
            "binance_usdm": lambda: _binance_levels("binance_usdm"),
            "bybit_spot": lambda: _bybit_levels("bybit_spot"),
            "bybit_linear": lambda: _bybit_levels("bybit_linear"),
            "okx_swap": _okx_levels,
        }.items():
            asks, bids = loader()
            ask_available = sum(Decimal(str(level[1])) for level in asks)
            bid_available = sum(Decimal(str(level[1])) for level in bids)
            ask_result = calculate_vwap_for_size(asks, str(ask_available + Decimal("1")), side="ask")
            bid_result = calculate_vwap_for_size(bids, str(bid_available + Decimal("1")), side="bid")
            with self.subTest(name=name):
                self.assertTrue(ask_result["insufficient_depth"])
                self.assertTrue(bid_result["insufficient_depth"])
                self.assertLess(ask_result["depth_coverage_pct"], Decimal("100"))
                self.assertLess(bid_result["depth_coverage_pct"], Decimal("100"))

    def test_tests_import_only_standard_library_and_depth_vwap(self) -> None:
        source = Path(__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
        forbidden_fragments = (
            "src.market_data.adapters",
            "src.market_data.parsers",
            "src.strategy",
            "src.market_data.packet_builder",
            "src.market_data.sampling",
            "requests",
            "aiohttp",
            "httpx",
            "socket",
            "urllib",
        )
        self.assertTrue(all(not any(fragment in module for fragment in forbidden_fragments) for module in imported_modules))
        self.assertIn("src.market_data.depth_vwap", imported_modules)

    def test_no_generated_json_files_created_by_fixture_tests(self) -> None:
        self.assertFalse(Path("data/generated_packets/depth_vwap_fixture_contract.json").exists())
        self.assertFalse(Path("data/market_samples/depth_vwap_fixture_contract.json").exists())

    def test_vwap_results_do_not_assert_execution_permission(self) -> None:
        asks, _bids = _binance_levels("binance_spot")
        result = calculate_vwap_for_size(asks, "1.0", side="ask")
        forbidden_keys = {"execution", "execution_permission", "trading_signal", "order", "account", "balance"}
        self.assertTrue(forbidden_keys.isdisjoint(result.keys()))
        self.assertIsNotNone(result["vwap"])


if __name__ == "__main__":
    unittest.main()
