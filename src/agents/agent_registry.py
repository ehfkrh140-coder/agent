import os

from src.agent_config import AgentConfig
from src.agents.generic_gemini_agent import GenericGeminiAgent


def build_agent(config: AgentConfig) -> GenericGeminiAgent:
    api_key = None
    if config.provider in {"gemini", "gemini_api"}:
        if not config.api_key_env:
            raise ValueError(f"api_key_env is required for gemini/gemini_api provider: {config.agent_id}")
        api_key = os.getenv(config.api_key_env, "").strip()
        if not api_key:
            raise ValueError(
                f"API key missing for agent {config.agent_id}. Set environment variable: {config.api_key_env}"
            )

    if config.provider == "gemini_cli" and not config.gemini_cli_home:
        raise ValueError(f"gemini_cli_home is required for gemini_cli provider: {config.agent_id}")

    return GenericGeminiAgent(config=config, api_key=api_key)
