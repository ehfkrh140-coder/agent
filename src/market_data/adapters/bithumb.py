from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml

from src.market_data.adapters.base import MarketDataAdapter, MarketDataAdapterError
from src.market_data.http_client import ReadOnlyHttpClient


class BithumbPublicSpotAdapter(MarketDataAdapter):
    """Public read-only Bithumb spot ticker/orderbook adapter."""

    adapter_type = "bithumb_public_spot"

    def __init__(
        self,
        adapter_id: str,
        *,
        config: dict[str, Any] | None = None,
        http_client: Any | None = None,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(adapter_id, config=config)
        self.base_url = str(self.config.get("base_url") or "https://api.bithumb.com")
        self.market = str(self.config.get("market") or "KRW-BTC")
        self.api_symbol = str(self.config.get("api_symbol") or "BTC_KRW")
        self.display_symbol = str(self.config.get("display_symbol") or "BTC/KRW")
        self.ticker_path = str(self.config.get("ticker_path") or "/public/ticker/{symbol}")
        self.orderbook_path = str(self.config.get("orderbook_path") or "/public/orderbook/{symbol}")
        self.orderbook_limit = int(self.config.get("orderbook_limit") or 15)
        self.fee_config_path = str(self.config.get("fee_config_path") or "configs/spot_fees.yaml")
        self.http_client = http_client or ReadOnlyHttpClient(
            timeout_seconds=float(self.config.get("timeout_seconds") or 10),
            max_retries=int(self.config.get("max_retries") or 2),
            user_agent=str(self.config.get("user_agent") or "agent-council-market-data-v1"),
        )
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc))

    def fetch_snapshot(self) -> dict[str, Any]:
        ticker_path = self.ticker_path.format(symbol=self.api_symbol, market=self.market)
        orderbook_path = self.orderbook_path.format(symbol=self.api_symbol, market=self.market)
        ticker_response = self._bithumb_get(ticker_path)
        orderbook_response = self._bithumb_get(orderbook_path)
        collected_at = _ensure_utc(self.now_fn())
        ticker = _data_object(ticker_response.data, "Bithumb ticker")
        orderbook = _data_object(orderbook_response.data, "Bithumb orderbook")
        observation = self._observation(
            ticker,
            orderbook,
            collected_at,
            latency_ms=ticker_response.elapsed_ms + orderbook_response.elapsed_ms,
        )
        return {
            "packet_id": f"bithumb_{self.api_symbol.lower()}_spot_{collected_at.strftime('%Y%m%d_%H%M%S')}",
            "created_at_utc": collected_at.isoformat(),
            "asset": _asset_from_display(self.display_symbol),
            "quote": _quote_from_display(self.display_symbol),
            "strategy_family": "cross_exchange_spot_spread",
            "strategy_id": "cross_exchange_spot_spread_v1",
            "signal_type": "cross_exchange_spot_spread",
            "observations": [observation],
            "adapter_metadata": {
                "adapter_id": self.adapter_id,
                "adapter_type": self.adapter_type,
                "fetched_at_utc": collected_at.isoformat(),
                "endpoints": [ticker_path, orderbook_path],
                "base_url": self.base_url,
            },
            "extensions": {
                "raw_summary": {
                    "ticker_status": ticker_response.data.get("status") if isinstance(ticker_response.data, dict) else None,
                    "orderbook_status": orderbook_response.data.get("status") if isinstance(orderbook_response.data, dict) else None,
                    "ticker_url": ticker_response.url,
                    "orderbook_url": orderbook_response.url,
                }
            },
        }

    def _bithumb_get(self, path: str) -> Any:
        response = self.http_client.get_json(self.base_url, path, None)
        if isinstance(response.data, dict):
            status = response.data.get("status")
            if status not in (None, "0000"):
                raise MarketDataAdapterError(f"Bithumb status {status}: {response.data.get('message') or 'unknown error'}")
        return response

    def _observation(
        self,
        ticker: dict[str, Any],
        orderbook: dict[str, Any],
        collected_at: datetime,
        latency_ms: int,
    ) -> dict[str, Any]:
        bids = orderbook.get("bids") or []
        asks = orderbook.get("asks") or []
        best_bid = bids[0] if bids and isinstance(bids[0], dict) else {}
        best_ask = asks[0] if asks and isinstance(asks[0], dict) else {}
        bid = _safe_float(best_bid.get("price"))
        ask = _safe_float(best_ask.get("price"))
        bid_size = _safe_float(best_bid.get("quantity"))
        ask_size = _safe_float(best_ask.get("quantity"))
        timestamp_ms = _safe_int(orderbook.get("timestamp")) or _safe_int(ticker.get("date"))
        timestamp = _datetime_from_ms(timestamp_ms) or collected_at
        max_data_age_ms = max(0, int(collected_at.timestamp() * 1000) - int(timestamp.timestamp() * 1000))
        top_notional = _min_not_none(
            bid * bid_size if bid is not None and bid_size is not None else None,
            ask * ask_size if ask is not None and ask_size is not None else None,
        )
        return {
            "observation_id": f"bithumb_{self.api_symbol.lower()}_spot",
            "venue_id": "bithumb",
            "venue_name": "Bithumb",
            "market_symbol": self.display_symbol,
            "instrument_type": "spot",
            "region": "KR",
            "last_price": _safe_float(ticker.get("closing_price") or ticker.get("trade_price")),
            "bid": bid,
            "ask": ask,
            "bid_size": bid_size,
            "ask_size": ask_size,
            "base_volume_24h": _safe_float(ticker.get("units_traded_24H") or ticker.get("acc_trade_volume_24h")),
            "quote_volume_24h": _safe_float(ticker.get("acc_trade_value_24H") or ticker.get("acc_trade_price_24h")),
            "timestamp_utc": timestamp.isoformat(),
            "fees": _fee_snapshot("bithumb", self.display_symbol, self.fee_config_path),
            "liquidity": {
                "orderbook_depth_available": bool(bids and asks),
                "volume_available": (ticker.get("units_traded_24H") or ticker.get("acc_trade_volume_24h")) not in (None, ""),
                "estimated_executable_notional": top_notional,
                "estimated_slippage_pct": 0.0 if bool(bids and asks) else None,
                "depth_levels": _bithumb_depth(bids, asks, limit=self.orderbook_limit),
            },
            "data_quality": {
                "timestamps_available": timestamp_ms is not None,
                "timestamps_aligned": None,
                "max_data_age_ms": max_data_age_ms,
                "source": "bithumb_public" if timestamp_ms is not None else "local_timestamp_fallback",
                "latency_ms": latency_ms,
                "is_realtime": True,
            },
            "health": {
                "api_status_known": True,
                "api_ok": True,
                "maintenance": False,
                "trading_enabled": True,
                "message": None,
            },
            "extensions": {"api_symbol": self.api_symbol, "api_market": self.market},
        }


def _data_object(data: Any, label: str) -> dict[str, Any]:
    if isinstance(data, dict):
        nested = data.get("data")
        if isinstance(nested, dict):
            return nested
        return data
    raise MarketDataAdapterError(f"{label} response has no data object")


def _bithumb_depth(bids: Any, asks: Any, *, limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index in range(limit):
        bid_level = bids[index] if isinstance(bids, list) and index < len(bids) else None
        ask_level = asks[index] if isinstance(asks, list) and index < len(asks) else None
        if not bid_level and not ask_level:
            break
        rows.append(
            {
                "level": index + 1,
                "bid_price": _safe_float(bid_level.get("price")) if isinstance(bid_level, dict) else None,
                "bid_size": _safe_float(bid_level.get("quantity")) if isinstance(bid_level, dict) else None,
                "ask_price": _safe_float(ask_level.get("price")) if isinstance(ask_level, dict) else None,
                "ask_size": _safe_float(ask_level.get("quantity")) if isinstance(ask_level, dict) else None,
            }
        )
    return rows


def _fee_snapshot(venue_id: str, display_symbol: str, fee_config_path: str) -> dict[str, Any] | None:
    path = Path(fee_config_path)
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    fee = ((data.get("spot_fees") or {}).get(venue_id) or {}).get(display_symbol)
    return dict(fee) if isinstance(fee, dict) else None


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


def _datetime_from_ms(value: int | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _asset_from_display(display_symbol: str) -> str:
    return display_symbol.split("/", 1)[0]


def _quote_from_display(display_symbol: str) -> str:
    return display_symbol.split("/", 1)[1] if "/" in display_symbol else "KRW"


def _min_not_none(*values: float | None) -> float | None:
    present = [value for value in values if value is not None]
    return min(present) if present else None
