import copy
import inspect
import json
import unittest
from pathlib import Path

from src.market_data.adapters.base import MarketDataAdapterError
from src.market_data.adapters.spot_futures_basis import (
    BinanceSpotFuturesBasisAdapter,
    BybitSpotFuturesBasisAdapter,
    DEFAULT_ADAPTER_ID,
    DEFAULT_BYBIT_ADAPTER_ID,
)
from src.market_data.packet_builder import OpportunityPacketBuilder


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "market_data" / "spot_futures_basis"
NOW_UTC = "2026-06-05T00:00:00Z"
EXPECTED_CALLS = (
    ("/v5/market/tickers", "spot"),
    ("/v5/market/orderbook", "spot"),
    ("/v5/market/instruments-info", "spot"),
    ("/v5/market/tickers", "linear"),
    ("/v5/market/orderbook", "linear"),
    ("/v5/market/instruments-info", "linear"),
)
EXPECTED_STAGES = {
    "spot_ticker",
    "spot_orderbook",
    "spot_instruments_info",
    "linear_ticker",
    "linear_orderbook",
    "linear_instruments_info",
}
FORBIDDEN_FIELD_SUBSTRINGS = (
    "apiKey",
    "secret",
    "token",
    "credential",
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
    "alert_enabled",
    "council_auto_call",
)
ALLOWED_PUBLIC_ORDERBOOK_WORDING = "orderbook"


def _load_fixture(filename):
    with (FIXTURE_DIR / filename).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _fixture_payloads():
    return {
        ("/v5/market/tickers", "spot"): _load_fixture("bybit_spot_ticker_btcusdt.json"),
        ("/v5/market/orderbook", "spot"): _load_fixture("bybit_spot_orderbook_btcusdt.json"),
        ("/v5/market/instruments-info", "spot"): _load_fixture("bybit_spot_instruments_info_btcusdt.json"),
        ("/v5/market/tickers", "linear"): _load_fixture("bybit_linear_ticker_btcusdt.json"),
        ("/v5/market/orderbook", "linear"): _load_fixture("bybit_linear_orderbook_btcusdt.json"),
        ("/v5/market/instruments-info", "linear"): _load_fixture("bybit_linear_instruments_info_btcusdt.json"),
    }


class MockResponse:
    def __init__(self, data, *, path, category):
        self.data = data
        self.http_status = 200
        self.safe_response_preview = f"mocked public bybit {category} response"
        self.elapsed_ms = 4
        self.url = f"mock://bybit-public{path}?category={category}"


class MockHttpClient:
    def __init__(self, payloads=None, *, fail_key=None):
        self.payloads = payloads or _fixture_payloads()
        self.fail_key = fail_key
        self.calls = []

    def get_json(self, base_url, path, params=None):
        params = dict(params or {})
        category = params.get("category")
        key = (path, category)
        self.calls.append((base_url, path, params))
        if key == self.fail_key:
            raise RuntimeError("mock public bybit failure secret token account order")
        return MockResponse(copy.deepcopy(self.payloads[key]), path=path, category=category)


class SpotFuturesBasisBybitAdapterTest(unittest.TestCase):
    def _adapter(self, http_client=None):
        return BybitSpotFuturesBasisAdapter(
            http_client=http_client or MockHttpClient(),
            now_fn=lambda: NOW_UTC,
        )

    def test_bybit_fetch_snapshot_builds_no_trade_packet(self):
        packet = self._adapter().fetch_snapshot()

        self.assertEqual("opportunity_packet_v0", packet["schema_version"])
        self.assertEqual("spot_futures_basis", packet["signal_type"])
        self.assertEqual("spot_futures_basis", packet["strategy_family"])
        self.assertEqual("spot_futures_basis_v0", packet["strategy_id"])
        self.assertEqual("bybit", packet["extensions"]["source_venue_id"])
        self.assertTrue(packet["extensions"]["no_trade_only"])
        self.assertEqual("NO_TRADE_ONLY", packet["extensions"]["execution_policy"])
        self.assertEqual(2, len(packet["observations"]))
        self.assertEqual(1, len(packet["candidates"]))
        self.assertEqual("bybit_btcusdt_spot_futures_basis_candidate", packet["candidates"][0]["candidate_id"])
        self._assert_no_forbidden_private_or_execution_fields(packet)

    def test_bybit_adapter_calls_expected_public_endpoints(self):
        http_client = MockHttpClient()
        self._adapter(http_client).fetch_snapshot()

        calls = [(path, params.get("category")) for _base_url, path, params in http_client.calls]
        self.assertEqual(list(EXPECTED_CALLS), calls)
        for _base_url, path, params in http_client.calls:
            lowered_path = path.lower().replace(ALLOWED_PUBLIC_ORDERBOOK_WORDING, "public_book")
            self.assertNotIn("private", lowered_path)
            self.assertNotIn("account", lowered_path)
            self.assertNotIn("balance", lowered_path)
            self.assertNotIn("position", lowered_path)
            self.assertNotIn("order", lowered_path)
            self.assertNotIn("cancel", lowered_path)
            self.assertIn(params["category"], {"spot", "linear"})
            self.assertEqual("BTCUSDT", params["symbol"])

    def test_bybit_adapter_metadata_and_diagnostics(self):
        packet = self._adapter().fetch_snapshot()
        extensions = packet["extensions"]
        metadata = extensions["adapter_metadata"]
        diagnostics = extensions["diagnostics"]

        self.assertEqual(DEFAULT_BYBIT_ADAPTER_ID, metadata["adapter_id"])
        self.assertEqual("bybit_spot_futures_basis", metadata["adapter_type"])
        self.assertEqual("bybit", metadata["venue_id"])
        self.assertEqual("spot", metadata["spot_category"])
        self.assertEqual("linear", metadata["perp_category"])
        self.assertTrue(metadata["no_trade_only"])
        self.assertEqual("NO_TRADE_ONLY", metadata["execution_policy"])
        self.assertEqual(6, len(diagnostics))
        self.assertEqual(EXPECTED_STAGES, {diagnostic["parser_stage"] for diagnostic in diagnostics})
        for diagnostic in diagnostics:
            self.assertIn("endpoint", diagnostic)
            self.assertIn("params", diagnostic)
            self.assertEqual(0, diagnostic["retCode"])
            self.assertEqual("OK", diagnostic["retMsg"])
            self.assertIn("http_status", diagnostic)
            self.assertIn("safe_response_preview", diagnostic)
            self.assertIn("elapsed_ms", diagnostic)
            self.assertIn("url", diagnostic)

    def test_bybit_adapter_uses_existing_parser_readiness_packet_builder(self):
        packet = self._adapter().fetch_snapshot()
        candidate = packet["candidates"][0]
        observation_ids = {observation["observation_id"] for observation in packet["observations"]}

        for field in (
            "readiness_status",
            "recommended_default_decision",
            "estimated_net_basis_pct",
        ):
            self.assertIn(field, candidate["metrics"])
        self.assertEqual(candidate["metrics"]["estimated_net_basis_pct"], candidate["estimated_net_gap_pct"])
        self.assertIn("src/market_data/parsers/spot_futures_basis.py", packet["detector_metadata"]["source_files"])
        self.assertIn("src/strategy/spot_futures_basis_readiness.py", packet["detector_metadata"]["source_files"])
        self.assertIn("src/market_data/spot_futures_basis_packet_builder.py", packet["detector_metadata"]["source_files"])
        self.assertIn("WATCH is not ENTER", packet["extensions"]["assumptions"])
        self.assertIn("no trading behavior", packet["extensions"]["assumptions"])
        self.assertIn("bybit_spot_btcusdt_spot_futures_basis", observation_ids)
        self.assertIn("bybit_linear_btcusdt_perp_spot_futures_basis", observation_ids)
        self.assertNotIn("binance_spot_btcusdt_spot_futures_basis", observation_ids)
        self.assertEqual("bybit_btcusdt_spot_futures_basis_candidate", candidate["candidate_id"])

    def test_bybit_adapter_public_fetch_error_is_safe(self):
        adapter = self._adapter(MockHttpClient(fail_key=("/v5/market/orderbook", "linear")))

        with self.assertRaises(MarketDataAdapterError) as context:
            adapter.fetch_snapshot()

        message = str(context.exception).lower()
        for forbidden in ("secret", "token", "account", "order", "apikey", "privatekey"):
            self.assertNotIn(forbidden, message)

    def test_bybit_adapter_no_file_network_or_generated_artifact_behavior(self):
        import src.market_data.adapters.spot_futures_basis as adapter_module

        source = inspect.getsource(adapter_module)
        self.assertNotIn("data/market_samples", source)
        self.assertNotIn("data/generated_packets", source)
        self.assertNotIn("open(", source)
        self.assertNotIn("Path(", source)
        self.assertNotIn("src.credentials", source.lower())
        self.assertNotIn("private_credentials", source.lower())


    def test_bybit_adapter_live_like_orderbook_without_category_builds_parser_ok_packet(self):
        payloads = _fixture_payloads()
        for key in (("/v5/market/orderbook", "spot"), ("/v5/market/orderbook", "linear")):
            payloads[key] = copy.deepcopy(payloads[key])
            payloads[key].pop("category", None)
            payloads[key]["result"].pop("category", None)

        packet = self._adapter(MockHttpClient(payloads=payloads)).fetch_snapshot()
        validated = OpportunityPacketBuilder().build(packet)
        dumped = validated.model_dump(mode="json")
        observations = {observation["instrument_type"]: observation for observation in dumped["observations"]}
        spot = observations["spot"]
        perp = observations["linear_perpetual"]
        candidate = dumped["candidates"][0]
        all_missing_fields = (
            spot["extensions"]["required_missing_fields"]
            + perp["extensions"]["required_missing_fields"]
            + candidate["required_missing_fields"]
        )

        self.assertEqual("OK", spot["extensions"]["parser_normalized_status"])
        self.assertEqual("OK", perp["extensions"]["parser_normalized_status"])
        self.assertEqual([], spot["extensions"]["required_missing_fields"])
        self.assertEqual([], perp["extensions"]["required_missing_fields"])
        self.assertEqual([], candidate["required_missing_fields"])
        self.assertNotIn("spot_orderbook_category_mismatch", all_missing_fields)
        self.assertNotIn("linear_orderbook_category_mismatch", all_missing_fields)
        self.assertEqual(6, len(dumped["extensions"]["diagnostics"]))
        self.assertTrue(dumped["extensions"]["no_trade_only"])
        self.assertEqual("NO_TRADE_ONLY", dumped["extensions"]["execution_policy"])

    def test_bybit_watch_still_no_trade_only_through_adapter(self):
        payloads = _fixture_payloads()
        payloads[("/v5/market/tickers", "linear")] = copy.deepcopy(payloads[("/v5/market/tickers", "linear")])
        payloads[("/v5/market/orderbook", "linear")] = copy.deepcopy(payloads[("/v5/market/orderbook", "linear")])
        ticker = payloads[("/v5/market/tickers", "linear")]["result"]["list"][0]
        ticker["bid1Price"] = "66000.00"
        ticker["ask1Price"] = "66010.00"
        ticker["lastPrice"] = "66005.00"
        payloads[("/v5/market/orderbook", "linear")]["result"]["b"][0] = ["66000.00", "2.500"]
        payloads[("/v5/market/orderbook", "linear")]["result"]["a"][0] = ["66010.00", "2.250"]

        packet = self._adapter(MockHttpClient(payloads=payloads)).fetch_snapshot()
        candidate = packet["candidates"][0]

        self.assertEqual("WATCH", candidate["metrics"]["recommended_default_decision"])
        self.assertTrue(candidate["metrics"]["readiness_pass"])
        self.assertTrue(packet["extensions"]["no_trade_only"])
        self.assertTrue(candidate["extensions"]["no_trade_only"])
        self.assertIn("WATCH is not ENTER", candidate["assumptions"])
        self.assertIn("no trading behavior", candidate["assumptions"])
        self._assert_no_forbidden_private_or_execution_fields(packet)

    def test_binance_adapter_regression_still_importable_with_default_adapter_id(self):
        adapter = BinanceSpotFuturesBasisAdapter(http_client=MockHttpClient(), now_fn=lambda: NOW_UTC)
        self.assertEqual(DEFAULT_ADAPTER_ID, adapter.adapter_id)
        self.assertEqual("binance_spot_futures_basis", adapter.adapter_type)

    def _assert_no_forbidden_private_or_execution_fields(self, value):
        if isinstance(value, dict):
            for key, nested in value.items():
                normalized_key = key.lower().replace(ALLOWED_PUBLIC_ORDERBOOK_WORDING, "public_book")
                for forbidden in FORBIDDEN_FIELD_SUBSTRINGS:
                    self.assertNotIn(forbidden.lower(), normalized_key, key)
                self._assert_no_forbidden_private_or_execution_fields(nested)
        elif isinstance(value, list):
            for item in value:
                self._assert_no_forbidden_private_or_execution_fields(item)
        elif isinstance(value, str):
            normalized_value = value.lower().replace(ALLOWED_PUBLIC_ORDERBOOK_WORDING, "public_book")
            for forbidden in FORBIDDEN_FIELD_SUBSTRINGS:
                self.assertNotIn(forbidden.lower(), normalized_value, value)


if __name__ == "__main__":
    unittest.main()
