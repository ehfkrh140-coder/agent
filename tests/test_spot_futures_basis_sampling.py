import copy
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.market_data.adapters.spot_futures_basis import BinanceSpotFuturesBasisAdapter
from src.market_data.sampling import run_market_sampling


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "market_data" / "spot_futures_basis"
ADAPTER_ID = "live_binance_spot_futures_basis_btcusdt"
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
ALLOWED_SCHEMA_KEYS_WITH_FORBIDDEN_SUBSTRINGS = {"orderbook_depth_available", "imbalance_side", "imbalance_ratio", "imbalance_pass"}


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


def _adapter(http_client: MockHttpClient | None = None) -> BinanceSpotFuturesBasisAdapter:
    return BinanceSpotFuturesBasisAdapter(
        http_client=http_client or MockHttpClient(),
        now_fn=lambda: NOW_UTC,
    )


def _sample(adapter: BinanceSpotFuturesBasisAdapter, *, samples_requested: int = 3) -> dict[str, Any]:
    return run_market_sampling(
        adapter,
        adapter_id=ADAPTER_ID,
        samples_requested=samples_requested,
        interval_seconds=0,
        output_path=None,
        also_save_packets=False,
        sleep_fn=lambda _seconds: None,
        now_fn=lambda: datetime(2026, 6, 5, 0, 0, 0, tzinfo=timezone.utc),
    )


def _watch_payloads() -> dict[str, dict[str, Any]]:
    payloads = _fixture_payloads()
    payloads["/api/v3/ticker/bookTicker"] = copy.deepcopy(payloads["/api/v3/ticker/bookTicker"])
    payloads["/fapi/v1/ticker/bookTicker"] = copy.deepcopy(payloads["/fapi/v1/ticker/bookTicker"])
    payloads["/api/v3/ticker/bookTicker"].update({"bidPrice": "99.90000000", "askPrice": "100.00000000"})
    payloads["/fapi/v1/ticker/bookTicker"].update({"bidPrice": "101.00000000", "askPrice": "101.10000000"})
    return payloads


class SpotFuturesBasisSamplingTest(unittest.TestCase):
    def test_run_market_sampling_spot_futures_basis_three_samples_ok(self):
        http_client = MockHttpClient()
        result = _sample(_adapter(http_client), samples_requested=3)

        self.assertEqual("market_sampling_v1", result["schema_version"])
        self.assertEqual(ADAPTER_ID, result["adapter_id"])
        self.assertEqual(3, result["samples_requested"])
        self.assertEqual(3, result["summary"]["samples_ok"])
        self.assertEqual(0, result["summary"]["samples_error"])
        self.assertEqual(21, len(http_client.calls))
        self.assertEqual(list(EXPECTED_PATHS) * 3, [call[1] for call in http_client.calls])
        for sample in result["samples"]:
            self.assertEqual("ok", sample["status"])
            self.assertEqual("spot_futures_basis", sample["strategy_family"])
            self.assertEqual("spot_futures_basis_v0", sample["strategy_id"])
            self.assertEqual(1, sample["candidate_count"])
            self.assertTrue(sample["no_trade_only"])
            self.assertEqual("NO_TRADE_ONLY", sample["execution_policy"])

    def test_sampling_summary_contains_readiness_counts(self):
        result = _sample(_adapter(), samples_requested=3)
        summary = result["summary"]
        readiness_counts = summary["readiness_status_counts"]

        self.assertEqual(3, summary["samples_ok"])
        self.assertIn("reject_count", summary)
        self.assertIn("watch_count", summary)
        self.assertIn("need_data_count", summary)
        self.assertEqual(summary["samples_ok"], sum(readiness_counts.values()))
        self.assertEqual(
            summary["samples_ok"],
            summary["reject_count"] + summary["watch_count"] + summary["need_data_count"],
        )
        self.assertTrue(any(status in readiness_counts for status in ("REJECT", "WATCH", "NEED_DATA")))

    def test_sampling_record_preserves_spot_futures_metrics(self):
        result = _sample(_adapter(), samples_requested=3)

        for sample in result["samples"]:
            best_candidate = sample["best_candidate"]
            self.assertEqual("spot_futures_basis_observation", best_candidate["candidate_type"])
            self.assertEqual("spot_futures_basis", sample["strategy_family"])
            self.assertIn(best_candidate["readiness_status"], {"REJECT", "WATCH", "NEED_DATA"})
            self.assertEqual(sample["readiness_status"], best_candidate["readiness_status"])
            self.assertEqual(sample["recommended_default_decision"], best_candidate["recommended_default_decision"])
            self.assertIn("estimated_net_gap_pct", best_candidate)
            self.assertEqual([], best_candidate["required_missing_fields"])
            self.assertEqual([], sample["required_missing_fields"])
            self.assertEqual("OK", best_candidate["parser_normalized_status"])
            self.assertEqual("OK", sample["parser_normalized_status"])
            self.assertEqual(7, sample["diagnostics_count"])

    def test_sampling_no_trade_and_no_private_fields(self):
        result = _sample(_adapter(), samples_requested=3)

        self._assert_no_forbidden_fields(result)
        for sample in result["samples"]:
            self.assertTrue(sample["no_trade_only"])
            self.assertEqual("NO_TRADE_ONLY", sample["execution_policy"])

    def test_sampling_does_not_write_generated_json_paths(self):
        market_samples_before = set(Path("data/market_samples").glob("*.json"))
        generated_packets_before = set(Path("data/generated_packets").glob("*.json"))

        result = _sample(_adapter(), samples_requested=3)

        self.assertIsNone(result["sampling_output_file"])
        self.assertNotIn("data/market_samples", repr(result))
        self.assertNotIn("data/generated_packets", repr(result))
        self.assertEqual(market_samples_before, set(Path("data/market_samples").glob("*.json")))
        self.assertEqual(generated_packets_before, set(Path("data/generated_packets").glob("*.json")))

    def test_sampling_with_watch_still_no_trade_only(self):
        result = _sample(_adapter(MockHttpClient(payloads=_watch_payloads())), samples_requested=3)
        summary = result["summary"]

        self.assertEqual(3, summary["samples_ok"])
        self.assertEqual(3, summary["readiness_status_counts"].get("WATCH"))
        self.assertEqual(3, summary["watch_count"])
        self.assertFalse(result["council_recommended"])
        for sample in result["samples"]:
            best_candidate = sample["best_candidate"]
            self.assertEqual("WATCH", sample["readiness_status"])
            self.assertEqual("WATCH", best_candidate["readiness_status"])
            self.assertTrue(sample["no_trade_only"])
            self.assertEqual("NO_TRADE_ONLY", sample["execution_policy"])
            self.assertTrue(sample["opportunity_packet"]["extensions"]["no_trade_only"])
            self.assertEqual("NO_TRADE_ONLY", sample["opportunity_packet"]["extensions"]["execution_policy"])
            assumptions = " ".join(sample["opportunity_packet"]["extensions"].get("assumptions", []))
            self.assertIn("WATCH is not ENTER", assumptions)
            self.assertIn("no trading behavior", assumptions)
            self.assertIn("does not trigger Council auto-call, alert, or execution", assumptions)

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
