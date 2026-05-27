import json
import subprocess
import sys
import unittest
from pathlib import Path
import types
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

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
            proc = MagicMock()
            proc.pid = 777
            proc.communicate.side_effect = [subprocess.TimeoutExpired(cmd=["gemini.cmd"], timeout=1, output="out", stderr="err"), ("", "")]
            with patch("subprocess.Popen", return_value=proc), patch("os.name", "posix"):
                with self.assertRaises(TimeoutError):
                    client.generate_structured(
                        prompt='{"summary":"ok"}',
                        response_schema=AgentResponse,
                        gemini_cli_home=td,
                        working_dir=td,
                    )


    def test_run_cli_command_timeout_converts_to_timeouterror(self):
        client = GeminiCliClient(timeout_seconds=30)
        proc = MagicMock()
        proc.pid = 1234
        proc.communicate.side_effect = [subprocess.TimeoutExpired(cmd=["gemini.cmd"], timeout=30, output="out", stderr="err"), ("", "")]

        with patch("subprocess.Popen", return_value=proc), patch("os.name", "posix"):
            with self.assertRaises(TimeoutError) as cm:
                client._run_cli_command(["gemini.cmd"], env={}, cwd=Path.cwd(), timeout_seconds=30)
            msg = str(cm.exception)
            self.assertIn("stdout_preview=out", msg)
            self.assertIn("stderr_preview=err", msg)
            self.assertIn("timed out", msg)

    def test_run_cli_command_windows_calls_taskkill_and_second_communicate_timeout5(self):
        client = GeminiCliClient(timeout_seconds=30)
        proc = MagicMock()
        proc.pid = 555
        first_exc = subprocess.TimeoutExpired(cmd=["gemini.cmd"], timeout=30, output="", stderr="")
        proc.communicate.side_effect = [first_exc, ("", "")]

        with patch("subprocess.Popen", return_value=proc), patch("os.name", "nt"), patch("subprocess.run") as mock_run:
            with self.assertRaises(TimeoutError):
                client._run_cli_command(["gemini.cmd"], env={}, cwd=Path.cwd(), timeout_seconds=30)
            mock_run.assert_called()
            args = mock_run.call_args[0][0]
            self.assertEqual(args[:3], ["taskkill", "/F", "/T"])
            # first timeout call + second collect call with 5s
            self.assertEqual(proc.communicate.call_args_list[1].kwargs.get("timeout"), 5)


    def test_auth_required_opening_page_detect(self):
        self.assertTrue(GeminiCliClient._detect_auth_required("Opening authentication page in your browser"))

    def test_auth_required_cancelled_detect(self):
        self.assertTrue(GeminiCliClient._detect_auth_required("Authentication cancelled by user"))

    def test_auth_required_fatal_cancel_detect(self):
        self.assertTrue(GeminiCliClient._detect_auth_required("FatalCancellationError"))


    def test_auth_warmup_help_runs(self):
        completed = subprocess.run([sys.executable, "tools/auth_warmup.py", "--help"], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0)

    def test_auth_warmup_login_only_cmd_shape(self):
        import tools.auth_warmup as aw

        cfg = types.SimpleNamespace(
            agent_id="agent_01",
            gemini_cli_home="C:/tmp/home",
            working_dir=".",
            expected_account="a@gmail.com",
            cli_command="gemini.cmd",
            timeout_seconds=30,
        )

        with patch("tools.auth_warmup.read_active_masked", return_value="a***@gmail.com"), patch("tools.auth_warmup.subprocess.run") as m:
            m.return_value.returncode = 0
            ok = aw.login_only_for_agent(cfg)
            self.assertTrue(ok)
            self.assertEqual(m.call_args[0][0], ["gemini.cmd"])

    def test_auth_warmup_verify_cmd_shape(self):
        import tools.auth_warmup as aw

        cfg = types.SimpleNamespace(
            agent_id="agent_01",
            gemini_cli_home="C:/tmp/home",
            working_dir=".",
            expected_account="a@gmail.com",
            cli_command="gemini.cmd",
            timeout_seconds=30,
        )

        with patch("src.llm.gemini_cli_client.GeminiCliClient._run_cli_command", return_value=(0, "{}", "")) as m:
            aw.verify_for_agent(cfg)
            cmd = m.call_args.kwargs["cmd"]
            self.assertEqual(cmd[0], "gemini.cmd")
            self.assertIn("--skip-trust", cmd)
            self.assertIn("--output-format", cmd)


    def test_interactive_file_uses_direct_gemini_cmd(self):
        client = GeminiCliClient(cli_command="gemini.cmd", timeout_seconds=30)
        with TemporaryDirectory() as td:
            out_dir = Path(td) / "out"
            out_dir.mkdir(parents=True, exist_ok=True)

            payload = {
                "summary": "ok",
                "key_points": [],
                "concerns": [],
                "questions": [],
                "suggested_next_steps": [],
                "confidence": 1.0,
            }
            stdout_wrapper = json.dumps({"response": json.dumps(payload)})

            def fake_run(cmd, env, cwd, timeout_seconds):
                self.assertEqual(cmd[0], "gemini.cmd")
                self.assertNotIn("powershell.exe", " ".join(cmd).lower())
                self.assertNotIn("tee-object", " ".join(cmd).lower())
                return 0, stdout_wrapper, ""

            with patch.object(client, "_run_cli_command", side_effect=fake_run):
                res = client.generate_structured_interactive_file(
                    prompt="x",
                    response_schema=AgentResponse,
                    gemini_cli_home=td,
                    working_dir=td,
                    output_dir=str(out_dir),
                    agent_id="agent_01",
                )
                self.assertEqual(res.response.summary, "ok")

    def test_interactive_file_missing_output_fails(self):
        client = GeminiCliClient(cli_command="gemini.cmd", timeout_seconds=30)
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as td:
            out_dir = Path(td) / "out"
            out_dir.mkdir(parents=True, exist_ok=True)
            with patch.object(client, "_run_cli_command", return_value=(0, "", "")):
                with self.assertRaises(RuntimeError):
                    client.generate_structured_interactive_file(
                        prompt="x",
                        response_schema=AgentResponse,
                        gemini_cli_home=td,
                        working_dir=td,
                        output_dir=str(out_dir),
                        agent_id="agent_01",
                    )

    def test_readme_uses_profile_home_not_home(self):
        readme = Path("README.md").read_text(encoding="utf-8")
        self.assertIn("$profileHome", readme)


if __name__ == "__main__":
    unittest.main()
