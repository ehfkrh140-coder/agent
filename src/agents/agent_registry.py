import os

from src.agent_config import AgentConfig
from src.agents.generic_gemini_agent import GenericGeminiAgent


def build_agent(config: AgentConfig) -> GenericGeminiAgent:
    api_key = os.getenv(config.api_key_env, "").strip()
    if not api_key:
        raise ValueError(
            f"API key missing for agent {config.agent_id}. Set environment variable: {config.api_key_env}"
        )
    return GenericGeminiAgent(config=config, api_key=api_key)
