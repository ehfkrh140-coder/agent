import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Type

from pydantic import BaseModel

from src.schemas.agent_response import AgentResponse
from src.validators.response_safety import add_warnings_to_concerns, validate_agent_response_safety

AUTH_PROMPT_PATTERNS = [
    "Opening authentication page",
    "Do you want to continue",
    "Authentication cancelled by user",
    "FatalCancellationError",
]


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
    cli_session_id: Optional[str] = None


class GeminiCliClient:
    def __init__(self, cli_command: str = "gemini.cmd", timeout_seconds: int = 120):
        self.cli_command = cli_command
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def default_policy_path() -> Path:
        return Path(__file__).resolve().parents[2] / "configs" / "gemini_cli_targeted_policy.toml"

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

    @staticmethod
    def _detect_auth_required(text: str) -> bool:
        t = (text or "").lower()
        return any(p.lower() in t for p in AUTH_PROMPT_PATTERNS)

    def _run_cli_command(self, cmd: list[str], env: dict, cwd: Path, timeout_seconds: int, input_text: Optional[str] = None) -> tuple[int, str, str]:
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
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
            stdout, stderr = process.communicate(input=input_text, timeout=timeout_seconds)
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


    @classmethod
    def extract_cli_session_id(cls, stdout: str) -> Optional[str]:
        try:
            outer = json.loads(cls._extract_first_json_object(stdout or ""))
        except Exception:
            return None
        if not isinstance(outer, dict):
            return None
        session_id = outer.get("session_id")
        return str(session_id) if session_id else None

    @classmethod
    def extract_tool_total_calls(cls, stdout: str) -> Optional[int]:
        try:
            outer = json.loads(cls._extract_first_json_object(stdout or ""))
        except Exception:
            return None
        if not isinstance(outer, dict):
            return None
        stats = outer.get("stats")
        tools = stats.get("tools") if isinstance(stats, dict) else None
        total_calls = tools.get("totalCalls") if isinstance(tools, dict) else None
        try:
            return int(total_calls)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _combine_warnings(*warnings: Optional[str]) -> Optional[str]:
        parts: list[str] = []
        for warning in warnings:
            if not warning:
                continue
            for item in str(warning).split(","):
                item = item.strip()
                if item and item not in parts:
                    parts.append(item)
        return ",".join(parts) if parts else None

    @staticmethod
    def _extract_user_message_from_prompt(prompt: str) -> str:
        marker = "사용자 메시지:\n"
        tail_marker = "\n\n최종 출력 계약:"
        if marker not in (prompt or ""):
            return prompt or ""
        user_part = (prompt or "").split(marker, 1)[1]
        if tail_marker in user_part:
            user_part = user_part.split(tail_marker, 1)[0]
        return user_part.strip()

    def _postprocess_response(self, *, response: BaseModel, warning: Optional[str], stdout: str, prompt: str) -> tuple[BaseModel, Optional[str]]:
        extra_warnings: list[str] = []
        total_calls = self.extract_tool_total_calls(stdout)
        if total_calls is not None and total_calls > 0:
            extra_warnings.append("tool_calls_detected")
        if isinstance(response, AgentResponse):
            safety_warnings = validate_agent_response_safety(response, self._extract_user_message_from_prompt(prompt))
            if safety_warnings:
                add_warnings_to_concerns(response, safety_warnings)
                extra_warnings.extend(safety_warnings)
        return response, self._combine_warnings(warning, ",".join(extra_warnings))

    def _build_generate_command(self, prompt: str = "", model: Optional[str] = None, approval_mode: str = "plan", policy_path: Optional[str] = None) -> list[str]:
        resolved_policy = Path(policy_path).resolve() if policy_path else self.default_policy_path().resolve()
        cmd = [
            self.cli_command,
            "--skip-trust",
            "--approval-mode",
            approval_mode,
            "--policy",
            str(resolved_policy),
            "-o",
            "json",
        ]
        if model:
            cmd.extend(["--model", model])
        return cmd

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
            return ProfilePreflightResult("FAILED", f"active account mismatch active={active_masked} expected={expected_masked}", active_masked, expected_masked)
        return ProfilePreflightResult("OK", f"{agent_id} profile ready", active_masked, expected_masked)

    def healthcheck_profile(self, *, gemini_cli_home: str, working_dir: Optional[str] = None) -> ProfilePreflightResult:
        wd = Path(working_dir) if working_dir else Path.cwd()
        wd.mkdir(parents=True, exist_ok=True)
        cmd = self._build_generate_command(model="flash")
        try:
            code, stdout, stderr = self._run_cli_command(cmd=cmd, env=self._build_env(gemini_cli_home), cwd=wd, timeout_seconds=20, input_text='{"summary":"ping"}')
        except TimeoutError:
            return ProfilePreflightResult("FAILED", "healthcheck timeout")
        combined = (stdout or "") + "\n" + (stderr or "")
        if self._detect_auth_required(combined):
            return ProfilePreflightResult("AUTH_REQUIRED", "interactive auth prompt detected")
        if code != 0:
            return ProfilePreflightResult("FAILED", f"healthcheck failed code={code}")
        return ProfilePreflightResult("OK", "healthcheck ok")

    def generate_structured_interactive_file(self, *, prompt: str, response_schema: Type[BaseModel], gemini_cli_home: str, working_dir: Optional[str] = None, output_dir: Optional[str] = None, agent_id: str = "agent", model: Optional[str] = None, approval_mode: str = "plan", policy_path: Optional[str] = None) -> CliCallResult:
        wd = Path(working_dir) if working_dir else Path.cwd()
        wd.mkdir(parents=True, exist_ok=True)
        out_dir = Path(output_dir) if output_dir else (wd / "outputs")
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = out_dir / f"{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        cmd = self._build_generate_command(prompt, model=model, approval_mode=approval_mode, policy_path=policy_path)
        returncode, stdout, stderr = self._run_cli_command(
            cmd=cmd,
            env=self._build_env(gemini_cli_home),
            cwd=wd,
            timeout_seconds=max(self.timeout_seconds, 300),
            input_text=prompt,
        )

        if self._detect_auth_required((stdout or "") + "\n" + (stderr or "")):
            raise RuntimeError(f"AUTH_REQUIRED: run python tools/auth_warmup.py --agent {agent_id} first.")
        if returncode != 0:
            raise RuntimeError(f"Gemini CLI failed with code {returncode}. stderr={self._preview(stderr)}")

        output_path.write_text(stdout or "", encoding="utf-8")
        if not (stdout or "").strip():
            raise RuntimeError(f"Interactive output file empty: {output_path}")

        response, warning = self.parse_agent_response_from_stdout(stdout or "", response_schema)
        response, warning = self._postprocess_response(response=response, warning=warning, stdout=stdout or "", prompt=prompt)
        return CliCallResult(
            response=response,
            warning=warning,
            stdout_preview=self._preview(stdout),
            stderr_preview=self._preview(stderr),
            cli_session_id=self.extract_cli_session_id(stdout),
        )

    def generate_structured(self, *, prompt: str, response_schema: Type[BaseModel], gemini_cli_home: str, working_dir: Optional[str] = None, model: Optional[str] = None, approval_mode: str = "plan", policy_path: Optional[str] = None) -> CliCallResult:
        wd = Path(working_dir) if working_dir else Path.cwd()
        wd.mkdir(parents=True, exist_ok=True)
        cmd = self._build_generate_command(prompt, model=model, approval_mode=approval_mode, policy_path=policy_path)
        returncode, stdout, stderr = self._run_cli_command(cmd=cmd, env=self._build_env(gemini_cli_home), cwd=wd, timeout_seconds=self.timeout_seconds, input_text=prompt)

        if self._detect_auth_required((stdout or "") + "\n" + (stderr or "")):
            raise RuntimeError("AUTH_REQUIRED: run python tools/auth_warmup.py --agent agent_XX first.")

        out_prev = self._preview(stdout)
        err_prev = self._preview(stderr)
        if returncode != 0:
            raise RuntimeError(f"Gemini CLI failed with code {returncode}. stderr={err_prev}")
        response, warning = self.parse_agent_response_from_stdout(stdout, response_schema)
        response, warning = self._postprocess_response(response=response, warning=warning, stdout=stdout, prompt=prompt)
        return CliCallResult(
            response=response,
            warning=warning,
            stdout_preview=out_prev,
            stderr_preview=err_prev,
            cli_session_id=self.extract_cli_session_id(stdout),
        )
