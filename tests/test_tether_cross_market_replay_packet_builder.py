from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import yaml

import main
from src.market_data.packet_builder import OpportunityPacketBuilder
from src.market_data.registry import build_adapter, load_market_data_config
from src.storage.council_session_store import CouncilSessionStore
from src.strategy.readiness import build_readiness_report


class TetherCrossMarketReplayPacketBuilderTests(unittest.TestCase):
    def build_packet(self):
        config = load_market_data_config("configs/market_data.yaml")
        adapter = build_adapter("replay_tether_cross_market_premium", config)
        snapshot = adapter.fetch_snapshot()
        return OpportunityPacketBuilder().build(snapshot)

    def test_replay_fixture_loads_and_builds_tether_packet(self) -> None:
        fixture = Path("data/fixtures/market_data/tether_cross_market_snapshot.json")
        data = json.loads(fixture.read_text(encoding="utf-8"))

        self.assertEqual(data["strategy_family"], "tether_cross_market_premium")
        self.assertEqual(data["strategy_id"], "usdt_krw_global_reference_v0")
        self.assertEqual(data["asset"], "USDT")
        self.assertEqual(data["quote"], "KRW")
        self.assertEqual(data["adapter_metadata"]["adapter_id"], "replay_tether_cross_market_premium")
        self.assertEqual(len(data["observations"]), 5)

        packet = self.build_packet()
        self.assertEqual(packet.strategy_family, "tether_cross_market_premium")
        self.assertEqual(packet.strategy_id, "usdt_krw_global_reference_v0")
        self.assertEqual(packet.asset, "USDT")
        self.assertEqual(packet.quote, "KRW")
        self.assertGreaterEqual(len(packet.observations), 5)

    def test_observations_include_domestic_and_global_reference_venues(self) -> None:
        packet = self.build_packet()
        by_venue = {observation.venue_id: observation for observation in packet.observations}

        for venue_id in ["upbit", "bithumb", "binance", "bybit", "okx"]:
            self.assertIn(venue_id, by_venue)
        self.assertEqual(by_venue["upbit"].market_symbol, "USDT/KRW")
        self.assertEqual(by_venue["bithumb"].market_symbol, "USDT/KRW")
        for venue_id in ["binance", "bybit", "okx"]:
            self.assertEqual(by_venue[venue_id].extensions["reference_role"], "global_usdt_reference")

    def test_candidates_include_both_domestic_directions_and_required_metrics(self) -> None:
        packet = self.build_packet()
        directions = {candidate.direction for candidate in packet.candidates}

        self.assertEqual({candidate.candidate_type for candidate in packet.candidates}, {"tether_domestic_spread_signal"})
        self.assertIn("buy_upbit_sell_bithumb_usdt_krw_signal", directions)
        self.assertIn("buy_bithumb_sell_upbit_usdt_krw_signal", directions)
        self.assertEqual(len(packet.candidates), 2)
        for candidate in packet.candidates:
            metrics = candidate.metrics
            self.assertIn("gross_gap_pct", metrics)
            self.assertIn("estimated_net_gap_pct", metrics)
            self.assertIn("global_usdt_mid", metrics)
            self.assertIn("global_usdt_depeg_flag", metrics)
            self.assertEqual(metrics["global_reference_venue_count"], 3)
            self.assertEqual(metrics["global_reference_sources"], ["binance", "bybit", "okx"])

    def test_strategy_remains_experimental_non_active_and_readiness_pass_false(self) -> None:
        registry = yaml.safe_load(Path("configs/strategy_registry.yaml").read_text(encoding="utf-8"))
        current = yaml.safe_load(Path("configs/strategy_current.yaml").read_text(encoding="utf-8"))
        tether = next(strategy for strategy in registry["strategies"] if strategy["strategy_family"] == "tether_cross_market_premium")
        packet = self.build_packet()
        report = build_readiness_report(packet)

        self.assertEqual(tether["status"], "experimental")
        self.assertEqual(tether["execution_policy"], "NO_TRADE_ONLY")
        self.assertEqual(current["active_strategy"]["strategy_id"], "cross_exchange_spot_spread_v1")
        self.assertIn(report["status"], {"WATCH", "REJECT", "NEED_DATA"})
        self.assertFalse(report["readiness_pass"])
        self.assertIn("experimental_strategy", report["warnings"])
        self.assertIn("non_active_strategy", report["warnings"])

    def test_collect_market_data_replay_writes_output_json(self) -> None:
        with TemporaryDirectory() as td:
            output_path = Path(td) / "replay_tether_cross_market_packet.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    "tools/collect_market_data.py",
                    "--adapter",
                    "replay_tether_cross_market_premium",
                    "--output",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertIn("OpportunityPacket saved", completed.stdout)
        self.assertEqual(payload["strategy_family"], "tether_cross_market_premium")
        self.assertEqual(payload["asset"], "USDT")
        self.assertEqual(payload["quote"], "KRW")
        self.assertGreaterEqual(len(payload["observations"]), 5)
        self.assertGreaterEqual(len(payload["candidates"]), 1)

    def test_main_dry_run_context_from_generated_packet_skips_gemini(self) -> None:
        with TemporaryDirectory() as td:
            output_path = Path(td) / "replay_tether_cross_market_packet.json"
            subprocess.run(
                [
                    sys.executable,
                    "tools/collect_market_data.py",
                    "--adapter",
                    "replay_tether_cross_market_premium",
                    "--output",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            with patch.object(
                sys,
                "argv",
                ["main.py", "--council", "--opportunity-file", str(output_path), "--dry-run-context"],
            ), patch("main.CouncilSessionStore", side_effect=lambda _base: CouncilSessionStore(td)), patch(
                "src.council.single_round_runner.AgentRunner.run_all", side_effect=AssertionError("Gemini should not run")
            ):
                main.main()
            saved = list(Path(td).glob("*.json"))

        self.assertTrue(saved)

    def test_handoff_evidence_file_documents_required_review_evidence(self) -> None:
        handoff = Path("docs/pr_handoffs/tether_cross_market_replay_packet_builder_v0.md")
        self.assertTrue(handoff.exists(), str(handoff))
        text = handoff.read_text(encoding="utf-8")
        for phrase in [
            "Task type: packet-builder",
            "## 1. Purpose",
            "## 2. Changed files",
            "## 3. Impact scope",
            "## 4. Tests run",
            "## 5. Manual smoke",
            "## 7. Risks",
            "## 8. Rollback plan",
            "## 9. Human review required",
            "## 10. No-trade compliance",
            "private API: no",
            "API key/secret/token: no",
            "balance/account: no",
            "order/cancel: no",
            "transfer/withdraw/deposit: no",
            "fiat/bank transfer: no",
            "auto-trading: no",
            "active strategy changed: no",
        ]:
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
