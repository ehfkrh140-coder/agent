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
        if not self.child_adapters:
            raise MarketDataAdapterError(f"Composite adapter {self.adapter_id} requires at least one child adapter")
        collected_at = datetime.now(timezone.utc)
        observations: list[dict[str, Any]] = []
        child_metadata: list[dict[str, Any]] = []
        for child in self.child_adapters:
            try:
                snapshot = child.fetch_snapshot()
            except Exception as exc:  # noqa: BLE001 - include adapter id in wrapper error
                raise MarketDataAdapterError(f"Child adapter {child.adapter_id} failed: {exc}") from exc
            observations.extend(snapshot.get("observations") or [])
            child_metadata.append(snapshot.get("adapter_metadata") or {"adapter_id": child.adapter_id})
        return {
            "packet_id": f"{self.adapter_id}_{collected_at.strftime('%Y%m%d_%H%M%S')}",
            "created_at_utc": collected_at.isoformat(),
            "asset": self.config.get("asset") or "BTC",
            "quote": self.config.get("quote") or "KRW",
            "signal_type": self.config.get("signal_type") or "cross_exchange_spot_spread",
            "strategy_family": self.config.get("strategy_family") or "cross_exchange_spot_spread",
            "strategy_id": self.config.get("strategy_id") or "cross_exchange_spot_spread_v1",
            "thresholds": dict(self.config.get("thresholds") or {}),
            "observations": observations,
            "adapter_metadata": {
                "adapter_id": self.adapter_id,
                "adapter_type": self.adapter_type,
                "fetched_at_utc": collected_at.isoformat(),
                "child_adapters": [child.adapter_id for child in self.child_adapters],
                "children": child_metadata,
            },
            "extensions": {"child_count": len(self.child_adapters)},
        }
