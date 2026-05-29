from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.schemas.agent_response import AgentResponse


class AgentRunResult(BaseModel):
    agent_id: str
    name: str
    status: str
    model: str
    provider: str
    response: Optional[AgentResponse] = None
    error: Optional[str] = None
    warning: Optional[str] = None
    stderr_preview: Optional[str] = None
    stdout_preview: Optional[str] = None
    active_account_masked: Optional[str] = None
    expected_account_masked: Optional[str] = None
    gemini_cli_home: Optional[str] = None
    preflight_status: Optional[str] = None
    elapsed_seconds: Optional[float] = None
    rate_429_detected: Optional[bool] = None
    auth_prompt_detected: Optional[bool] = None
    timed_out: Optional[bool] = None
    cli_session_id: Optional[str] = None


class SessionRecord(BaseModel):
    session_id: str
    created_at_utc: datetime
    user_message: str
    results: list[AgentRunResult]
