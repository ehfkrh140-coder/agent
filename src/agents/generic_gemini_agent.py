from pathlib import Path

from src.agent_config import AgentConfig
from src.llm.gemini_cli_client import GeminiCliClient
from src.llm.gemini_client import GeminiClient
from src.schemas.agent_response import AgentResponse


class GenericGeminiAgent:
    def __init__(self, config: AgentConfig, api_key: str | None = None):
        self.config = config
        self.api_client = None
        self.cli_client = None

        if config.provider == "gemini_cli":
            self.cli_client = GeminiCliClient(
                cli_command=config.cli_command,
                timeout_seconds=config.timeout_seconds,
            )
        elif config.provider in {"gemini", "gemini_api"}:
            if not api_key:
                raise ValueError("api_key is required for gemini/gemini_api provider")
            self.api_client = GeminiClient(
                api_key=api_key,
                model=config.model,
                temperature=config.temperature,
            )
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")

    def _load_system_prompt(self) -> str:
        path = Path(self.config.system_prompt_path)
        if not path.exists():
            raise FileNotFoundError(
                f"System prompt file not found for agent {self.config.agent_id}: {path}"
            )
        return path.read_text(encoding="utf-8").strip()

    @staticmethod
    def _build_cli_prompt(system_prompt: str, user_message: str) -> str:
        return (
            f"{system_prompt}\n\n"
            "아래 사용자 메시지를 분석하세요.\n"
            "반드시 AgentResponse JSON schema 형식의 순수 JSON 객체만 출력하세요.\n"
            "다른 설명, 마크다운, 코드블록을 절대 추가하지 마세요.\n\n"
            f"사용자 메시지:\n{user_message}"
        )

    def run(self, user_message: str) -> AgentResponse:
        system_prompt = self._load_system_prompt()

        if self.config.provider == "gemini_cli":
            cli_prompt = self._build_cli_prompt(system_prompt, user_message)
            return self.cli_client.generate_structured(
                prompt=cli_prompt,
                response_schema=AgentResponse,
                gemini_cli_home=self.config.gemini_cli_home or "",
            )

        return self.api_client.generate_structured(
            system_prompt=system_prompt,
            user_message=user_message,
            response_schema=AgentResponse,
        )
