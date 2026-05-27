from pathlib import Path

from src.agent_config import AgentConfig
from src.llm.gemini_client import GeminiClient
from src.schemas.agent_response import AgentResponse


class GenericGeminiAgent:
    def __init__(self, config: AgentConfig, api_key: str):
        if config.provider.lower() != "gemini":
            raise ValueError(f"Unsupported provider: {config.provider}")

        self.config = config
        self.client = GeminiClient(
            api_key=api_key,
            model=config.model,
            temperature=config.temperature,
        )

    def _load_system_prompt(self) -> str:
        path = Path(self.config.system_prompt_path)
        if not path.exists():
            raise FileNotFoundError(
                f"System prompt file not found for agent {self.config.agent_id}: {path}"
            )
        return path.read_text(encoding="utf-8").strip()

    def run(self, user_message: str) -> AgentResponse:
        system_prompt = self._load_system_prompt()
        return self.client.generate_structured(
            system_prompt=system_prompt,
            user_message=user_message,
            response_schema=AgentResponse,
        )
