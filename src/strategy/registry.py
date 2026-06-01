from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

STRATEGY_REGISTRY_PATH = Path("configs/strategy_registry.yaml")
STRATEGY_CURRENT_PATH = Path("configs/strategy_current.yaml")


def load_strategy_registry(path: str | Path = STRATEGY_REGISTRY_PATH) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("strategy registry root must be a mapping")
    return data


def load_strategy_current(path: str | Path = STRATEGY_CURRENT_PATH) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("strategy current root must be a mapping")
    return data


def strategy_by_family(family: str, registry: dict[str, Any] | None = None) -> dict[str, Any] | None:
    registry = registry or load_strategy_registry()
    for strategy in registry.get("strategies", []):
        if strategy.get("strategy_family") == family:
            return strategy
    return None


def active_strategy(current: dict[str, Any] | None = None) -> dict[str, Any]:
    current = current or load_strategy_current()
    return dict(current.get("active_strategy") or {})
