from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.market_data.adapters.base import MarketDataAdapter, MarketDataAdapterError


class ReplayMarketDataAdapter(MarketDataAdapter):
    """Fixture-backed adapter for deterministic, network-free tests and smoke runs."""

    adapter_type = "replay"

    def __init__(self, adapter_id: str, *, fixture_path: str | Path, config: dict[str, Any] | None = None) -> None:
        super().__init__(adapter_id, config=config)
        self.fixture_path = Path(fixture_path)

    def fetch_snapshot(self) -> dict[str, Any]:
        if not self.fixture_path.exists():
            raise MarketDataAdapterError(f"Replay fixture not found: {self.fixture_path}")
        try:
            data = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise MarketDataAdapterError(f"Replay fixture is not valid JSON: {self.fixture_path}") from exc
        if not isinstance(data, dict):
            raise MarketDataAdapterError("Replay fixture root must be a JSON object")
        data.setdefault("adapter_metadata", {})
        data["adapter_metadata"].setdefault("adapter_id", self.adapter_id)
        data["adapter_metadata"].setdefault("adapter_type", self.adapter_type)
        data["adapter_metadata"].setdefault("fixture_path", str(self.fixture_path))
        return data
