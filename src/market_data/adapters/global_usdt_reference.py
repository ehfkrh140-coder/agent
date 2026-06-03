from __future__ import annotations

import json
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
        self.ticker_candidates = self._ticker_candidates()
        self.http_client = http_client or ReadOnlyHttpClient(
            timeout_seconds=float(self.config.get("timeout_seconds") or 10),
            max_retries=int(self.config.get("max_retries") or 2),
            user_agent=str(self.config.get("user_agent") or "agent-council-market-data-v1"),
        )
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc))

    def fetch_snapshot(self) -> dict[str, Any]:
        if not self.base_url or not self.ticker_candidates:
            raise MarketDataAdapterError(
                f"Global USDT reference adapter {self.adapter_id} requires base_url and ticker_path or ticker_candidates"
            )

        diagnostics: list[dict[str, Any]] = []
        for index, candidate in enumerate(self.ticker_candidates):
            diagnostic = self._base_diagnostic(index, candidate)
            try:
                response = self.http_client.get_json(self.base_url, candidate["ticker_path"], candidate["ticker_params"])
            except Exception as exc:  # noqa: BLE001 - convert every candidate failure to safe diagnostics
                diagnostic.update(_diagnostic_from_error(exc, "http_get"))
                diagnostics.append(diagnostic)
                continue

            collected_at = _ensure_utc(self.now_fn())
            diagnostic.update(
                {
                    "parser_stage": "http_get",
                    "http_status": getattr(response, "http_status", None),
                    "safe_response_preview": _safe_preview(getattr(response, "safe_response_preview", None) or response.data),
                }
            )
            try:
                parsed = self._parse_ticker(response.data, candidate["response_format"])
            except Exception as exc:  # noqa: BLE001 - preserve parser diagnostics for this candidate
                diagnostic.update(_diagnostic_from_error(exc, "parse", response.data))
                diagnostics.append(diagnostic)
                continue

            raw_bid = _safe_float(parsed.get("bid"))
            raw_ask = _safe_float(parsed.get("ask"))
            if raw_bid is None or raw_ask is None:
                diagnostic.update(
                    {
                        "parser_stage": "parse",
                        "error_message": f"{self.adapter_id} did not expose both bid and ask for {self.market_symbol}",
                    }
                )
                diagnostics.append(diagnostic)
                continue

            try:
                bid, ask = _normalize_bid_ask(raw_bid, raw_ask, candidate.get("normalize"))
            except MarketDataAdapterError as exc:
                diagnostic.update(_diagnostic_from_error(exc, "normalize", response.data))
                diagnostics.append(diagnostic)
                continue
            if bid <= 0 or ask <= 0 or bid >= ask:
                diagnostic.update(
                    {
                        "parser_stage": "normalize",
                        "error_message": f"normalized bid/ask invalid for {self.adapter_id}: bid={bid}, ask={ask}",
                    }
                )
                diagnostics.append(diagnostic)
                continue

            timestamp = _coerce_timestamp(parsed.get("timestamp")) or collected_at
            max_data_age_ms = max(0, int(collected_at.timestamp() * 1000) - int(timestamp.timestamp() * 1000))
            diagnostic.update(
                {
                    "parser_stage": "normalize",
                    "error_message": None,
                    "api_market": parsed.get("symbol") or candidate["ticker_params"].get("symbol") or candidate["ticker_params"].get("instId"),
                    "normalize": candidate.get("normalize", "direct"),
                }
            )
            selected_candidate = _selected_candidate(index, candidate)
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
                    "response_format": candidate["response_format"],
                    "api_market": diagnostic["api_market"],
                    "normalized_market_symbol": self.market_symbol,
                    "normalize": candidate.get("normalize", "direct"),
                    "raw_bid": raw_bid,
                    "raw_ask": raw_ask,
                    "selected_candidate": selected_candidate,
                    "diagnostics_summary": diagnostic,
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
                    "endpoint": candidate["ticker_path"],
                    "ticker_path": candidate["ticker_path"],
                    "base_url": self.base_url,
                    "request_params": dict(candidate["ticker_params"]),
                    "response_format": candidate["response_format"],
                    "selected_candidate": selected_candidate,
                    "global_reference_diagnostics": diagnostics + [diagnostic],
                    "public_read_only": True,
                    "no_private_api": True,
                },
                "extensions": {
                    "raw_summary": {"ticker_url": response.url},
                    "selected_candidate": selected_candidate,
                    "global_reference_diagnostics": diagnostics + [diagnostic],
                },
            }

        error = MarketDataAdapterError(
            f"Global USDT reference adapter {self.adapter_id} failed all candidates: {_format_diagnostics(diagnostics)}"
        )
        setattr(error, "diagnostics", diagnostics)
        raise error

    def _ticker_candidates(self) -> list[dict[str, Any]]:
        raw_candidates = self.config.get("ticker_candidates")
        candidates: list[dict[str, Any]] = []
        if isinstance(raw_candidates, list):
            for raw in raw_candidates:
                if not isinstance(raw, dict):
                    continue
                path = str(raw.get("ticker_path") or raw.get("endpoint") or self.ticker_path or "")
                params = dict(raw.get("ticker_params") or raw.get("params") or {})
                candidates.append(
                    {
                        "ticker_path": path,
                        "ticker_params": params,
                        "response_format": str(raw.get("response_format") or self.response_format),
                        "normalize": str(raw.get("normalize") or "direct"),
                    }
                )
        if not candidates and self.ticker_path:
            candidates.append(
                {
                    "ticker_path": self.ticker_path,
                    "ticker_params": self.ticker_params,
                    "response_format": self.response_format,
                    "normalize": str(self.config.get("normalize") or "direct"),
                }
            )
        return candidates

    def _base_diagnostic(self, index: int, candidate: dict[str, Any]) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "venue_id": self.venue_id,
            "candidate_index": index,
            "base_url": self.base_url,
            "endpoint": candidate.get("ticker_path"),
            "ticker_path": candidate.get("ticker_path"),
            "request_params": dict(candidate.get("ticker_params") or {}),
            "response_format": candidate.get("response_format"),
            "parser_stage": None,
            "http_status": None,
            "exchange_error_code": None,
            "exchange_error_message": None,
            "error_message": None,
        }

    def _parse_ticker(self, data: Any, response_format: str) -> dict[str, Any]:
        if response_format == "binance_book_ticker":
            return _parse_binance_book_ticker(data)
        if response_format == "bybit_v5_ticker":
            return _parse_bybit_v5_ticker(data)
        if response_format == "okx_ticker":
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


def _normalize_bid_ask(raw_bid: float, raw_ask: float, normalize: Any) -> tuple[float, float]:
    if str(normalize or "direct") == "inverse":
        if raw_bid <= 0 or raw_ask <= 0:
            raise MarketDataAdapterError(f"cannot inverse-normalize non-positive raw bid/ask: bid={raw_bid}, ask={raw_ask}")
        return 1.0 / raw_ask, 1.0 / raw_bid
    return raw_bid, raw_ask


def _diagnostic_from_error(exc: Exception, parser_stage: str, payload: Any | None = None) -> dict[str, Any]:
    text = str(exc)
    result: dict[str, Any] = {
        "parser_stage": parser_stage,
        "error_message": text,
        "safe_response_preview": _safe_preview(getattr(exc, "safe_response_preview", None) or payload),
    }
    http_status = getattr(exc, "http_status", None)
    if http_status is not None:
        result["http_status"] = http_status
    code = getattr(exc, "exchange_error_code", None)
    message = getattr(exc, "exchange_error_message", None)
    payload_code, payload_message = _exchange_error(payload)
    code = code if code is not None else payload_code
    message = message if message is not None else payload_message
    if code is None or message is None:
        parsed_code, parsed_message = _exchange_error_from_text(text)
        code = code if code is not None else parsed_code
        message = message if message is not None else parsed_message
    if code is not None:
        result["exchange_error_code"] = code
    if message is not None:
        result["exchange_error_message"] = message
    return result


def _exchange_error(payload: Any | None) -> tuple[Any | None, Any | None]:
    if not isinstance(payload, dict):
        return None, None
    if "retCode" in payload or "retMsg" in payload:
        return payload.get("retCode"), payload.get("retMsg")
    if "code" in payload or "msg" in payload:
        return payload.get("code"), payload.get("msg")
    return payload.get("code"), payload.get("msg") or payload.get("message")


def _exchange_error_from_text(text: str) -> tuple[str | None, str | None]:
    if "Bybit reference status " in text and ":" in text:
        tail = text.split("Bybit reference status ", 1)[1]
        code, message = tail.split(":", 1)
        return code.strip(), message.strip()
    if "OKX reference status " in text and ":" in text:
        tail = text.split("OKX reference status ", 1)[1]
        code, message = tail.split(":", 1)
        return code.strip(), message.strip()
    return None, None


def _selected_candidate(index: int, candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_index": index,
        "ticker_path": candidate.get("ticker_path"),
        "endpoint": candidate.get("ticker_path"),
        "request_params": dict(candidate.get("ticker_params") or {}),
        "response_format": candidate.get("response_format"),
        "normalize": candidate.get("normalize", "direct"),
    }


def _format_diagnostics(diagnostics: list[dict[str, Any]]) -> str:
    parts = []
    for item in diagnostics:
        params = item.get("request_params") or {}
        symbol = params.get("symbol") or params.get("instId") or params
        parts.append(
            f"{item.get('adapter_id')}[{item.get('venue_id')}] candidate={item.get('candidate_index')} "
            f"endpoint={item.get('endpoint')} symbol={symbol} stage={item.get('parser_stage')} "
            f"status={item.get('http_status')} code={item.get('exchange_error_code')} "
            f"message={item.get('exchange_error_message') or item.get('error_message')}"
        )
    return "; ".join(parts) or "no diagnostics"


def _safe_preview(value: Any | None, *, limit: int = 500) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, ensure_ascii=False, sort_keys=True)
        except TypeError:
            text = str(value)
    return text[:limit]


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
        numeric = numeric // 1000
    try:
        return datetime.fromtimestamp(numeric, tz=timezone.utc)
    except (OSError, OverflowError, ValueError):
        return None


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
