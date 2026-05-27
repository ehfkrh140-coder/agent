from typing import Optional

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    agent_id: str
    name: str
    provider: str = "gemini_cli"
    gemini_cli_home: str
    cli_command: str = "gemini.cmd"
    timeout_seconds: int = Field(default=120, ge=1, le=600)
    working_dir: Optional[str] = None
    expected_account: Optional[str] = None
    system_prompt_path: str
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    run_mode: str = "interactive_file"
    output_dir: Optional[str] = None
