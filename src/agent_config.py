from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    agent_id: str
    name: str
    provider: str
    model: str
    api_key_env: str
    system_prompt_path: str
    temperature: float = Field(ge=0.0, le=2.0, default=0.7)
