from pydantic import BaseModel, Field


class AgentResponse(BaseModel):
    summary: str
    key_points: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    suggested_next_steps: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
