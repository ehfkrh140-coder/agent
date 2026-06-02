from __future__ import annotations

import json
from pathlib import Path
import unittest

import yaml

from src.council.scenarios import load_scenario
from src.schemas.opportunity_packet import OpportunityPacket
from src.strategy.readiness import build_readiness_report
from src.strategy.tether_cross_market_premium import (
    classify_domestic_spread_side,
    classify_global_usdt_health,
    compute_domestic_mid,
    compute_domestic_spread,
    compute_domestic_spread_pct,
    compute_estimated_net_gap_pct,
    compute_global_usdt_depeg_pct,
    safe_float,
)


class TetherCrossMarketPremiumTest(unittest.TestCase):
    scenario_expectations = {
        "tether_cross_market_missing_bithumb_need_data": "NEED_DATA",
        "tether_cross_market_missing_global_reference_need_data": "NEED_DATA",
        "tether_cross_market_domestic_spread_positive_watch": "WATCH",
        "tether_cross_market_high_fee_reject": "REJECT",
        "tether_cross_market_depeg_risk_reject": "REJECT",
        "tether_cross_market_last_price_only_need_data": "NEED_DATA",
        "tether_cross_market_balanced_no_spread_reject": "REJECT",
    }

    def test_formula_helper_computes_domestic_spread_and_net_gap(self) -> None:
        self.assertEqual(compute_domestic_spread(1390, 1400), 10)
        self.assertAlmostEqual(compute_domestic_spread_pct(1390, 1400), 0.7194244604)
        self.assertAlmostEqual(compute_estimated_net_gap_pct(0.72, 0.05, 0.05, 0.05, 0.10), 0.47)
        self.assertEqual(compute_domestic_mid(1388, 1390), 1389)
        self.assertEqual(classify_domestic_spread_side("Upbit", "Bithumb"), "buy_upbit_sell_bithumb")

    def test_global_depeg_helper_detects_healthy_and_depeg_states(self) -> None:
        healthy = classify_global_usdt_health(1.0001, 0.5)
        depeg = classify_global_usdt_health(0.97, 0.5)
        self.assertEqual(healthy["status"], "healthy")
        self.assertFalse(healthy["global_usdt_depeg_flag"])
        self.assertEqual(depeg["status"], "depeg")
        self.assertTrue(depeg["global_usdt_depeg_flag"])
        self.assertAlmostEqual(compute_global_usdt_depeg_pct(0.97), -3.0)

    def test_malformed_inputs_return_conservative_values(self) -> None:
        self.assertIsNone(safe_float("not-a-number"))
        self.assertIsNone(compute_domestic_spread(None, 1400))
        self.assertIsNone(compute_domestic_spread_pct(0, 1400))
        self.assertIsNone(compute_estimated_net_gap_pct(1, 0.1, "bad", 0.1, 0.1))
        self.assertEqual(classify_global_usdt_health("bad", 0.5)["status"], "unknown")
        self.assertIsNone(classify_domestic_spread_side("upbit", "upbit"))

    def test_registry_marks_tether_experimental_non_active_no_trade(self) -> None:
        registry = yaml.safe_load(Path("configs/strategy_registry.yaml").read_text(encoding="utf-8"))
        current = yaml.safe_load(Path("configs/strategy_current.yaml").read_text(encoding="utf-8"))
        tether = next(item for item in registry["strategies"] if item["strategy_family"] == "tether_cross_market_premium")
        self.assertEqual(tether["strategy_id"], "usdt_krw_global_reference_v0")
        self.assertEqual(tether["status"], "experimental")
        self.assertEqual(tether["priority"], "P1")
        self.assertEqual(tether["execution_policy"], "NO_TRADE_ONLY")
        self.assertIn("non-active strategy", " ".join(tether["readiness_rules"]))
        self.assertEqual(current["active_strategy"]["strategy_id"], "cross_exchange_spot_spread_v1")
        active = [item for item in registry["strategies"] if item.get("status") == "active"]
        self.assertEqual([item["strategy_id"] for item in active], ["cross_exchange_spot_spread_v1"])

    def test_tether_scenarios_parse_and_exclude_expected_behavior_from_agent_context(self) -> None:
        for scenario_name in self.scenario_expectations:
            with self.subTest(scenario=scenario_name):
                path = Path("data/test_scenarios") / f"{scenario_name}.json"
                data = json.loads(path.read_text(encoding="utf-8"))
                packet = OpportunityPacket.model_validate(data)
                self.assertEqual(packet.strategy_family, "tether_cross_market_premium")
                self.assertIsNotNone(packet.expected_behavior)
                self.assertNotIn("expected_behavior", packet.agent_context_dict())

    def test_tether_scenario_readiness_statuses_are_evaluate_only(self) -> None:
        for scenario_name, expected_status in self.scenario_expectations.items():
            with self.subTest(scenario=scenario_name):
                packet = load_scenario(scenario_name)
                report = build_readiness_report(packet)
                self.assertEqual(report["status"], expected_status)
                self.assertFalse(report["readiness_pass"])
                self.assertFalse(report.get("council_recommended"))
                self.assertIn("experimental_strategy", report["warnings"])
                self.assertIn("non_active_strategy", report["warnings"])

    def test_specific_tether_readiness_failure_reasons(self) -> None:
        missing_bithumb = build_readiness_report(load_scenario("tether_cross_market_missing_bithumb_need_data"))
        missing_global = build_readiness_report(load_scenario("tether_cross_market_missing_global_reference_need_data"))
        depeg = build_readiness_report(load_scenario("tether_cross_market_depeg_risk_reject"))
        last_price = build_readiness_report(load_scenario("tether_cross_market_last_price_only_need_data"))
        self.assertIn("domestic.bithumb_usdt_krw_observation", missing_bithumb["missing_required_fields"])
        self.assertIn("global_reference.binance_bybit_okx", missing_global["missing_required_fields"])
        self.assertIn("global_usdt_depeg_risk", depeg["warnings"])
        self.assertIn("last_price_only_candidate", last_price["warnings"])


if __name__ == "__main__":
    unittest.main()
