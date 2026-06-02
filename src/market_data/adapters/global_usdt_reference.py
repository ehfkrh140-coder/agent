from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from src.market_data.adapters.base import MarketDataAdapter, MarketDataAdapterError
from src.market_data.http_client import ReadOnlyHttpClient


class GlobalUsdtReferenceAdapter(MarketDataAdapter):
    """Public read-only adapter for global USDT reference ticker/orderbook data."""

    adapter_type = "global_usdt_reference"

    def __init__(
        self,
        adapter_id: str,
        *,
        config: dict[str, Any] | None = None,
        http_client: Any | None = None,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(adapter_id, config=config)
        self.base_url = str(self.config.get("base_url") or "")
        self.venue_id = str(self.config.get("venue_id") or adapter_id).lower()
        self.venue_name = str(self.config.get("venue_name") or self.venue_id.title())
        self.market_symbol = str(self.config.get("market_symbol") or "USDT/USDC")
        self.instrument_type = str(self.config.get("instrument_type") or "reference")
        self.ticker_path = str(self.config.get("ticker_path") or "")
        self.ticker_params = dict(self.config.get("ticker_params") or {})
        self.response_format = str(self.config.get("response_format") or "generic_ticker")
        self.http_client = http_client or ReadOnlyHttpClient(
            timeout_seconds=float(self.config.get("timeout_seconds") or 10),
            max_retries=int(self.config.get("max_retries") or 2),
            user_agent=str(self.config.get("user_agent") or "agent-council-market-data-v1"),
        )
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc))

    def fetch_snapshot(self) -> dict[str, Any]:
        if not self.base_url or not self.ticker_path:
            raise MarketDataAdapterError(f"Global USDT reference adapter {self.adapter_id} requires base_url and ticker_path")
        response = self.http_client.get_json(self.base_url, self.ticker_path, self.ticker_params)
        collected_at = _ensure_utc(self.now_fn())
        parsed = self._parse_ticker(response.data)
        bid = _safe_float(parsed.get("bid"))
        ask = _safe_float(parsed.get("ask"))
        if bid is None or ask is None:
            raise MarketDataAdapterError(f"{self.adapter_id} did not expose both bid and ask for {self.market_symbol}")
        timestamp = _coerce_timestamp(parsed.get("timestamp")) or collected_at
        max_data_age_ms = max(0, int(collected_at.timestamp() * 1000) - int(timestamp.timestamp() * 1000))
        observation = {
            "observation_id": f"{self.venue_id}_{self.market_symbol.lower().replace('/', '_').replace('-', '_')}_reference",
            "venue_id": self.venue_id,
            "venue_name": self.venue_name,
            "market_symbol": self.market_symbol,
            "instrument_type": self.instrument_type,
            "region": "GLOBAL",
            "bid": bid,
            "ask": ask,
            "bid_size": _safe_float(parsed.get("bid_size")),
            "ask_size": _safe_float(parsed.get("ask_size")),
            "timestamp_utc": timestamp.isoformat(),
            "liquidity": {
                "orderbook_depth_available": False,
                "volume_available": False,
                "estimated_executable_notional": None,
                "estimated_slippage_pct": 0.0,
                "depth_levels": [],
            },
            "data_quality": {
                "timestamps_available": parsed.get("timestamp") is not None,
                "timestamps_aligned": None,
                "max_data_age_ms": max_data_age_ms,
                "source": f"{self.venue_id}_public_reference",
                "latency_ms": response.elapsed_ms,
                "is_realtime": True,
            },
            "health": {
                "api_status_known": True,
                "api_ok": True,
                "maintenance": False,
                "trading_enabled": None,
                "message": None,
            },
            "extensions": {
                "reference_role": "global_usdt_reference",
                "response_format": self.response_format,
                "api_market": parsed.get("symbol") or self.ticker_params.get("symbol") or self.ticker_params.get("instId"),
            },
        }
        return {
            "packet_id": f"{self.adapter_id}_{collected_at.strftime('%Y%m%d_%H%M%S')}",
            "created_at_utc": collected_at.isoformat(),
            "asset": "USDT",
            "quote": "KRW",
            "strategy_family": "tether_cross_market_premium",
            "strategy_id": "usdt_krw_global_reference_v0",
            "signal_type": "tether_cross_market_premium",
            "observations": [observation],
            "adapter_metadata": {
                "adapter_id": self.adapter_id,
                "adapter_type": self.adapter_type,
                "fetched_at_utc": collected_at.isoformat(),
                "endpoint": self.ticker_path,
                "base_url": self.base_url,
                "public_read_only": True,
                "no_private_api": True,
            },
            "extensions": {"raw_summary": {"ticker_url": response.url}},
        }

    def _parse_ticker(self, data: Any) -> dict[str, Any]:
        if self.response_format == "binance_book_ticker":
            return _parse_binance_book_ticker(data)
        if self.response_format == "bybit_v5_ticker":
            return _parse_bybit_v5_ticker(data)
        if self.response_format == "okx_ticker":
            return _parse_okx_ticker(data)
        return _parse_generic_ticker(data)


def _parse_binance_book_ticker(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise MarketDataAdapterError("Binance reference response root is not an object")
    return {
        "symbol": data.get("symbol"),
        "bid": data.get("bidPrice"),
        "ask": data.get("askPrice"),
        "bid_size": data.get("bidQty"),
        "ask_size": data.get("askQty"),
        "timestamp": data.get("time") or data.get("timestamp"),
    }


def _parse_bybit_v5_ticker(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise MarketDataAdapterError("Bybit reference response root is not an object")
    if data.get("retCode") not in (None, 0, "0"):
        raise MarketDataAdapterError(f"Bybit reference status {data.get('retCode')}: {data.get('retMsg')}")
    rows = ((data.get("result") or {}).get("list") or []) if isinstance(data.get("result"), dict) else []
    row = next((item for item in rows if isinstance(item, dict)), None)
    if row is None:
        raise MarketDataAdapterError("Bybit reference response has no ticker entry")
    return {
        "symbol": row.get("symbol"),
        "bid": row.get("bid1Price") or row.get("bidPrice"),
        "ask": row.get("ask1Price") or row.get("askPrice"),
        "bid_size": row.get("bid1Size") or row.get("bidSize"),
        "ask_size": row.get("ask1Size") or row.get("askSize"),
        "timestamp": data.get("time") or row.get("time") or row.get("timestamp"),
    }


def _parse_okx_ticker(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise MarketDataAdapterError("OKX reference response root is not an object")
    if data.get("code") not in (None, "0", 0):
        raise MarketDataAdapterError(f"OKX reference status {data.get('code')}: {data.get('msg')}")
    rows = data.get("data") or []
    row = next((item for item in rows if isinstance(item, dict)), None)
    if row is None:
        raise MarketDataAdapterError("OKX reference response has no ticker entry")
    return {
        "symbol": row.get("instId"),
        "bid": row.get("bidPx"),
        "ask": row.get("askPx"),
        "bid_size": row.get("bidSz"),
        "ask_size": row.get("askSz"),
        "timestamp": row.get("ts") or data.get("ts"),
    }


def _parse_generic_ticker(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise MarketDataAdapterError("Generic reference response root is not an object")
    return {
        "symbol": data.get("symbol") or data.get("instId"),
        "bid": data.get("bid") or data.get("bidPrice") or data.get("bidPx"),
        "ask": data.get("ask") or data.get("askPrice") or data.get("askPx"),
        "bid_size": data.get("bid_size") or data.get("bidQty") or data.get("bidSz"),
        "ask_size": data.get("ask_size") or data.get("askQty") or data.get("askSz"),
        "timestamp": data.get("timestamp") or data.get("time") or data.get("ts"),
    }


def _safe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _coerce_timestamp(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return _ensure_utc(value)
    if isinstance(value, str) and value.endswith("Z"):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            pass
    if isinstance(value, str) and "T" in value:
        try:
            return _ensure_utc(datetime.fromisoformat(value))
        except ValueError:
            pass
    numeric = _safe_int(value)
    if numeric is None:
        return None
    if numeric > 10_000_000_000:
        return datetime.fromtimestamp(numeric / 1000, tz=timezone.utc)
    return datetime.fromtimestamp(numeric, tz=timezone.utc)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
