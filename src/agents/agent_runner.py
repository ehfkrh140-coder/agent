import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.agent_config import AgentConfig
from src.agents.agent_registry import build_agent
from src.schemas.session_record import AgentRunResult

RATE_429_PATTERNS = ["429", "rateLimitExceeded", "No capacity available"]
AUTH_PROMPT_PATTERNS = ["Opening authentication page", "Do you want to continue", "AUTH_REQUIRED"]


def _contains_any(text: str, patterns: list[str]) -> bool:
    lowered = (text or "").lower()
    return any(pattern.lower() in lowered for pattern in patterns)


class AgentRunner:
    def __init__(self, agent_configs: list[AgentConfig]):
        self.agent_configs = agent_configs

    @staticmethod
    def detect_rate_429(text: str) -> bool:
        return _contains_any(text, RATE_429_PATTERNS)

    @staticmethod
    def detect_auth_prompt(text: str) -> bool:
        return _contains_any(text, AUTH_PROMPT_PATTERNS)

    @staticmethod
    def detect_timeout(text: str) -> bool:
        return "timed out" in (text or "").lower()

    def _run_one(self, config: AgentConfig) -> AgentRunResult:
        started = time.perf_counter()
        preflight = None
        try:
            print(f"Running {config.agent_id} ({config.name})...")
            agent = build_agent(config)

            preflight = agent.preflight() if hasattr(agent, "preflight") else None
            if preflight is not None:
                status = preflight.status
                if status == "OK":
                    print(f"{config.agent_id} preflight OK active={preflight.active_account_masked}")
                else:
                    raise RuntimeError(f"preflight {status}: {preflight.message}")

            print(f"{config.agent_id} run_mode={config.run_mode}. If Gemini asks 'Do you want to continue?', type Y.")
            print(
                f"{config.agent_id} run command: {config.cli_command} --skip-trust -p <prompt omitted> --output-format json"
            )
            print(f"home={config.gemini_cli_home}")
            print(f"cwd={config.working_dir}")
            print(f"timeout={config.timeout_seconds}")

            run_output = agent.run(user_message=self._user_message)
            response = run_output.response if hasattr(run_output, "response") else run_output
            warning = getattr(run_output, "warning", None)
            stdout_preview = getattr(run_output, "stdout_preview", None)
            stderr_preview = getattr(run_output, "stderr_preview", None)
            cli_session_id = getattr(run_output, "cli_session_id", None)
            combined = "\n".join([stdout_preview or "", stderr_preview or "", warning or ""])
            elapsed_seconds = round(time.perf_counter() - started, 3)

            print(f"{config.agent_id} success")
            return AgentRunResult(
                agent_id=config.agent_id,
                name=config.name,
                status="success",
                model=config.model or "gemini-cli",
                provider=config.provider,
                response=response,
                warning=warning,
                stdout_preview=stdout_preview,
                stderr_preview=stderr_preview,
                active_account_masked=getattr(preflight, "active_account_masked", None) if preflight else None,
                expected_account_masked=getattr(preflight, "expected_account_masked", None) if preflight else None,
                gemini_cli_home=getattr(config, "gemini_cli_home", None),
                preflight_status=getattr(preflight, "status", None) if preflight else None,
                elapsed_seconds=elapsed_seconds,
                rate_429_detected=self.detect_rate_429(combined),
                auth_prompt_detected=self.detect_auth_prompt(combined),
                timed_out=self.detect_timeout(combined),
                cli_session_id=cli_session_id,
            )
        except Exception as exc:
            msg = str(exc)
            if "AUTH_REQUIRED" in msg:
                msg = f"AUTH_REQUIRED: run python tools/auth_warmup.py --agent {config.agent_id} --repair-login"
            elapsed_seconds = round(time.perf_counter() - started, 3)
            print(f"{config.agent_id} failed: {msg}")
            return AgentRunResult(
                agent_id=config.agent_id,
                name=config.name,
                status="failed",
                model=config.model or "gemini-cli",
                provider=config.provider,
                error=msg,
                gemini_cli_home=getattr(config, "gemini_cli_home", None),
                preflight_status=getattr(preflight, "status", None) if preflight else None,
                elapsed_seconds=elapsed_seconds,
                rate_429_detected=self.detect_rate_429(msg),
                auth_prompt_detected=self.detect_auth_prompt(msg),
                timed_out=isinstance(exc, TimeoutError) or self.detect_timeout(msg),
            )

    def run_all(self, user_message: str, parallel: bool = False, max_workers: int = 2) -> list[AgentRunResult]:
        print("=== Gemini CLI Profile Preflight ===")
        self._user_message = user_message
        if not parallel:
            return [self._run_one(config) for config in self.agent_configs]

        max_workers = max(1, max_workers)
        ordered_results: list[AgentRunResult | None] = [None] * len(self.agent_configs)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._run_one, config): index
                for index, config in enumerate(self.agent_configs)
            }
            for future in as_completed(futures):
                index = futures[future]
                try:
                    ordered_results[index] = future.result()
                except Exception as exc:
                    config = self.agent_configs[index]
                    msg = str(exc)
                    ordered_results[index] = AgentRunResult(
                        agent_id=config.agent_id,
                        name=config.name,
                        status="failed",
                        model=config.model or "gemini-cli",
                        provider=config.provider,
                        error=msg,
                        gemini_cli_home=getattr(config, "gemini_cli_home", None),
                        elapsed_seconds=0.0,
                        rate_429_detected=self.detect_rate_429(msg),
                        auth_prompt_detected=self.detect_auth_prompt(msg),
                        timed_out=isinstance(exc, TimeoutError) or self.detect_timeout(msg),
                    )
        return [result for result in ordered_results if result is not None]
