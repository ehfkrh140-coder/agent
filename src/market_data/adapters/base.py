from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


class MarketDataAdapterError(RuntimeError):
    """Raised when a read-only market data adapter cannot produce a snapshot."""


class MarketDataAdapter(ABC):
    """Read-only public market data adapter interface.

    Adapters must only read public market data or replay fixtures. They must not
    place orders, move funds, manage accounts, or require private credentials.
    """

    adapter_type: str

    def __init__(self, adapter_id: str, *, config: Mapping[str, Any] | None = None) -> None:
        self.adapter_id = adapter_id
        self.config = dict(config or {})

    @abstractmethod
    def fetch_snapshot(self) -> dict[str, Any]:
        """Return a raw market data snapshot suitable for OpportunityPacketBuilder."""
