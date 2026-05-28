from pathlib import Path
from typing import List

import yaml

from src.agent_config import AgentConfig


def load_agent_configs(config_path: str) -> List[AgentConfig]:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    agents = raw.get("agents", [])
    if not isinstance(agents, list):
        raise ValueError("'agents' must be a list in YAML config")

    return [AgentConfig.model_validate(item) for item in agents]
