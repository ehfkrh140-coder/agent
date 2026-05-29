from __future__ import annotations

import json
from pathlib import Path

from src.schemas.opportunity_packet import OpportunityPacket

SCENARIO_DIR = Path("data/test_scenarios")


def list_scenarios(base_dir: Path | str = SCENARIO_DIR) -> list[str]:
    path = Path(base_dir)
    if not path.exists():
        return []
    return sorted(p.stem for p in path.glob("*.json"))


def scenario_path(name: str, base_dir: Path | str = SCENARIO_DIR) -> Path:
    path = Path(base_dir) / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Scenario not found: {path}")
    return path


def load_opportunity_file(path: str | Path) -> OpportunityPacket:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    return OpportunityPacket.model_validate(data)


def load_scenario(name: str, base_dir: Path | str = SCENARIO_DIR) -> OpportunityPacket:
    return load_opportunity_file(scenario_path(name, base_dir=base_dir))
