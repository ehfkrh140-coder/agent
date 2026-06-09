"""Public read-only Spot-Futures Basis adapters.

These adapters are intentionally analysis-only. They accept injectable HTTP
clients, fetch public no-key spot/perp payloads, and connect the existing parser,
readiness helper, and pure packet builder. They do not register themselves,
write files, call Council, alert, or execute trades.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Mapping

from src.market_data.adapters.base import MarketDataAdapter, MarketDataAdapterError
from src.market_data.http_client import ReadOnlyHttpClient
from src.market_data.parsers.spot_futures_basis import (
    build_spot_futures_basis_source_bundle,
    parse_binance_perp_observation,
    parse_binance_spot_observation,
    parse_bybit_perp_observation,
    parse_bybit_spot_observation,
)
from src.market_data.spot_futures_basis_packet_builder import build_spot_futures_basis_opportunity_packet
from src.strategy.spot_futures_basis_readiness import evaluate_spot_futures_basis_readiness

DEFAULT_ADAPTER_ID = "live_binance_spot_futures_basis_btcusdt"
DEFAULT_BYBIT_ADAPTER_ID = "live_bybit_spot_futures_basis_btcusdt"
ADAPTER_TYPE = "binance_spot_futures_basis"
BYBIT_ADAPTER_TYPE = "bybit_spot_futures_basis"
STRATEGY_FAMILY = "spot_futures_basis"
STRATEGY_ID = "spot_futures_basis_v0"
STATUS = "experimental_non_active_no_trade_only"
NO_TRADE_EXECUTION_POLICY = "NO_TRADE_ONLY"
BINANCE_VENUE_ID = "binance"
BYBIT_VENUE_ID = "bybit"
BINANCE_SPOT_VENUE_NAME = "Binance Spot"
BINANCE_USDM_VENUE_NAME = "Binance USDⓈ-M Futures"
BYBIT_SPOT_VENUE_NAME = "Bybit Spot"
BYBIT_DERIVATIVES_VENUE_NAME = "Bybit Derivatives V5"
DEFAULT_SPOT_BASE_URL = "https://api.binance.com"
DEFAULT_FUTURES_BASE_URL = "https://fapi.binance.com"
DEFAULT_BYBIT_BASE_URL = "https://api.bybit.com"
DEFAULT_SYMBOL = "BTCUSDT"
DEFAULT_DEPTH_LIMIT = 5
DEFAULT_BYBIT_SPOT_CATEGORY = "spot"
DEFAULT_BYBIT_PERP_CATEGORY = "linear"

_ENDPOINT_SPECS = (
    {
        "name": "spot_book_ticker",
        "base": "spot",
        "path": "/api/v3/ticker/bookTicker",
        "params": "spot_symbol",
    },
    {
        "name": "spot_depth",
        "base": "spot",
        "path": "/api/v3/depth",
        "params": "spot_depth",
    },
    {
        "name": "spot_exchange_info",
        "base": "spot",
        "path": "/api/v3/exchangeInfo",
        "params": "spot_symbol",
    },
    {
        "name": "futures_book_ticker",
        "base": "futures",
        "path": "/fapi/v1/ticker/bookTicker",
        "params": "perp_symbol",
    },
    {
        "name": "futures_depth",
        "base": "futures",
        "path": "/fapi/v1/depth",
        "params": "perp_depth",
    },
    {
        "name": "futures_premium_index",
        "base": "futures",
        "path": "/fapi/v1/premiumIndex",
        "params": "perp_symbol",
    },
    {
        "name": "futures_exchange_info",
        "base": "futures",
        "path": "/fapi/v1/exchangeInfo",
        "params": "perp_symbol",
    },
)


_BYBIT_ENDPOINT_SPECS = (
    {
        "name": "spot_ticker",
        "path": "/v5/market/tickers",
        "params": "spot_ticker",
    },
    {
        "name": "spot_orderbook",
        "path": "/v5/market/orderbook",
        "params": "spot_orderbook",
    },
    {
        "name": "spot_instruments_info",
        "path": "/v5/market/instruments-info",
        "params": "spot_instruments_info",
    },
    {
        "name": "linear_ticker",
        "path": "/v5/market/tickers",
        "params": "linear_ticker",
    },
    {
        "name": "linear_orderbook",
        "path": "/v5/market/orderbook",
        "params": "linear_orderbook",
    },
    {
        "name": "linear_instruments_info",
        "path": "/v5/market/instruments-info",
        "params": "linear_instruments_info",
    },
)

_REQUIRED_ASSUMPTIONS = (
    "public no-key endpoints only",
    "analysis-only packet",
    "no private API",
    "no trading behavior",
    "WATCH is not ENTER",
    "mark price is not executable",
)


class BinanceSpotFuturesBasisAdapter(MarketDataAdapter):
    """First public-read-only Spot-Futures Basis adapter for Binance BTCUSDT."""

    adapter_type = ADAPTER_TYPE

    def __init__(
        self,
        adapter_id: str = DEFAULT_ADAPTER_ID,
        *,
        config: Mapping[str, Any] | None = None,
        http_client: Any | None = None,
        now_fn: Callable[[], str | datetime] | None = None,
    ) -> None:
        super().__init__(adapter_id, config=config)
        self.http_client = http_client or ReadOnlyHttpClient()
        self.now_fn = now_fn or _utc_now
        self.spot_base_url = str(self.config.get("spot_base_url", DEFAULT_SPOT_BASE_URL))
        self.futures_base_url = str(self.config.get("futures_base_url", DEFAULT_FUTURES_BASE_URL))
        self.spot_symbol = str(self.config.get("spot_symbol", DEFAULT_SYMBOL))
        self.perp_symbol = str(self.config.get("perp_symbol", DEFAULT_SYMBOL))
        self.depth_limit = self.config.get("depth_limit", DEFAULT_DEPTH_LIMIT)

    def fetch_snapshot(self) -> dict[str, Any]:
        """Fetch public payloads and return an analysis-only OpportunityPacket dict."""

        fetched_at_utc = _format_utc(self.now_fn())
        payloads: dict[str, dict[str, Any]] = {}
        diagnostics: list[dict[str, Any]] = []

        for spec in _ENDPOINT_SPECS:
            payload, diagnostic = self._public_get(spec)
            payloads[spec["name"]] = payload
            diagnostics.append(diagnostic)

        spot_observation = parse_binance_spot_observation(
            payloads["spot_book_ticker"],
            payloads["spot_depth"],
            payloads["spot_exchange_info"],
            fetched_at_utc=fetched_at_utc,
            latency_ms=_max_elapsed_ms(diagnostics, ("spot_book_ticker", "spot_depth", "spot_exchange_info")),
        )
        perp_observation = parse_binance_perp_observation(
            payloads["futures_book_ticker"],
            payloads["futures_depth"],
            payloads["futures_premium_index"],
            payloads["futures_exchange_info"],
            fetched_at_utc=fetched_at_utc,
            latency_ms=_max_elapsed_ms(
                diagnostics,
                ("futures_book_ticker", "futures_depth", "futures_premium_index", "futures_exchange_info"),
            ),
        )
        source_bundle = build_spot_futures_basis_source_bundle(spot_observation, perp_observation)
        readiness_result = evaluate_spot_futures_basis_readiness(source_bundle)
        packet = build_spot_futures_basis_opportunity_packet(
            source_bundle,
            readiness_result,
            created_at_utc=fetched_at_utc,
        )
        self._attach_adapter_extensions(packet, diagnostics, fetched_at_utc)
        return packet

    def _public_get(self, spec: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        base_url = self.spot_base_url if spec["base"] == "spot" else self.futures_base_url
        path = str(spec["path"])
        params = self._params_for(str(spec["params"]))
        parser_stage = str(spec["name"])
        diagnostic: dict[str, Any] = {
            "endpoint": path,
            "params": dict(params),
            "parser_stage": parser_stage,
        }
        try:
            response = self.http_client.get_json(base_url, path, params)
        except Exception as exc:
            diagnostic["error_type"] = exc.__class__.__name__
            diagnostic["error_message"] = _safe_error_message(exc)
            error = MarketDataAdapterError(f"Public endpoint fetch failed for {parser_stage}: {_safe_error_message(exc)}")
            setattr(error, "diagnostic", diagnostic)
            raise error from exc

        payload = _response_payload(response)
        if not isinstance(payload, dict):
            error = MarketDataAdapterError(f"Public endpoint returned non-object payload for {parser_stage}")
            setattr(error, "diagnostic", diagnostic)
            raise error
        diagnostic.update(_response_diagnostic_fields(response))
        diagnostic.update(_payload_diagnostic_fields(payload))
        return payload, diagnostic

    def _params_for(self, params_kind: str) -> dict[str, Any]:
        if params_kind == "spot_symbol":
            return {"symbol": self.spot_symbol}
        if params_kind == "perp_symbol":
            return {"symbol": self.perp_symbol}
        if params_kind == "spot_depth":
            return {"symbol": self.spot_symbol, "limit": self.depth_limit}
        if params_kind == "perp_depth":
            return {"symbol": self.perp_symbol, "limit": self.depth_limit}
        raise MarketDataAdapterError(f"Unknown public params kind: {params_kind}")

    def _attach_adapter_extensions(
        self,
        packet: dict[str, Any],
        diagnostics: list[dict[str, Any]],
        fetched_at_utc: str,
    ) -> None:
        extensions = packet.setdefault("extensions", {})
        assumptions = extensions.setdefault("assumptions", [])
        if not isinstance(assumptions, list):
            assumptions = []
            extensions["assumptions"] = assumptions
        for assumption in _REQUIRED_ASSUMPTIONS:
            if assumption not in assumptions:
                assumptions.append(assumption)
        extensions["adapter_metadata"] = {
            "adapter_id": self.adapter_id,
            "adapter_type": self.adapter_type,
            "venue_id": BINANCE_VENUE_ID,
            "spot_venue_name": BINANCE_SPOT_VENUE_NAME,
            "perp_venue_name": BINANCE_USDM_VENUE_NAME,
            "strategy_family": STRATEGY_FAMILY,
            "strategy_id": STRATEGY_ID,
            "status": STATUS,
            "experimental_strategy": True,
            "non_active_strategy": True,
            "no_trade_only": True,
            "execution_policy": NO_TRADE_EXECUTION_POLICY,
            "endpoints": [spec["path"] for spec in _ENDPOINT_SPECS],
            "fetched_at_utc": fetched_at_utc,
        }
        extensions["diagnostics"] = diagnostics



class BybitSpotFuturesBasisAdapter(MarketDataAdapter):
    """Public-read-only Spot-Futures Basis adapter for Bybit BTCUSDT."""

    adapter_type = BYBIT_ADAPTER_TYPE

    def __init__(
        self,
        adapter_id: str = DEFAULT_BYBIT_ADAPTER_ID,
        *,
        config: Mapping[str, Any] | None = None,
        http_client: Any | None = None,
        now_fn: Callable[[], str | datetime] | None = None,
    ) -> None:
        super().__init__(adapter_id, config=config)
        self.http_client = http_client or ReadOnlyHttpClient()
        self.now_fn = now_fn or _utc_now
        self.base_url = str(self.config.get("base_url", DEFAULT_BYBIT_BASE_URL))
        self.spot_symbol = str(self.config.get("spot_symbol", DEFAULT_SYMBOL))
        self.perp_symbol = str(self.config.get("perp_symbol", DEFAULT_SYMBOL))
        self.spot_category = str(self.config.get("spot_category", DEFAULT_BYBIT_SPOT_CATEGORY))
        self.perp_category = str(self.config.get("perp_category", DEFAULT_BYBIT_PERP_CATEGORY))
        self.depth_limit = self.config.get("depth_limit", DEFAULT_DEPTH_LIMIT)

    def fetch_snapshot(self) -> dict[str, Any]:
        """Fetch public Bybit payloads and return an analysis-only OpportunityPacket dict."""

        fetched_at_utc = _format_utc(self.now_fn())
        payloads: dict[str, dict[str, Any]] = {}
        diagnostics: list[dict[str, Any]] = []

        for spec in _BYBIT_ENDPOINT_SPECS:
            payload, diagnostic = self._public_get(spec)
            payloads[spec["name"]] = payload
            diagnostics.append(diagnostic)

        spot_observation = parse_bybit_spot_observation(
            payloads["spot_ticker"],
            payloads["spot_orderbook"],
            payloads["spot_instruments_info"],
            created_at_utc=fetched_at_utc,
            latency_ms=_max_elapsed_ms(diagnostics, ("spot_ticker", "spot_orderbook", "spot_instruments_info")),
        )
        perp_observation = parse_bybit_perp_observation(
            payloads["linear_ticker"],
            payloads["linear_orderbook"],
            payloads["linear_instruments_info"],
            created_at_utc=fetched_at_utc,
            latency_ms=_max_elapsed_ms(
                diagnostics,
                ("linear_ticker", "linear_orderbook", "linear_instruments_info"),
            ),
        )
        source_bundle = build_spot_futures_basis_source_bundle(spot_observation, perp_observation)
        readiness_result = evaluate_spot_futures_basis_readiness(source_bundle)
        packet = build_spot_futures_basis_opportunity_packet(
            source_bundle,
            readiness_result,
            created_at_utc=fetched_at_utc,
        )
        self._attach_adapter_extensions(packet, diagnostics, fetched_at_utc)
        return packet

    def _public_get(self, spec: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        path = str(spec["path"])
        params = self._params_for(str(spec["params"]))
        parser_stage = str(spec["name"])
        diagnostic: dict[str, Any] = {
            "endpoint": path,
            "params": dict(params),
            "parser_stage": parser_stage,
        }
        try:
            response = self.http_client.get_json(self.base_url, path, params)
        except Exception as exc:
            diagnostic["error_type"] = exc.__class__.__name__
            diagnostic["error_message"] = _safe_error_message(exc)
            safe_stage = parser_stage.replace("orderbook", "public_book")
            error = MarketDataAdapterError(f"Public endpoint fetch failed for {safe_stage}: {_safe_error_message(exc)}")
            setattr(error, "diagnostic", diagnostic)
            raise error from exc

        payload = _response_payload(response)
        if not isinstance(payload, dict):
            error = MarketDataAdapterError(f"Public endpoint returned non-object payload for {parser_stage}")
            setattr(error, "diagnostic", diagnostic)
            raise error
        diagnostic.update(_response_diagnostic_fields(response))
        diagnostic.update(_payload_diagnostic_fields(payload))
        return payload, diagnostic

    def _params_for(self, params_kind: str) -> dict[str, Any]:
        if params_kind == "spot_ticker":
            return {"category": self.spot_category, "symbol": self.spot_symbol}
        if params_kind == "spot_orderbook":
            return {"category": self.spot_category, "symbol": self.spot_symbol, "limit": self.depth_limit}
        if params_kind == "spot_instruments_info":
            return {"category": self.spot_category, "symbol": self.spot_symbol}
        if params_kind == "linear_ticker":
            return {"category": self.perp_category, "symbol": self.perp_symbol}
        if params_kind == "linear_orderbook":
            return {"category": self.perp_category, "symbol": self.perp_symbol, "limit": self.depth_limit}
        if params_kind == "linear_instruments_info":
            return {"category": self.perp_category, "symbol": self.perp_symbol}
        raise MarketDataAdapterError(f"Unknown public params kind: {params_kind}")

    def _attach_adapter_extensions(
        self,
        packet: dict[str, Any],
        diagnostics: list[dict[str, Any]],
        fetched_at_utc: str,
    ) -> None:
        extensions = packet.setdefault("extensions", {})
        assumptions = extensions.setdefault("assumptions", [])
        if not isinstance(assumptions, list):
            assumptions = []
            extensions["assumptions"] = assumptions
        for assumption in _REQUIRED_ASSUMPTIONS:
            if assumption not in assumptions:
                assumptions.append(assumption)
        extensions["adapter_metadata"] = {
            "adapter_id": self.adapter_id,
            "adapter_type": self.adapter_type,
            "venue_id": BYBIT_VENUE_ID,
            "spot_venue_name": BYBIT_SPOT_VENUE_NAME,
            "perp_venue_name": BYBIT_DERIVATIVES_VENUE_NAME,
            "spot_category": self.spot_category,
            "perp_category": self.perp_category,
            "strategy_family": STRATEGY_FAMILY,
            "strategy_id": STRATEGY_ID,
            "status": STATUS,
            "experimental_strategy": True,
            "non_active_strategy": True,
            "no_trade_only": True,
            "execution_policy": NO_TRADE_EXECUTION_POLICY,
            "endpoints": [spec["path"] for spec in _BYBIT_ENDPOINT_SPECS],
            "fetched_at_utc": fetched_at_utc,
        }
        extensions["diagnostics"] = diagnostics


def _response_payload(response: Any) -> Any:
    if isinstance(response, dict):
        return response.get("data", response)
    return getattr(response, "data", None)


def _response_diagnostic_fields(response: Any) -> dict[str, Any]:
    if isinstance(response, dict):
        return {
            key: response[key]
            for key in ("http_status", "safe_response_preview", "elapsed_ms", "url")
            if key in response
        }
    fields: dict[str, Any] = {}
    for key in ("http_status", "safe_response_preview", "elapsed_ms", "url"):
        value = getattr(response, key, None)
        if value is not None:
            fields[key] = value
    return fields


def _payload_diagnostic_fields(payload: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for key in ("retCode", "retMsg"):
        if key in payload:
            fields[key] = payload[key]
    return fields


def _max_elapsed_ms(diagnostics: list[dict[str, Any]], parser_stages: tuple[str, ...]) -> int | float | None:
    elapsed_values = [
        diagnostic.get("elapsed_ms")
        for diagnostic in diagnostics
        if diagnostic.get("parser_stage") in parser_stages and isinstance(diagnostic.get("elapsed_ms"), int | float)
    ]
    if not elapsed_values:
        return None
    return max(elapsed_values)


def _safe_error_message(exc: Exception) -> str:
    message = str(exc)
    for forbidden in (
        "apiKey",
        "secret",
        "token",
        "account",
        "balance",
        "position",
        "orderId",
        "clientOrderId",
        "order",
        "cancel",
        "withdraw",
        "deposit",
        "transfer",
        "privateKey",
    ):
        message = message.replace(forbidden, "[redacted]")
    return message


def _format_utc(value: str | datetime) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, str) and value:
        return value
    raise MarketDataAdapterError("now_fn must return a datetime or non-empty UTC timestamp string")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
