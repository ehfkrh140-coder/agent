from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from src.market_data.adapters.base import MarketDataAdapter
from src.market_data.adapters.bithumb import BithumbPublicSpotAdapter
from src.market_data.adapters.bybit import BybitPublicMarketDataAdapter
from src.market_data.adapters.composite import CompositeSpotSpreadAdapter
from src.market_data.adapters.replay import ReplayMarketDataAdapter
from src.market_data.adapters.upbit import UpbitPublicSpotAdapter

DEFAULT_CONFIG_PATH = Path("configs/market_data.yaml")


def load_market_data_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    config_path = Path(path)
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Market data config must be a mapping: {config_path}")
    return data


def build_adapter(adapter_id: str, config: dict[str, Any] | None = None) -> MarketDataAdapter:
    config = config or load_market_data_config()
    adapters = config.get("adapters") or {}
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
    if adapter_type == "upbit_public_spot":
        return UpbitPublicSpotAdapter(adapter_id, config=adapter_config)
    if adapter_type == "bithumb_public_spot":
        return BithumbPublicSpotAdapter(adapter_id, config=adapter_config)
    if adapter_type == "composite_spot_spread":
        child_ids = adapter_config.get("venues") or []
        if not isinstance(child_ids, list) or not child_ids:
            raise ValueError(f"Composite adapter {adapter_id} requires venues")
        child_adapters = [build_adapter(child_id, config) for child_id in child_ids]
        return CompositeSpotSpreadAdapter(adapter_id, config=adapter_config, child_adapters=child_adapters)
    raise ValueError(f"Unsupported adapter type for v0: {adapter_type!r}")


def list_adapters(config: dict[str, Any] | None = None) -> list[str]:
    config = config or load_market_data_config()
    return sorted((config.get("adapters") or {}).keys())
