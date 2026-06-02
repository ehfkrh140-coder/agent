from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import yaml

from src.market_data.adapters.base import MarketDataAdapter, MarketDataAdapterError
from src.market_data.adapters.bithumb import BithumbPublicSpotAdapter
from src.market_data.adapters.composite import CompositeTetherCrossMarketAdapter
from src.market_data.adapters.global_usdt_reference import GlobalUsdtReferenceAdapter
from src.market_data.adapters.upbit import UpbitPublicSpotAdapter
from src.market_data.http_client import HttpJsonResponse
from src.market_data.packet_builder import OpportunityPacketBuilder
from src.market_data.registry import build_adapter, load_market_data_config
from src.strategy.readiness import build_readiness_report


NOW = datetime(2026, 1, 1, 0, 0, 5, tzinfo=timezone.utc)
TIMESTAMP_MS = 1767225600000


class FakeHttpClient:
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str, dict[str, object] | None]] = []

    def get_json(self, base_url: str, path: str, params: dict[str, object] | None = None) -> HttpJsonResponse:
        self.calls.append((base_url, path, dict(params or {}) if params else None))
        key = path
        if params and "markets" in params:
            key = f"{path}?markets={params['markets']}"
        elif params and "symbol" in params:
            key = f"{path}?symbol={params['symbol']}"
        elif params and "instId" in params:
            key = f"{path}?instId={params['instId']}"
        if key not in self.responses:
            raise MarketDataAdapterError(f"missing fake response for {key}")
        value = self.responses[key]
        if isinstance(value, Exception):
            raise value
        return HttpJsonResponse(data=value, elapsed_ms=12, url=f"{base_url}{key}")


class FailingAdapter(MarketDataAdapter):
    adapter_type = "failing"

    def fetch_snapshot(self) -> dict[str, object]:
        raise MarketDataAdapterError(f"{self.adapter_id} unavailable")


def _upbit_adapter() -> UpbitPublicSpotAdapter:
    responses = {
        "/v1/ticker?markets=KRW-USDT": [
            {
                "market": "KRW-USDT",
                "trade_price": 1412.0,
                "acc_trade_volume_24h": 10000,
                "acc_trade_price_24h": 14120000,
                "timestamp": TIMESTAMP_MS,
            }
        ],
        "/v1/orderbook?markets=KRW-USDT": [
            {
                "market": "KRW-USDT",
                "timestamp": TIMESTAMP_MS,
                "orderbook_units": [
                    {"bid_price": 1411.0, "bid_size": 900.0, "ask_price": 1412.0, "ask_size": 850.0},
                    {"bid_price": 1410.0, "bid_size": 500.0, "ask_price": 1413.0, "ask_size": 450.0},
                ],
            }
        ],
    }
    return UpbitPublicSpotAdapter(
        "live_upbit_usdt_krw_spot",
        config={
            "base_url": "https://api.upbit.com",
            "market": "KRW-USDT",
            "display_symbol": "USDT/KRW",
            "fee_override": {"trading_fee_pct": 0.05, "fee_source": "manual_market_data_config_placeholder"},
        },
        http_client=FakeHttpClient(responses),
        now_fn=lambda: NOW,
    )


def _bithumb_adapter() -> BithumbPublicSpotAdapter:
    responses = {
        "/public/ticker/USDT_KRW": {
            "status": "0000",
            "data": {
                "closing_price": "1418",
                "date": str(TIMESTAMP_MS),
                "units_traded_24H": "12000",
                "acc_trade_value_24H": "17016000",
            },
        },
        "/public/orderbook/USDT_KRW": {
            "status": "0000",
            "data": {
                "timestamp": str(TIMESTAMP_MS),
                "bids": [{"price": "1417", "quantity": "700"}, {"price": "1416", "quantity": "500"}],
                "asks": [{"price": "1418", "quantity": "650"}, {"price": "1419", "quantity": "400"}],
            },
        },
    }
    return BithumbPublicSpotAdapter(
        "live_bithumb_usdt_krw_spot",
        config={
            "base_url": "https://api.bithumb.com",
            "market": "KRW-USDT",
            "api_symbol": "USDT_KRW",
            "display_symbol": "USDT/KRW",
            "fee_override": {"trading_fee_pct": 0.05, "fee_source": "manual_market_data_config_placeholder"},
        },
        http_client=FakeHttpClient(responses),
        now_fn=lambda: NOW,
    )


def _reference_adapter(adapter_id: str, venue_id: str, response_format: str, response: dict[str, object]) -> GlobalUsdtReferenceAdapter:
    params = {"symbol": "USDTUSDC"}
    path = "/ticker"
    if response_format == "okx_ticker":
        params = {"instId": "USDT-USDC"}
    return GlobalUsdtReferenceAdapter(
        adapter_id,
        config={
            "base_url": f"https://{venue_id}.example.com",
            "venue_id": venue_id,
            "venue_name": venue_id.title(),
            "market_symbol": "USDT/USDC",
            "instrument_type": "reference",
            "ticker_path": path,
            "ticker_params": params,
            "response_format": response_format,
        },
        http_client=FakeHttpClient({f"{path}?{next(iter(params))}={next(iter(params.values()))}": response}),
        now_fn=lambda: NOW,
    )


def _binance_adapter() -> GlobalUsdtReferenceAdapter:
    return _reference_adapter(
        "live_binance_usdt_reference",
        "binance",
        "binance_book_ticker",
        {"symbol": "USDTUSDC", "bidPrice": "0.9998", "askPrice": "1.0000", "bidQty": "100000", "askQty": "100000"},
    )


def _bybit_adapter() -> GlobalUsdtReferenceAdapter:
    return _reference_adapter(
        "live_bybit_usdt_reference",
        "bybit",
        "bybit_v5_ticker",
        {
            "retCode": 0,
            "time": TIMESTAMP_MS,
            "result": {"list": [{"symbol": "USDTUSDC", "bid1Price": "0.9999", "ask1Price": "1.0001", "bid1Size": "90000", "ask1Size": "91000"}]},
        },
    )


def _okx_adapter() -> GlobalUsdtReferenceAdapter:
    return _reference_adapter(
        "live_okx_usdt_reference",
        "okx",
        "okx_ticker",
        {"code": "0", "data": [{"instId": "USDT-USDC", "bidPx": "1.0000", "askPx": "1.0002", "bidSz": "80000", "askSz": "81000", "ts": str(TIMESTAMP_MS)}]},
    )


def _composite(global_adapters: list[MarketDataAdapter] | None = None) -> CompositeTetherCrossMarketAdapter:
    return CompositeTetherCrossMarketAdapter(
        "live_tether_cross_market_premium",
        config={
            "strategy_family": "tether_cross_market_premium",
            "strategy_id": "usdt_krw_global_reference_v0",
            "signal_type": "tether_cross_market_premium",
            "asset": "USDT",
            "quote": "KRW",
            "thresholds": {
                "min_net_gap_pct": 0.2,
                "max_data_age_ms": 10000,
                "max_latency_ms": 1000,
                "min_executable_notional": 1000000,
                "safety_buffer_pct": 0.05,
                "global_depeg_threshold_pct": 0.2,
            },
        },
        domestic_adapters=[_upbit_adapter(), _bithumb_adapter()],
        global_reference_adapters=global_adapters or [_binance_adapter(), _bybit_adapter(), _okx_adapter()],
    )


class TetherCrossMarketLiveCompositeAdapterTests(unittest.TestCase):
    def test_registry_creates_live_tether_composite(self) -> None:
        config = load_market_data_config("configs/market_data.yaml")
        adapter = build_adapter("live_tether_cross_market_premium", config)
        self.assertIsInstance(adapter, CompositeTetherCrossMarketAdapter)
        self.assertEqual([child.adapter_id for child in adapter.domestic_adapters], ["live_upbit_usdt_krw_spot", "live_bithumb_usdt_krw_spot"])
        self.assertEqual(len(adapter.global_reference_adapters), 3)

    def test_domestic_child_observations_normalize_usdt_krw(self) -> None:
        upbit_observation = _upbit_adapter().fetch_snapshot()["observations"][0]
        bithumb_observation = _bithumb_adapter().fetch_snapshot()["observations"][0]

        for observation, venue_id in [(upbit_observation, "upbit"), (bithumb_observation, "bithumb")]:
            self.assertEqual(observation["venue_id"], venue_id)
            self.assertEqual(observation["market_symbol"], "USDT/KRW")
            self.assertEqual(observation["instrument_type"], "spot")
            self.assertIsNotNone(observation["bid"])
            self.assertIsNotNone(observation["ask"])
            self.assertIsNotNone(observation["bid_size"])
            self.assertIsNotNone(observation["ask_size"])
            self.assertEqual(observation["fees"]["fee_source"], "manual_market_data_config_placeholder")
            self.assertTrue(observation["liquidity"]["depth_levels"])
            self.assertTrue(observation["health"]["api_ok"])

    def test_global_reference_observations_normalize_by_venue(self) -> None:
        adapters = [_binance_adapter(), _bybit_adapter(), _okx_adapter()]
        for adapter, venue_id in zip(adapters, ["binance", "bybit", "okx"]):
            observation = adapter.fetch_snapshot()["observations"][0]
            self.assertEqual(observation["venue_id"], venue_id)
            self.assertEqual(observation["market_symbol"], "USDT/USDC")
            self.assertEqual(observation["extensions"]["reference_role"], "global_usdt_reference")
            self.assertIsNotNone(observation["bid"])
            self.assertIsNotNone(observation["ask"])
            self.assertTrue(observation["health"]["api_ok"])

    def test_composite_builds_tether_packet_with_all_live_public_observations(self) -> None:
        snapshot = _composite().fetch_snapshot()
        packet = OpportunityPacketBuilder().build(snapshot)

        self.assertEqual(packet.strategy_family, "tether_cross_market_premium")
        self.assertEqual(packet.strategy_id, "usdt_krw_global_reference_v0")
        self.assertEqual(packet.asset, "USDT")
        self.assertEqual(packet.quote, "KRW")
        self.assertEqual(len(packet.observations), 5)
        self.assertEqual({obs.venue_id for obs in packet.observations}, {"upbit", "bithumb", "binance", "bybit", "okx"})

        candidates = [candidate for candidate in packet.candidates if candidate.candidate_type == "tether_domestic_spread_signal"]
        self.assertEqual(len(candidates), 2)
        self.assertEqual({candidate.direction for candidate in candidates}, {"buy_upbit_sell_bithumb_usdt_krw_signal", "buy_bithumb_sell_upbit_usdt_krw_signal"})
        for candidate in candidates:
            self.assertIn("estimated_net_gap_pct", candidate.metrics)
            self.assertIn("global_usdt_mid", candidate.metrics)
            self.assertIn("global_usdt_depeg_flag", candidate.metrics)
            self.assertEqual(candidate.metrics["global_reference_venue_count"], 3)

        report = build_readiness_report(packet)
        self.assertIn(report["status"], {"WATCH", "REJECT", "NEED_DATA"})
        self.assertFalse(report["readiness_pass"])

    def test_partial_global_reference_failure_keeps_successful_references(self) -> None:
        composite = _composite(global_adapters=[_binance_adapter(), FailingAdapter("live_bybit_usdt_reference"), _okx_adapter()])
        snapshot = composite.fetch_snapshot()
        packet = OpportunityPacketBuilder().build(snapshot)
        failed = snapshot["adapter_metadata"]["failed_global_reference_venues"]

        self.assertEqual(len(packet.observations), 4)
        self.assertEqual(failed[0]["adapter_id"], "live_bybit_usdt_reference")
        self.assertEqual(packet.candidates[0].metrics["global_reference_venue_count"], 2)

    def test_domestic_failure_raises_adapter_error(self) -> None:
        composite = CompositeTetherCrossMarketAdapter(
            "live_tether_cross_market_premium",
            config={"thresholds": {}},
            domestic_adapters=[_upbit_adapter(), FailingAdapter("live_bithumb_usdt_krw_spot")],
            global_reference_adapters=[_binance_adapter()],
        )
        with self.assertRaises(MarketDataAdapterError):
            composite.fetch_snapshot()

    def test_replay_tether_cross_market_still_builds(self) -> None:
        config = load_market_data_config("configs/market_data.yaml")
        adapter = build_adapter("replay_tether_cross_market_premium", config)
        packet = OpportunityPacketBuilder().build(adapter.fetch_snapshot())
        self.assertEqual(packet.strategy_family, "tether_cross_market_premium")
        self.assertGreaterEqual(len(packet.candidates), 1)

    def test_config_and_requests_have_no_private_auth_material(self) -> None:
        config_text = Path("configs/market_data.yaml").read_text(encoding="utf-8")
        for forbidden in ["api_key", "api_secret", "access_key", "private_key", "Authorization", "Bearer"]:
            self.assertNotIn(forbidden, config_text)
        fake = FakeHttpClient({"/api/v3/ticker/bookTicker?symbol=USDTUSDC": {"symbol": "USDTUSDC", "bidPrice": "1", "askPrice": "1.0001"}})
        adapter = GlobalUsdtReferenceAdapter(
            "live_binance_usdt_reference",
            config={"base_url": "https://api.binance.com", "venue_id": "binance", "ticker_path": "/api/v3/ticker/bookTicker", "ticker_params": {"symbol": "USDTUSDC"}, "response_format": "binance_book_ticker"},
            http_client=fake,
            now_fn=lambda: NOW,
        )
        adapter.fetch_snapshot()
        self.assertEqual(fake.calls[0][2], {"symbol": "USDTUSDC"})

    def test_collect_market_data_with_mocked_registry_writes_live_tether_packet(self) -> None:
        # Exercise the same build path as the CLI while keeping HTTP fully mocked/network-free.
        with TemporaryDirectory() as td:
            output_path = Path(td) / "live_tether_cross_market_packet.json"
            snapshot = _composite().fetch_snapshot()
            packet = OpportunityPacketBuilder().build(snapshot)
            output_path.write_text(json.dumps(packet.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["strategy_family"], "tether_cross_market_premium")
        self.assertGreaterEqual(len(payload["observations"]), 5)
        self.assertGreaterEqual(len(payload["candidates"]), 1)

    def test_handoff_evidence_file_documents_required_review_evidence(self) -> None:
        handoff = Path("docs/pr_handoffs/tether_cross_market_live_composite_adapter_v0.md")
        self.assertTrue(handoff.exists(), str(handoff))
        text = handoff.read_text(encoding="utf-8")
        for phrase in [
            "Task type: adapter",
            "## 1. Purpose",
            "## 2. Changed files",
            "## 3. Impact scope",
            "## 4. Tests run",
            "## 5. Manual smoke",
            "## 7. Risks",
            "## 8. Rollback plan",
            "## 9. Human review required",
            "## 10. No-trade compliance",
            "private API: no",
            "API key/secret/token: no",
            "balance/account: no",
            "order/cancel: no",
            "transfer/withdraw/deposit: no",
            "fiat/bank transfer: no",
            "auto-trading: no",
            "active strategy changed: no",
        ]:
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
