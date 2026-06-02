from __future__ import annotations

import unittest
from typing import Any

from src.market_data.adapters.base import MarketDataAdapter
from src.market_data.adapters.composite import CompositeOrderbookImbalanceAdapter, CompositeSpotSpreadAdapter
from src.market_data.packet_builder import OpportunityPacketBuilder
from src.market_data.registry import build_adapter, load_market_data_config
from src.strategy.readiness import build_readiness_report


class StaticObservationAdapter(MarketDataAdapter):
    adapter_type = "static_public_spot_test"

    def __init__(self, adapter_id: str, observation: dict[str, Any]) -> None:
        super().__init__(adapter_id, config={})
        self.observation = observation

    def fetch_snapshot(self) -> dict[str, Any]:
        return {
            "observations": [self.observation],
            "adapter_metadata": {"adapter_id": self.adapter_id, "adapter_type": self.adapter_type},
        }


class OrderbookImbalanceLiveCompositeTests(unittest.TestCase):
    def test_registry_builds_live_orderbook_imbalance_composite_without_network_call(self):
        config = load_market_data_config("configs/market_data.yaml")

        adapter = build_adapter("live_upbit_bithumb_orderbook_imbalance", config)

        self.assertIsInstance(adapter, CompositeOrderbookImbalanceAdapter)
        self.assertEqual([child.adapter_id for child in adapter.child_adapters], ["live_upbit_spot", "live_bithumb_spot"])
        self.assertEqual(adapter.config["strategy_family"], "orderbook_imbalance")
        self.assertTrue(adapter.config["experimental"])

    def test_existing_spot_spread_composite_registry_path_is_unchanged(self):
        config = load_market_data_config("configs/market_data.yaml")

        adapter = build_adapter("live_upbit_bithumb_spot_spread", config)

        self.assertIsInstance(adapter, CompositeSpotSpreadAdapter)
        self.assertEqual([child.adapter_id for child in adapter.child_adapters], ["live_upbit_spot", "live_bithumb_spot"])

    def test_composite_orderbook_snapshot_builds_experimental_packet(self):
        adapter = CompositeOrderbookImbalanceAdapter(
            "live_upbit_bithumb_orderbook_imbalance",
            config={
                "asset": "BTC",
                "quote": "KRW",
                "strategy_family": "orderbook_imbalance",
                "strategy_id": "orderbook_imbalance_v0",
                "thresholds": {"imbalance_ratio_threshold": 1.5, "max_data_age_ms": 3000, "target_notional": 1_000_000},
            },
            child_adapters=[
                StaticObservationAdapter("live_upbit_spot", spot_observation("upbit", bid_size=0.5, ask_size=0.1)),
                StaticObservationAdapter("live_bithumb_spot", spot_observation("bithumb", bid_size=0.2, ask_size=0.2)),
            ],
        )

        snapshot = adapter.fetch_snapshot()
        packet = OpportunityPacketBuilder().build(snapshot)
        report = build_readiness_report(packet)

        self.assertEqual(snapshot["strategy_family"], "orderbook_imbalance")
        self.assertEqual(snapshot["strategy_id"], "orderbook_imbalance_v0")
        self.assertEqual(snapshot["signal_type"], "orderbook_imbalance")
        self.assertEqual(snapshot["adapter_metadata"]["generated_from"], "composite_orderbook_imbalance")
        self.assertEqual(snapshot["adapter_metadata"]["adapter_id"], "live_upbit_bithumb_orderbook_imbalance")
        self.assertTrue(snapshot["extensions"]["experimental_strategy"])
        self.assertTrue(snapshot["extensions"]["non_active_strategy"])
        self.assertEqual(snapshot["extensions"]["source_child_adapters"], ["live_upbit_spot", "live_bithumb_spot"])
        self.assertEqual(packet.strategy_family, "orderbook_imbalance")
        self.assertGreaterEqual(len(packet.observations), 2)
        self.assertGreaterEqual(len(packet.candidates), 1)
        self.assertEqual(packet.candidates[0].candidate_type, "orderbook_imbalance_signal")
        self.assertIsNone(packet.candidates[0].estimated_net_gap_pct)
        self.assertEqual(packet.detector_metadata.generated_from, "composite_orderbook_imbalance")
        self.assertEqual(report["strategy_status"], "experimental")
        self.assertIn("experimental_strategy", report["warnings"])
        self.assertIn("non_active_strategy", report["warnings"])
        self.assertFalse(report["readiness_pass"])


def spot_observation(venue_id: str, *, bid_size: float, ask_size: float) -> dict[str, Any]:
    bid = 99_990_000
    ask = 100_000_000
    return {
        "observation_id": f"{venue_id}_btc_krw_orderbook",
        "venue_id": venue_id,
        "venue_name": venue_id.title(),
        "market_symbol": "BTC/KRW",
        "instrument_type": "spot",
        "region": "KR",
        "last_price": 99_995_000,
        "bid": bid,
        "ask": ask,
        "bid_size": bid_size,
        "ask_size": ask_size,
        "timestamp_utc": "2026-06-01T00:00:00+00:00",
        "liquidity": {
            "orderbook_depth_available": True,
            "volume_available": True,
            "estimated_executable_notional": None,
            "estimated_slippage_pct": None,
            "depth_levels": [
                {"level": 1, "bid_price": bid, "bid_size": bid_size, "ask_price": ask, "ask_size": ask_size},
                {"level": 2, "bid_price": bid - 10_000, "bid_size": bid_size, "ask_price": ask + 10_000, "ask_size": ask_size},
            ],
        },
        "data_quality": {
            "timestamps_available": True,
            "max_data_age_ms": 500,
            "latency_ms": 100,
            "is_realtime": True,
        },
        "health": {"api_status_known": True, "api_ok": True},
    }


if __name__ == "__main__":
    unittest.main()
