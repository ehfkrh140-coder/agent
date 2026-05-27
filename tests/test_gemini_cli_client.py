import json
import unittest
from pathlib import Path

from src.agent_config import AgentConfig
from src.llm.gemini_cli_client import GeminiCliClient
from src.schemas.agent_response import AgentResponse


class GeminiCliClientParsingTests(unittest.TestCase):
    def test_outer_response_valid_json(self):
        outer = {"response": json.dumps({"summary": "ok", "key_points": [], "concerns": [], "questions": [], "suggested_next_steps": [], "confidence": 1.0})}
        parsed, warning = GeminiCliClient.parse_agent_response_from_stdout(json.dumps(outer), AgentResponse)
        self.assertEqual(parsed.summary, "ok")
        self.assertIsNone(warning)

    def test_response_code_block_json(self):
        outer = {"response": "```json\n{\"summary\":\"ok\",\"key_points\":[],\"concerns\":[],\"questions\":[],\"suggested_next_steps\":[],\"confidence\":1.0}\n```"}
        parsed, warning = GeminiCliClient.parse_agent_response_from_stdout(json.dumps(outer), AgentResponse)
        self.assertEqual(parsed.summary, "ok")
        self.assertIsNone(warning)

    def test_plain_text_fallback(self):
        parsed, warning = GeminiCliClient.parse_agent_response_from_stdout("안녕하세요", AgentResponse)
        self.assertEqual(warning, "non_json_output")
        self.assertIn("non_json_output", parsed.concerns)

    def test_invalid_json_fallback(self):
        outer = {"response": "{summary:ok,key_points:[],concerns:[],questions:[],suggested_next_steps:[],confidence:1.0}"}
        parsed, warning = GeminiCliClient.parse_agent_response_from_stdout(json.dumps(outer), AgentResponse)
        self.assertEqual(warning, "non_json_output")
        self.assertEqual(parsed.confidence, 0.0)

    def test_warning_prefix_and_brace_in_string(self):
        inner = {"summary": "ok {brace}", "key_points": [], "concerns": [], "questions": [], "suggested_next_steps": [], "confidence": 1.0}
        outer = {"response": json.dumps(inner, ensure_ascii=False)}
        stdout = "warning text\n" + json.dumps(outer, ensure_ascii=False)
        parsed, _ = GeminiCliClient.parse_agent_response_from_stdout(stdout, AgentResponse)
        self.assertEqual(parsed.summary, "ok {brace}")

    def test_mask_email(self):
        masked = GeminiCliClient.mask_email("qhrb9292@gmail.com")
        self.assertTrue(masked.startswith("qhrb"))
        self.assertIn("****@gmail.com", masked)

    def test_preflight_expected_mismatch(self):
        client = GeminiCliClient()
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as td:
            p = Path(td) / ".gemini"
            p.mkdir(parents=True)
            (p / "google_accounts.json").write_text(json.dumps({"active": "a@gmail.com"}), encoding="utf-8")
            r = client.preflight_profile(agent_id="a", gemini_cli_home=td, expected_account="b@gmail.com", working_dir=td)
            self.assertEqual(r.status, "FAILED")

    def test_auth_prompt_detection(self):
        txt = "Opening authentication page in your browser. Do you want to continue? [Y/n]"
        self.assertTrue(any(k.lower() in txt.lower() for k in ["Opening authentication page", "Do you want to continue"]))

    def test_readme_uses_profile_home_not_home(self):
        readme = Path("README.md").read_text(encoding="utf-8")
        self.assertIn("$profileHome", readme)


if __name__ == "__main__":
    unittest.main()
