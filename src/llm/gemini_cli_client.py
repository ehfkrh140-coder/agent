import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Type

from pydantic import BaseModel

AUTH_PROMPT_PATTERNS = ["Opening authentication page", "Do you want to continue"]


@dataclass
class ProfilePreflightResult:
    status: str
    message: str
    active_account_masked: Optional[str] = None
    expected_account_masked: Optional[str] = None


@dataclass
class CliCallResult:
    response: BaseModel
    warning: Optional[str] = None
    stdout_preview: Optional[str] = None
    stderr_preview: Optional[str] = None


class GeminiCliClient:
    def __init__(self, cli_command: str = "gemini.cmd", timeout_seconds: int = 120):
        self.cli_command = cli_command
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _preview(text: str, limit: int = 4000) -> str:
        return (text or "")[:limit]

    @staticmethod
    def mask_email(email: Optional[str]) -> Optional[str]:
        if not email or "@" not in email:
            return None
        local, domain = email.split("@", 1)
        keep = min(4, max(1, len(local)))
        return f"{local[:keep]}****@{domain}"

    def _run_cli_command(self, cmd: list[str], env: dict, cwd: Path, timeout_seconds: int) -> tuple[int, str, str]:
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            cwd=str(cwd),
            shell=False,
            creationflags=creationflags,
        )

        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
            return process.returncode or 0, stdout or "", stderr or ""
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""

            if os.name == "nt":
                try:
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                        stdin=subprocess.DEVNULL,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=10,
                        shell=False,
                    )
                except Exception:
                    pass
            else:
                try:
                    process.kill()
                except Exception:
                    pass

            try:
                s2, e2 = process.communicate(timeout=5)
                stdout = stdout or (s2 or "")
                stderr = stderr or (e2 or "")
            except Exception:
                pass

            raise TimeoutError(
                f"Gemini CLI timed out after {timeout_seconds}s. pid={process.pid} "
                f"stdout_preview={self._preview(stdout)} stderr_preview={self._preview(stderr)}"
            ) from exc

    @staticmethod
    def _extract_first_json_object(text: str) -> str:
        start = text.find("{")
        if start < 0:
            raise ValueError("No JSON object start found")
        depth = 0
        in_string = False
        escape = False
        for idx in range(start, len(text)):
            ch = text[idx]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
            else:
                if ch == '"':
                    in_string = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        return text[start : idx + 1]
        raise ValueError("No complete JSON object found")

    @staticmethod
    def _strip_json_code_block(text: str) -> str:
        m = re.search(r"```json\s*(.*?)\s*```", text or "", flags=re.DOTALL | re.IGNORECASE)
        return m.group(1).strip() if m else (text or "").strip()

    @classmethod
    def _try_parse_json_text(cls, text: str) -> Optional[dict]:
        cleaned = cls._strip_json_code_block(text)
        try:
            return json.loads(cleaned)
        except Exception:
            pass
        try:
            return json.loads(cls._extract_first_json_object(cleaned))
        except Exception:
            return None

    @classmethod
    def parse_agent_response_from_stdout(cls, stdout: str, response_schema: Type[BaseModel]) -> tuple[BaseModel, Optional[str]]:
        warning = None
        response_text = ""
        parsed_inner = None

        try:
            outer = json.loads(cls._extract_first_json_object(stdout))
            response_text = outer.get("response") if isinstance(outer, dict) else ""
            if isinstance(response_text, str) and response_text.strip():
                parsed_inner = cls._try_parse_json_text(response_text)
        except Exception:
            pass

        if parsed_inner is None:
            parsed_inner = cls._try_parse_json_text(stdout)

        if isinstance(parsed_inner, dict):
            try:
                return response_schema.model_validate(parsed_inner), warning
            except Exception:
                pass

        warning = "non_json_output"
        fallback = {
            "summary": (response_text or stdout or "")[:1000],
            "key_points": [],
            "concerns": ["non_json_output"],
            "questions": [],
            "suggested_next_steps": ["프롬프트를 더 엄격하게 하거나 raw_output을 확인하세요."],
            "confidence": 0.0,
        }
        return response_schema.model_validate(fallback), warning

    def _build_env(self, gemini_cli_home: str) -> dict:
        env = os.environ.copy()
        env.update(
            {
                "GEMINI_CLI_HOME": gemini_cli_home,
                "GEMINI_FORCE_ENCRYPTED_FILE_STORAGE": "true",
                "GEMINI_FORCE_FILE_STORAGE": "true",
                "GEMINI_CLI_TRUST_WORKSPACE": "true",
                "NO_COLOR": "1",
                "TERM": "dumb",
            }
        )
        return env

    def preflight_profile(self, *, agent_id: str, gemini_cli_home: str, expected_account: Optional[str], working_dir: Optional[str]) -> ProfilePreflightResult:
        home = Path(gemini_cli_home)
        if not home.exists():
            return ProfilePreflightResult("FAILED", f"home path not found: {gemini_cli_home}")

        accounts_path = home / ".gemini" / "google_accounts.json"
        if not accounts_path.exists():
            return ProfilePreflightResult("FAILED", f"google_accounts.json not found: {accounts_path}")

        try:
            data = json.loads(accounts_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return ProfilePreflightResult("FAILED", f"google_accounts.json read error: {exc}")

        active = data.get("active") if isinstance(data, dict) else None
        if not active:
            return ProfilePreflightResult("FAILED", "active account not found")

        active_masked = self.mask_email(active)
        expected_masked = self.mask_email(expected_account)
        if expected_account and active.lower() != expected_account.lower():
            return ProfilePreflightResult(
                "FAILED",
                f"active account mismatch active={active_masked} expected={expected_masked}",
                active_masked,
                expected_masked,
            )

        return ProfilePreflightResult("OK", f"{agent_id} profile ready", active_masked, expected_masked)

    def healthcheck_profile(self, *, gemini_cli_home: str, working_dir: Optional[str] = None) -> ProfilePreflightResult:
        wd = Path(working_dir) if working_dir else Path.cwd()
        wd.mkdir(parents=True, exist_ok=True)
        cmd = [self.cli_command, "--skip-trust", "-p", '{"summary":"ping"}', "--output-format", "json"]
        try:
            code, stdout, stderr = self._run_cli_command(
                cmd=cmd,
                env=self._build_env(gemini_cli_home),
                cwd=wd,
                timeout_seconds=20,
            )
        except TimeoutError:
            return ProfilePreflightResult("FAILED", "healthcheck timeout")

        combined = (stdout or "") + "\n" + (stderr or "")
        if any(p.lower() in combined.lower() for p in AUTH_PROMPT_PATTERNS):
            return ProfilePreflightResult("AUTH_REQUIRED", "interactive auth prompt detected")
        if code != 0:
            return ProfilePreflightResult("FAILED", f"healthcheck failed code={code}")
        return ProfilePreflightResult("OK", "healthcheck ok")

    def generate_structured(
        self,
        *,
        prompt: str,
        response_schema: Type[BaseModel],
        gemini_cli_home: str,
        working_dir: Optional[str] = None,
    ) -> CliCallResult:
        wd = Path(working_dir) if working_dir else Path.cwd()
        wd.mkdir(parents=True, exist_ok=True)
        cmd = [self.cli_command, "--skip-trust", "-p", prompt, "--output-format", "json"]

        returncode, stdout, stderr = self._run_cli_command(
            cmd=cmd,
            env=self._build_env(gemini_cli_home),
            cwd=wd,
            timeout_seconds=self.timeout_seconds,
        )

        out_prev = self._preview(stdout)
        err_prev = self._preview(stderr)

        if returncode != 0:
            raise RuntimeError(f"Gemini CLI failed with code {returncode}. stderr={err_prev}")

        response, warning = self.parse_agent_response_from_stdout(stdout, response_schema)
        return CliCallResult(response=response, warning=warning, stdout_preview=out_prev, stderr_preview=err_prev)
