from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable

from src.market_data.adapters.base import MarketDataAdapter, MarketDataAdapterError
from src.market_data.http_client import HttpJsonResponse, ReadOnlyHttpClient
from src.market_data.parsers.mark_orderbook_gap_hunt import parse_mark_orderbook_gap_snapshot
from src.schemas.opportunity_packet import (
    DataQualitySnapshot,
    DerivativesSnapshot,
    DetectorMetadata,
    LiquiditySnapshot,
    MarketObservation,
    OpportunityCandidate,
    OpportunityPacket,
    VenueHealthSnapshot,
)
from src.strategy.mark_orderbook_gap_hunt_readiness import evaluate_mark_orderbook_gap_readiness


MARK_ORDERBOOK_GAP_EXECUTION_POLICY = "NO_TRADE_ONLY"
MARK_ORDERBOOK_GAP_COMMON_METADATA = {
    "experimental_strategy": True,
    "non_active_strategy": True,
    "no_trade_only": True,
    "execution_policy": MARK_ORDERBOOK_GAP_EXECUTION_POLICY,
}
MARK_ORDERBOOK_GAP_EXTENSION_ASSUMPTIONS = (
    "public no-key endpoints only",
    "analysis-only packet",
    "adapter may be registered but remains disabled/experimental/non-active unless explicitly enabled in config",
    "sampling integration is separate from packet generation",
    "timestamp/data_age policy unchanged",
    "no private API",
    "no trading behavior",
)
MARK_ORDERBOOK_GAP_CANDIDATE_ASSUMPTIONS = (
    "mark price is not executable",
    "WATCH is analysis-only",
    "no private API",
    "no trading behavior",
)


def _mark_orderbook_gap_adapter_metadata(
    *,
    adapter_id: str,
    adapter_type: str,
    venue_fields: dict[str, Any],
    endpoints: list[str],
    fetched_at_utc: datetime,
) -> dict[str, Any]:
    return {
        "adapter_id": adapter_id,
        "adapter_type": adapter_type,
        **venue_fields,
        **MARK_ORDERBOOK_GAP_COMMON_METADATA,
        "endpoints": endpoints,
        "fetched_at_utc": fetched_at_utc.isoformat(),
    }


def _mark_orderbook_gap_extension_assumptions() -> list[str]:
    return list(MARK_ORDERBOOK_GAP_EXTENSION_ASSUMPTIONS)


def _mark_orderbook_gap_candidate_assumptions() -> list[str]:
    return list(MARK_ORDERBOOK_GAP_CANDIDATE_ASSUMPTIONS)


class BinanceMarkOrderbookGapHuntAdapter(MarketDataAdapter):
    """Public read-only Binance USDⓈ-M BTCUSDT Mark-Orderbook Gap adapter.

    The adapter fetches only public no-key market-data endpoints, delegates
    parsing/readiness to pure helpers, and returns an analysis-only
    ``OpportunityPacket``. Registration/configuration is controlled outside the
    adapter; configured entries must remain disabled/experimental/non-active
    unless explicitly enabled by config review.
    """

    adapter_type = "binance_mark_orderbook_gap_hunt"

    DEFAULT_ADAPTER_ID = "live_binance_mark_orderbook_gap_btcusdt"
    BASE_URL = "https://fapi.binance.com"
    MARK_PRICE_PATH = "/fapi/v1/premiumIndex"
    ORDERBOOK_PATH = "/fapi/v1/depth"
    METADATA_PATH = "/fapi/v1/exchangeInfo"

    def __init__(
        self,
        adapter_id: str = DEFAULT_ADAPTER_ID,
        *,
        config: dict[str, Any] | None = None,
        http_client: Any | None = None,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(adapter_id, config=config)
        self.base_url = str(self.config.get("base_url") or self.BASE_URL)
        self.symbol = str(self.config.get("symbol") or "BTCUSDT")
        self.asset = str(self.config.get("asset") or "BTC")
        self.quote = str(self.config.get("quote") or "USDT")
        self.orderbook_limit = int(self.config.get("orderbook_limit") or 5)
        self.max_data_age_ms = self.config.get("max_data_age_ms")
        self.fee_slippage_buffer_pct = self.config.get("fee_slippage_buffer_pct", "0")
        self.min_net_gap_pct = self.config.get("min_net_gap_pct", "0")
        self.liquidity_pass = self.config.get("liquidity_pass", True)
        self.require_freshness = bool(self.config.get("require_freshness", False))
        self.size_or_notional_resolved = bool(self.config.get("size_or_notional_resolved", True))
        self.http_client = http_client or ReadOnlyHttpClient(
            timeout_seconds=float(self.config.get("timeout_seconds") or 10),
            max_retries=int(self.config.get("max_retries") or 2),
            user_agent=str(self.config.get("user_agent") or "agent-council-market-data-v1"),
        )
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc))

    def fetch_snapshot(self) -> dict[str, Any]:
        """Fetch public responses and return an OpportunityPacket JSON dict."""

        return self.fetch_packet().model_dump(mode="json")

    def fetch_packet(self) -> OpportunityPacket:
        """Fetch public market data and build an analysis-only packet."""

        diagnostics: list[dict[str, Any]] = []
        mark_response = self._public_get(
            self.MARK_PRICE_PATH,
            {"symbol": self.symbol},
            parser_stage="mark_price",
            diagnostics=diagnostics,
        )
        orderbook_response = self._public_get(
            self.ORDERBOOK_PATH,
            {"symbol": self.symbol, "limit": self.orderbook_limit},
            parser_stage="orderbook",
            diagnostics=diagnostics,
        )
        metadata_response = self._public_get(
            self.METADATA_PATH,
            {},
            parser_stage="metadata",
            diagnostics=diagnostics,
        )
        collected_at = _ensure_utc(self.now_fn())
        collected_at_iso = collected_at.isoformat()
        total_latency_ms = sum(diagnostic.get("elapsed_ms") or 0 for diagnostic in diagnostics)
        filtered_metadata = self._metadata_for_symbol(metadata_response.data)

        parser_output = parse_mark_orderbook_gap_snapshot(
            venue_id="binance",
            parser_mode="binance_usdm",
            mark_response=mark_response.data,
            orderbook_response=orderbook_response.data,
            metadata_response=filtered_metadata,
            ticker_response=None,
            collected_at_utc=collected_at_iso,
            latency_ms=total_latency_ms,
            max_data_age_ms=self.max_data_age_ms,
        )
        readiness = evaluate_mark_orderbook_gap_readiness(
            parser_output,
            fee_slippage_buffer_pct=self.fee_slippage_buffer_pct,
            liquidity_pass=self.liquidity_pass,
            require_freshness=self.require_freshness,
            size_or_notional_resolved=self.size_or_notional_resolved,
            min_net_gap_pct=self.min_net_gap_pct,
        )
        return self._packet(
            parser_output=parser_output,
            readiness=readiness,
            diagnostics=diagnostics,
            collected_at=collected_at,
            total_latency_ms=total_latency_ms,
        )

    def _public_get(
        self,
        path: str,
        params: dict[str, Any],
        *,
        parser_stage: str,
        diagnostics: list[dict[str, Any]],
    ) -> HttpJsonResponse:
        diagnostic: dict[str, Any] = {
            "endpoint": path,
            "params": dict(params),
            "parser_stage": parser_stage,
        }
        try:
            response = self.http_client.get_json(self.base_url, path, params)
        except Exception as exc:  # noqa: BLE001 - attach safe diagnostics to adapter error
            diagnostic.update(_diagnostic_from_error(exc))
            diagnostics.append(diagnostic)
            error = MarketDataAdapterError(f"Binance mark-orderbook public fetch failed at {parser_stage}: {exc}")
            setattr(error, "diagnostics", diagnostics)
            raise error from exc
        diagnostic.update(
            {
                "http_status": getattr(response, "http_status", None),
                "safe_response_preview": getattr(response, "safe_response_preview", None) or _safe_preview(response.data),
                "elapsed_ms": getattr(response, "elapsed_ms", None),
                "url": getattr(response, "url", None),
            }
        )
        diagnostics.append(diagnostic)
        return response

    def _metadata_for_symbol(self, metadata: dict[str, Any]) -> dict[str, Any]:
        symbols = metadata.get("symbols")
        if not isinstance(symbols, list):
            raise MarketDataAdapterError("Binance exchangeInfo response has no symbols list")
        for entry in symbols:
            if isinstance(entry, dict) and entry.get("symbol") == self.symbol:
                return {"symbols": [entry]}
        raise MarketDataAdapterError(f"Binance exchangeInfo response has no metadata for {self.symbol}")

    def _packet(
        self,
        *,
        parser_output: dict[str, Any],
        readiness: dict[str, Any],
        diagnostics: list[dict[str, Any]],
        collected_at: datetime,
        total_latency_ms: int,
    ) -> OpportunityPacket:
        observation_id = f"binance_{self.symbol.lower()}_mark_orderbook_gap"
        observation = MarketObservation(
            observation_id=observation_id,
            venue_id="binance",
            venue_name="Binance USDⓈ-M Futures",
            market_symbol=self.symbol,
            instrument_type=parser_output.get("instrument_type"),
            region="GLOBAL",
            mark_price=_float_or_none(parser_output.get("mark_price")),
            index_price=_float_or_none(parser_output.get("index_price")),
            tick=_float_or_none(parser_output.get("tick_size")),
            step=_float_or_none(parser_output.get("quantity_step")),
            bid=_float_or_none(parser_output.get("bid")),
            ask=_float_or_none(parser_output.get("ask")),
            bid_size=_float_or_none(parser_output.get("bid_size_raw")),
            ask_size=_float_or_none(parser_output.get("ask_size_raw")),
            timestamp_utc=_datetime_from_ms(parser_output.get("timestamp")),
            liquidity=LiquiditySnapshot(
                orderbook_depth_available=parser_output.get("bid") is not None and parser_output.get("ask") is not None,
                volume_available=False,
                estimated_executable_notional=None,
                estimated_slippage_pct=None,
                depth_levels=[],
            ),
            derivatives=DerivativesSnapshot(
                funding_rate_pct=_float_or_none(parser_output.get("funding_rate")),
                next_funding_time_utc=_datetime_from_ms(parser_output.get("next_funding_time")),
                mark_price=_float_or_none(parser_output.get("mark_price")),
                index_price=_float_or_none(parser_output.get("index_price")),
            ),
            data_quality=DataQualitySnapshot(
                timestamps_available=parser_output.get("timestamp") is not None,
                timestamps_aligned=None,
                max_data_age_ms=_int_or_none(parser_output.get("data_age_ms")),
                source="binance_public_usdm",
                latency_ms=total_latency_ms,
                is_realtime=True,
            ),
            health=VenueHealthSnapshot(
                api_status_known=True,
                api_ok=True,
                maintenance=False,
                trading_enabled=True,
                message=None,
            ),
            extensions={
                "instrument_id": parser_output.get("instrument_id"),
                "bid_size_unit": parser_output.get("bid_size_unit"),
                "ask_size_unit": parser_output.get("ask_size_unit"),
                "min_order_size": parser_output.get("min_order_size"),
                "min_notional": parser_output.get("min_notional"),
                "margin_asset": parser_output.get("margin_asset"),
                "parser_mode": parser_output.get("parser_mode"),
                "parser_normalized_status": parser_output.get("normalized_status"),
            },
        )
        metrics = readiness.get("metrics") or {}
        candidate = OpportunityCandidate(
            candidate_id=f"{observation_id}_candidate",
            candidate_type="mark_orderbook_gap_observation",
            strategy_family="mark_orderbook_gap_hunt",
            strategy_id="mark_orderbook_gap_hunt_v0",
            source_observation_id=observation_id,
            source_venue_id="binance",
            direction="analysis_only_mark_orderbook_gap_observation",
            gross_gap_pct=_float_or_none(metrics.get("max_observed_gap_pct")),
            estimated_net_gap_pct=_float_or_none(metrics.get("estimated_net_gap_pct")),
            long_gap_pct=_float_or_none(metrics.get("long_gap_pct")),
            short_gap_pct=_float_or_none(metrics.get("short_gap_pct")),
            liquidity_pass=metrics.get("liquidity_pass"),
            freshness_pass=metrics.get("freshness_pass"),
            gap_pass=readiness.get("readiness_status") == "WATCH",
            guard_pass=True,
            metrics={
                "readiness_status": readiness.get("readiness_status"),
                "recommended_default_decision": readiness.get("recommended_default_decision"),
                "readiness_pass": readiness.get("readiness_pass"),
                "comparability_pass": metrics.get("comparability_pass"),
                "fee_slippage_buffer_pct": metrics.get("fee_slippage_buffer_pct"),
                "estimated_net_gap_pct": metrics.get("estimated_net_gap_pct"),
                "max_observed_gap_pct": metrics.get("max_observed_gap_pct"),
                "parser_normalized_status": parser_output.get("normalized_status"),
            },
            thresholds={
                "fee_slippage_buffer_pct": self.fee_slippage_buffer_pct,
                "min_net_gap_pct": self.min_net_gap_pct,
                "max_data_age_ms": self.max_data_age_ms,
                "require_freshness": self.require_freshness,
                "size_or_notional_resolved": self.size_or_notional_resolved,
            },
            required_missing_fields=list(readiness.get("required_missing_fields") or []),
            assumptions=_mark_orderbook_gap_candidate_assumptions(),
            extensions={
                "warnings": list(readiness.get("warnings") or []),
                "comparability_pass": metrics.get("comparability_pass"),
            },
        )
        return OpportunityPacket(
            packet_id=f"binance_{self.symbol.lower()}_mark_orderbook_gap_{collected_at.strftime('%Y%m%d_%H%M%S')}",
            created_at_utc=collected_at,
            asset=self.asset,
            quote=self.quote,
            signal_type="mark_orderbook_gap_hunt",
            strategy_family="mark_orderbook_gap_hunt",
            strategy_id="mark_orderbook_gap_hunt_v0",
            observations=[observation],
            candidates=[candidate],
            detector_metadata=DetectorMetadata(
                detector_name="binance_mark_orderbook_gap_hunt_adapter",
                detector_version="v0",
                generated_from="public_binance_usdm_mark_depth_exchange_info",
                source_files=[
                    "src/market_data/adapters/mark_orderbook_gap_hunt.py",
                    "src/market_data/parsers/mark_orderbook_gap_hunt.py",
                    "src/strategy/mark_orderbook_gap_hunt_readiness.py",
                ],
            ),
            extensions={
                "adapter_metadata": _mark_orderbook_gap_adapter_metadata(
                    adapter_id=self.adapter_id,
                    adapter_type=self.adapter_type,
                    venue_fields={"venue_id": "binance"},
                    endpoints=[self.MARK_PRICE_PATH, self.ORDERBOOK_PATH, self.METADATA_PATH],
                    fetched_at_utc=collected_at,
                ),
                "parser_output": parser_output,
                "readiness": readiness,
                "diagnostics": diagnostics,
                "assumptions": _mark_orderbook_gap_extension_assumptions(),
            },
        )


class BybitMarkOrderbookGapHuntAdapter(MarketDataAdapter):
    """Public read-only Bybit V5 linear BTCUSDT Mark-Orderbook Gap adapter.

    The adapter fetches only public no-key Bybit market-data endpoints, delegates
    parsing/readiness to pure shared helpers, and returns an analysis-only
    ``OpportunityPacket``. Registration/configuration is controlled outside the
    adapter; configured entries must remain disabled/experimental/non-active
    unless explicitly enabled by config review.
    """

    adapter_type = "bybit_mark_orderbook_gap_hunt"

    DEFAULT_ADAPTER_ID = "live_bybit_mark_orderbook_gap_btcusdt"
    BASE_URL = "https://api.bybit.com"
    TICKER_PATH = "/v5/market/tickers"
    ORDERBOOK_PATH = "/v5/market/orderbook"
    METADATA_PATH = "/v5/market/instruments-info"

    def __init__(
        self,
        adapter_id: str = DEFAULT_ADAPTER_ID,
        *,
        config: dict[str, Any] | None = None,
        http_client: Any | None = None,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(adapter_id, config=config)
        self.base_url = str(self.config.get("base_url") or self.BASE_URL)
        self.category = str(self.config.get("category") or "linear")
        self.symbol = str(self.config.get("symbol") or "BTCUSDT")
        self.asset = str(self.config.get("asset") or "BTC")
        self.quote = str(self.config.get("quote") or "USDT")
        self.orderbook_limit = int(self.config.get("orderbook_limit") or 5)
        self.max_data_age_ms = self.config.get("max_data_age_ms")
        self.fee_slippage_buffer_pct = self.config.get("fee_slippage_buffer_pct", "0")
        self.min_net_gap_pct = self.config.get("min_net_gap_pct", "0")
        self.liquidity_pass = self.config.get("liquidity_pass", True)
        self.require_freshness = bool(self.config.get("require_freshness", False))
        self.size_or_notional_resolved = bool(self.config.get("size_or_notional_resolved", True))
        self.http_client = http_client or ReadOnlyHttpClient(
            timeout_seconds=float(self.config.get("timeout_seconds") or 10),
            max_retries=int(self.config.get("max_retries") or 2),
            user_agent=str(self.config.get("user_agent") or "agent-council-market-data-v1"),
        )
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc))

    def fetch_snapshot(self) -> dict[str, Any]:
        """Fetch public responses and return an OpportunityPacket JSON dict."""

        return self.fetch_packet().model_dump(mode="json")

    def fetch_packet(self) -> OpportunityPacket:
        """Fetch public Bybit market data and build an analysis-only packet."""

        diagnostics: list[dict[str, Any]] = []
        ticker_response = self._public_get(
            self.TICKER_PATH,
            {"category": self.category, "symbol": self.symbol},
            parser_stage="ticker",
            diagnostics=diagnostics,
        )
        orderbook_response = self._public_get(
            self.ORDERBOOK_PATH,
            {"category": self.category, "symbol": self.symbol, "limit": self.orderbook_limit},
            parser_stage="orderbook",
            diagnostics=diagnostics,
        )
        metadata_response = self._public_get(
            self.METADATA_PATH,
            {"category": self.category, "symbol": self.symbol},
            parser_stage="metadata",
            diagnostics=diagnostics,
        )
        collected_at = _ensure_utc(self.now_fn())
        collected_at_iso = collected_at.isoformat()
        total_latency_ms = sum(diagnostic.get("elapsed_ms") or 0 for diagnostic in diagnostics)

        parser_output = parse_mark_orderbook_gap_snapshot(
            venue_id="bybit",
            parser_mode="bybit_linear",
            mark_response=ticker_response.data,
            ticker_response=ticker_response.data,
            orderbook_response=orderbook_response.data,
            metadata_response=metadata_response.data,
            collected_at_utc=collected_at_iso,
            latency_ms=total_latency_ms,
            max_data_age_ms=self.max_data_age_ms,
        )
        readiness = evaluate_mark_orderbook_gap_readiness(
            parser_output,
            fee_slippage_buffer_pct=self.fee_slippage_buffer_pct,
            liquidity_pass=self.liquidity_pass,
            require_freshness=self.require_freshness,
            size_or_notional_resolved=self.size_or_notional_resolved,
            min_net_gap_pct=self.min_net_gap_pct,
        )
        return self._packet(
            parser_output=parser_output,
            readiness=readiness,
            diagnostics=diagnostics,
            collected_at=collected_at,
            total_latency_ms=total_latency_ms,
        )

    def _public_get(
        self,
        path: str,
        params: dict[str, Any],
        *,
        parser_stage: str,
        diagnostics: list[dict[str, Any]],
    ) -> HttpJsonResponse:
        diagnostic: dict[str, Any] = {
            "endpoint": path,
            "params": dict(params),
            "parser_stage": parser_stage,
        }
        try:
            response = self.http_client.get_json(self.base_url, path, params)
        except Exception as exc:  # noqa: BLE001 - attach safe diagnostics to adapter error
            diagnostic.update(_diagnostic_from_error(exc))
            diagnostics.append(diagnostic)
            error = MarketDataAdapterError(f"Bybit mark-orderbook public fetch failed at {parser_stage}: {exc}")
            setattr(error, "diagnostics", diagnostics)
            raise error from exc
        data = response.data
        if isinstance(data, dict):
            diagnostic["retCode"] = data.get("retCode")
            diagnostic["retMsg"] = data.get("retMsg")
        diagnostic.update(
            {
                "http_status": getattr(response, "http_status", None),
                "safe_response_preview": getattr(response, "safe_response_preview", None) or _safe_preview(data),
                "elapsed_ms": getattr(response, "elapsed_ms", None),
                "url": getattr(response, "url", None),
            }
        )
        diagnostics.append(diagnostic)
        if isinstance(data, dict) and data.get("retCode") not in (None, 0, "0"):
            error = MarketDataAdapterError(
                f"Bybit public response retCode={data.get('retCode')} at {parser_stage}: {data.get('retMsg')}"
            )
            setattr(error, "diagnostics", diagnostics)
            raise error
        return response

    def _packet(
        self,
        *,
        parser_output: dict[str, Any],
        readiness: dict[str, Any],
        diagnostics: list[dict[str, Any]],
        collected_at: datetime,
        total_latency_ms: int,
    ) -> OpportunityPacket:
        observation_id = f"bybit_{self.symbol.lower()}_mark_orderbook_gap"
        observation = MarketObservation(
            observation_id=observation_id,
            venue_id="bybit",
            venue_name="Bybit Derivatives V5",
            market_symbol=self.symbol,
            instrument_type=parser_output.get("instrument_type") or "linear_perpetual",
            region="GLOBAL",
            mark_price=_float_or_none(parser_output.get("mark_price")),
            index_price=_float_or_none(parser_output.get("index_price")),
            tick=_float_or_none(parser_output.get("tick_size")),
            step=_float_or_none(parser_output.get("quantity_step")),
            bid=_float_or_none(parser_output.get("bid")),
            ask=_float_or_none(parser_output.get("ask")),
            bid_size=_float_or_none(parser_output.get("bid_size_raw")),
            ask_size=_float_or_none(parser_output.get("ask_size_raw")),
            timestamp_utc=_datetime_from_ms(parser_output.get("timestamp")),
            liquidity=LiquiditySnapshot(
                orderbook_depth_available=parser_output.get("bid") is not None and parser_output.get("ask") is not None,
                volume_available=False,
                estimated_executable_notional=None,
                estimated_slippage_pct=None,
                depth_levels=[],
            ),
            derivatives=DerivativesSnapshot(
                funding_rate_pct=_float_or_none(parser_output.get("funding_rate")),
                next_funding_time_utc=_datetime_from_ms(parser_output.get("next_funding_time")),
                mark_price=_float_or_none(parser_output.get("mark_price")),
                index_price=_float_or_none(parser_output.get("index_price")),
            ),
            data_quality=DataQualitySnapshot(
                timestamps_available=parser_output.get("timestamp") is not None,
                timestamps_aligned=None,
                max_data_age_ms=_int_or_none(parser_output.get("data_age_ms")),
                source="bybit_public_v5_linear",
                latency_ms=total_latency_ms,
                is_realtime=True,
            ),
            health=VenueHealthSnapshot(
                api_status_known=True,
                api_ok=True,
                maintenance=False,
                trading_enabled=True,
                message=None,
            ),
            extensions={
                "instrument_id": parser_output.get("instrument_id"),
                "bid_size_unit": parser_output.get("bid_size_unit"),
                "ask_size_unit": parser_output.get("ask_size_unit"),
                "min_order_size": parser_output.get("min_order_size"),
                "min_notional": parser_output.get("min_notional"),
                "settle_currency": parser_output.get("settle_currency"),
                "category": self.category,
                "parser_mode": parser_output.get("parser_mode"),
                "parser_normalized_status": parser_output.get("normalized_status"),
            },
        )
        metrics = readiness.get("metrics") or {}
        candidate = OpportunityCandidate(
            candidate_id=f"{observation_id}_candidate",
            candidate_type="mark_orderbook_gap_observation",
            strategy_family="mark_orderbook_gap_hunt",
            strategy_id="mark_orderbook_gap_hunt_v0",
            source_observation_id=observation_id,
            source_venue_id="bybit",
            direction="analysis_only_mark_orderbook_gap_observation",
            gross_gap_pct=_float_or_none(metrics.get("max_observed_gap_pct")),
            estimated_net_gap_pct=_float_or_none(metrics.get("estimated_net_gap_pct")),
            long_gap_pct=_float_or_none(metrics.get("long_gap_pct")),
            short_gap_pct=_float_or_none(metrics.get("short_gap_pct")),
            liquidity_pass=metrics.get("liquidity_pass"),
            freshness_pass=metrics.get("freshness_pass"),
            gap_pass=readiness.get("readiness_status") == "WATCH",
            guard_pass=True,
            metrics={
                "readiness_status": readiness.get("readiness_status"),
                "recommended_default_decision": readiness.get("recommended_default_decision"),
                "readiness_pass": readiness.get("readiness_pass"),
                "comparability_pass": metrics.get("comparability_pass"),
                "fee_slippage_buffer_pct": metrics.get("fee_slippage_buffer_pct"),
                "estimated_net_gap_pct": metrics.get("estimated_net_gap_pct"),
                "max_observed_gap_pct": metrics.get("max_observed_gap_pct"),
                "parser_normalized_status": parser_output.get("normalized_status"),
            },
            thresholds={
                "fee_slippage_buffer_pct": self.fee_slippage_buffer_pct,
                "min_net_gap_pct": self.min_net_gap_pct,
                "max_data_age_ms": self.max_data_age_ms,
                "require_freshness": self.require_freshness,
                "size_or_notional_resolved": self.size_or_notional_resolved,
            },
            required_missing_fields=list(readiness.get("required_missing_fields") or []),
            assumptions=_mark_orderbook_gap_candidate_assumptions(),
            extensions={
                "warnings": list(readiness.get("warnings") or []),
                "comparability_pass": metrics.get("comparability_pass"),
            },
        )
        return OpportunityPacket(
            packet_id=f"bybit_{self.symbol.lower()}_mark_orderbook_gap_{collected_at.strftime('%Y%m%d_%H%M%S')}",
            created_at_utc=collected_at,
            asset=self.asset,
            quote=self.quote,
            signal_type="mark_orderbook_gap_hunt",
            strategy_family="mark_orderbook_gap_hunt",
            strategy_id="mark_orderbook_gap_hunt_v0",
            observations=[observation],
            candidates=[candidate],
            detector_metadata=DetectorMetadata(
                detector_name="bybit_mark_orderbook_gap_hunt_adapter",
                detector_version="v0",
                generated_from="public_bybit_v5_linear_ticker_orderbook_instruments_info",
                source_files=[
                    "src/market_data/adapters/mark_orderbook_gap_hunt.py",
                    "src/market_data/parsers/mark_orderbook_gap_hunt.py",
                    "src/strategy/mark_orderbook_gap_hunt_readiness.py",
                ],
            ),
            extensions={
                "adapter_metadata": _mark_orderbook_gap_adapter_metadata(
                    adapter_id=self.adapter_id,
                    adapter_type=self.adapter_type,
                    venue_fields={
                        "venue_id": "bybit",
                        "venue_name": "Bybit Derivatives V5",
                        "category": self.category,
                    },
                    endpoints=[self.TICKER_PATH, self.ORDERBOOK_PATH, self.METADATA_PATH],
                    fetched_at_utc=collected_at,
                ),
                "parser_output": parser_output,
                "readiness": readiness,
                "diagnostics": diagnostics,
                "assumptions": _mark_orderbook_gap_extension_assumptions(),
            },
        )


class OkxMarkOrderbookGapHuntAdapter(MarketDataAdapter):
    """Public read-only OKX BTC-USDT-SWAP Mark-Orderbook Gap adapter.

    The adapter fetches only public no-key OKX market-data endpoints, delegates
    parsing/readiness to pure shared helpers, and returns an analysis-only
    ``OpportunityPacket``. Registration/configuration is controlled outside the
    adapter; configured entries must remain disabled/experimental/non-active
    unless explicitly enabled by config review.
    """

    adapter_type = "okx_mark_orderbook_gap_hunt"

    DEFAULT_ADAPTER_ID = "live_okx_mark_orderbook_gap_btc_usdt_swap"
    BASE_URL = "https://www.okx.com"
    MARK_PRICE_PATH = "/api/v5/public/mark-price"
    ORDERBOOK_PATH = "/api/v5/market/books"
    METADATA_PATH = "/api/v5/public/instruments"

    def __init__(
        self,
        adapter_id: str = DEFAULT_ADAPTER_ID,
        *,
        config: dict[str, Any] | None = None,
        http_client: Any | None = None,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(adapter_id, config=config)
        self.base_url = str(self.config.get("base_url") or self.BASE_URL)
        self.inst_type = str(self.config.get("instType") or self.config.get("inst_type") or "SWAP")
        self.inst_id = str(self.config.get("instId") or self.config.get("inst_id") or "BTC-USDT-SWAP")
        self.asset = str(self.config.get("asset") or "BTC")
        self.quote = str(self.config.get("quote") or "USDT")
        self.orderbook_size = int(self.config.get("orderbook_size") or self.config.get("orderbook_limit") or 5)
        self.max_data_age_ms = self.config.get("max_data_age_ms")
        self.fee_slippage_buffer_pct = self.config.get("fee_slippage_buffer_pct", "0")
        self.min_net_gap_pct = self.config.get("min_net_gap_pct", "0")
        self.liquidity_pass = self.config.get("liquidity_pass", True)
        self.require_freshness = bool(self.config.get("require_freshness", False))
        self.size_or_notional_resolved = bool(self.config.get("size_or_notional_resolved", True))
        self.http_client = http_client or ReadOnlyHttpClient(
            timeout_seconds=float(self.config.get("timeout_seconds") or 10),
            max_retries=int(self.config.get("max_retries") or 2),
            user_agent=str(self.config.get("user_agent") or "agent-council-market-data-v1"),
        )
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc))

    def fetch_snapshot(self) -> dict[str, Any]:
        """Fetch public responses and return an OpportunityPacket JSON dict."""

        return self.fetch_packet().model_dump(mode="json")

    def fetch_packet(self) -> OpportunityPacket:
        """Fetch public OKX market data and build an analysis-only packet."""

        diagnostics: list[dict[str, Any]] = []
        mark_response = self._public_get(
            self.MARK_PRICE_PATH,
            {"instType": self.inst_type, "instId": self.inst_id},
            parser_stage="mark_price",
            diagnostics=diagnostics,
        )
        orderbook_response = self._public_get(
            self.ORDERBOOK_PATH,
            {"instId": self.inst_id, "sz": self.orderbook_size},
            parser_stage="orderbook",
            diagnostics=diagnostics,
        )
        metadata_response = self._public_get(
            self.METADATA_PATH,
            {"instType": self.inst_type, "instId": self.inst_id},
            parser_stage="metadata",
            diagnostics=diagnostics,
        )
        collected_at = _ensure_utc(self.now_fn())
        collected_at_iso = collected_at.isoformat()
        total_latency_ms = sum(diagnostic.get("elapsed_ms") or 0 for diagnostic in diagnostics)

        parser_output = parse_mark_orderbook_gap_snapshot(
            venue_id="okx",
            parser_mode="okx_swap",
            mark_response=self._payload_with_data_or_none(mark_response.data),
            ticker_response=None,
            orderbook_response=self._payload_with_data_or_none(orderbook_response.data),
            metadata_response=self._payload_with_data_or_none(metadata_response.data),
            collected_at_utc=collected_at_iso,
            latency_ms=total_latency_ms,
            max_data_age_ms=self.max_data_age_ms,
        )
        readiness = evaluate_mark_orderbook_gap_readiness(
            parser_output,
            fee_slippage_buffer_pct=self.fee_slippage_buffer_pct,
            liquidity_pass=self.liquidity_pass,
            require_freshness=self.require_freshness,
            size_or_notional_resolved=self.size_or_notional_resolved,
            min_net_gap_pct=self.min_net_gap_pct,
        )
        return self._packet(
            parser_output=parser_output,
            readiness=readiness,
            diagnostics=diagnostics,
            collected_at=collected_at,
            total_latency_ms=total_latency_ms,
        )

    def _public_get(
        self,
        path: str,
        params: dict[str, Any],
        *,
        parser_stage: str,
        diagnostics: list[dict[str, Any]],
    ) -> HttpJsonResponse:
        diagnostic: dict[str, Any] = {
            "endpoint": path,
            "params": dict(params),
            "parser_stage": parser_stage,
        }
        try:
            response = self.http_client.get_json(self.base_url, path, params)
        except Exception as exc:  # noqa: BLE001 - attach safe diagnostics to adapter error
            diagnostic.update(_diagnostic_from_error(exc))
            diagnostics.append(diagnostic)
            error = MarketDataAdapterError(f"OKX mark-orderbook public fetch failed at {parser_stage}: {exc}")
            setattr(error, "diagnostics", diagnostics)
            raise error from exc
        data = response.data
        if isinstance(data, dict):
            diagnostic["code"] = data.get("code")
            diagnostic["msg"] = data.get("msg")
        diagnostic.update(
            {
                "http_status": getattr(response, "http_status", None),
                "safe_response_preview": getattr(response, "safe_response_preview", None) or _safe_preview(data),
                "elapsed_ms": getattr(response, "elapsed_ms", None),
                "url": getattr(response, "url", None),
            }
        )
        diagnostics.append(diagnostic)
        if isinstance(data, dict) and data.get("code") not in (None, "0", 0):
            error = MarketDataAdapterError(
                f"OKX public response code={data.get('code')} at {parser_stage}: {data.get('msg')}"
            )
            setattr(error, "diagnostics", diagnostics)
            raise error
        return response

    def _payload_with_data_or_none(self, payload: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(payload, dict):
            return None
        data = payload.get("data")
        if not isinstance(data, list) or not data:
            return None
        return payload

    def _packet(
        self,
        *,
        parser_output: dict[str, Any],
        readiness: dict[str, Any],
        diagnostics: list[dict[str, Any]],
        collected_at: datetime,
        total_latency_ms: int,
    ) -> OpportunityPacket:
        packet_inst = str(parser_output.get("instrument_id") or self.inst_id)
        observation_id = f"okx_{packet_inst.lower().replace('-', '_')}_mark_orderbook_gap"
        observation = MarketObservation(
            observation_id=observation_id,
            venue_id="okx",
            venue_name="OKX",
            market_symbol=packet_inst,
            instrument_type=parser_output.get("instrument_type") or "linear_swap",
            region="GLOBAL",
            mark_price=_float_or_none(parser_output.get("mark_price")),
            index_price=_float_or_none(parser_output.get("index_price")),
            tick=_float_or_none(parser_output.get("tick_size")),
            step=_float_or_none(parser_output.get("lot_size")),
            bid=_float_or_none(parser_output.get("bid")),
            ask=_float_or_none(parser_output.get("ask")),
            bid_size=_float_or_none(parser_output.get("bid_size_raw")),
            ask_size=_float_or_none(parser_output.get("ask_size_raw")),
            timestamp_utc=_datetime_from_ms(parser_output.get("timestamp")),
            liquidity=LiquiditySnapshot(
                orderbook_depth_available=parser_output.get("bid") is not None and parser_output.get("ask") is not None,
                volume_available=False,
                estimated_executable_notional=None,
                estimated_slippage_pct=None,
                depth_levels=[],
            ),
            derivatives=DerivativesSnapshot(
                funding_rate_pct=_float_or_none(parser_output.get("funding_rate")),
                next_funding_time_utc=_datetime_from_ms(parser_output.get("next_funding_time")),
                mark_price=_float_or_none(parser_output.get("mark_price")),
                index_price=_float_or_none(parser_output.get("index_price")),
            ),
            data_quality=DataQualitySnapshot(
                timestamps_available=parser_output.get("timestamp") is not None,
                timestamps_aligned=None,
                max_data_age_ms=_int_or_none(parser_output.get("data_age_ms")),
                source="okx_public_swap",
                latency_ms=total_latency_ms,
                is_realtime=True,
            ),
            health=VenueHealthSnapshot(
                api_status_known=True,
                api_ok=True,
                maintenance=False,
                trading_enabled=True,
                message=None,
            ),
            extensions={
                "instrument_id": packet_inst,
                "inst_type": self.inst_type,
                "bid_size_unit": parser_output.get("bid_size_unit"),
                "ask_size_unit": parser_output.get("ask_size_unit"),
                "contract_value": parser_output.get("contract_value"),
                "contract_multiplier": parser_output.get("contract_multiplier"),
                "contract_value_currency": parser_output.get("contract_value_currency"),
                "settle_currency": parser_output.get("settle_currency"),
                "lot_size": parser_output.get("lot_size"),
                "min_order_size": parser_output.get("min_order_size"),
                "parser_mode": parser_output.get("parser_mode"),
                "parser_normalized_status": parser_output.get("normalized_status"),
            },
        )
        metrics = readiness.get("metrics") or {}
        candidate = OpportunityCandidate(
            candidate_id=f"{observation_id}_candidate",
            candidate_type="mark_orderbook_gap_observation",
            strategy_family="mark_orderbook_gap_hunt",
            strategy_id="mark_orderbook_gap_hunt_v0",
            source_observation_id=observation_id,
            source_venue_id="okx",
            direction="analysis_only_mark_orderbook_gap_observation",
            gross_gap_pct=_float_or_none(metrics.get("max_observed_gap_pct")),
            estimated_net_gap_pct=_float_or_none(metrics.get("estimated_net_gap_pct")),
            long_gap_pct=_float_or_none(metrics.get("long_gap_pct")),
            short_gap_pct=_float_or_none(metrics.get("short_gap_pct")),
            liquidity_pass=metrics.get("liquidity_pass"),
            freshness_pass=metrics.get("freshness_pass"),
            gap_pass=readiness.get("readiness_status") == "WATCH",
            guard_pass=True,
            metrics={
                "readiness_status": readiness.get("readiness_status"),
                "recommended_default_decision": readiness.get("recommended_default_decision"),
                "readiness_pass": readiness.get("readiness_pass"),
                "comparability_pass": metrics.get("comparability_pass"),
                "fee_slippage_buffer_pct": metrics.get("fee_slippage_buffer_pct"),
                "estimated_net_gap_pct": metrics.get("estimated_net_gap_pct"),
                "max_observed_gap_pct": metrics.get("max_observed_gap_pct"),
                "parser_normalized_status": parser_output.get("normalized_status"),
            },
            thresholds={
                "fee_slippage_buffer_pct": self.fee_slippage_buffer_pct,
                "min_net_gap_pct": self.min_net_gap_pct,
                "max_data_age_ms": self.max_data_age_ms,
                "require_freshness": self.require_freshness,
                "size_or_notional_resolved": self.size_or_notional_resolved,
            },
            required_missing_fields=list(readiness.get("required_missing_fields") or []),
            assumptions=_mark_orderbook_gap_candidate_assumptions(),
            extensions={
                "warnings": list(readiness.get("warnings") or []),
                "comparability_pass": metrics.get("comparability_pass"),
            },
        )
        return OpportunityPacket(
            packet_id=f"okx_{packet_inst.lower().replace('-', '_')}_mark_orderbook_gap_{collected_at.strftime('%Y%m%d_%H%M%S')}",
            created_at_utc=collected_at,
            asset=self.asset,
            quote=self.quote,
            signal_type="mark_orderbook_gap_hunt",
            strategy_family="mark_orderbook_gap_hunt",
            strategy_id="mark_orderbook_gap_hunt_v0",
            observations=[observation],
            candidates=[candidate],
            detector_metadata=DetectorMetadata(
                detector_name="okx_mark_orderbook_gap_hunt_adapter",
                detector_version="v0",
                generated_from="public_okx_swap_mark_price_books_instruments",
                source_files=[
                    "src/market_data/adapters/mark_orderbook_gap_hunt.py",
                    "src/market_data/parsers/mark_orderbook_gap_hunt.py",
                    "src/strategy/mark_orderbook_gap_hunt_readiness.py",
                ],
            ),
            extensions={
                "adapter_metadata": _mark_orderbook_gap_adapter_metadata(
                    adapter_id=self.adapter_id,
                    adapter_type=self.adapter_type,
                    venue_fields={
                        "venue_id": "okx",
                        "venue_name": "OKX",
                        "instType": self.inst_type,
                        "instId": self.inst_id,
                    },
                    endpoints=[self.MARK_PRICE_PATH, self.ORDERBOOK_PATH, self.METADATA_PATH],
                    fetched_at_utc=collected_at,
                ),
                "parser_output": parser_output,
                "readiness": readiness,
                "diagnostics": diagnostics,
                "assumptions": _mark_orderbook_gap_extension_assumptions(),
            },
        )


def _diagnostic_from_error(exc: Exception) -> dict[str, Any]:
    return {
        "parser_stage": "http_get_error",
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "http_status": getattr(exc, "http_status", None),
        "safe_response_preview": getattr(exc, "safe_response_preview", None),
        "exchange_error_code": getattr(exc, "exchange_error_code", None),
        "exchange_error_message": getattr(exc, "exchange_error_message", None),
    }


def _safe_preview(data: Any) -> str:
    try:
        return json.dumps(data, ensure_ascii=False, sort_keys=True)[:500]
    except (TypeError, ValueError):
        return repr(data)[:500]


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _datetime_from_ms(value: Any) -> datetime | None:
    timestamp_ms = _float_or_none(value)
    if timestamp_ms is None:
        return None
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
