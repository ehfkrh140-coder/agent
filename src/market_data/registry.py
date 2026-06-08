from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from src.market_data.adapters.base import MarketDataAdapter
from src.market_data.adapters.bithumb import BithumbPublicSpotAdapter
from src.market_data.adapters.bybit import BybitPublicMarketDataAdapter
from src.market_data.adapters.composite import (
    CompositeOrderbookImbalanceAdapter,
    CompositeSpotSpreadAdapter,
    CompositeTetherCrossMarketAdapter,
)
from src.market_data.adapters.global_usdt_reference import GlobalUsdtReferenceAdapter
from src.market_data.adapters.mark_orderbook_gap_hunt import (
    BinanceMarkOrderbookGapHuntAdapter,
    BybitMarkOrderbookGapHuntAdapter,
    OkxMarkOrderbookGapHuntAdapter,
)
from src.market_data.adapters.replay import ReplayMarketDataAdapter
from src.market_data.adapters.spot_futures_basis import BinanceSpotFuturesBasisAdapter
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
    if adapter_type == "binance_mark_orderbook_gap_hunt":
        return BinanceMarkOrderbookGapHuntAdapter(adapter_id, config=adapter_config)
    if adapter_type == "bybit_mark_orderbook_gap_hunt":
        return BybitMarkOrderbookGapHuntAdapter(adapter_id, config=adapter_config)
    if adapter_type == "okx_mark_orderbook_gap_hunt":
        return OkxMarkOrderbookGapHuntAdapter(adapter_id, config=adapter_config)
    if adapter_type == "binance_spot_futures_basis":
        return BinanceSpotFuturesBasisAdapter(adapter_id, config=adapter_config)
    if adapter_type == "upbit_public_spot":
        return UpbitPublicSpotAdapter(adapter_id, config=adapter_config)
    if adapter_type == "bithumb_public_spot":
        return BithumbPublicSpotAdapter(adapter_id, config=adapter_config)
    if adapter_type == "global_usdt_reference":
        return GlobalUsdtReferenceAdapter(adapter_id, config=adapter_config)
    if adapter_type == "composite_tether_cross_market_premium":
        domestic_ids = adapter_config.get("domestic_venues") or []
        global_ids = adapter_config.get("global_reference_venues") or []
        if not isinstance(domestic_ids, list) or not domestic_ids:
            raise ValueError(f"Tether composite adapter {adapter_id} requires domestic_venues")
        if not isinstance(global_ids, list) or not global_ids:
            raise ValueError(f"Tether composite adapter {adapter_id} requires global_reference_venues")
        return CompositeTetherCrossMarketAdapter(
            adapter_id,
            config=adapter_config,
            domestic_adapters=[build_adapter(child_id, config) for child_id in domestic_ids],
            global_reference_adapters=[build_adapter(child_id, config) for child_id in global_ids],
        )
    if adapter_type in {"composite_spot_spread", "composite_orderbook_imbalance"}:
        child_ids = adapter_config.get("venues") or []
        if not isinstance(child_ids, list) or not child_ids:
            raise ValueError(f"Composite adapter {adapter_id} requires venues")
        child_adapters = [build_adapter(child_id, config) for child_id in child_ids]
        if adapter_type == "composite_orderbook_imbalance":
            return CompositeOrderbookImbalanceAdapter(adapter_id, config=adapter_config, child_adapters=child_adapters)
        return CompositeSpotSpreadAdapter(adapter_id, config=adapter_config, child_adapters=child_adapters)
    raise ValueError(f"Unsupported adapter type for v0: {adapter_type!r}")


def list_adapters(config: dict[str, Any] | None = None) -> list[str]:
    config = config or load_market_data_config()
    return sorted((config.get("adapters") or {}).keys())
