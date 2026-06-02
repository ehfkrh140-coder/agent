from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.council.scenarios import load_opportunity_file
from src.market_data.orderbook_imbalance import compute_orderbook_imbalance
from src.market_data.packet_builder import OpportunityPacketBuilder
from src.market_data.registry import build_adapter, load_market_data_config
from src.strategy.readiness import build_readiness_report


class OrderbookImbalanceDetectorTests(unittest.TestCase):
    def test_compute_orderbook_imbalance_bid_heavy(self):
        result = compute_orderbook_imbalance(observation_with_depth(bid_size=0.5, ask_size=0.1), threshold=1.5, target_notional=1_000_000)

        self.assertEqual(result["imbalance_side"], "BID_HEAVY")
        self.assertEqual(result["direction"], "bid_heavy_orderbook_signal")
        self.assertTrue(result["imbalance_pass"])
        self.assertGreater(result["bid_depth_notional"], result["ask_depth_notional"])
        self.assertGreater(result["imbalance_ratio"], 1.5)
        self.assertTrue(result["liquidity_pass"])

    def test_compute_orderbook_imbalance_ask_heavy(self):
        result = compute_orderbook_imbalance(observation_with_depth(bid_size=0.1, ask_size=0.5), threshold=1.5, target_notional=1_000_000)

        self.assertEqual(result["imbalance_side"], "ASK_HEAVY")
        self.assertEqual(result["direction"], "ask_heavy_orderbook_signal")
        self.assertTrue(result["imbalance_pass"])
        self.assertGreater(result["ask_depth_notional"], result["bid_depth_notional"])

    def test_compute_orderbook_imbalance_balanced_and_empty_depth_are_safe(self):
        balanced = compute_orderbook_imbalance(observation_with_depth(bid_size=0.2, ask_size=0.2), threshold=1.5, target_notional=1_000_000)
        empty = compute_orderbook_imbalance({"bid": 99_990_000, "ask": 100_000_000, "liquidity": {"depth_levels": []}}, threshold=1.5)

        self.assertEqual(balanced["imbalance_side"], "BALANCED")
        self.assertFalse(balanced["imbalance_pass"])
        self.assertEqual(empty["depth_levels_used"], 0)
        self.assertIsNone(empty["imbalance_ratio"])
        self.assertEqual(empty["imbalance_side"], "BALANCED")

    def test_packet_builder_builds_orderbook_imbalance_packet_from_snapshot(self):
        snapshot = json.loads(Path("data/fixtures/market_data/orderbook_imbalance_snapshot.json").read_text(encoding="utf-8"))
        packet = OpportunityPacketBuilder().build(snapshot)

        self.assertEqual(packet.strategy_family, "orderbook_imbalance")
        self.assertEqual(packet.strategy_id, "orderbook_imbalance_v0")
        self.assertEqual(packet.signal_type, "orderbook_imbalance")
        self.assertEqual(len(packet.observations), 2)
        self.assertEqual(len(packet.candidates), 2)
        candidate = packet.candidates[0]
        self.assertEqual(candidate.candidate_type, "orderbook_imbalance_signal")
        self.assertIn(candidate.direction, ["bid_heavy_orderbook_signal", "ask_heavy_orderbook_signal", "balanced_orderbook_signal"])
        self.assertIn("bid_depth_notional", candidate.metrics)
        self.assertIn("ask_depth_notional", candidate.metrics)
        self.assertIn("imbalance_ratio", candidate.metrics)
        self.assertIn("depth_levels_used", candidate.metrics)
        self.assertIsNone(candidate.estimated_net_gap_pct)

    def test_readiness_for_built_packet_remains_experimental_non_active(self):
        snapshot = json.loads(Path("data/fixtures/market_data/orderbook_imbalance_snapshot.json").read_text(encoding="utf-8"))
        packet = OpportunityPacketBuilder().build(snapshot)
        report = build_readiness_report(packet)

        self.assertIn(report["recommended_default_decision"], ["WATCH", "REJECT", "NEED_DATA"])
        self.assertEqual(report["strategy_status"], "experimental")
        self.assertIn("experimental_strategy", report["warnings"])
        self.assertIn("non_active_strategy", report["warnings"])
        self.assertFalse(report["readiness_pass"])
        self.assertIn("no Council handoff", report["basis"])

    def test_replay_orderbook_imbalance_adapter_builds_packet(self):
        adapter = build_adapter("replay_orderbook_imbalance", load_market_data_config())
        packet = OpportunityPacketBuilder().build(adapter.fetch_snapshot())

        self.assertEqual(packet.strategy_family, "orderbook_imbalance")
        self.assertGreaterEqual(len(packet.candidates), 1)
        self.assertIsNone(packet.candidates[0].estimated_net_gap_pct)

    def test_collect_market_data_replay_orderbook_imbalance_writes_packet(self):
        with tempfile.TemporaryDirectory() as td:
            output_path = Path(td) / "orderbook_packet.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    "tools/collect_market_data.py",
                    "--adapter",
                    "replay_orderbook_imbalance",
                    "--output",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("OpportunityPacket saved", completed.stdout)
            packet = load_opportunity_file(output_path)
        self.assertEqual(packet.strategy_family, "orderbook_imbalance")
        self.assertGreaterEqual(len(packet.candidates), 1)


def observation_with_depth(*, bid_size: float, ask_size: float) -> dict:
    return {
        "bid": 99_990_000,
        "ask": 100_000_000,
        "liquidity": {
            "depth_levels": [
                {"level": 1, "bid_price": 99_990_000, "bid_size": bid_size, "ask_price": 100_000_000, "ask_size": ask_size},
                {"level": 2, "bid_price": 99_980_000, "bid_size": bid_size, "ask_price": 100_010_000, "ask_size": ask_size},
            ]
        },
        "data_quality": {"max_data_age_ms": 500, "latency_ms": 100},
    }


if __name__ == "__main__":
    unittest.main()
