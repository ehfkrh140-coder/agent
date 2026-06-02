from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from src.market_data.adapters.base import MarketDataAdapter, MarketDataAdapterError
from src.market_data.http_client import HttpJsonResponse, ReadOnlyHttpClient


class BybitPublicMarketDataAdapter(MarketDataAdapter):
    """Public read-only Bybit market data adapter for Mark-Orderbook Gap packets."""

    adapter_type = "bybit_public"
    TICKERS_PATH = "/v5/market/tickers"
    ORDERBOOK_PATH = "/v5/market/orderbook"

    def __init__(
        self,
        adapter_id: str,
        *,
        config: dict[str, Any] | None = None,
        http_client: Any | None = None,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(adapter_id, config=config)
        self.base_url = str(self.config.get("base_url") or "https://api.bybit.com")
        self.category = str(self.config.get("category") or "linear")
        self.symbol = str(self.config.get("symbol") or "BTCUSDT")
        self.display_symbol = str(self.config.get("display_symbol") or "BTC/USDT-PERP")
        self.orderbook_limit = int(self.config.get("orderbook_limit") or 25)
        self.unit = _safe_float(self.config.get("unit"), default=1.0)
        self.http_client = http_client or ReadOnlyHttpClient(
            timeout_seconds=float(self.config.get("timeout_seconds") or 10),
            max_retries=int(self.config.get("max_retries") or 2),
            user_agent=str(self.config.get("user_agent") or "agent-council-market-data-v1"),
        )
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc))

    def fetch_snapshot(self) -> dict[str, Any]:
        ticker_response = self._bybit_get(
            self.TICKERS_PATH,
            {"category": self.category, "symbol": self.symbol},
        )
        orderbook_response = self._bybit_get(
            self.ORDERBOOK_PATH,
            {"category": self.category, "symbol": self.symbol, "limit": self.orderbook_limit},
        )
        collected_at = self._ensure_utc(self.now_fn())
        ticker = self._first_ticker(ticker_response.data)
        orderbook = self._result(orderbook_response.data)
        total_elapsed_ms = ticker_response.elapsed_ms + orderbook_response.elapsed_ms
        observation = self._observation(ticker, orderbook, collected_at, total_elapsed_ms)
        return {
            "packet_id": f"bybit_{self.symbol.lower()}_mark_orderbook_gap_{collected_at.strftime('%Y%m%d_%H%M%S')}",
            "created_at_utc": collected_at.isoformat(),
            "asset": self._asset_from_symbol(),
            "quote": "USDT" if self.symbol.endswith("USDT") else self.symbol[-3:],
            "strategy_family": "mark_orderbook_gap",
            "strategy_id": "mark_orderbook_gap_hunt_v0",
            "thresholds": dict(self.config.get("thresholds") or {}),
            "guards": dict(self.config.get("guards") or {}),
            "observations": [observation],
            "adapter_metadata": {
                "adapter_id": self.adapter_id,
                "adapter_type": self.adapter_type,
                "fetched_at_utc": collected_at.isoformat(),
                "endpoints": [self.TICKERS_PATH, self.ORDERBOOK_PATH],
                "base_url": self.base_url,
            },
            "extensions": {
                "raw_summary": {
                    "ticker_ret_code": ticker_response.data.get("retCode"),
                    "orderbook_ret_code": orderbook_response.data.get("retCode"),
                    "ticker_url": ticker_response.url,
                    "orderbook_url": orderbook_response.url,
                }
            },
        }

    def _bybit_get(self, path: str, params: dict[str, Any]) -> HttpJsonResponse:
        response = self.http_client.get_json(self.base_url, path, params)
        ret_code = response.data.get("retCode")
        if ret_code != 0:
            ret_msg = response.data.get("retMsg") or "unknown Bybit error"
            raise MarketDataAdapterError(f"Bybit retCode {ret_code}: {ret_msg}")
        return response

    def _first_ticker(self, data: dict[str, Any]) -> dict[str, Any]:
        items = self._result(data).get("list") or []
        if not items:
            raise MarketDataAdapterError("Bybit ticker response has no result.list entries")
        first = items[0]
        if not isinstance(first, dict):
            raise MarketDataAdapterError("Bybit ticker entry is not an object")
        return first

    def _result(self, data: dict[str, Any]) -> dict[str, Any]:
        result = data.get("result") or {}
        if not isinstance(result, dict):
            raise MarketDataAdapterError("Bybit response result is not an object")
        return result

    def _observation(
        self,
        ticker: dict[str, Any],
        orderbook: dict[str, Any],
        collected_at: datetime,
        latency_ms: int,
    ) -> dict[str, Any]:
        bids = orderbook.get("b") or []
        asks = orderbook.get("a") or []
        best_bid = _first_level(bids)
        best_ask = _first_level(asks)
        bid = _safe_float(best_bid[0]) if best_bid else _safe_float(ticker.get("bid1Price"))
        bid_size = _safe_float(best_bid[1]) if best_bid else _safe_float(ticker.get("bid1Size"))
        ask = _safe_float(best_ask[0]) if best_ask else _safe_float(ticker.get("ask1Price"))
        ask_size = _safe_float(best_ask[1]) if best_ask else _safe_float(ticker.get("ask1Size"))
        exchange_timestamp_ms = _safe_int(orderbook.get("cts")) or _safe_int(orderbook.get("ts"))
        timestamp = _datetime_from_ms(exchange_timestamp_ms)
        max_data_age_ms = None
        if exchange_timestamp_ms is not None:
            max_data_age_ms = max(0, int(collected_at.timestamp() * 1000) - exchange_timestamp_ms)
        depth_levels = _compact_depth(bids, asks, limit=min(self.orderbook_limit, 25))
        top_ask_notional = ask * ask_size * self.unit if ask is not None and ask_size is not None else None
        next_funding_time = _datetime_from_ms(_safe_int(ticker.get("nextFundingTime")))
        return {
            "observation_id": f"bybit_{self.symbol.lower()}_linear",
            "venue_id": "bybit",
            "venue_name": "Bybit",
            "market_symbol": self.display_symbol,
            "instrument_type": "perpetual",
            "region": "GLOBAL",
            "last_price": _safe_float(ticker.get("lastPrice")),
            "mark_price": _safe_float(ticker.get("markPrice")),
            "index_price": _safe_float(ticker.get("indexPrice")),
            "unit": self.unit,
            "bid": bid,
            "ask": ask,
            "bid_size": bid_size,
            "ask_size": ask_size,
            "base_volume_24h": _safe_float(ticker.get("volume24h")),
            "quote_volume_24h": _safe_float(ticker.get("turnover24h")),
            "timestamp_utc": timestamp.isoformat() if timestamp else None,
            "derivatives": {
                "funding_rate_pct": _safe_float(ticker.get("fundingRate")),
                "next_funding_time_utc": next_funding_time.isoformat() if next_funding_time else None,
                "open_interest": _safe_float(ticker.get("openInterest")),
                "mark_price": _safe_float(ticker.get("markPrice")),
                "index_price": _safe_float(ticker.get("indexPrice")),
            },
            "liquidity": {
                "orderbook_depth_available": bool(bids and asks),
                "volume_available": ticker.get("volume24h") not in (None, ""),
                "estimated_executable_notional": top_ask_notional,
                "estimated_slippage_pct": None,
                "depth_levels": depth_levels,
            },
            "data_quality": {
                "timestamps_available": timestamp is not None,
                "timestamps_aligned": None,
                "max_data_age_ms": max_data_age_ms,
                "source": "bybit_public_v5",
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
            "extensions": {
                "orderbook_update_id": orderbook.get("u"),
                "orderbook_sequence": orderbook.get("seq"),
            },
        }

    def _asset_from_symbol(self) -> str:
        if self.symbol.endswith("USDT"):
            return self.symbol[: -len("USDT")]
        return self.symbol

    def _ensure_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


def _safe_float(value: Any, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


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


def _first_level(levels: Any) -> list[Any] | None:
    if isinstance(levels, list) and levels and isinstance(levels[0], list) and len(levels[0]) >= 2:
        return levels[0]
    return None


def _compact_depth(bids: Any, asks: Any, *, limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index in range(limit):
        bid_level = bids[index] if isinstance(bids, list) and index < len(bids) else None
        ask_level = asks[index] if isinstance(asks, list) and index < len(asks) else None
        if not bid_level and not ask_level:
            break
        rows.append(
            {
                "level": index + 1,
                "bid_price": _safe_float(bid_level[0]) if isinstance(bid_level, list) and len(bid_level) >= 2 else None,
                "bid_size": _safe_float(bid_level[1]) if isinstance(bid_level, list) and len(bid_level) >= 2 else None,
                "ask_price": _safe_float(ask_level[0]) if isinstance(ask_level, list) and len(ask_level) >= 2 else None,
                "ask_size": _safe_float(ask_level[1]) if isinstance(ask_level, list) and len(ask_level) >= 2 else None,
            }
        )
    return rows
