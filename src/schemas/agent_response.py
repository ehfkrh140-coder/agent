from pydantic import BaseModel, Field


class AgentResponse(BaseModel):
    summary: str
    key_points: list[str]
    concerns: list[str]
    questions: list[str]
    suggested_next_steps: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
