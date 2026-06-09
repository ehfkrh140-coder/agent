import copy
import inspect
import json
import unittest
from pathlib import Path
from typing import Any

from src.market_data.adapters.spot_futures_basis import BinanceSpotFuturesBasisAdapter
from src.market_data.packet_builder import OpportunityPacketBuilder
from src.market_data.parsers.spot_futures_basis import (
    build_spot_futures_basis_source_bundle,
    parse_binance_perp_observation,
    parse_binance_spot_observation,
)
from src.market_data.spot_futures_basis_packet_builder import build_spot_futures_basis_opportunity_packet
from src.strategy.spot_futures_basis_readiness import evaluate_spot_futures_basis_readiness


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "market_data" / "spot_futures_basis"
CREATED_AT_UTC = "2026-06-05T00:00:00Z"
EXPECTED_PATHS = (
    "/api/v3/ticker/bookTicker",
    "/api/v3/depth",
    "/api/v3/exchangeInfo",
    "/fapi/v1/ticker/bookTicker",
    "/fapi/v1/depth",
    "/fapi/v1/premiumIndex",
    "/fapi/v1/exchangeInfo",
)
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


def _load_fixture(filename: str) -> dict[str, Any]:
    with (FIXTURE_DIR / filename).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _fixture_payloads() -> dict[str, dict[str, Any]]:
    return {
        "/api/v3/ticker/bookTicker": _load_fixture("binance_spot_book_ticker_btcusdt.json"),
        "/api/v3/depth": _load_fixture("binance_spot_depth_btcusdt.json"),
        "/api/v3/exchangeInfo": _load_fixture("binance_spot_exchange_info_btcusdt.json"),
        "/fapi/v1/ticker/bookTicker": _load_fixture("binance_futures_book_ticker_btcusdt.json"),
        "/fapi/v1/depth": _load_fixture("binance_futures_depth_btcusdt.json"),
        "/fapi/v1/premiumIndex": _load_fixture("binance_futures_premium_index_btcusdt.json"),
        "/fapi/v1/exchangeInfo": _load_fixture("binance_futures_exchange_info_btcusdt.json"),
    }


def _spot_exchange_info_with_notional_filter(*, key: str = "minNotional", value: str = "5.00000000") -> dict[str, Any]:
    exchange_info = _load_fixture("binance_spot_exchange_info_btcusdt.json")
    symbol = exchange_info["symbols"][0]
    symbol["filters"] = [
        item for item in symbol["filters"] if item.get("filterType") not in {"MIN_NOTIONAL", "NOTIONAL"}
    ]
    symbol["filters"].append({"filterType": "NOTIONAL", key: value})
    return exchange_info


def _source_bundle_with_spot_exchange_info(spot_exchange_info: dict[str, Any]) -> dict[str, Any]:
    spot = parse_binance_spot_observation(
        _load_fixture("binance_spot_book_ticker_btcusdt.json"),
        _load_fixture("binance_spot_depth_btcusdt.json"),
        spot_exchange_info,
    )
    perp = parse_binance_perp_observation(
        _load_fixture("binance_futures_book_ticker_btcusdt.json"),
        _load_fixture("binance_futures_depth_btcusdt.json"),
        _load_fixture("binance_futures_premium_index_btcusdt.json"),
        _load_fixture("binance_futures_exchange_info_btcusdt.json"),
    )
    return build_spot_futures_basis_source_bundle(spot, perp)


class MockResponse:
    def __init__(self, data: dict[str, Any], *, path: str) -> None:
        self.data = data
        self.http_status = 200
        self.safe_response_preview = "mocked public response"
        self.elapsed_ms = 3
        self.url = f"mock://public{path}"


class MockHttpClient:
    def __init__(self, payloads: dict[str, dict[str, Any]] | None = None) -> None:
        self.payloads = payloads or _fixture_payloads()
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def get_json(self, base_url: str, path: str, params: dict[str, Any] | None = None) -> MockResponse:
        self.calls.append((base_url, path, dict(params or {})))
        return MockResponse(copy.deepcopy(self.payloads[path]), path=path)


def _source_bundle() -> dict[str, Any]:
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
    return build_spot_futures_basis_source_bundle(spot, perp)


def _packet_from_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    readiness = evaluate_spot_futures_basis_readiness(bundle)
    return build_spot_futures_basis_opportunity_packet(
        bundle,
        readiness,
        created_at_utc=CREATED_AT_UTC,
        packet_id="collect_path_test_packet",
    )


def _adapter(http_client: MockHttpClient) -> BinanceSpotFuturesBasisAdapter:
    return BinanceSpotFuturesBasisAdapter(http_client=http_client, now_fn=lambda: CREATED_AT_UTC)


class SpotFuturesBasisCollectPathTest(unittest.TestCase):
    def test_opportunity_packet_builder_accepts_spot_futures_basis_packet(self):
        packet_dict = _packet_from_bundle(_source_bundle())

        packet = OpportunityPacketBuilder().build(packet_dict)
        dumped = packet.model_dump(mode="json")

        self.assertEqual("opportunity_packet_v0", dumped["schema_version"])
        self.assertEqual("spot_futures_basis", dumped["signal_type"])
        self.assertEqual("spot_futures_basis", dumped["strategy_family"])
        self.assertEqual("spot_futures_basis_v0", dumped["strategy_id"])
        self.assertEqual(2, len(dumped["observations"]))
        self.assertEqual(1, len(dumped["candidates"]))
        self.assertTrue(dumped["extensions"]["no_trade_only"])
        self.assertEqual("NO_TRADE_ONLY", dumped["extensions"]["execution_policy"])

    def test_collect_path_equivalent_snapshot_from_adapter_mocked(self):
        http_client = MockHttpClient()
        snapshot = _adapter(http_client).fetch_snapshot()

        packet = OpportunityPacketBuilder().build(snapshot)
        dumped = packet.model_dump(mode="json")

        self.assertEqual("live_binance_spot_futures_basis_btcusdt", dumped["extensions"]["adapter_metadata"]["adapter_id"])
        self.assertEqual(7, len(dumped["extensions"]["diagnostics"]))
        self.assertEqual(list(EXPECTED_PATHS), [call[1] for call in http_client.calls])
        for base_url, path, _params in http_client.calls:
            self.assertTrue(base_url.startswith("https://api.binance.com") or base_url.startswith("https://fapi.binance.com"))
            self.assertIn(path, EXPECTED_PATHS)

    def test_builder_preserves_no_trade_watch_assumptions(self):
        bundle = _source_bundle()
        spot = bundle["spot_observation"]
        perp = bundle["perp_observation"]
        spot["best_ask"] = 100.0
        spot["best_bid"] = 99.9
        perp["best_bid"] = 101.0
        perp["best_ask"] = 101.1
        packet_dict = _packet_from_bundle(bundle)

        packet = OpportunityPacketBuilder().build(packet_dict)
        dumped = packet.model_dump(mode="json", exclude_none=True)
        candidate = dumped["candidates"][0]

        self.assertEqual("WATCH", candidate["metrics"]["recommended_default_decision"])
        self.assertTrue(candidate["metrics"]["readiness_pass"])
        self.assertTrue(dumped["extensions"]["no_trade_only"])
        self.assertTrue(candidate["extensions"]["no_trade_only"])
        self.assertIn("WATCH is not ENTER", candidate["assumptions"])
        self.assertIn("no trading behavior", candidate["assumptions"])
        self.assertIn("WATCH does not trigger Council auto-call, alert, or execution", candidate["assumptions"])
        self._assert_no_forbidden_fields(dumped)


    def test_collect_path_builder_accepts_live_like_fractional_data_age_packet(self):
        bundle = _source_bundle()
        bundle["spot_observation"]["data_age_ms"] = 42.4242
        bundle["perp_observation"]["data_age_ms"] = -558.491943359375
        packet_dict = _packet_from_bundle(bundle)

        packet = OpportunityPacketBuilder().build(packet_dict)
        dumped = packet.model_dump(mode="json", exclude_none=True)
        perp_observation = dumped["observations"][1]

        self.assertEqual("opportunity_packet_v0", dumped["schema_version"])
        self.assertEqual("spot_futures_basis", dumped["signal_type"])
        self.assertEqual("spot_futures_basis_v0", dumped["strategy_id"])
        self.assertTrue(dumped["extensions"]["no_trade_only"])
        self.assertEqual(-558, perp_observation["data_quality"]["max_data_age_ms"])
        self.assertEqual(-558.491943359375, perp_observation["extensions"]["raw_data_age_ms"])

    def test_collect_path_live_shape_notional_packet_no_need_data_from_min_notional(self):
        bundle = _source_bundle_with_spot_exchange_info(_spot_exchange_info_with_notional_filter())
        spot = bundle["spot_observation"]
        readiness = evaluate_spot_futures_basis_readiness(bundle)
        packet_dict = build_spot_futures_basis_opportunity_packet(
            bundle,
            readiness,
            created_at_utc=CREATED_AT_UTC,
            packet_id="collect_path_live_shape_notional_test_packet",
        )

        packet = OpportunityPacketBuilder().build(packet_dict)
        dumped = packet.model_dump(mode="json", exclude_none=True)

        self.assertEqual("OK", spot["parser_normalized_status"])
        self.assertNotIn("spot_min_notional_missing", spot["required_missing_fields"])
        self.assertNotIn("spot_min_notional_missing", readiness["required_missing_fields"])
        self.assertNotIn("spot_spot_min_notional_missing", readiness["required_missing_fields"])
        self.assertNotEqual("NEED_DATA", readiness["readiness_status"])
        self.assertEqual("opportunity_packet_v0", dumped["schema_version"])
        self.assertEqual("spot_futures_basis", dumped["signal_type"])
        self.assertEqual("spot_futures_basis_v0", dumped["strategy_id"])
        self.assertTrue(dumped["extensions"]["no_trade_only"])

    def test_builder_rejects_or_errors_on_unsupported_strategy_still(self):
        snapshot = {
            "strategy_family": "unknown_strategy_family",
            "asset": "BTC",
            "quote": "USDT",
        }

        with self.assertRaises(ValueError):
            OpportunityPacketBuilder().build(snapshot)

    def test_no_private_or_execution_fields_after_builder(self):
        packet = OpportunityPacketBuilder().build(_packet_from_bundle(_source_bundle()))

        self._assert_no_forbidden_fields(packet.model_dump(mode="json", exclude_none=True))

    def test_no_generated_json_paths_referenced(self):
        import src.market_data.packet_builder as packet_builder

        source = inspect.getsource(packet_builder)
        self.assertNotIn("data/market_samples", source)
        self.assertNotIn("data/generated_packets", source)

        dumped = OpportunityPacketBuilder().build(_packet_from_bundle(_source_bundle())).model_dump(
            mode="json",
            exclude_none=True,
        )
        self.assertNotIn("data/market_samples", repr(dumped))
        self.assertNotIn("data/generated_packets", repr(dumped))

    def _assert_no_forbidden_fields(self, value: Any) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if key not in ALLOWED_SCHEMA_KEYS_WITH_FORBIDDEN_SUBSTRINGS:
                    normalized_key = str(key).lower()
                    for forbidden in FORBIDDEN_FIELD_SUBSTRINGS:
                        self.assertNotIn(forbidden.lower(), normalized_key, key)
                self._assert_no_forbidden_fields(nested)
        elif isinstance(value, list):
            for item in value:
                self._assert_no_forbidden_fields(item)


if __name__ == "__main__":
    unittest.main()
