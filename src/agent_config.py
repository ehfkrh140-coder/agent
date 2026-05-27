from typing import Optional, Literal

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    agent_id: str
    name: str
    provider: Literal["gemini", "gemini_api", "gemini_cli"]
    model: str
    api_key_env: Optional[str] = None
    gemini_cli_home: Optional[str] = None
    cli_command: str = "gemini"
    timeout_seconds: int = Field(default=120, ge=1, le=600)
    system_prompt_path: str
    temperature: float = Field(ge=0.0, le=2.0, default=0.7)
