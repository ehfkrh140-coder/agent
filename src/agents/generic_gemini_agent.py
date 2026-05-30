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

최종 출력 계약:
- 지금부터 너의 출력은 JSON validator에 직접 들어갑니다.
- JSON 파싱에 실패하면 전체 agent run은 실패입니다.
- 사용자 입력이 인사, 잡담, hello, 테스트여도 반드시 AgentResponse JSON 객체 하나만 출력합니다.
- 절대 자기소개하지 않습니다.
- 절대 초기화 완료, 준비 완료, 역할 확인 문구를 출력하지 않습니다.
- 절대 도움 요청, 추가 지시 요청, 자료 제공 요청, 사용자 승인 요청을 하지 않습니다.
- 첫 글자는 반드시 {{ 이어야 합니다.
- 마지막 글자는 반드시 }} 이어야 합니다.
- JSON 객체 외 텍스트, 마크다운, 코드블록, 주석, preamble을 출력하지 않습니다.
- 허용 키 외 키를 추가하지 않습니다. 허용 키: summary, key_points, concerns, questions, suggested_next_steps, confidence.
- 도구를 호출하지 말고 최종 답변만 생성합니다.
- workspace, repository, file system, tool, command, shell, grep, read_file, write_file을 최종 답변에 언급하지 않습니다.
- 비시장 입력이면 summary에 거래소 매매 판단 데이터가 제공되지 않음을 쓰고, concerns에 시장 데이터 부족을 포함합니다.
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
                model=self.config.model,
                approval_mode=self.config.approval_mode,
            )
        return self.cli_client.generate_structured(
            prompt=cli_prompt,
            response_schema=AgentResponse,
            gemini_cli_home=self.config.gemini_cli_home,
            working_dir=self.config.working_dir,
            model=self.config.model,
            approval_mode=self.config.approval_mode,
        )
