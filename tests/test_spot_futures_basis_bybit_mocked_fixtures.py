import json
import unittest
from pathlib import Path


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "market_data" / "spot_futures_basis"

FIXTURE_FILES = {
    "spot_ticker": "bybit_spot_ticker_btcusdt.json",
    "spot_orderbook": "bybit_spot_orderbook_btcusdt.json",
    "spot_instruments_info": "bybit_spot_instruments_info_btcusdt.json",
    "linear_ticker": "bybit_linear_ticker_btcusdt.json",
    "linear_orderbook": "bybit_linear_orderbook_btcusdt.json",
    "linear_instruments_info": "bybit_linear_instruments_info_btcusdt.json",
}

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

FORBIDDEN_LIVE_CAPTURE_METADATA = (
    "generated_at",
    "captured_at",
    "live_endpoint_url",
)

GENERATED_ARTIFACT_PATHS = (
    "data/market_samples",
    "data/generated_packets",
)


class SpotFuturesBasisBybitMockedFixturesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_paths = {
            fixture_id: FIXTURE_DIR / filename
            for fixture_id, filename in FIXTURE_FILES.items()
        }
        cls.fixtures = {}
        for fixture_id, path in cls.fixture_paths.items():
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

    def test_all_fixtures_have_bybit_v5_envelope(self):
        expected_fields = {"retCode", "retMsg", "result", "retExtInfo", "time"}
        for fixture_id, payload in self.fixtures.items():
            with self.subTest(fixture_id=fixture_id):
                self.assertTrue(expected_fields.issubset(payload), fixture_id)
                self.assertEqual(0, payload["retCode"])
                self.assertEqual("OK", payload["retMsg"])
                self.assertIsInstance(payload["result"], dict)
                self.assertIsInstance(payload["retExtInfo"], dict)
                self.assertIsInstance(payload["time"], int)

    def test_fixture_paths_are_contract_fixture_paths_not_generated_paths(self):
        for fixture_id, path in self.fixture_paths.items():
            with self.subTest(fixture_id=fixture_id):
                path_text = path.as_posix()
                self.assertIn("tests/fixtures/market_data/spot_futures_basis", path_text)
                for forbidden_path in GENERATED_ARTIFACT_PATHS:
                    self.assertNotIn(forbidden_path, path_text)

    def test_no_forbidden_private_account_execution_keys_or_values(self):
        for fixture_id, payload in self.fixtures.items():
            with self.subTest(fixture_id=fixture_id):
                self._assert_no_forbidden_private_account_or_execution_content(payload)

    def test_no_live_capture_metadata_or_generated_artifact_paths_in_contents(self):
        for fixture_id, payload in self.fixtures.items():
            with self.subTest(fixture_id=fixture_id):
                self._assert_no_forbidden_metadata_or_generated_paths(payload)

    def test_spot_fixtures_preserve_spot_category_and_symbol(self):
        for fixture_id in ("spot_ticker", "spot_instruments_info"):
            payload = self.fixtures[fixture_id]
            self.assertEqual("spot", payload["result"]["category"], fixture_id)
            self.assertEqual("BTCUSDT", payload["result"]["list"][0]["symbol"], fixture_id)

        orderbook = self.fixtures["spot_orderbook"]["result"]
        self.assertEqual("spot", orderbook["category"])
        self.assertEqual("BTCUSDT", orderbook["s"])

    def test_linear_fixtures_preserve_linear_category_and_symbol(self):
        for fixture_id in ("linear_ticker", "linear_instruments_info"):
            payload = self.fixtures[fixture_id]
            self.assertEqual("linear", payload["result"]["category"], fixture_id)
            self.assertEqual("BTCUSDT", payload["result"]["list"][0]["symbol"], fixture_id)

        orderbook = self.fixtures["linear_orderbook"]["result"]
        self.assertEqual("linear", orderbook["category"])
        self.assertEqual("BTCUSDT", orderbook["s"])

    def test_spot_and_linear_product_semantics_are_separated(self):
        spot_instrument = self.fixtures["spot_instruments_info"]["result"]["list"][0]
        linear_instrument = self.fixtures["linear_instruments_info"]["result"]["list"][0]

        self.assertEqual("BTCUSDT", spot_instrument["symbol"])
        self.assertEqual("BTCUSDT", linear_instrument["symbol"])
        self.assertNotIn("contractType", spot_instrument)
        self.assertEqual("LinearPerpetual", linear_instrument["contractType"])
        self.assertEqual("USDT", linear_instrument["settleCoin"])
        self.assertEqual("spot", self.fixtures["spot_ticker"]["result"]["category"])
        self.assertEqual("linear", self.fixtures["linear_ticker"]["result"]["category"])

    def test_orderbook_fixtures_have_at_least_two_bid_and_ask_levels(self):
        for fixture_id in ("spot_orderbook", "linear_orderbook"):
            orderbook = self.fixtures[fixture_id]["result"]
            for side in ("b", "a"):
                with self.subTest(fixture_id=fixture_id, side=side):
                    levels = orderbook[side]
                    self.assertIsInstance(levels, list)
                    self.assertGreaterEqual(len(levels), 2)
                    for level in levels:
                        self.assertIsInstance(level, list)
                        self.assertEqual(2, len(level))
                        self.assertGreater(float(level[0]), 0.0)
                        self.assertGreater(float(level[1]), 0.0)

    def test_ticker_fixtures_have_coherent_positive_top_of_book(self):
        for fixture_id in ("spot_ticker", "linear_ticker"):
            ticker = self.fixtures[fixture_id]["result"]["list"][0]
            bid_price = float(ticker["bid1Price"])
            ask_price = float(ticker["ask1Price"])
            bid_size = float(ticker["bid1Size"])
            ask_size = float(ticker["ask1Size"])
            with self.subTest(fixture_id=fixture_id):
                self.assertGreater(bid_price, 0.0)
                self.assertGreater(ask_price, 0.0)
                self.assertLess(bid_price, ask_price)
                self.assertGreater(bid_size, 0.0)
                self.assertGreater(ask_size, 0.0)
                self.assertIn("lastPrice", ticker)

    def test_default_prices_allow_positive_gross_but_negative_net_fixture_case(self):
        spot_ticker = self.fixtures["spot_ticker"]["result"]["list"][0]
        linear_ticker = self.fixtures["linear_ticker"]["result"]["list"][0]
        spot_ask = float(spot_ticker["ask1Price"])
        spot_bid = float(spot_ticker["bid1Price"])
        linear_bid = float(linear_ticker["bid1Price"])
        linear_ask = float(linear_ticker["ask1Price"])

        long_spot_short_perp_gross_pct = ((linear_bid - spot_ask) / spot_ask) * 100
        long_perp_short_spot_gross_pct = ((spot_bid - linear_ask) / linear_ask) * 100

        self.assertGreater(long_spot_short_perp_gross_pct, 0.0)
        self.assertLess(long_spot_short_perp_gross_pct, 0.2)
        self.assertLess(long_perp_short_spot_gross_pct, 0.0)

    def test_linear_ticker_preserves_context_only_market_fields(self):
        ticker = self.fixtures["linear_ticker"]["result"]["list"][0]
        for field in ("markPrice", "indexPrice", "fundingRate", "nextFundingTime"):
            self.assertIn(field, ticker)
            self.assertNotEqual("", ticker[field])

    def test_linear_instruments_info_contains_contract_metadata(self):
        instrument = self.fixtures["linear_instruments_info"]["result"]["list"][0]
        self.assertEqual("LinearPerpetual", instrument["contractType"])
        self.assertEqual("Trading", instrument["status"])
        self.assertEqual("BTC", instrument["baseCoin"])
        self.assertEqual("USDT", instrument["quoteCoin"])
        self.assertEqual("USDT", instrument["settleCoin"])
        self.assertIn("tickSize", instrument["priceFilter"])
        self.assertIn("qtyStep", instrument["lotSizeFilter"])
        self.assertIn("minOrderQty", instrument["lotSizeFilter"])
        self.assertIn("minNotionalValue", instrument["lotSizeFilter"])
        self.assertEqual(480, instrument["fundingInterval"])

    def test_spot_instruments_info_contains_spot_metadata(self):
        instrument = self.fixtures["spot_instruments_info"]["result"]["list"][0]
        self.assertEqual("BTC", instrument["baseCoin"])
        self.assertEqual("USDT", instrument["quoteCoin"])
        self.assertEqual("Trading", instrument["status"])
        self.assertIn("tickSize", instrument["priceFilter"])
        self.assertIn("basePrecision", instrument["lotSizeFilter"])
        self.assertIn("quotePrecision", instrument["lotSizeFilter"])
        self.assertIn("minOrderQty", instrument["lotSizeFilter"])
        self.assertIn("minOrderAmt", instrument["lotSizeFilter"])

    def _assert_no_forbidden_private_account_or_execution_content(self, value):
        if isinstance(value, dict):
            for key, nested in value.items():
                normalized_key = key.lower()
                for forbidden in FORBIDDEN_KEY_SUBSTRINGS:
                    self.assertNotIn(forbidden, normalized_key, key)
                self._assert_no_forbidden_private_account_or_execution_content(nested)
        elif isinstance(value, list):
            for item in value:
                self._assert_no_forbidden_private_account_or_execution_content(item)
        elif isinstance(value, str):
            normalized_value = value.lower()
            for forbidden in FORBIDDEN_KEY_SUBSTRINGS:
                self.assertNotIn(forbidden, normalized_value, value)

    def _assert_no_forbidden_metadata_or_generated_paths(self, value):
        if isinstance(value, dict):
            for key, nested in value.items():
                normalized_key = key.lower()
                for forbidden in FORBIDDEN_LIVE_CAPTURE_METADATA:
                    self.assertNotIn(forbidden, normalized_key, key)
                self._assert_no_forbidden_metadata_or_generated_paths(nested)
        elif isinstance(value, list):
            for item in value:
                self._assert_no_forbidden_metadata_or_generated_paths(item)
        elif isinstance(value, str):
            normalized_value = value.lower()
            for forbidden in FORBIDDEN_LIVE_CAPTURE_METADATA:
                self.assertNotIn(forbidden, normalized_value, value)
            for forbidden_path in GENERATED_ARTIFACT_PATHS:
                self.assertNotIn(forbidden_path, value)


if __name__ == "__main__":
    unittest.main()
