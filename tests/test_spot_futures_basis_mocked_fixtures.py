import json
import unittest
from pathlib import Path


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "market_data" / "spot_futures_basis"

FIXTURE_FILES = {
    "spot_book_ticker": "binance_spot_book_ticker_btcusdt.json",
    "spot_depth": "binance_spot_depth_btcusdt.json",
    "spot_exchange_info": "binance_spot_exchange_info_btcusdt.json",
    "futures_book_ticker": "binance_futures_book_ticker_btcusdt.json",
    "futures_depth": "binance_futures_depth_btcusdt.json",
    "futures_premium_index": "binance_futures_premium_index_btcusdt.json",
    "futures_exchange_info": "binance_futures_exchange_info_btcusdt.json",
}

FORBIDDEN_KEY_SUBSTRINGS = (
    "apikey",
    "secret",
    "token",
    "account",
    "balance",
    "position",
    "orderid",
    "clientorderid",
    "order",
    "cancel",
    "withdraw",
    "deposit",
    "transfer",
    "privatekey",
)


class SpotFuturesBasisMockedFixturesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = {}
        for fixture_id, filename in FIXTURE_FILES.items():
            path = FIXTURE_DIR / filename
            cls.assert_fixture_path_allowed(path)
            with path.open("r", encoding="utf-8") as handle:
                cls.fixtures[fixture_id] = json.load(handle)

    @staticmethod
    def assert_fixture_path_allowed(path):
        path_text = path.as_posix()
        assert path.exists(), f"fixture does not exist: {path_text}"
        assert "tests/fixtures/market_data/spot_futures_basis" in path_text
        assert "data/market_samples" not in path_text
        assert "data/generated_packets" not in path_text

    def test_all_fixture_files_exist_and_parse_as_json(self):
        self.assertEqual(set(FIXTURE_FILES), set(self.fixtures))
        for fixture_id, payload in self.fixtures.items():
            self.assertIsInstance(payload, dict, fixture_id)

    def test_required_top_level_fields_exist(self):
        expected_fields = {
            "spot_book_ticker": {"symbol", "bidPrice", "bidQty", "askPrice", "askQty"},
            "spot_depth": {"lastUpdateId", "bids", "asks"},
            "spot_exchange_info": {"symbols"},
            "futures_book_ticker": {"symbol", "bidPrice", "bidQty", "askPrice", "askQty", "time"},
            "futures_depth": {"lastUpdateId", "E", "T", "bids", "asks"},
            "futures_premium_index": {
                "symbol",
                "markPrice",
                "indexPrice",
                "lastFundingRate",
                "interestRate",
                "nextFundingTime",
                "time",
            },
            "futures_exchange_info": {"symbols"},
        }
        for fixture_id, fields in expected_fields.items():
            self.assertTrue(fields.issubset(self.fixtures[fixture_id]), fixture_id)

    def test_symbols_are_btcusdt(self):
        symbol_fixture_ids = (
            "spot_book_ticker",
            "futures_book_ticker",
            "futures_premium_index",
        )
        for fixture_id in symbol_fixture_ids:
            self.assertEqual("BTCUSDT", self.fixtures[fixture_id]["symbol"])

        for fixture_id in ("spot_exchange_info", "futures_exchange_info"):
            symbols = self.fixtures[fixture_id]["symbols"]
            self.assertIsInstance(symbols, list)
            self.assertGreaterEqual(len(symbols), 1)
            btcusdt = symbols[0]
            self.assertEqual("BTCUSDT", btcusdt["symbol"])
            self.assertEqual("TRADING", btcusdt["status"])
            self.assertEqual("BTC", btcusdt["baseAsset"])
            self.assertEqual("USDT", btcusdt["quoteAsset"])

    def test_book_and_depth_fixtures_have_at_least_two_levels(self):
        for fixture_id in ("spot_depth", "futures_depth"):
            payload = self.fixtures[fixture_id]
            for side in ("bids", "asks"):
                self.assertIsInstance(payload[side], list)
                self.assertGreaterEqual(len(payload[side]), 2)
                for level in payload[side]:
                    self.assertIsInstance(level, list)
                    self.assertEqual(2, len(level))
                    self.assertIsInstance(level[0], str)
                    self.assertIsInstance(level[1], str)

    def test_exchange_info_contains_symbols_array_and_filters(self):
        for fixture_id in ("spot_exchange_info", "futures_exchange_info"):
            symbols = self.fixtures[fixture_id]["symbols"]
            self.assertIsInstance(symbols, list)
            self.assertGreaterEqual(len(symbols), 1)
            filters = symbols[0]["filters"]
            self.assertIsInstance(filters, list)
            self.assertGreaterEqual(len(filters), 3)
            filter_types = {item["filterType"] for item in filters}
            self.assertIn("PRICE_FILTER", filter_types)
            self.assertIn("LOT_SIZE", filter_types)
            self.assertIn("MIN_NOTIONAL", filter_types)

        futures_symbol = self.fixtures["futures_exchange_info"]["symbols"][0]
        self.assertEqual("USDT", futures_symbol["marginAsset"])
        self.assertEqual("PERPETUAL", futures_symbol["contractType"])

    def test_futures_premium_index_context_fields_exist(self):
        premium_index = self.fixtures["futures_premium_index"]
        for field in ("markPrice", "indexPrice", "lastFundingRate", "nextFundingTime"):
            self.assertIn(field, premium_index)

    def test_no_forbidden_private_account_or_execution_keys(self):
        for fixture_id, payload in self.fixtures.items():
            with self.subTest(fixture_id=fixture_id):
                self._assert_no_forbidden_keys(payload)

    def test_fixture_paths_are_not_generated_artifact_paths(self):
        for filename in FIXTURE_FILES.values():
            path = FIXTURE_DIR / filename
            path_text = path.as_posix()
            self.assertIn("tests/fixtures/market_data/spot_futures_basis", path_text)
            self.assertNotIn("data/market_samples", path_text)
            self.assertNotIn("data/generated_packets", path_text)

    def _assert_no_forbidden_keys(self, value):
        if isinstance(value, dict):
            for key, nested in value.items():
                normalized_key = key.lower()
                for forbidden in FORBIDDEN_KEY_SUBSTRINGS:
                    self.assertNotIn(forbidden, normalized_key, key)
                self._assert_no_forbidden_keys(nested)
        elif isinstance(value, list):
            for item in value:
                self._assert_no_forbidden_keys(item)


if __name__ == "__main__":
    unittest.main()
