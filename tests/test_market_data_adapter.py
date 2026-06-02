import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.market_data.packet_builder import OpportunityPacketBuilder
from src.market_data.registry import build_adapter, list_adapters, load_market_data_config


class MarketDataAdapterTests(unittest.TestCase):
    def test_registry_lists_replay_adapters(self):
        config = load_market_data_config("configs/market_data.yaml")
        self.assertIn("replay_mark_orderbook_gap", list_adapters(config))
        self.assertIn("replay_cross_exchange_spot_spread", list_adapters(config))

    def test_replay_adapter_loads_fixture_snapshot(self):
        adapter = build_adapter("replay_mark_orderbook_gap", load_market_data_config("configs/market_data.yaml"))
        snapshot = adapter.fetch_snapshot()
        self.assertEqual(snapshot["strategy_family"], "mark_orderbook_gap")
        self.assertEqual(snapshot["adapter_metadata"]["adapter_type"], "replay")
        self.assertIn("fixture_path", snapshot["adapter_metadata"])

    def test_mark_orderbook_gap_packet_builder(self):
        adapter = build_adapter("replay_mark_orderbook_gap", load_market_data_config("configs/market_data.yaml"))
        packet = OpportunityPacketBuilder().build(adapter.fetch_snapshot())
        self.assertEqual(packet.strategy_family, "mark_orderbook_gap")
        self.assertEqual(packet.strategy_id, "mark_orderbook_gap_hunt_v0")
        self.assertEqual(len(packet.observations), 1)
        self.assertEqual(packet.observations[0].mark_price, 100.0)
        self.assertGreaterEqual(len(packet.candidates), 1)
        candidate = packet.candidates[0]
        self.assertEqual(candidate.side_candidate, "LONG")
        self.assertAlmostEqual(candidate.target_gap_pct, 0.2)
        self.assertAlmostEqual(candidate.long_gap_pct, 0.6)
        self.assertAlmostEqual(candidate.long_notional, 1491.0)
        self.assertTrue(candidate.gap_pass)
        self.assertTrue(candidate.liquidity_pass)
        self.assertTrue(candidate.freshness_pass)
        self.assertTrue(candidate.guard_pass)
        self.assertIn("liquidity.estimated_slippage_pct", candidate.required_missing_fields)

    def test_cross_exchange_spot_packet_builder_uses_ask_and_bid(self):
        adapter = build_adapter("replay_cross_exchange_spot_spread", load_market_data_config("configs/market_data.yaml"))
        packet = OpportunityPacketBuilder().build(adapter.fetch_snapshot())
        self.assertEqual(packet.strategy_family, "cross_exchange_spot_spread")
        self.assertEqual(len(packet.observations), 2)
        self.assertEqual(len(packet.candidates), 1)
        candidate = packet.candidates[0]
        self.assertEqual(candidate.source_venue_id, "upbit")
        self.assertEqual(candidate.target_venue_id, "bithumb")
        self.assertEqual(candidate.direction, "buy_source_ask_sell_target_bid_candidate")
        self.assertEqual(candidate.gross_gap_absolute, 650000)
        self.assertAlmostEqual(candidate.gross_gap_pct, 0.65)
        self.assertEqual(candidate.metrics["source_ask"], 100000000)
        self.assertEqual(candidate.metrics["target_bid"], 100650000)

    def test_collect_market_data_cli_writes_opportunity_packet(self):
        with TemporaryDirectory() as td:
            output_path = Path(td) / "packet.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    "tools/collect_market_data.py",
                    "--adapter",
                    "replay_mark_orderbook_gap",
                    "--output",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("OpportunityPacket saved", completed.stdout)
            packet = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(packet["schema_version"], "opportunity_packet_v0")
            self.assertEqual(packet["strategy_family"], "mark_orderbook_gap")
            self.assertEqual(packet["candidates"][0]["long_gap_pct"], 0.6)


if __name__ == "__main__":
    unittest.main()
