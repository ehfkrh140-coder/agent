from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import yaml

import tools.run_strategy_scenarios as run_strategy_scenarios
from src.agent_config import AgentConfig
from src.council.scenarios import load_scenario
from src.council.single_round_runner import SingleRoundCouncilRunner
from src.schemas.opportunity_packet import OpportunityPacket
from src.strategy.readiness import build_readiness_report
from src.strategy.registry import load_strategy_current, load_strategy_registry
from src.storage.council_session_store import CouncilSessionStore


ACTIVE_SPOT_SCENARIOS = [
    "spot_executable_spread_missing_depth",
    "spot_executable_spread_watch",
    "spot_executable_spread_high_fee_reject",
    "spot_executable_spread_stale_reject",
    "spot_executable_spread_low_liquidity_reject",
]


def make_configs():
    return [
        AgentConfig(
            agent_id=f"agent_0{i}",
            name=f"Agent 0{i}",
            provider="gemini_cli",
            model="flash",
            gemini_cli_home=f"C:/x/agent_0{i}",
            system_prompt_path=f"prompts/agent_0{i}.md",
        )
        for i in range(1, 6)
    ]


class StrategyRegistryReadinessTests(unittest.TestCase):
    def test_current_trading_rule_doc_exists_and_excludes_mark_fields(self):
        text = Path("docs/current_trading_rule_v1.md").read_text(encoding="utf-8")
        self.assertIn("Cross-Exchange Spot Executable Spread v1", text)
        self.assertIn("mark_price is not required", text)
        self.assertIn("index_price is not required", text)
        self.assertIn("leverage is not required", text)

    def test_strategy_configs_parse_and_active_strategy_is_spot(self):
        registry = load_strategy_registry()
        current = load_strategy_current()
        families = {item["strategy_family"]: item for item in registry["strategies"]}
        self.assertEqual(families["cross_exchange_spot_spread"]["status"], "active")
        self.assertEqual(families["cross_exchange_spot_spread"]["priority"], "P0")
        self.assertEqual(families["mark_orderbook_gap"]["status"], "experimental")
        self.assertEqual(current["active_strategy"]["strategy_family"], "cross_exchange_spot_spread")
        self.assertIn("mark_orderbook_gap", current["active_strategy"]["disabled_strategy_families"])

    def test_strategy_catalog_marks_active_and_experimental(self):
        text = Path("docs/strategy_catalog.md").read_text(encoding="utf-8")
        self.assertIn("Active Strategy: P0 Cross-Exchange Spot Executable Spread", text)
        self.assertIn("status: `active`", text)
        self.assertIn("Experimental Strategy: Mark-Orderbook Gap Hunt", text)
        self.assertIn("status: `experimental`", text)
        self.assertIn("current active v1 strategy does not use mark/index/leverage", text)

    def test_active_spot_scenarios_are_valid_and_do_not_use_mark_fields(self):
        for name in ACTIVE_SPOT_SCENARIOS:
            with self.subTest(name=name):
                packet = load_scenario(name)
                self.assertEqual(packet.strategy_family, "cross_exchange_spot_spread")
                self.assertEqual(packet.strategy_id, "cross_exchange_spot_spread_v1")
                self.assertIsNotNone(packet.expected_behavior)
                self.assertNotIn("expected_behavior", packet.agent_context_dict())
                for obs in packet.observations:
                    self.assertIsNone(obs.mark_price)
                    self.assertIsNone(obs.index_price)
                    self.assertIsNone(obs.leverage)

    def test_readiness_missing_depth_is_need_data(self):
        report = build_readiness_report(load_scenario("spot_executable_spread_missing_depth"))
        self.assertEqual(report["recommended_default_decision"], "NEED_DATA")
        self.assertFalse(report["readiness_pass"])
        self.assertIn("source.ask", report["missing_required_fields"])
        self.assertIn("source.orderbook_depth", report["missing_required_fields"])
        self.assertIn("last_price_only_candidate", report["warnings"])

    def test_readiness_high_fee_rejects_non_positive_net_gap(self):
        report = build_readiness_report(load_scenario("spot_executable_spread_high_fee_reject"))
        self.assertEqual(report["recommended_default_decision"], "REJECT")
        self.assertIn("non_positive_estimated_net_gap", report["warnings"])

    def test_readiness_stale_and_low_liquidity_reject(self):
        stale = build_readiness_report(load_scenario("spot_executable_spread_stale_reject"))
        low_liquidity = build_readiness_report(load_scenario("spot_executable_spread_low_liquidity_reject"))
        self.assertIn(stale["recommended_default_decision"], ["REJECT", "NEED_DATA"])
        self.assertIn("stale_candidate", stale["warnings"])
        self.assertIn(low_liquidity["recommended_default_decision"], ["REJECT", "NEED_DATA"])
        self.assertIn("low_liquidity_candidate", low_liquidity["warnings"])

    def test_readiness_watch_passes(self):
        report = build_readiness_report(load_scenario("spot_executable_spread_watch"))
        self.assertTrue(report["readiness_pass"])
        self.assertEqual(report["recommended_default_decision"], "WATCH")
        self.assertEqual(report["basis"], "source ask / target bid executable spread readiness")

    def test_mark_orderbook_is_experimental_disabled(self):
        report = build_readiness_report(load_scenario("mark_orderbook_gap_long_watch"))
        self.assertFalse(report["readiness_pass"])
        self.assertEqual(report["strategy_status"], "experimental")
        self.assertIn("experimental_strategy", report["warnings"])
        self.assertIn("disabled_strategy_family", report["warnings"])

    def test_council_context_includes_readiness_report(self):
        packet = load_scenario("spot_executable_spread_missing_depth")
        runner = SingleRoundCouncilRunner(make_configs())
        chair_context, review_contexts, final_context = runner.build_dry_run_contexts(packet.summary_message(), opportunity_packet=packet)
        self.assertIn("readiness_report", chair_context)
        self.assertIn("readiness_report", review_contexts["agent_02"])
        self.assertIn("readiness_report", final_context)
        self.assertFalse(final_context["readiness_report"]["readiness_pass"])
        self.assertNotIn("expected_behavior", final_context["opportunity_packet"])

    def test_active_spot_context_instruction_blocks_private_execution_scope(self):
        packet = load_scenario("spot_executable_spread_watch")
        runner = SingleRoundCouncilRunner(make_configs())
        _, review_contexts, final_context = runner.build_dry_run_contexts(packet.summary_message(), opportunity_packet=packet)
        for instruction in [review_contexts["agent_02"]["instruction"], final_context["instruction"]]:
            self.assertIn("public spot bid/ask/orderbook", instruction)
            self.assertIn("last_price 차이만으로 수익 기회 판단 금지", instruction)
            self.assertIn("source ask와 target bid 또는 VWAP", instruction)
            self.assertIn("private endpoint", instruction)
            self.assertIn("잔고 조회", instruction)
            self.assertIn("주문", instruction)
            self.assertIn("출금", instruction)
            self.assertIn("이체", instruction)
            self.assertIn("public market data 재검증", instruction)
            self.assertIn("fee config 확인", instruction)
            self.assertIn("depth/VWAP/slippage", instruction)
            self.assertIn("timestamp/data_age/latency", instruction)

    def test_batch_evaluate_only_does_not_call_gemini(self):
        with patch.object(sys, "argv", ["run_strategy_scenarios.py", "--all", "--evaluate-only"]), \
             patch("src.council.single_round_runner.AgentRunner.run_all", side_effect=AssertionError("Gemini should not run")), \
             patch("sys.stdout", new_callable=io.StringIO) as out:
            run_strategy_scenarios.main()
        output = out.getvalue()
        self.assertIn("spot_executable_spread_watch", output)
        self.assertIn("cross_exchange_spot_spread", output)

    def test_batch_dry_run_context_does_not_call_gemini(self):
        with TemporaryDirectory() as td, \
             patch.object(sys, "argv", ["run_strategy_scenarios.py", "--scenario", "spot_executable_spread_watch", "--dry-run-context"]), \
             patch.object(run_strategy_scenarios, "CouncilSessionStore", side_effect=lambda _base: CouncilSessionStore(td)), \
             patch("src.council.single_round_runner.AgentRunner.run_all", side_effect=AssertionError("Gemini should not run")), \
             patch("sys.stdout", new_callable=io.StringIO) as out:
            run_strategy_scenarios.main()
        self.assertIn("dry_run_context", out.getvalue())


if __name__ == "__main__":
    unittest.main()
