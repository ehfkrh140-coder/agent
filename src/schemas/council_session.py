from datetime import datetime
from typing import Any, Optional

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


class ScenarioEvaluationMetadata(BaseModel):
    expected_behavior_present: bool = False
    expected_behavior: Optional[dict[str, Any]] = None
    final_summary_contains_expected_decision: Optional[bool] = None
    final_confidence_within_expected_max: Optional[bool] = None
    must_not_include_violations: list[str] = Field(default_factory=list)


class CouncilSessionRecord(BaseModel):
    session_id: str
    created_at_utc: datetime
    user_message: str
    council_flow: CouncilFlowMetadata
    results: list[AgentRunResult]
    chair_context: Optional[dict] = None
    review_contexts: dict[str, dict] = Field(default_factory=dict)
    final_context: Optional[dict] = None
    opportunity_packet: Optional[dict[str, Any]] = None
    scenario_name: Optional[str] = None
    opportunity_file_path: Optional[str] = None
    expected_behavior: Optional[dict[str, Any]] = None
    scenario_evaluation: Optional[ScenarioEvaluationMetadata] = None
