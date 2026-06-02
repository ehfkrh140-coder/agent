from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import tools.run_strategy_scenarios as run_strategy_scenarios
from src.council.scenarios import load_scenario
from src.strategy.readiness import build_readiness_report
from src.strategy.registry import load_strategy_current, load_strategy_registry, strategy_by_family

ORDERBOOK_IMBALANCE_SCENARIOS = {
    "orderbook_imbalance_missing_depth": "NEED_DATA",
    "orderbook_imbalance_bid_heavy_watch": "WATCH",
    "orderbook_imbalance_ask_heavy_watch": "WATCH",
    "orderbook_imbalance_balanced_reject": "REJECT",
    "orderbook_imbalance_stale_reject": "REJECT",
}


class OrderbookImbalanceExperimentalTests(unittest.TestCase):
    def test_registry_marks_orderbook_imbalance_experimental_without_active_change(self):
        registry = load_strategy_registry()
        current = load_strategy_current()
        strategy = strategy_by_family("orderbook_imbalance", registry)

        self.assertIsNotNone(strategy)
        assert strategy is not None
        self.assertEqual(strategy["status"], "experimental")
        self.assertEqual(strategy["priority"], "P1")
        self.assertEqual(strategy["execution_policy"], "NO_TRADE_ONLY")
        self.assertIn("not_active_v1", strategy["forbidden_for_active_if_any"])
        self.assertEqual(current["active_strategy"]["strategy_family"], "cross_exchange_spot_spread")
        self.assertEqual(current["active_strategy"]["strategy_id"], "cross_exchange_spot_spread_v1")

    def test_orderbook_imbalance_scenarios_are_schema_valid_and_exclude_expected_behavior_from_context(self):
        for name in ORDERBOOK_IMBALANCE_SCENARIOS:
            with self.subTest(name=name):
                packet = load_scenario(name)
                self.assertEqual(packet.schema_version, "opportunity_packet_v0")
                self.assertEqual(packet.strategy_family, "orderbook_imbalance")
                self.assertEqual(packet.strategy_id, "orderbook_imbalance_v0")
                self.assertEqual(packet.candidates[0].candidate_type, "orderbook_imbalance_signal")
                self.assertIsNotNone(packet.expected_behavior)
                self.assertNotIn("expected_behavior", packet.agent_context_dict())

    def test_readiness_decisions_for_manual_orderbook_imbalance_scenarios(self):
        for name, expected in ORDERBOOK_IMBALANCE_SCENARIOS.items():
            with self.subTest(name=name):
                report = build_readiness_report(load_scenario(name))
                self.assertEqual(report["recommended_default_decision"], expected)
                self.assertEqual(report["strategy_status"], "experimental")
                self.assertIn("experimental_strategy", report["warnings"])
                self.assertIn("non_active_strategy", report["warnings"])
                self.assertFalse(report["readiness_pass"])
                self.assertIn("non-active", report["basis"])

    def test_bid_and_ask_heavy_watch_reports_computed_metrics_without_active_handoff_pass(self):
        bid_report = build_readiness_report(load_scenario("orderbook_imbalance_bid_heavy_watch"))
        ask_report = build_readiness_report(load_scenario("orderbook_imbalance_ask_heavy_watch"))

        self.assertEqual(bid_report["computed_metrics"]["imbalance_side"], "BID_HEAVY")
        self.assertEqual(ask_report["computed_metrics"]["imbalance_side"], "ASK_HEAVY")
        self.assertTrue(bid_report["experimental_pass"])
        self.assertTrue(ask_report["experimental_pass"])
        self.assertFalse(bid_report["readiness_pass"])
        self.assertFalse(ask_report["readiness_pass"])

    def test_strategy_catalog_documents_experimental_orderbook_imbalance(self):
        text = Path("docs/strategy_catalog.md").read_text(encoding="utf-8")

        self.assertIn("Experimental Strategy: Orderbook Imbalance", text)
        self.assertIn("strategy_id: `orderbook_imbalance_v0`", text)
        self.assertIn("status: `experimental`", text)
        self.assertIn("orderbook_imbalance는 그 자체로 executable spread가 아니다", text)
        self.assertIn("active strategy는 계속 `cross_exchange_spot_spread_v1`", text)

    def test_batch_evaluate_only_for_orderbook_imbalance(self):
        with patch.object(sys, "argv", ["run_strategy_scenarios.py", "--strategy", "orderbook_imbalance", "--evaluate-only"]), \
             patch("src.council.single_round_runner.AgentRunner.run_all", side_effect=AssertionError("Gemini should not run")), \
             patch("sys.stdout", new_callable=io.StringIO) as out:
            run_strategy_scenarios.main()
        output = out.getvalue()
        self.assertIn("orderbook_imbalance_missing_depth\torderbook_imbalance\tNEED_DATA", output)
        self.assertIn("orderbook_imbalance_bid_heavy_watch\torderbook_imbalance\tWATCH", output)
        self.assertIn("orderbook_imbalance_ask_heavy_watch\torderbook_imbalance\tWATCH", output)
        self.assertIn("experimental_strategy", output)


if __name__ == "__main__":
    unittest.main()
