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


class CompositeTetherCrossMarketAdapter(MarketDataAdapter):
    """Combine public domestic USDT/KRW and global USDT references into a Tether snapshot."""

    adapter_type = "composite_tether_cross_market_premium"

    def __init__(
        self,
        adapter_id: str,
        *,
        config: dict[str, Any] | None = None,
        domestic_adapters: Iterable[MarketDataAdapter] | None = None,
        global_reference_adapters: Iterable[MarketDataAdapter] | None = None,
    ) -> None:
        super().__init__(adapter_id, config=config)
        self.domestic_adapters = list(domestic_adapters or [])
        self.global_reference_adapters = list(global_reference_adapters or [])

    def fetch_snapshot(self) -> dict[str, Any]:
        if not self.domestic_adapters:
            raise MarketDataAdapterError(f"Composite adapter {self.adapter_id} requires domestic adapters")
        if not self.global_reference_adapters:
            raise MarketDataAdapterError(f"Composite adapter {self.adapter_id} requires global reference adapters")

        collected_at = datetime.now(timezone.utc)
        observations: list[dict[str, Any]] = []
        domestic_metadata: list[dict[str, Any]] = []
        global_metadata: list[dict[str, Any]] = []
        failed_global_references: list[dict[str, Any]] = []

        for child in self.domestic_adapters:
            try:
                snapshot = child.fetch_snapshot()
            except Exception as exc:  # noqa: BLE001 - fail fast with child id for domestic data
                raise MarketDataAdapterError(f"Domestic child adapter {child.adapter_id} failed: {exc}") from exc
            child_observations = snapshot.get("observations") or []
            if not child_observations:
                raise MarketDataAdapterError(f"Domestic child adapter {child.adapter_id} returned no observations")
            observations.extend(child_observations)
            domestic_metadata.append(snapshot.get("adapter_metadata") or {"adapter_id": child.adapter_id})

        for child in self.global_reference_adapters:
            try:
                snapshot = child.fetch_snapshot()
            except Exception as exc:  # noqa: BLE001 - partial global failure is carried as metadata
                failed_global_references.append({"adapter_id": child.adapter_id, "reason": str(exc)})
                continue
            child_observations = snapshot.get("observations") or []
            if not child_observations:
                failed_global_references.append({"adapter_id": child.adapter_id, "reason": "no observations returned"})
                continue
            observations.extend(child_observations)
            global_metadata.append(snapshot.get("adapter_metadata") or {"adapter_id": child.adapter_id})

        if not global_metadata:
            failed = ", ".join(item["adapter_id"] for item in failed_global_references) or "none"
            raise MarketDataAdapterError(f"All global USDT reference adapters failed for {self.adapter_id}: {failed}")

        domestic_ids = [child.adapter_id for child in self.domestic_adapters]
        global_ids = [child.adapter_id for child in self.global_reference_adapters]
        return {
            "packet_id": f"{self.adapter_id}_{collected_at.strftime('%Y%m%d_%H%M%S')}",
            "created_at_utc": collected_at.isoformat(),
            "asset": self.config.get("asset") or "USDT",
            "quote": self.config.get("quote") or "KRW",
            "signal_type": self.config.get("signal_type") or "tether_cross_market_premium",
            "strategy_family": self.config.get("strategy_family") or "tether_cross_market_premium",
            "strategy_id": self.config.get("strategy_id") or "usdt_krw_global_reference_v0",
            "thresholds": dict(self.config.get("thresholds") or {}),
            "observations": observations,
            "adapter_metadata": {
                "adapter_id": self.adapter_id,
                "adapter_type": self.adapter_type,
                "generated_from": self.adapter_type,
                "fetched_at_utc": collected_at.isoformat(),
                "domestic_child_adapters": domestic_ids,
                "global_reference_child_adapters": global_ids,
                "children": {
                    "domestic": domestic_metadata,
                    "global_reference": global_metadata,
                },
                "failed_global_reference_venues": failed_global_references,
                "public_read_only": True,
                "no_private_api": True,
            },
            "extensions": {
                "experimental_strategy": True,
                "non_active_strategy": True,
                "no_trade_only": True,
                "source_child_adapters": domestic_ids + global_ids,
                "domestic_child_adapters": domestic_ids,
                "global_reference_child_adapters": global_ids,
                "successful_global_reference_count": len(global_metadata),
                "failed_global_reference_venues": failed_global_references,
            },
        }


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
