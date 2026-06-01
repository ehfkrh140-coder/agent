from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml

from src.market_data.adapters.base import MarketDataAdapter, MarketDataAdapterError
from src.market_data.http_client import HttpJsonResponse


class UpbitPublicSpotAdapter(MarketDataAdapter):
    """Public read-only Upbit spot ticker/orderbook adapter."""

    adapter_type = "upbit_public_spot"

    def __init__(
        self,
        adapter_id: str,
        *,
        config: dict[str, Any] | None = None,
        http_client: Any | None = None,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(adapter_id, config=config)
        self.base_url = str(self.config.get("base_url") or "https://api.upbit.com")
        self.market = str(self.config.get("market") or "KRW-BTC")
        self.display_symbol = str(self.config.get("display_symbol") or "BTC/KRW")
        self.ticker_path = str(self.config.get("ticker_path") or "/v1/ticker")
        self.orderbook_path = str(self.config.get("orderbook_path") or "/v1/orderbook")
        self.orderbook_limit = int(self.config.get("orderbook_limit") or 15)
        self.fee_config_path = str(self.config.get("fee_config_path") or "configs/spot_fees.yaml")
        self.http_client = http_client or _UpbitReadOnlyHttpClient(
            timeout_seconds=float(self.config.get("timeout_seconds") or 10),
            max_retries=int(self.config.get("max_retries") or 2),
            user_agent=str(self.config.get("user_agent") or "agent-council-market-data-v1"),
        )
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc))

    def fetch_snapshot(self) -> dict[str, Any]:
        ticker_response = self.http_client.get_json(self.base_url, self.ticker_path, {"markets": self.market})
        orderbook_response = self.http_client.get_json(self.base_url, self.orderbook_path, {"markets": self.market})
        collected_at = _ensure_utc(self.now_fn())
        ticker = _first_object(ticker_response.data, "Upbit ticker")
        orderbook = _first_object(orderbook_response.data, "Upbit orderbook")
        observation = self._observation(
            ticker,
            orderbook,
            collected_at,
            latency_ms=ticker_response.elapsed_ms + orderbook_response.elapsed_ms,
        )
        return {
            "packet_id": f"upbit_{self.market.lower()}_spot_{collected_at.strftime('%Y%m%d_%H%M%S')}",
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
                "endpoints": [self.ticker_path, self.orderbook_path],
                "base_url": self.base_url,
            },
            "extensions": {
                "raw_summary": {
                    "ticker_url": ticker_response.url,
                    "orderbook_url": orderbook_response.url,
                }
            },
        }

    def _observation(
        self,
        ticker: dict[str, Any],
        orderbook: dict[str, Any],
        collected_at: datetime, latency_ms: int
    ) -> dict[str, Any]:
        units = orderbook.get("orderbook_units") or []
        best = units[0] if units and isinstance(units[0], dict) else {}
        bid = _safe_float(best.get("bid_price"))
        ask = _safe_float(best.get("ask_price"))
        bid_size = _safe_float(best.get("bid_size"))
        ask_size = _safe_float(best.get("ask_size"))
        timestamp_ms = _safe_int(orderbook.get("timestamp")) or _safe_int(ticker.get("timestamp"))
        timestamp = _datetime_from_ms(timestamp_ms) or collected_at
        max_data_age_ms = max(0, int(collected_at.timestamp() * 1000) - int(timestamp.timestamp() * 1000))
        top_notional = _min_not_none(
            bid * bid_size if bid is not None and bid_size is not None else None,
            ask * ask_size if ask is not None and ask_size is not None else None,
        )
        return {
            "observation_id": f"upbit_{self.market.lower().replace('-', '_')}_spot",
            "venue_id": "upbit",
            "venue_name": "Upbit",
            "market_symbol": self.display_symbol,
            "instrument_type": "spot",
            "region": "KR",
            "last_price": _safe_float(ticker.get("trade_price")),
            "bid": bid,
            "ask": ask,
            "bid_size": bid_size,
            "ask_size": ask_size,
            "base_volume_24h": _safe_float(ticker.get("acc_trade_volume_24h")),
            "quote_volume_24h": _safe_float(ticker.get("acc_trade_price_24h")),
            "timestamp_utc": timestamp.isoformat(),
            "fees": _fee_snapshot("upbit", self.display_symbol, self.fee_config_path),
            "liquidity": {
                "orderbook_depth_available": bool(units),
                "volume_available": ticker.get("acc_trade_volume_24h") not in (None, ""),
                "estimated_executable_notional": top_notional,
                "estimated_slippage_pct": 0.0 if bool(units) else None,
                "depth_levels": _upbit_depth(units, limit=self.orderbook_limit),
            },
            "data_quality": {
                "timestamps_available": timestamp_ms is not None,
                "timestamps_aligned": None,
                "max_data_age_ms": max_data_age_ms,
                "source": "upbit_public_v1" if timestamp_ms is not None else "local_timestamp_fallback",
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
            "extensions": {"api_market": self.market},
        }


class _UpbitReadOnlyHttpClient:
    """Stdlib-only public GET helper that accepts Upbit array response roots."""

    def __init__(self, *, timeout_seconds: float, max_retries: int, user_agent: str) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.user_agent = user_agent

    def get_json(self, base_url: str, path: str, params: dict[str, Any] | None = None) -> HttpJsonResponse:
        if not path.startswith("/"):
            raise MarketDataAdapterError("HTTP path must be absolute and read-only")
        query = urllib.parse.urlencode({key: value for key, value in (params or {}).items() if value is not None})
        url = urllib.parse.urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
        if query:
            url = f"{url}?{query}"
        headers = {"User-Agent": self.user_agent, "Accept": "application/json"}
        request = urllib.request.Request(url, headers=headers, method="GET")
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            started = time.perf_counter()
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    status = getattr(response, "status", response.getcode())
                    body = response.read().decode("utf-8", errors="replace")
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                if status < 200 or status >= 300:
                    raise MarketDataAdapterError(f"HTTP status {status} for {url}")
                try:
                    data = json.loads(body)
                except json.JSONDecodeError as exc:
                    raise MarketDataAdapterError(f"Invalid JSON response from {url}") from exc
                return HttpJsonResponse(data=data, elapsed_ms=elapsed_ms, url=url)
            except urllib.error.HTTPError as exc:
                last_error = MarketDataAdapterError(f"HTTP status {exc.code} for {url}")
            except urllib.error.URLError as exc:
                last_error = MarketDataAdapterError(f"Network error for {url}: {exc.reason}")
            except TimeoutError:
                last_error = MarketDataAdapterError(f"Timeout fetching {url}")
            except MarketDataAdapterError as exc:
                last_error = exc
            if attempt < self.max_retries:
                continue
        if last_error is None:
            raise MarketDataAdapterError(f"Unknown HTTP error for {url}")
        raise MarketDataAdapterError(str(last_error)) from last_error


def _first_object(data: Any, label: str) -> dict[str, Any]:
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data[0]
    if isinstance(data, dict):
        return data
    raise MarketDataAdapterError(f"{label} response has no object entry")


def _upbit_depth(units: Any, *, limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not isinstance(units, list):
        return rows
    for index, unit in enumerate(units[:limit]):
        if not isinstance(unit, dict):
            continue
        rows.append(
            {
                "level": index + 1,
                "bid_price": _safe_float(unit.get("bid_price")),
                "bid_size": _safe_float(unit.get("bid_size")),
                "ask_price": _safe_float(unit.get("ask_price")),
                "ask_size": _safe_float(unit.get("ask_size")),
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
