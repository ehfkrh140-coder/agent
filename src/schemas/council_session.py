from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.schemas.session_record import AgentRunResult


class CouncilFlowMetadata(BaseModel):
    mode: str = "single_round_v1"
    chair_agent_id: str = "agent_01"
    review_agent_ids: list[str] = Field(default_factory=lambda: ["agent_02", "agent_03", "agent_04"])
    final_agent_id: str = "agent_05"
    review_parallel: bool = False
    max_workers: int = 2
    final_policy: str = "run_after_review_failures_with_available_context"


class CouncilSessionRecord(BaseModel):
    session_id: str
    created_at_utc: datetime
    user_message: str
    council_flow: CouncilFlowMetadata
    results: list[AgentRunResult]
    chair_context: Optional[dict] = None
    review_contexts: dict[str, dict] = Field(default_factory=dict)
    final_context: Optional[dict] = None
