from src.agent_config import AgentConfig
from src.agents.agent_registry import build_agent
from src.schemas.session_record import AgentRunResult


class AgentRunner:
    def __init__(self, agent_configs: list[AgentConfig]):
        self.agent_configs = agent_configs

    def run_all(self, user_message: str) -> list[AgentRunResult]:
        results: list[AgentRunResult] = []

        for config in self.agent_configs:
            try:
                agent = build_agent(config)
                response = agent.run(user_message)
                results.append(
                    AgentRunResult(
                        agent_id=config.agent_id,
                        name=config.name,
                        status="success",
                        model=config.model,
                        provider=config.provider,
                        response=response,
                    )
                )
            except Exception as exc:  # keep full run alive
                results.append(
                    AgentRunResult(
                        agent_id=config.agent_id,
                        name=config.name,
                        status="failed",
                        model=config.model,
                        provider=config.provider,
                        error=str(exc),
                    )
                )

        return results
