import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from src.llm.gemini_cli_client import GeminiCliClient
from src.schemas.agent_response import AgentResponse
from src.validators.response_safety import validate_agent_response_safety


VALID_PAYLOAD = {
    "summary": "ok",
    "key_points": [],
    "concerns": [],
    "questions": [],
    "suggested_next_steps": [],
    "confidence": 0.1,
}


class StdinPolicySafetyTests(unittest.TestCase):
    def test_generate_command_uses_stdin_mode_policy_approval_and_model(self):
        client = GeminiCliClient(cli_command="gemini.cmd")
        cmd = client._build_generate_command("prompt", model="flash")

        self.assertNotIn("-p", cmd)
        self.assertNotIn("--output-format", cmd)
        self.assertNotIn("|", cmd)
        self.assertIn("--approval-mode", cmd)
        self.assertEqual(cmd[cmd.index("--approval-mode") + 1], "plan")
        self.assertIn("--model", cmd)
        self.assertEqual(cmd[cmd.index("--model") + 1], "flash")
        self.assertIn("--policy", cmd)
        policy_arg = Path(cmd[cmd.index("--policy") + 1])
        self.assertTrue(policy_arg.is_absolute())
        self.assertEqual(policy_arg.name, "gemini_cli_targeted_policy.toml")
        self.assertIn("-o", cmd)
        self.assertEqual(cmd[cmd.index("-o") + 1], "json")

    def test_run_cli_command_pipes_prompt_to_stdin(self):
        client = GeminiCliClient(cli_command="gemini.cmd")
        proc = MagicMock()
        proc.pid = 123
        proc.returncode = 0
        proc.communicate.return_value = (json.dumps({"response": json.dumps(VALID_PAYLOAD)}), "")

        with patch("subprocess.Popen", return_value=proc) as popen:
            code, stdout, stderr = client._run_cli_command(
                cmd=["gemini.cmd", "--skip-trust", "-o", "json"],
                env={},
                cwd=Path.cwd(),
                timeout_seconds=30,
                input_text="hello prompt",
            )

        self.assertEqual(code, 0)
        self.assertTrue(stdout)
        self.assertEqual(stderr, "")
        self.assertEqual(popen.call_args.kwargs["stdin"], subprocess.PIPE)
        proc.communicate.assert_called_once_with(input="hello prompt", timeout=30)

    def test_generate_structured_passes_prompt_via_input_and_detects_tools(self):
        client = GeminiCliClient(cli_command="gemini.cmd")
        stdout = json.dumps({
            "response": json.dumps(VALID_PAYLOAD),
            "stats": {"tools": {"totalCalls": 1, "byName": {"list_directory": 1}}},
        })
        with patch.object(client, "_run_cli_command", return_value=(0, stdout, "")) as run_cmd:
            result = client.generate_structured(
                prompt="안녕?",
                response_schema=AgentResponse,
                gemini_cli_home="C:/tmp/home",
                working_dir=".",
                model="flash",
            )

        self.assertIn("tool_calls_detected", result.warning)
        self.assertEqual(run_cmd.call_args.kwargs["input_text"], "안녕?")
        cmd = run_cmd.call_args.kwargs["cmd"]
        self.assertNotIn("-p", cmd)
        self.assertIn("--approval-mode", cmd)
        self.assertIn("--policy", cmd)
        self.assertIn("--model", cmd)


    def test_agents_config_uses_flash_model_and_plan_approval(self):
        from src.config_loader import load_agent_configs

        configs = load_agent_configs("configs/agents.yaml")
        self.assertEqual(len(configs), 5)
        for config in configs:
            self.assertEqual(config.model, "flash")
            self.assertEqual(config.approval_mode, "plan")

    def test_policy_file_is_utf8_without_bom_and_not_wildcard_deny_all(self):
        policy_path = Path("configs/gemini_cli_targeted_policy.toml")
        raw = policy_path.read_bytes()
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
        text = raw.decode("utf-8")
        self.assertNotIn('toolName = "*"', text)
        for tool_name in ["update_topic", "list_directory", "google_web_search"]:
            self.assertIn(f'toolName = "{tool_name}"', text)

    def test_safety_validator_allows_risk_check_phrases(self):
        allowed_phrases = [
            "전송 비용 리스크 확인",
            "전송 시간 확인",
            "입출금 가능 여부 확인",
            "수수료 확인",
            "호가 깊이 확인",
            "실행 중단 조건 설정",
            "리스크 게이트",
            "BEP 계산",
            "순수익 시뮬레이션",
            "데이터 수집",
            "API 상태 확인",
        ]
        response = AgentResponse(
            summary="리스크 검토",
            key_points=allowed_phrases,
            concerns=[],
            questions=[],
            suggested_next_steps=allowed_phrases,
            confidence=0.2,
        )

        warnings = validate_agent_response_safety(response, "BTC 가격 차이")

        self.assertNotIn("unsafe_trade_suggestion", warnings)

    def test_safety_validator_detects_unsafe_trade_suggestion(self):
        unsafe_phrases = [
            "거래소 A에서 매수 후 B로 전송해 매도",
            "즉시 매수",
            "즉시 매도",
            "전량 매도",
            "주문 실행",
            "실제 실행",
            "자동매매 실행",
            "선물 포지션 진입",
            "헤지 포지션 진입",
            "execute the trade",
            "buy on A and sell on B",
            "transfer BTC then sell",
        ]
        for phrase in unsafe_phrases:
            with self.subTest(phrase=phrase):
                response = AgentResponse(
                    summary=phrase,
                    key_points=[],
                    concerns=[],
                    questions=[],
                    suggested_next_steps=[],
                    confidence=0.2,
                )
                warnings = validate_agent_response_safety(response, "BTC 가격 차이")
                self.assertIn("unsafe_trade_suggestion", warnings)

    def test_safety_validator_detects_unsafe_suggested_step(self):
        response = AgentResponse(
            summary="검토 요약",
            key_points=[],
            concerns=[],
            questions=[],
            suggested_next_steps=["즉시 주문 실행"],
            confidence=0.2,
        )
        warnings = validate_agent_response_safety(response, "BTC 가격 차이")
        self.assertIn("unsafe_trade_suggestion", warnings)

    def test_safety_validator_detects_unverified_market_assumption(self):
        response = AgentResponse(
            summary="수수료 0이고 유동성 풍부하여 실질 수익 가능성이 높음",
            key_points=[],
            concerns=[],
            questions=[],
            suggested_next_steps=[],
            confidence=0.85,
        )
        warnings = validate_agent_response_safety(
            response,
            "수수료, 호가 깊이, 체결량, 타임스탬프 정보는 아직 없습니다.",
        )
        self.assertIn("unverified_market_assumption", warnings)

    def test_generic_agent_passes_approval_mode_to_generate_structured(self):
        from src.agent_config import AgentConfig
        from src.agents.generic_gemini_agent import GenericGeminiAgent

        cfg = AgentConfig(
            agent_id="agent_approval",
            name="Agent Approval",
            provider="gemini_cli",
            model="flash",
            approval_mode="plan",
            gemini_cli_home="C:/tmp/home",
            system_prompt_path="prompts/agent_01.md",
            run_mode="direct",
        )
        agent = GenericGeminiAgent(cfg)
        with patch.object(agent.cli_client, "generate_structured") as mocked:
            mocked.return_value = AgentResponse(summary="ok", confidence=0.1)
            agent.run("hello")

        self.assertEqual(mocked.call_args.kwargs["approval_mode"], "plan")

    def test_generic_agent_passes_approval_mode_to_interactive_file(self):
        from src.agent_config import AgentConfig
        from src.agents.generic_gemini_agent import GenericGeminiAgent

        cfg = AgentConfig(
            agent_id="agent_approval_file",
            name="Agent Approval File",
            provider="gemini_cli",
            model="flash",
            approval_mode="plan",
            gemini_cli_home="C:/tmp/home",
            system_prompt_path="prompts/agent_01.md",
            run_mode="interactive_file",
        )
        agent = GenericGeminiAgent(cfg)
        with patch.object(agent.cli_client, "generate_structured_interactive_file") as mocked:
            mocked.return_value = AgentResponse(summary="ok", confidence=0.1)
            agent.run("hello")

        self.assertEqual(mocked.call_args.kwargs["approval_mode"], "plan")


if __name__ == "__main__":
    unittest.main()
