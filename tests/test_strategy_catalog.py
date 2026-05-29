import json
import unittest
from pathlib import Path

from src.council.scenarios import load_scenario
from src.schemas.opportunity_packet import OpportunityPacket


MARK_SCENARIOS = [
    "mark_orderbook_gap_long_watch",
    "mark_orderbook_gap_short_watch",
    "mark_orderbook_gap_stale_reject",
    "mark_orderbook_gap_low_liquidity_reject",
    "mark_orderbook_gap_guard_blocked",
]


class StrategyCatalogTests(unittest.TestCase):
    def test_strategy_catalog_exists_and_includes_p0_strategies(self):
        text = Path("docs/strategy_catalog.md").read_text(encoding="utf-8")
        self.assertIn("Strategy 01. Mark-Orderbook Gap Hunt", text)
        self.assertIn("strategy_id: `mark_orderbook_gap_hunt_v0`", text)
        self.assertIn("status: `P0-A`", text)
        self.assertIn("Strategy 02. Cross-Exchange Spot Executable Spread", text)
        self.assertIn("strategy_id: `cross_exchange_spot_spread_v0`", text)
        self.assertIn("status: `P0-B`", text)
        self.assertIn("target_gap_pct = max(base_percent / leverage, min_gap_floor_pct)", text)
        self.assertIn("gross_spread = target_bid - source_ask", text)
        self.assertIn("NO_TRADE_ONLY", text)

    def test_opportunity_packet_strategy_fields_parse(self):
        packet = load_scenario("mark_orderbook_gap_long_watch")
        self.assertEqual(packet.strategy_family, "mark_orderbook_gap")
        self.assertEqual(packet.strategy_id, "mark_orderbook_gap_hunt_v0")

    def test_market_observation_mark_orderbook_fields_parse(self):
        obs = load_scenario("mark_orderbook_gap_long_watch").observations[0]
        self.assertEqual(obs.mark_price, 100.0)
        self.assertAlmostEqual(obs.index_price, 99.9)
        self.assertEqual(obs.leverage, 10)
        self.assertEqual(obs.max_leverage, 50)
        self.assertEqual(obs.unit, 1)
        self.assertEqual(obs.tick, 0.1)
        self.assertEqual(obs.step, 0.001)

    def test_opportunity_candidate_strategy_metrics_parse(self):
        candidate = load_scenario("mark_orderbook_gap_long_watch").candidates[0]
        self.assertEqual(candidate.strategy_family, "mark_orderbook_gap")
        self.assertEqual(candidate.strategy_id, "mark_orderbook_gap_hunt_v0")
        self.assertEqual(candidate.side_candidate, "LONG")
        self.assertEqual(candidate.target_gap_pct, 0.2)
        self.assertEqual(candidate.long_gap_pct, 0.6)
        self.assertEqual(candidate.long_notional, 1491.0)
        self.assertTrue(candidate.liquidity_pass)
        self.assertTrue(candidate.gap_pass)
        self.assertTrue(candidate.freshness_pass)
        self.assertTrue(candidate.guard_pass)
        self.assertIn("base_percent", candidate.metrics)
        self.assertIn("manual_blacklisted", candidate.guards)
        self.assertIn("min_notional", candidate.thresholds)

    def test_mark_orderbook_gap_scenarios_are_valid(self):
        for name in MARK_SCENARIOS:
            with self.subTest(name=name):
                packet = load_scenario(name)
                self.assertEqual(packet.strategy_family, "mark_orderbook_gap")
                self.assertEqual(packet.strategy_id, "mark_orderbook_gap_hunt_v0")
                self.assertEqual(packet.candidates[0].strategy_family, "mark_orderbook_gap")
                self.assertIsNotNone(packet.expected_behavior)

    def test_expected_behavior_excluded_from_agent_context(self):
        packet = load_scenario("mark_orderbook_gap_long_watch")
        context = packet.agent_context_dict()
        self.assertNotIn("expected_behavior", context)
        self.assertIn("strategy_family", context)
        self.assertIn("long_gap_pct", context["candidates"][0])

    def test_unknown_extra_fields_do_not_break_strategy_parsing(self):
        raw = json.loads(Path("data/test_scenarios/mark_orderbook_gap_long_watch.json").read_text(encoding="utf-8"))
        raw["future_strategy_field"] = "ok"
        raw["observations"][0]["future_mark_field"] = 123
        raw["candidates"][0]["future_candidate_field"] = {"x": True}
        packet = OpportunityPacket.model_validate(raw)
        self.assertEqual(getattr(packet, "future_strategy_field"), "ok")
        self.assertEqual(getattr(packet.observations[0], "future_mark_field"), 123)
        self.assertEqual(getattr(packet.candidates[0], "future_candidate_field"), {"x": True})

    def test_missing_data_gap_has_spot_strategy_metadata(self):
        packet = load_scenario("missing_data_gap")
        self.assertEqual(packet.strategy_family, "cross_exchange_spot_spread")
        self.assertEqual(packet.strategy_id, "cross_exchange_spot_spread_v0")
        candidate = packet.candidates[0]
        self.assertEqual(candidate.candidate_type, "spot_executable_spread_candidate")
        self.assertEqual(candidate.direction, "buy_source_ask_sell_target_bid_candidate")


if __name__ == "__main__":
    unittest.main()
