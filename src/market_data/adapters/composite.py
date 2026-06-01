from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

from src.market_data.adapters.base import MarketDataAdapter, MarketDataAdapterError


class CompositeSpotSpreadAdapter(MarketDataAdapter):
    """Combine public spot venue observations into a cross-exchange spread snapshot."""

    adapter_type = "composite_spot_spread"

    def __init__(
        self,
        adapter_id: str,
        *,
        config: dict[str, Any] | None = None,
        child_adapters: Iterable[MarketDataAdapter] | None = None,
    ) -> None:
        super().__init__(adapter_id, config=config)
        self.child_adapters = list(child_adapters or [])

    def fetch_snapshot(self) -> dict[str, Any]:
        return _build_composite_snapshot(
            self,
            default_signal_type="cross_exchange_spot_spread",
            default_strategy_family="cross_exchange_spot_spread",
            default_strategy_id="cross_exchange_spot_spread_v1",
            extra_extensions={},
        )


class CompositeOrderbookImbalanceAdapter(MarketDataAdapter):
    """Combine existing public spot venue observations into an experimental imbalance snapshot."""

    adapter_type = "composite_orderbook_imbalance"

    def __init__(
        self,
        adapter_id: str,
        *,
        config: dict[str, Any] | None = None,
        child_adapters: Iterable[MarketDataAdapter] | None = None,
    ) -> None:
        super().__init__(adapter_id, config=config)
        self.child_adapters = list(child_adapters or [])

    def fetch_snapshot(self) -> dict[str, Any]:
        return _build_composite_snapshot(
            self,
            default_signal_type="orderbook_imbalance",
            default_strategy_family="orderbook_imbalance",
            default_strategy_id="orderbook_imbalance_v0",
            extra_extensions={
                "experimental_strategy": True,
                "non_active_strategy": True,
                "source_child_adapters": [child.adapter_id for child in self.child_adapters],
            },
        )


def _build_composite_snapshot(
    adapter: MarketDataAdapter,
    *,
    default_signal_type: str,
    default_strategy_family: str,
    default_strategy_id: str,
    extra_extensions: dict[str, Any],
) -> dict[str, Any]:
    if not getattr(adapter, "child_adapters", None):
        raise MarketDataAdapterError(f"Composite adapter {adapter.adapter_id} requires at least one child adapter")
    collected_at = datetime.now(timezone.utc)
    observations: list[dict[str, Any]] = []
    child_metadata: list[dict[str, Any]] = []
    child_adapters = list(adapter.child_adapters)
    for child in child_adapters:
        try:
            snapshot = child.fetch_snapshot()
        except Exception as exc:  # noqa: BLE001 - include adapter id in wrapper error
            raise MarketDataAdapterError(f"Child adapter {child.adapter_id} failed: {exc}") from exc
        observations.extend(snapshot.get("observations") or [])
        child_metadata.append(snapshot.get("adapter_metadata") or {"adapter_id": child.adapter_id})
    extensions = {"child_count": len(child_adapters)}
    extensions.update(extra_extensions)
    return {
        "packet_id": f"{adapter.adapter_id}_{collected_at.strftime('%Y%m%d_%H%M%S')}",
        "created_at_utc": collected_at.isoformat(),
        "asset": adapter.config.get("asset") or "BTC",
        "quote": adapter.config.get("quote") or "KRW",
        "signal_type": adapter.config.get("signal_type") or default_signal_type,
        "strategy_family": adapter.config.get("strategy_family") or default_strategy_family,
        "strategy_id": adapter.config.get("strategy_id") or default_strategy_id,
        "thresholds": dict(adapter.config.get("thresholds") or {}),
        "observations": observations,
        "adapter_metadata": {
            "adapter_id": adapter.adapter_id,
            "adapter_type": adapter.adapter_type,
            "generated_from": adapter.adapter_type,
            "fetched_at_utc": collected_at.isoformat(),
            "child_adapters": [child.adapter_id for child in child_adapters],
            "children": child_metadata,
        },
        "extensions": extensions,
    }
