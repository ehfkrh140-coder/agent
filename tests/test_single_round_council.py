import json
import types
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from concurrent.futures import Future
from unittest.mock import patch

from src.agent_config import AgentConfig
from src.council.single_round_runner import SingleRoundCouncilRunner
from src.schemas.agent_response import AgentResponse
from src.schemas.session_record import AgentRunResult
from src.storage.council_session_store import CouncilSessionStore


def make_config(agent_id: str) -> AgentConfig:
    return AgentConfig(
        agent_id=agent_id,
        name=agent_id,
        provider="gemini_cli",
        model="flash",
        gemini_cli_home=f"C:/x/{agent_id}",
        system_prompt_path=f"prompts/{agent_id}.md",
    )


def make_result(agent_id: str, summary: str, status: str = "success") -> AgentRunResult:
    response = None if status != "success" else AgentResponse(
        summary=summary,
        key_points=[f"{agent_id} point"],
        concerns=[],
        questions=[],
        suggested_next_steps=[],
        confidence=0.5,
    )
    return AgentRunResult(
        agent_id=agent_id,
        name=agent_id,
        status=status,
        model="flash",
        provider="gemini_cli",
        response=response,
        error=None if status == "success" else f"{agent_id} failed",
    )


class SingleRoundCouncilRunnerTests(unittest.TestCase):
    def setUp(self):
        self.configs = [make_config(f"agent_0{i}") for i in range(1, 6)]

    def test_chair_runs_first_and_review_inputs_include_chair_response(self):
        calls = []
        results = {
            "agent_01": make_result("agent_01", "chair brief"),
            "agent_02": make_result("agent_02", "pro"),
            "agent_03": make_result("agent_03", "con"),
            "agent_04": make_result("agent_04", "risk"),
            "agent_05": make_result("agent_05", "final"),
        }

        def fake_run_agent(self, agent_id, message):
            calls.append((agent_id, message))
            return results[agent_id]

        with patch.object(SingleRoundCouncilRunner, "_run_agent", fake_run_agent):
            council_results, flow, chair_context, review_contexts, final_context = SingleRoundCouncilRunner(self.configs).run("original", parallel=False)

        self.assertEqual(calls[0], ("agent_01", "original"))
        for agent_id, message in calls[1:4]:
            self.assertIn(agent_id, ["agent_02", "agent_03", "agent_04"])
            payload = json.loads(message)
            self.assertEqual(payload["original_user_message"], "original")
            self.assertEqual(payload["chair_brief"]["response"]["summary"], "chair brief")
        self.assertEqual([r.agent_id for r in council_results], ["agent_01", "agent_02", "agent_03", "agent_04", "agent_05"])
        self.assertEqual(flow.mode, "single_round_v1")
        self.assertEqual(chair_context["stage"], "chair")
        self.assertEqual(set(review_contexts.keys()), {"agent_02", "agent_03", "agent_04"})
        self.assertEqual(final_context["agent_01_chair"]["response"]["summary"], "chair brief")

    def test_final_input_contains_agent_01_to_04_results(self):
        calls = []
        results = {f"agent_0{i}": make_result(f"agent_0{i}", f"summary {i}") for i in range(1, 6)}

        def fake_run_agent(self, agent_id, message):
            calls.append((agent_id, message))
            return results[agent_id]

        with patch.object(SingleRoundCouncilRunner, "_run_agent", fake_run_agent):
            SingleRoundCouncilRunner(self.configs).run("original", parallel=False)

        final_agent_id, final_message = calls[-1]
        self.assertEqual(final_agent_id, "agent_05")
        payload = json.loads(final_message)
        self.assertEqual(payload["original_user_message"], "original")
        self.assertEqual(payload["agent_01_chair"]["response"]["summary"], "summary 1")
        self.assertEqual(payload["agent_02_pro"]["response"]["summary"], "summary 2")
        self.assertEqual(payload["agent_03_con"]["response"]["summary"], "summary 3")
        self.assertEqual(payload["agent_04_risk"]["response"]["summary"], "summary 4")

    def test_parallel_review_results_are_sorted_by_agent_id(self):
        runner = SingleRoundCouncilRunner(self.configs)
        review_messages = {agent_id: agent_id for agent_id in ["agent_02", "agent_03", "agent_04"]}
        future_by_agent = {}
        for agent_id in ["agent_04", "agent_02", "agent_03"]:
            future = Future()
            future.set_result(make_result(agent_id, agent_id))
            future_by_agent[agent_id] = future

        class FakeExecutor:
            def __init__(self, max_workers):
                self.max_workers = max_workers
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return False
            def submit(self, fn, agent_id, message):
                return future_by_agent[agent_id]

        with patch("src.council.single_round_runner.ThreadPoolExecutor", FakeExecutor), patch("src.council.single_round_runner.as_completed", return_value=[future_by_agent["agent_04"], future_by_agent["agent_02"], future_by_agent["agent_03"]]):
            results = runner._run_review_agents(review_messages, parallel=True, max_workers=2)

        self.assertEqual([result.agent_id for result in results], ["agent_02", "agent_03", "agent_04"])

    def test_final_runs_with_failed_review_context(self):
        calls = []
        results = {
            "agent_01": make_result("agent_01", "chair"),
            "agent_02": make_result("agent_02", "pro"),
            "agent_03": make_result("agent_03", "", status="failed"),
            "agent_04": make_result("agent_04", "risk"),
            "agent_05": make_result("agent_05", "final"),
        }

        def fake_run_agent(self, agent_id, message):
            calls.append((agent_id, message))
            return results[agent_id]

        with patch.object(SingleRoundCouncilRunner, "_run_agent", fake_run_agent):
            council_results, flow, _, _, final_context = SingleRoundCouncilRunner(self.configs).run("original", parallel=False)

        self.assertEqual(calls[-1][0], "agent_05")
        self.assertEqual(final_context["agent_03_con"]["status"], "failed")
        self.assertEqual(flow.final_policy, "run_after_review_failures_with_available_context")
        self.assertEqual([result.status for result in council_results], ["success", "success", "failed", "success", "success"])

    def test_council_session_store_writes_flow_metadata(self):
        with TemporaryDirectory() as td:
            runner = SingleRoundCouncilRunner(self.configs)
            result = make_result("agent_01", "chair")
            path = CouncilSessionStore(td).save(
                user_message="original",
                results=[result],
                council_flow=runner.flow,
                chair_context={"chair_brief": {"status": "success"}},
                review_contexts={},
                final_context=None,
            )
            saved = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(saved["council_flow"]["mode"], "single_round_v1")
        self.assertEqual(saved["results"][0]["agent_id"], "agent_01")

    def test_main_has_council_option(self):
        text = Path("main.py").read_text(encoding="utf-8")
        self.assertIn("--council", text)
        self.assertIn("SingleRoundCouncilRunner", text)


if __name__ == "__main__":
    unittest.main()
