from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from src.market_data.probes.usdt_krw_public_probe import (
    ProbeHttpResponse,
    SCHEMA_VERSION,
    load_probe_config,
    probe_source,
    run_probe_report,
)
from tools.probe_usdt_krw_sources import main as probe_cli_main


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/usdt_krw_probe_sources.yaml"
STRATEGY_CURRENT_PATH = ROOT / "configs/strategy_current.yaml"
STRATEGY_REGISTRY_PATH = ROOT / "configs/strategy_registry.yaml"


class UsdtKrwPublicProbeTests(unittest.TestCase):
    def test_config_loads_without_credentials(self) -> None:
        config = load_probe_config(CONFIG_PATH)
        self.assertEqual(config["schema_version"], "usdt_krw_probe_sources_v0")
        source_ids = {source["source_id"] for source in config["sources"]}
        self.assertIn("upbit", source_ids)
        self.assertIn("bithumb", source_ids)
        self.assertIn("binance", source_ids)
        serialized = json.dumps(config).lower()
        for forbidden in ("api_key", "apikey", "secret", "token", "authorization", "password"):
            self.assertNotIn(forbidden, serialized)
        self.assertTrue(all(source.get("no_private_api") is True for source in config["sources"]))

    def test_probe_result_schema_is_stable(self) -> None:
        result = probe_source(
            {
                "source_id": "coinone",
                "role": "domestic_usdt_krw",
                "no_private_api": True,
                "safe_public_probe": False,
                "notes": ["unknown endpoint"],
            },
            created_at_utc="2026-06-02T00:00:00+00:00",
        )
        self.assertEqual(result["schema_version"], SCHEMA_VERSION)
        self.assertEqual(
            set(result),
            {
                "schema_version",
                "created_at_utc",
                "source_id",
                "role",
                "status",
                "pair_availability",
                "public_ticker_shape_detected",
                "public_orderbook_shape_detected",
                "timestamp_detected",
                "latency_ms",
                "http_status",
                "error",
                "notes",
            },
        )
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["pair_availability"], "unknown")

    def test_upbit_mocked_public_responses_mark_usdt_krw_available(self) -> None:
        seen_headers: list[dict[str, str]] = []

        def fake_get(url: str, *, timeout_seconds: float, headers: dict[str, str]) -> ProbeHttpResponse:
            seen_headers.append(headers)
            if "/v1/market/all" in url:
                return ProbeHttpResponse([{"market": "KRW-USDT", "korean_name": "테더"}], 200, 4, url)
            if "/v1/ticker" in url:
                return ProbeHttpResponse([{"market": "KRW-USDT", "trade_price": 1390.0, "timestamp": 1780000000000}], 200, 5, url)
            if "/v1/orderbook" in url:
                return ProbeHttpResponse(
                    [
                        {
                            "market": "KRW-USDT",
                            "timestamp": 1780000000000,
                            "orderbook_units": [{"bid_price": 1389.0, "ask_price": 1390.0}],
                        }
                    ],
                    200,
                    6,
                    url,
                )
            raise AssertionError(f"unexpected URL {url}")

        source = _source("upbit")
        result = probe_source(source, http_get_json=fake_get, created_at_utc="2026-06-02T00:00:00+00:00")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["pair_availability"], "available")
        self.assertTrue(result["public_ticker_shape_detected"])
        self.assertTrue(result["public_orderbook_shape_detected"])
        self.assertTrue(result["timestamp_detected"])
        self.assertTrue(seen_headers)
        for headers in seen_headers:
            lowered = {key.lower() for key in headers}
            self.assertNotIn("authorization", lowered)
            self.assertNotIn("x-api-key", lowered)

    def test_bithumb_mocked_public_responses_mark_usdt_krw_available(self) -> None:
        def fake_get(url: str, *, timeout_seconds: float, headers: dict[str, str]) -> ProbeHttpResponse:
            if "/public/ticker/USDT_KRW" in url:
                return ProbeHttpResponse(
                    {"status": "0000", "data": {"closing_price": "1391", "date": "1780000000000", "symbol": "USDT_KRW"}},
                    200,
                    3,
                    url,
                )
            if "/public/orderbook/USDT_KRW" in url:
                return ProbeHttpResponse(
                    {
                        "status": "0000",
                        "data": {
                            "timestamp": "1780000000000",
                            "payment_currency": "KRW",
                            "order_currency": "USDT",
                            "bids": [{"price": "1390", "quantity": "100"}],
                            "asks": [{"price": "1391", "quantity": "90"}],
                        },
                    },
                    200,
                    4,
                    url,
                )
            raise AssertionError(f"unexpected URL {url}")

        result = probe_source(_source("bithumb"), http_get_json=fake_get, created_at_utc="2026-06-02T00:00:00+00:00")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["pair_availability"], "available")
        self.assertTrue(result["public_ticker_shape_detected"])
        self.assertTrue(result["public_orderbook_shape_detected"])

    def test_uncertain_source_is_skipped_without_false_positive(self) -> None:
        result = probe_source(_source("korbit"), created_at_utc="2026-06-02T00:00:00+00:00")
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["pair_availability"], "unknown")
        self.assertIsNone(result["public_ticker_shape_detected"])

    def test_global_reference_mocked_response_detects_ticker_shape(self) -> None:
        def fake_get(url: str, *, timeout_seconds: float, headers: dict[str, str]) -> ProbeHttpResponse:
            return ProbeHttpResponse({"symbol": "USDCUSDT", "bidPrice": "0.9999", "askPrice": "1.0001"}, 200, 2, url)

        result = probe_source(_source("binance"), http_get_json=fake_get, created_at_utc="2026-06-02T00:00:00+00:00")
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["public_ticker_shape_detected"])
        self.assertEqual(result["pair_availability"], "available")

    def test_fx_unknown_source_remains_skipped_without_safe_endpoint(self) -> None:
        result = probe_source(_source("official_fx_source_candidate"), created_at_utc="2026-06-02T00:00:00+00:00")
        self.assertEqual(result["role"], "fx_reference")
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["pair_availability"], "unknown")

    def test_cli_writes_output_json_with_skipped_mock_config(self) -> None:
        config = {
            "schema_version": "usdt_krw_probe_sources_v0",
            "sources": [
                {
                    "source_id": "coinone",
                    "role": "domestic_usdt_krw",
                    "enabled_for_probe": True,
                    "base_url": "placeholder_public_coinone_base_url",
                    "no_private_api": True,
                    "expected_public_only": True,
                    "safe_public_probe": False,
                    "pair_candidates": ["USDT/KRW"],
                    "endpoints": {},
                    "notes": ["network-free CLI test"],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "probe.yaml"
            output_path = Path(tmpdir) / "probe.json"
            config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
            exit_code = probe_cli_main(["--config", str(config_path), "--output", str(output_path), "--timeout", "0.1"])
            self.assertEqual(exit_code, 0)
            report = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(report["schema_version"], "usdt_krw_public_probe_report_v0")
        self.assertEqual(report["results"][0]["status"], "skipped")
        self.assertEqual(report["next_recommended_step"], "review_probe_results_before_experimental_scaffolding")

    def test_report_summary_counts_roles_and_available_pairs(self) -> None:
        def fake_get(url: str, *, timeout_seconds: float, headers: dict[str, str]) -> ProbeHttpResponse:
            return ProbeHttpResponse({"symbol": "USDCUSDT", "bidPrice": "0.9999", "askPrice": "1.0001"}, 200, 2, url)

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "probe.yaml"
            config_path.write_text(
                yaml.safe_dump({"schema_version": "usdt_krw_probe_sources_v0", "sources": [_source("binance")]}),
                encoding="utf-8",
            )
            report = run_probe_report(config_path=config_path, http_get_json=fake_get, now_fn=lambda: "2026-06-02T00:00:00+00:00")
        self.assertEqual(report["summary"]["global_sources_checked"], 1)
        self.assertEqual(report["summary"]["available_pairs"][0]["source_id"], "binance")

    def test_active_strategy_remains_cross_exchange_spot_spread_v1(self) -> None:
        current = yaml.safe_load(STRATEGY_CURRENT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(current["active_strategy"]["strategy_id"], "cross_exchange_spot_spread_v1")

    def test_stablecoin_krw_premium_remains_future(self) -> None:
        registry = yaml.safe_load(STRATEGY_REGISTRY_PATH.read_text(encoding="utf-8"))
        stablecoin = [
            strategy
            for strategy in registry["strategies"]
            if strategy.get("strategy_family") == "stablecoin_krw_premium"
        ][0]
        self.assertEqual(stablecoin["strategy_id"], "usdt_krw_kimchi_premium_v0")
        self.assertEqual(stablecoin["status"], "future")
        self.assertEqual(stablecoin["execution_policy"], "NO_TRADE_ONLY")


def _source(source_id: str) -> dict[str, object]:
    config = load_probe_config(CONFIG_PATH)
    for source in config["sources"]:
        if source["source_id"] == source_id:
            return source
    raise AssertionError(f"missing source {source_id}")


if __name__ == "__main__":
    unittest.main()
