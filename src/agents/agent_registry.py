from src.agent_config import AgentConfig
from src.agents.generic_gemini_agent import GenericGeminiAgent


def build_agent(config: AgentConfig) -> GenericGeminiAgent:
    if config.provider != "gemini_cli":
        raise ValueError(
            f"Unsupported provider for this runtime: {config.provider}. Use provider=gemini_cli"
        )
    if not config.gemini_cli_home:
        raise ValueError(f"gemini_cli_home is required for gemini_cli provider: {config.agent_id}")
    return GenericGeminiAgent(config=config)
