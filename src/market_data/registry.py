from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from src.market_data.adapters.base import MarketDataAdapter
from src.market_data.adapters.bybit import BybitPublicMarketDataAdapter
from src.market_data.adapters.replay import ReplayMarketDataAdapter


DEFAULT_CONFIG_PATH = Path("configs/market_data.yaml")


def load_market_data_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    config_path = Path(path)
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("market data config root must be a mapping")
    return data


def build_adapter(adapter_id: str, config: dict[str, Any] | None = None) -> MarketDataAdapter:
    config = config or load_market_data_config()
    adapters = config.get("adapters", {})
    if adapter_id not in adapters:
        raise KeyError(f"Unknown market data adapter: {adapter_id}")
    adapter_config = dict(adapters[adapter_id] or {})
    adapter_type = adapter_config.get("type")
    if adapter_type == "replay":
        fixture_path = adapter_config.get("fixture_path")
        if not fixture_path:
            raise ValueError(f"Replay adapter {adapter_id} requires fixture_path")
        return ReplayMarketDataAdapter(adapter_id, fixture_path=fixture_path, config=adapter_config)
    if adapter_type == "bybit_public":
        return BybitPublicMarketDataAdapter(adapter_id, config=adapter_config)
    raise ValueError(f"Unsupported adapter type for v0: {adapter_type!r}")


def list_adapters(config: dict[str, Any] | None = None) -> list[str]:
    config = config or load_market_data_config()
    return sorted((config.get("adapters") or {}).keys())
