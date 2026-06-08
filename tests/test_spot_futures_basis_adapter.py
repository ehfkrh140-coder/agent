import copy
import inspect
import json
import unittest
from pathlib import Path

from src.market_data.adapters.base import MarketDataAdapterError
from src.market_data.adapters.spot_futures_basis import BinanceSpotFuturesBasisAdapter


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "market_data" / "spot_futures_basis"
NOW_UTC = "2026-06-05T00:00:00Z"
EXPECTED_PATHS = (
    "/api/v3/ticker/bookTicker",
    "/api/v3/depth",
    "/api/v3/exchangeInfo",
    "/fapi/v1/ticker/bookTicker",
    "/fapi/v1/depth",
    "/fapi/v1/premiumIndex",
    "/fapi/v1/exchangeInfo",
)
EXPECTED_STAGES = {
    "spot_book_ticker",
    "spot_depth",
    "spot_exchange_info",
    "futures_book_ticker",
    "futures_depth",
    "futures_premium_index",
    "futures_exchange_info",
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
    "order",
    "cancel",
    "withdraw",
    "deposit",
    "transfer",
    "privateKey",
)
ALLOWED_SCHEMA_KEYS_WITH_FORBIDDEN_SUBSTRINGS = {"orderbook_depth_available"}


def _load_fixture(filename):
    with (FIXTURE_DIR / filename).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _fixture_payloads():
    return {
        "/api/v3/ticker/bookTicker": _load_fixture("binance_spot_book_ticker_btcusdt.json"),
        "/api/v3/depth": _load_fixture("binance_spot_depth_btcusdt.json"),
        "/api/v3/exchangeInfo": _load_fixture("binance_spot_exchange_info_btcusdt.json"),
        "/fapi/v1/ticker/bookTicker": _load_fixture("binance_futures_book_ticker_btcusdt.json"),
        "/fapi/v1/depth": _load_fixture("binance_futures_depth_btcusdt.json"),
        "/fapi/v1/premiumIndex": _load_fixture("binance_futures_premium_index_btcusdt.json"),
        "/fapi/v1/exchangeInfo": _load_fixture("binance_futures_exchange_info_btcusdt.json"),
    }


class MockResponse:
    def __init__(self, data, *, path):
        self.data = data
        self.http_status = 200
        self.safe_response_preview = "mocked public response"
        self.elapsed_ms = 3
        self.url = f"mock://public{path}"


class MockHttpClient:
    def __init__(self, payloads=None, *, fail_path=None):
        self.payloads = payloads or _fixture_payloads()
        self.fail_path = fail_path
        self.calls = []

    def get_json(self, base_url, path, params=None):
        self.calls.append((base_url, path, dict(params or {})))
        if path == self.fail_path:
            raise RuntimeError("mock public failure secret token account order")
        return MockResponse(copy.deepcopy(self.payloads[path]), path=path)


class SpotFuturesBasisAdapterTest(unittest.TestCase):
    def _adapter(self, http_client=None):
        return BinanceSpotFuturesBasisAdapter(
            http_client=http_client or MockHttpClient(),
            now_fn=lambda: NOW_UTC,
        )

    def test_fetch_snapshot_builds_no_trade_packet(self):
        packet = self._adapter().fetch_snapshot()

        self.assertEqual("opportunity_packet_v0", packet["schema_version"])
        self.assertEqual("spot_futures_basis", packet["signal_type"])
        self.assertEqual("spot_futures_basis_v0", packet["strategy_id"])
        self.assertTrue(packet["extensions"]["no_trade_only"])
        self.assertEqual("NO_TRADE_ONLY", packet["extensions"]["execution_policy"])
        self.assertEqual(2, len(packet["observations"]))
        self.assertEqual(1, len(packet["candidates"]))
        self._assert_no_forbidden_fields(packet)

    def test_adapter_calls_expected_public_endpoints(self):
        http_client = MockHttpClient()
        self._adapter(http_client).fetch_snapshot()

        self.assertEqual(list(EXPECTED_PATHS), [call[1] for call in http_client.calls])
        for _base_url, path, _params in http_client.calls:
            lowered = path.lower()
            self.assertNotIn("private", lowered)
            self.assertNotIn("account", lowered)
            self.assertNotIn("balance", lowered)
            self.assertNotIn("position", lowered)
            self.assertNotIn("order", lowered)

    def test_adapter_metadata_and_diagnostics(self):
        packet = self._adapter().fetch_snapshot()
        extensions = packet["extensions"]
        metadata = extensions["adapter_metadata"]
        diagnostics = extensions["diagnostics"]

        self.assertEqual("live_binance_spot_futures_basis_btcusdt", metadata["adapter_id"])
        self.assertEqual("binance_spot_futures_basis", metadata["adapter_type"])
        self.assertTrue(metadata["no_trade_only"])
        self.assertEqual("NO_TRADE_ONLY", metadata["execution_policy"])
        self.assertEqual(list(EXPECTED_PATHS), metadata["endpoints"])
        self.assertEqual(7, len(diagnostics))
        self.assertEqual(EXPECTED_STAGES, {diagnostic["parser_stage"] for diagnostic in diagnostics})
        for diagnostic in diagnostics:
            self.assertIn("endpoint", diagnostic)
            self.assertIn("params", diagnostic)
            self.assertIn("http_status", diagnostic)
            self.assertIn("safe_response_preview", diagnostic)
            self.assertIn("elapsed_ms", diagnostic)
            self.assertIn("url", diagnostic)

    def test_adapter_uses_existing_parser_readiness_packet_builder(self):
        packet = self._adapter().fetch_snapshot()
        candidate = packet["candidates"][0]

        for field in ("readiness_status", "recommended_default_decision", "estimated_net_basis_pct"):
            self.assertIn(field, candidate["metrics"])
        self.assertIn("src/market_data/parsers/spot_futures_basis.py", packet["detector_metadata"]["source_files"])
        self.assertIn("src/strategy/spot_futures_basis_readiness.py", packet["detector_metadata"]["source_files"])
        self.assertIn("src/market_data/spot_futures_basis_packet_builder.py", packet["detector_metadata"]["source_files"])
        self.assertIn("WATCH is not ENTER", packet["extensions"]["assumptions"])
        self.assertIn("no trading behavior", packet["extensions"]["assumptions"])

    def test_adapter_public_fetch_error_is_safe(self):
        adapter = self._adapter(MockHttpClient(fail_path="/fapi/v1/premiumIndex"))

        with self.assertRaises(MarketDataAdapterError) as context:
            adapter.fetch_snapshot()

        message = str(context.exception).lower()
        for forbidden in ("secret", "token", "account", "order", "apikey", "privatekey"):
            self.assertNotIn(forbidden, message)

    def test_no_file_network_or_generated_artifact_behavior(self):
        import src.market_data.adapters.spot_futures_basis as adapter_module

        source = inspect.getsource(adapter_module)
        self.assertNotIn("data/market_samples", source)
        self.assertNotIn("data/generated_packets", source)
        self.assertNotIn("open(", source)
        self.assertNotIn("Path(", source)
        self.assertNotIn("src.credentials", source.lower())
        self.assertNotIn("private_credentials", source.lower())

    def test_watch_still_no_trade_only_through_adapter(self):
        payloads = _fixture_payloads()
        payloads["/api/v3/ticker/bookTicker"] = copy.deepcopy(payloads["/api/v3/ticker/bookTicker"])
        payloads["/fapi/v1/ticker/bookTicker"] = copy.deepcopy(payloads["/fapi/v1/ticker/bookTicker"])
        payloads["/api/v3/ticker/bookTicker"].update({"bidPrice": "99.90000000", "askPrice": "100.00000000"})
        payloads["/fapi/v1/ticker/bookTicker"].update({"bidPrice": "101.00000000", "askPrice": "101.10000000"})
        packet = self._adapter(MockHttpClient(payloads=payloads)).fetch_snapshot()
        candidate = packet["candidates"][0]

        self.assertEqual("WATCH", candidate["metrics"]["recommended_default_decision"])
        self.assertTrue(packet["extensions"]["no_trade_only"])
        self.assertTrue(candidate["extensions"]["no_trade_only"])
        self.assertIn("WATCH is not ENTER", candidate["assumptions"])
        self.assertIn("no trading behavior", candidate["assumptions"])
        self._assert_no_forbidden_fields(packet)

    def _assert_no_forbidden_fields(self, value):
        if isinstance(value, dict):
            for key, nested in value.items():
                if key not in ALLOWED_SCHEMA_KEYS_WITH_FORBIDDEN_SUBSTRINGS:
                    normalized_key = key.lower()
                    for forbidden in FORBIDDEN_FIELD_SUBSTRINGS:
                        self.assertNotIn(forbidden.lower(), normalized_key, key)
                self._assert_no_forbidden_fields(nested)
        elif isinstance(value, list):
            for item in value:
                self._assert_no_forbidden_fields(item)


if __name__ == "__main__":
    unittest.main()
