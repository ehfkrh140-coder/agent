import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

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

    def test_preflight_ok_and_no_subprocess(self):
        client = GeminiCliClient()
        with TemporaryDirectory() as td:
            g = Path(td) / ".gemini"
            g.mkdir(parents=True)
            (g / "google_accounts.json").write_text(json.dumps({"active": "a@gmail.com"}), encoding="utf-8")
            with patch("subprocess.run") as mocked:
                r = client.preflight_profile(agent_id="a1", gemini_cli_home=td, expected_account="a@gmail.com", working_dir=td)
                self.assertEqual(r.status, "OK")
                mocked.assert_not_called()

    def test_preflight_failed_mismatch(self):
        client = GeminiCliClient()
        with TemporaryDirectory() as td:
            g = Path(td) / ".gemini"
            g.mkdir(parents=True)
            (g / "google_accounts.json").write_text(json.dumps({"active": "a@gmail.com"}), encoding="utf-8")
            r = client.preflight_profile(agent_id="a1", gemini_cli_home=td, expected_account="b@gmail.com", working_dir=td)
            self.assertEqual(r.status, "FAILED")

    def test_preflight_failed_missing_file(self):
        client = GeminiCliClient()
        with TemporaryDirectory() as td:
            r = client.preflight_profile(agent_id="a1", gemini_cli_home=td, expected_account=None, working_dir=td)
            self.assertEqual(r.status, "FAILED")

    def test_healthcheck_method_exists(self):
        client = GeminiCliClient()
        self.assertTrue(hasattr(client, "healthcheck_profile"))


    def test_generate_structured_timeout_raises_timeouterror(self):
        client = GeminiCliClient(timeout_seconds=1)
        with TemporaryDirectory() as td:
            g = Path(td) / ".gemini"
            g.mkdir(parents=True)
            (g / "google_accounts.json").write_text(json.dumps({"active": "a@gmail.com"}), encoding="utf-8")
            with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["gemini.cmd"], timeout=1, output="out", stderr="err")):
                with self.assertRaises(TimeoutError):
                    client.generate_structured(
                        prompt='{"summary":"ok"}',
                        response_schema=AgentResponse,
                        gemini_cli_home=td,
                        working_dir=td,
                    )

    def test_readme_uses_profile_home_not_home(self):
        readme = Path("README.md").read_text(encoding="utf-8")
        self.assertIn("$profileHome", readme)


if __name__ == "__main__":
    unittest.main()
