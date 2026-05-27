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


class SessionRecord(BaseModel):
    session_id: str
    created_at_utc: datetime
    user_message: str
    results: list[AgentRunResult]
