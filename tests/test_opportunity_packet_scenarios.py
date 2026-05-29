import io
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import main
from src.agent_config import AgentConfig
from src.council.scenarios import list_scenarios, load_opportunity_file, load_scenario, scenario_path
from src.council.single_round_runner import SingleRoundCouncilRunner
from src.storage.council_session_store import CouncilSessionStore
from src.schemas.opportunity_packet import OpportunityPacket


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


class OpportunityPacketScenarioTests(unittest.TestCase):
    def test_all_scenarios_parse_as_opportunity_packets(self):
        names = list_scenarios()
        self.assertGreaterEqual(len(names), 8)
        for name in names:
            with self.subTest(name=name):
                packet = load_scenario(name)
                self.assertEqual(packet.schema_version, "opportunity_packet_v0")
                self.assertGreaterEqual(len(packet.observations), 1)
                self.assertGreaterEqual(len(packet.candidates), 1)

    def test_two_and_three_exchange_scenarios_parse(self):
        missing = load_scenario("missing_data_gap")
        multi = load_scenario("multi_exchange_best_edge")
        self.assertEqual(len(missing.observations), 2)
        self.assertGreaterEqual(len(multi.observations), 3)
        self.assertGreaterEqual(len(multi.candidates), 2)

    def test_extensions_and_unknown_fields_do_not_break_parsing(self):
        raw = json.loads(Path("data/test_scenarios/missing_data_gap.json").read_text(encoding="utf-8"))
        raw["unknown_top_level"] = {"future": True}
        raw["observations"][0]["future_observation_field"] = "ok"
        raw["observations"][0]["extensions"]["custom_metric"] = 123
        packet = OpportunityPacket.model_validate(raw)
        self.assertEqual(packet.extensions.get("notes"), raw["extensions"].get("notes"))
        self.assertEqual(packet.observations[0].extensions["custom_metric"], 123)
        self.assertEqual(getattr(packet, "unknown_top_level")["future"], True)

    def test_human_context_and_expected_behavior_parse(self):
        veto = load_scenario("human_veto")
        bullish = load_scenario("human_bullish_thesis")
        self.assertTrue(veto.human_context.veto)
        self.assertTrue(bullish.human_context.provided)
        self.assertIsNotNone(veto.expected_behavior)
        self.assertIn("REJECT", veto.expected_behavior.acceptable_final_decisions)

    def test_load_opportunity_file_uses_given_path(self):
        path = scenario_path("high_fee_reject")
        packet = load_opportunity_file(path)
        self.assertEqual(packet.packet_id, "high_fee_reject")

    def test_agent_context_contains_packet_and_excludes_expected_behavior(self):
        packet = load_scenario("human_bullish_thesis")
        runner = SingleRoundCouncilRunner(make_configs())
        chair_context, review_contexts, final_context = runner.build_dry_run_contexts(packet.summary_message(), opportunity_packet=packet)
        self.assertIn("opportunity_packet", chair_context)
        self.assertIn("human_context", chair_context["opportunity_packet"])
        self.assertNotIn("expected_behavior", chair_context["opportunity_packet"])
        self.assertIn("opportunity_packet", review_contexts["agent_02"])
        self.assertIn("chair_brief", review_contexts["agent_02"])
        self.assertIn("opportunity_packet", final_context)
        self.assertIn("agent_01_chair", final_context)
        self.assertIn("agent_04_risk", final_context)
        self.assertNotIn("expected_behavior", final_context["opportunity_packet"])

    def test_multi_exchange_observations_are_preserved_in_context(self):
        packet = load_scenario("multi_exchange_best_edge")
        runner = SingleRoundCouncilRunner(make_configs())
        chair_context, _, final_context = runner.build_dry_run_contexts(packet.summary_message(), opportunity_packet=packet)
        self.assertGreaterEqual(len(chair_context["opportunity_packet"]["observations"]), 3)
        self.assertGreaterEqual(len(final_context["opportunity_packet"]["observations"]), 3)

    def test_list_scenarios_cli_outputs_names(self):
        with patch.object(sys, "argv", ["main.py", "--list-scenarios"]), patch("sys.stdout", new_callable=io.StringIO) as out:
            main.main()
        output = out.getvalue()
        self.assertIn("missing_data_gap", output)
        self.assertIn("multi_exchange_best_edge", output)

    def test_scenario_cli_loads_expected_path_and_dry_run_skips_agents(self):
        with TemporaryDirectory() as td, \
             patch.object(sys, "argv", ["main.py", "--council", "--scenario", "missing_data_gap", "--dry-run-context"]), \
             patch("main.load_agent_configs", return_value=make_configs()), \
             patch("main.CouncilSessionStore", side_effect=lambda _base: CouncilSessionStore(td)), \
             patch("src.council.single_round_runner.AgentRunner.run_all", side_effect=AssertionError("Gemini should not run")), \
             patch("sys.stdout", new_callable=io.StringIO) as out:
            main.main()
        self.assertIn("Dry-run context saved", out.getvalue())

    def test_opportunity_file_cli_loads_given_file_in_dry_run(self):
        path = str(scenario_path("human_veto"))
        with TemporaryDirectory() as td, \
             patch.object(sys, "argv", ["main.py", "--council", "--opportunity-file", path, "--dry-run-context"]), \
             patch("main.load_agent_configs", return_value=make_configs()), \
             patch("main.CouncilSessionStore", side_effect=lambda _base: CouncilSessionStore(td)), \
             patch("src.council.single_round_runner.AgentRunner.run_all", side_effect=AssertionError("Gemini should not run")), \
             patch("sys.stdout", new_callable=io.StringIO) as out:
            main.main()
        self.assertIn("Dry-run context saved", out.getvalue())

    def test_scenario_requires_council(self):
        with patch.object(sys, "argv", ["main.py", "--scenario", "missing_data_gap"]), patch("sys.stdout", new_callable=io.StringIO) as out:
            main.main()
        self.assertIn("require --council", out.getvalue())


if __name__ == "__main__":
    unittest.main()
