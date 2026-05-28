from pathlib import Path

from src.agent_config import AgentConfig
from src.llm.gemini_cli_client import CliCallResult, GeminiCliClient, ProfilePreflightResult
from src.schemas.agent_response import AgentResponse


class GenericGeminiAgent:
    def __init__(self, config: AgentConfig):
        if config.provider != "gemini_cli":
            raise ValueError(f"Unsupported provider: {config.provider}. This runtime supports gemini_cli only.")
        self.config = config
        self.cli_client = GeminiCliClient(
            cli_command=config.cli_command,
            timeout_seconds=config.timeout_seconds,
        )

    def preflight(self) -> ProfilePreflightResult | None:
        if self.config.provider != "gemini_cli":
            return None
        return self.cli_client.preflight_profile(
            agent_id=self.config.agent_id,
            gemini_cli_home=self.config.gemini_cli_home,
            expected_account=self.config.expected_account,
            working_dir=self.config.working_dir,
        )

    def _load_system_prompt(self) -> str:
        path = Path(self.config.system_prompt_path)
        if not path.exists():
            raise FileNotFoundError(f"System prompt file not found for agent {self.config.agent_id}: {path}")
        return path.read_text(encoding="utf-8").strip()

    @staticmethod
    def _build_cli_prompt(system_prompt: str, user_message: str) -> str:
        return f"""{system_prompt}

최우선 규칙:
- 사용자 메시지에만 답하세요.
- 프로젝트 파일을 읽거나 분석하지 마세요.
- 도구 사용을 시도하지 마세요.
- 마크다운을 출력하지 마세요.
- 코드블록을 출력하지 마세요.
- 아래 JSON 객체 스키마 형태의 순수 JSON만 출력하세요.

출력 예시:
{{
  "summary": "string",
  "key_points": ["string"],
  "concerns": ["string"],
  "questions": ["string"],
  "suggested_next_steps": ["string"],
  "confidence": 0.0
}}

사용자 메시지:
{user_message}
"""

    def run(self, user_message: str) -> AgentResponse | CliCallResult:
        system_prompt = self._load_system_prompt()

        cli_prompt = self._build_cli_prompt(system_prompt, user_message)
        if self.config.run_mode == "interactive_file":
            return self.cli_client.generate_structured_interactive_file(
                prompt=cli_prompt,
                response_schema=AgentResponse,
                gemini_cli_home=self.config.gemini_cli_home,
                working_dir=self.config.working_dir,
                output_dir=self.config.output_dir,
                agent_id=self.config.agent_id,
            )
        return self.cli_client.generate_structured(
            prompt=cli_prompt,
            response_schema=AgentResponse,
            gemini_cli_home=self.config.gemini_cli_home,
            working_dir=self.config.working_dir,
        )
