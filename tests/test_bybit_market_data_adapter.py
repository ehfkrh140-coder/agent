from __future__ import annotations

import io
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import tools.collect_market_data as collect_market_data
from src.market_data.adapters.base import MarketDataAdapterError
from src.market_data.adapters.bybit import BybitPublicMarketDataAdapter
from src.market_data.http_client import HttpJsonResponse
from src.market_data.packet_builder import OpportunityPacketBuilder
from src.market_data.registry import build_adapter, load_market_data_config


class FakeHttpClient:
    def __init__(self, ticker_data: dict, orderbook_data: dict) -> None:
        self.ticker_data = ticker_data
        self.orderbook_data = orderbook_data
        self.calls = []

    def get_json(self, base_url: str, path: str, params: dict):
        self.calls.append((base_url, path, params))
        if path.endswith("/tickers"):
            return HttpJsonResponse(data=self.ticker_data, elapsed_ms=12, url=f"{base_url}{path}")
        if path.endswith("/orderbook"):
            return HttpJsonResponse(data=self.orderbook_data, elapsed_ms=18, url=f"{base_url}{path}")
        raise AssertionError(path)


def ok_ticker(mark_price="100.0"):
    return {
        "retCode": 0,
        "retMsg": "OK",
        "result": {
            "list": [
                {
                    "symbol": "BTCUSDT",
                    "lastPrice": "99.8",
                    "markPrice": mark_price,
                    "indexPrice": "99.9",
                    "bid1Price": "99.2",
                    "bid1Size": "1.1",
                    "ask1Price": "99.5",
                    "ask1Size": "1.2",
                    "volume24h": "12345",
                    "turnover24h": "1234500",
                    "fundingRate": "0.0001",
                    "nextFundingTime": "1780003600000",
                    "openInterest": "999",
                }
            ]
        },
    }


def ok_orderbook():
    return {
        "retCode": 0,
        "retMsg": "OK",
        "result": {
            "s": "BTCUSDT",
            "b": [["99.3", "10"], ["99.2", "2"]],
            "a": [["99.4", "15"], ["99.5", "3"]],
            "ts": 1780000000000,
            "cts": 1780000000500,
            "u": 123,
            "seq": 456,
        },
    }


class BybitMarketDataAdapterTests(unittest.TestCase):
    def make_adapter(self, ticker_data=None, orderbook_data=None):
        return BybitPublicMarketDataAdapter(
            "live_bybit_mark_orderbook_gap",
            config={
                "base_url": "https://api.bybit.com",
                "category": "linear",
                "symbol": "BTCUSDT",
                "display_symbol": "BTC/USDT-PERP",
                "orderbook_limit": 25,
                "thresholds": {
                    "base_percent": 2.0,
                    "min_gap_floor_pct": 0.2,
                    "min_notional": 500.0,
                    "max_data_age_ms": 3000,
                },
                "guards": {
                    "manual_blacklisted": False,
                    "runtime_blocked": False,
                    "open_position": False,
                    "pending_duplicate": False,
                },
            },
            http_client=FakeHttpClient(ticker_data or ok_ticker(), orderbook_data or ok_orderbook()),
            now_fn=lambda: datetime.fromtimestamp(1780000001000 / 1000, tz=timezone.utc),
        )

    def test_bybit_adapter_maps_ticker_and_orderbook_to_snapshot(self):
        adapter = self.make_adapter()
        snapshot = adapter.fetch_snapshot()
        self.assertEqual(snapshot["strategy_family"], "mark_orderbook_gap")
        self.assertEqual(snapshot["strategy_id"], "mark_orderbook_gap_hunt_v0")
        self.assertEqual(snapshot["adapter_metadata"]["adapter_type"], "bybit_public")
        observation = snapshot["observations"][0]
        self.assertEqual(observation["venue_id"], "bybit")
        self.assertEqual(observation["market_symbol"], "BTC/USDT-PERP")
        self.assertEqual(observation["last_price"], 99.8)
        self.assertEqual(observation["mark_price"], 100.0)
        self.assertEqual(observation["index_price"], 99.9)
        self.assertEqual(observation["bid"], 99.3)
        self.assertEqual(observation["ask"], 99.4)
        self.assertEqual(observation["bid_size"], 10.0)
        self.assertEqual(observation["ask_size"], 15.0)
        self.assertEqual(observation["data_quality"]["max_data_age_ms"], 500)
        self.assertEqual(observation["data_quality"]["latency_ms"], 30)
        self.assertTrue(observation["data_quality"]["timestamps_available"])
        self.assertTrue(observation["liquidity"]["orderbook_depth_available"])
        self.assertEqual(observation["liquidity"]["estimated_executable_notional"], 1491.0)
        self.assertEqual(observation["derivatives"]["funding_rate_pct"], 0.0001)
        self.assertEqual(len(observation["liquidity"]["depth_levels"]), 2)

    def test_bybit_snapshot_builds_mark_orderbook_packet(self):
        packet = OpportunityPacketBuilder().build(self.make_adapter().fetch_snapshot())
        self.assertEqual(packet.strategy_family, "mark_orderbook_gap")
        self.assertEqual(packet.detector_metadata.generated_from, "bybit_public")
        self.assertEqual(packet.observations[0].venue_id, "bybit")
        self.assertGreaterEqual(len(packet.candidates), 1)
        candidate = packet.candidates[0]
        self.assertEqual(candidate.side_candidate, "LONG")
        self.assertAlmostEqual(candidate.long_gap_pct, 0.6)
        self.assertAlmostEqual(candidate.long_notional, 1491.0)
        self.assertTrue(candidate.freshness_pass)

    def test_bybit_ret_code_failure_raises_adapter_error(self):
        adapter = self.make_adapter(ticker_data={"retCode": 10001, "retMsg": "bad request", "result": {}})
        with self.assertRaises(MarketDataAdapterError):
            adapter.fetch_snapshot()

    def test_invalid_numeric_strings_become_none(self):
        adapter = self.make_adapter(ticker_data=ok_ticker(mark_price="not-a-number"))
        snapshot = adapter.fetch_snapshot()
        observation = snapshot["observations"][0]
        self.assertIsNone(observation["mark_price"])
        packet = OpportunityPacketBuilder().build(snapshot)
        self.assertEqual(len(packet.candidates), 0)

    def test_registry_builds_live_bybit_adapter(self):
        adapter = build_adapter("live_bybit_mark_orderbook_gap", load_market_data_config("configs/market_data.yaml"))
        self.assertIsInstance(adapter, BybitPublicMarketDataAdapter)
        self.assertEqual(adapter.base_url, "https://api.bybit.com")

    def test_collect_market_data_live_adapter_can_be_mocked(self):
        class FakeAdapter:
            def fetch_snapshot(self):
                return self_snapshot

        self_snapshot = self.make_adapter().fetch_snapshot()
        with TemporaryDirectory() as td:
            output_path = Path(td) / "bybit_packet.json"
            argv = [
                "collect_market_data.py",
                "--adapter",
                "live_bybit_mark_orderbook_gap",
                "--output",
                str(output_path),
            ]
            with patch.object(sys, "argv", argv), \
                 patch.object(collect_market_data, "build_adapter", return_value=FakeAdapter()), \
                 patch("sys.stdout", new_callable=io.StringIO) as out:
                collect_market_data.main()
            self.assertIn("OpportunityPacket saved", out.getvalue())
            packet = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(packet["strategy_family"], "mark_orderbook_gap")
            self.assertEqual(packet["observations"][0]["venue_id"], "bybit")


if __name__ == "__main__":
    unittest.main()
