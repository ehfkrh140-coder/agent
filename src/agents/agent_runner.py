from src.agent_config import AgentConfig
from src.agents.agent_registry import build_agent
from src.schemas.session_record import AgentRunResult


class AgentRunner:
    def __init__(self, agent_configs: list[AgentConfig]):
        self.agent_configs = agent_configs

    def run_all(self, user_message: str) -> list[AgentRunResult]:
        results: list[AgentRunResult] = []
        print("=== Gemini CLI Profile Preflight ===")

        for config in self.agent_configs:
            print(f"Running {config.agent_id} ({config.name})...")
            try:
                agent = build_agent(config)

                preflight = agent.preflight() if hasattr(agent, "preflight") else None
                if preflight is not None:
                    status = preflight.status
                    if status == "OK":
                        print(f"{config.agent_id} preflight OK active={preflight.active_account_masked}")
                    else:
                        raise RuntimeError(f"preflight {status}: {preflight.message}")

                print(
                    f"{config.agent_id} run command: {config.cli_command} --skip-trust -p <prompt omitted> --output-format json"
                )
                print(f"home={config.gemini_cli_home}")
                print(f"cwd={config.working_dir}")
                print(f"timeout={config.timeout_seconds}")

                run_output = agent.run(user_message)
                response = run_output.response if hasattr(run_output, "response") else run_output
                warning = getattr(run_output, "warning", None)
                stdout_preview = getattr(run_output, "stdout_preview", None)
                stderr_preview = getattr(run_output, "stderr_preview", None)

                print(f"{config.agent_id} success")
                results.append(
                    AgentRunResult(
                        agent_id=config.agent_id,
                        name=config.name,
                        status="success",
                        model=getattr(config, "model", "gemini-cli"),
                        provider=config.provider,
                        response=response,
                        warning=warning,
                        stdout_preview=stdout_preview,
                        stderr_preview=stderr_preview,
                        active_account_masked=getattr(preflight, "active_account_masked", None) if preflight else None,
                        expected_account_masked=getattr(preflight, "expected_account_masked", None) if preflight else None,
                        gemini_cli_home=getattr(config, "gemini_cli_home", None),
                        preflight_status=getattr(preflight, "status", None) if preflight else None,
                    )
                )
            except Exception as exc:
                print(f"{config.agent_id} failed: {exc}")
                results.append(
                    AgentRunResult(
                        agent_id=config.agent_id,
                        name=config.name,
                        status="failed",
                        model=getattr(config, "model", "gemini-cli"),
                        provider=config.provider,
                        error=str(exc),
                        gemini_cli_home=getattr(config, "gemini_cli_home", None),
                    )
                )

        return results
