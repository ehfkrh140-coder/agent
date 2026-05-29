from __future__ import annotations

import unittest
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from src.market_data.adapters.base import MarketDataAdapter
from src.market_data.adapters.bithumb import BithumbPublicSpotAdapter
from src.market_data.adapters.composite import CompositeSpotSpreadAdapter
from src.market_data.adapters.upbit import UpbitPublicSpotAdapter
from src.market_data.packet_builder import OpportunityPacketBuilder
from src.market_data.registry import build_adapter, load_market_data_config


@dataclass
class FakeResponse:
    data: Any
    elapsed_ms: int = 7
    url: str = "https://example.test/public"


class FakeHttpClient:
    def __init__(self, responses: dict[str, Any]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def get_json(self, base_url: str, path: str, params: dict[str, Any] | None = None) -> FakeResponse:
        self.calls.append((base_url, path, params))
        if path not in self.responses:
            raise AssertionError(f"unexpected live or unmocked request path: {path}")
        return FakeResponse(data=self.responses[path], url=f"{base_url}{path}")


class StaticAdapter(MarketDataAdapter):
    adapter_type = "static_test"

    def __init__(self, adapter_id: str, observation: dict[str, Any]) -> None:
        super().__init__(adapter_id, config={})
        self.observation = observation

    def fetch_snapshot(self) -> dict[str, Any]:
        return {
            "observations": [self.observation],
            "adapter_metadata": {"adapter_id": self.adapter_id, "adapter_type": self.adapter_type},
        }


FIXED_NOW = datetime.fromtimestamp(1780000001, tz=timezone.utc)


class PublicSpotAdapterTests(unittest.TestCase):
    def test_upbit_mocked_ticker_orderbook_normalizes_observation(self):
        adapter = UpbitPublicSpotAdapter(
            "live_upbit_spot",
            config={"fee_config_path": "configs/spot_fees.yaml", "orderbook_limit": 2},
            http_client=FakeHttpClient(
                {
                    "/v1/ticker": [
                        {
                            "market": "KRW-BTC",
                            "trade_price": 100_000_000,
                            "acc_trade_volume_24h": 12.5,
                            "acc_trade_price_24h": 1_250_000_000,
                            "timestamp": 1_780_000_000_000,
                        }
                    ],
                    "/v1/orderbook": [
                        {
                            "market": "KRW-BTC",
                            "timestamp": 1_780_000_000_500,
                            "orderbook_units": [
                                {"ask_price": 100_000_000, "bid_price": 99_990_000, "ask_size": 0.6, "bid_size": 0.4},
                                {"ask_price": 100_010_000, "bid_price": 99_980_000, "ask_size": 0.8, "bid_size": 0.7},
                            ],
                        }
                    ],
                }
            ),
            now_fn=lambda: FIXED_NOW,
        )

        snapshot = adapter.fetch_snapshot()
        obs = snapshot["observations"][0]

        self.assertEqual(obs["venue_id"], "upbit")
        self.assertEqual(obs["instrument_type"], "spot")
        self.assertEqual(obs["market_symbol"], "BTC/KRW")
        self.assertEqual(obs["last_price"], 100_000_000)
        self.assertEqual(obs["ask"], 100_000_000)
        self.assertEqual(obs["bid"], 99_990_000)
        self.assertEqual(obs["ask_size"], 0.6)
        self.assertEqual(obs["bid_size"], 0.4)
        self.assertEqual(obs["fees"]["fee_source"], "manual_config_placeholder")
        self.assertTrue(obs["liquidity"]["orderbook_depth_available"])
        self.assertEqual(obs["liquidity"]["estimated_executable_notional"], 39_996_000)
        self.assertEqual(obs["data_quality"]["max_data_age_ms"], 500)
        self.assertEqual(obs["data_quality"]["latency_ms"], 14)

    def test_bithumb_mocked_ticker_orderbook_normalizes_observation(self):
        adapter = BithumbPublicSpotAdapter(
            "live_bithumb_spot",
            config={"fee_config_path": "configs/spot_fees.yaml", "orderbook_limit": 2},
            http_client=FakeHttpClient(
                {
                    "/public/ticker/BTC_KRW": {
                        "status": "0000",
                        "data": {
                            "closing_price": "100700000",
                            "units_traded_24H": "10.0",
                            "acc_trade_value_24H": "1007000000",
                            "date": "1780000000000",
                        },
                    },
                    "/public/orderbook/BTC_KRW": {
                        "status": "0000",
                        "data": {
                            "timestamp": "1780000000500",
                            "bids": [{"price": "100650000", "quantity": "0.5"}],
                            "asks": [{"price": "100700000", "quantity": "0.3"}],
                        },
                    },
                }
            ),
            now_fn=lambda: FIXED_NOW,
        )

        snapshot = adapter.fetch_snapshot()
        obs = snapshot["observations"][0]

        self.assertEqual(obs["venue_id"], "bithumb")
        self.assertEqual(obs["instrument_type"], "spot")
        self.assertEqual(obs["market_symbol"], "BTC/KRW")
        self.assertEqual(obs["last_price"], 100_700_000)
        self.assertEqual(obs["bid"], 100_650_000)
        self.assertEqual(obs["ask"], 100_700_000)
        self.assertEqual(obs["bid_size"], 0.5)
        self.assertEqual(obs["ask_size"], 0.3)
        self.assertEqual(obs["fees"]["fee_source"], "manual_config_placeholder")
        self.assertEqual(obs["liquidity"]["estimated_executable_notional"], 30_210_000)
        self.assertEqual(obs["data_quality"]["max_data_age_ms"], 500)
        self.assertEqual(obs["data_quality"]["latency_ms"], 14)

    def test_composite_adapter_combines_two_observations(self):
        upbit_obs = self._spot_observation("upbit", ask=100_000_000, bid=99_990_000, ask_size=0.6, bid_size=0.4)
        bithumb_obs = self._spot_observation("bithumb", ask=100_700_000, bid=100_650_000, ask_size=0.3, bid_size=0.5)
        adapter = CompositeSpotSpreadAdapter(
            "live_upbit_bithumb_spot_spread",
            config={"asset": "BTC", "quote": "KRW", "thresholds": {"min_net_gap_pct": 0.2, "safety_buffer_pct": 0.05}},
            child_adapters=[StaticAdapter("live_upbit_spot", upbit_obs), StaticAdapter("live_bithumb_spot", bithumb_obs)],
        )

        snapshot = adapter.fetch_snapshot()

        self.assertEqual(snapshot["strategy_family"], "cross_exchange_spot_spread")
        self.assertEqual(snapshot["strategy_id"], "cross_exchange_spot_spread_v1")
        self.assertEqual(len(snapshot["observations"]), 2)
        self.assertEqual(snapshot["adapter_metadata"]["child_adapters"], ["live_upbit_spot", "live_bithumb_spot"])

    def test_packet_builder_creates_candidate_from_source_ask_target_bid_with_net_gap(self):
        snapshot = {
            "asset": "BTC",
            "quote": "KRW",
            "strategy_family": "cross_exchange_spot_spread",
            "strategy_id": "cross_exchange_spot_spread_v1",
            "thresholds": {"min_notional": 1_000_000, "min_net_gap_pct": 0.2, "safety_buffer_pct": 0.05, "max_data_age_ms": 3000},
            "observations": [
                self._spot_observation("upbit", ask=100_000_000, bid=99_990_000, ask_size=0.6, bid_size=0.4),
                self._spot_observation("bithumb", ask=100_700_000, bid=100_650_000, ask_size=0.3, bid_size=0.5),
            ],
        }

        packet = OpportunityPacketBuilder().build(snapshot)

        self.assertEqual(len(packet.candidates), 1)
        candidate = packet.candidates[0]
        self.assertEqual(candidate.source_venue_id, "upbit")
        self.assertEqual(candidate.target_venue_id, "bithumb")
        self.assertEqual(candidate.gross_gap_absolute, 650_000)
        self.assertAlmostEqual(candidate.gross_gap_pct, 0.65)
        self.assertAlmostEqual(candidate.estimated_net_gap_pct, 0.5)
        self.assertEqual(candidate.metrics["source_ask"], 100_000_000)
        self.assertEqual(candidate.metrics["target_bid"], 100_650_000)
        self.assertEqual(candidate.metrics["source_fee_pct"], 0.05)
        self.assertEqual(candidate.metrics["target_fee_pct"], 0.05)
        self.assertEqual(candidate.metrics["estimated_slippage_pct"], 0.0)
        self.assertTrue(candidate.metrics["net_gap_pass"])

    def test_packet_builder_allows_zero_candidates_when_bid_ask_spread_absent(self):
        snapshot = {
            "asset": "BTC",
            "quote": "KRW",
            "strategy_family": "cross_exchange_spot_spread",
            "strategy_id": "cross_exchange_spot_spread_v1",
            "thresholds": {"min_notional": 1_000_000, "safety_buffer_pct": 0.05, "max_data_age_ms": 3000},
            "observations": [
                self._spot_observation("upbit", ask=100_000_000, bid=99_990_000, ask_size=0.6, bid_size=0.4),
                self._spot_observation("bithumb", ask=100_050_000, bid=99_950_000, ask_size=0.3, bid_size=0.5),
            ],
        }

        packet = OpportunityPacketBuilder().build(snapshot)

        self.assertEqual(packet.candidates, [])

    def test_registry_builds_live_upbit_bithumb_composite_without_network_call(self):
        config = load_market_data_config("configs/market_data.yaml")
        adapter = build_adapter("live_upbit_bithumb_spot_spread", config)
        self.assertIsInstance(adapter, CompositeSpotSpreadAdapter)
        self.assertEqual([child.adapter_id for child in adapter.child_adapters], ["live_upbit_spot", "live_bithumb_spot"])

    def _spot_observation(
        self,
        venue_id: str,
        *,
        ask: float,
        bid: float,
        ask_size: float,
        bid_size: float,
    ) -> dict[str, Any]:
        return {
            "observation_id": f"{venue_id}_btc_krw_spot",
            "venue_id": venue_id,
            "venue_name": venue_id.title(),
            "market_symbol": "BTC/KRW",
            "instrument_type": "spot",
            "region": "KR",
            "last_price": (ask + bid) / 2,
            "bid": bid,
            "ask": ask,
            "bid_size": bid_size,
            "ask_size": ask_size,
            "timestamp_utc": "2026-05-29T00:00:00+00:00",
            "fees": {"trading_fee_pct": 0.05, "fee_source": "manual_config_placeholder"},
            "liquidity": {
                "orderbook_depth_available": True,
                "volume_available": True,
                "estimated_executable_notional": min(ask * ask_size, bid * bid_size),
                "estimated_slippage_pct": 0.0,
                "depth_levels": [{"level": 1, "bid_price": bid, "bid_size": bid_size, "ask_price": ask, "ask_size": ask_size}],
            },
            "data_quality": {
                "timestamps_available": True,
                "max_data_age_ms": 500,
                "latency_ms": 14,
                "is_realtime": True,
            },
            "health": {"api_status_known": True, "api_ok": True},
        }


if __name__ == "__main__":
    unittest.main()
