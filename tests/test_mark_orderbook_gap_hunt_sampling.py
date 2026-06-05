from __future__ import annotations

import copy
import json
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from src.market_data.sampling import run_market_sampling
from src.schemas.opportunity_packet import OpportunityPacket


NOW = datetime(2026, 6, 4, 0, 0, tzinfo=timezone.utc)


class StaticPacketAdapter:
    def __init__(self, packet: dict) -> None:
        self.packet = packet

    def fetch_snapshot(self) -> dict:
        return copy.deepcopy(self.packet)


def _mark_packet(*, readiness_status: str = "REJECT", gross_gap_pct: float = 0.004, net_gap_pct: float = -0.196) -> dict:
    recommended = readiness_status
    net_gap_pass = net_gap_pct > 0
    return {
        "schema_version": "opportunity_packet_v0",
        "packet_id": f"packet_{readiness_status.lower()}",
        "created_at_utc": "2026-06-04T00:00:00+00:00",
        "asset": "BTC",
        "quote": "USDT",
        "signal_type": "mark_orderbook_gap_hunt",
        "strategy_family": "mark_orderbook_gap_hunt",
        "strategy_id": "mark_orderbook_gap_hunt_v0",
        "observations": [
            {
                "observation_id": "binance_btcusdt_mark_orderbook_gap",
                "venue_id": "binance",
                "venue_name": "Binance USDⓈ-M Futures",
                "market_symbol": "BTCUSDT",
                "instrument_type": "linear_perpetual",
                "mark_price": 62413.6,
                "index_price": 62444.55652174,
                "bid": 62416.3,
                "ask": 62416.4,
                "bid_size": 1.25,
                "ask_size": 0.75,
                "data_quality": {
                    "timestamps_available": True,
                    "max_data_age_ms": 200,
                    "latency_ms": 11,
                    "source": "binance_public_usdm",
                    "is_realtime": True,
                },
                "liquidity": {
                    "orderbook_depth_available": True,
                    "volume_available": False,
                    "depth_levels": [],
                },
                "extensions": {
                    "parser_normalized_status": "OK",
                    "bid_size_unit": "base_asset",
                    "ask_size_unit": "base_asset",
                },
            }
        ],
        "candidates": [
            {
                "candidate_id": "binance_btcusdt_mark_orderbook_gap_candidate",
                "candidate_type": "mark_orderbook_gap_observation",
                "strategy_family": "mark_orderbook_gap_hunt",
                "strategy_id": "mark_orderbook_gap_hunt_v0",
                "source_observation_id": "binance_btcusdt_mark_orderbook_gap",
                "source_venue_id": "binance",
                "direction": "analysis_only_mark_orderbook_gap_observation",
                "gross_gap_pct": gross_gap_pct,
                "estimated_net_gap_pct": net_gap_pct,
                "long_gap_pct": gross_gap_pct,
                "short_gap_pct": -0.002,
                "liquidity_pass": True,
                "freshness_pass": True,
                "gap_pass": readiness_status == "WATCH",
                "guard_pass": True,
                "metrics": {
                    "readiness_status": readiness_status,
                    "recommended_default_decision": recommended,
                    "readiness_pass": False,
                    "comparability_pass": True,
                    "fee_slippage_buffer_pct": 0.2,
                    "estimated_net_gap_pct": net_gap_pct,
                    "max_observed_gap_pct": gross_gap_pct,
                    "parser_normalized_status": "OK",
                    "net_gap_pass": net_gap_pass,
                },
                "thresholds": {
                    "fee_slippage_buffer_pct": 0.2,
                    "min_net_gap_pct": 0,
                    "require_freshness": True,
                    "size_or_notional_resolved": True,
                },
                "required_missing_fields": [],
                "assumptions": [
                    "mark price is not executable",
                    "WATCH is analysis-only",
                    "no private API",
                    "no trading behavior",
                ],
            }
        ],
        "detector_metadata": {
            "detector_name": "binance_mark_orderbook_gap_hunt_adapter",
            "detector_version": "v0",
            "generated_from": "public_binance_usdm_mark_depth_exchange_info",
        },
        "extensions": {
            "adapter_metadata": {
                "adapter_id": "live_binance_mark_orderbook_gap_btcusdt",
                "adapter_type": "binance_mark_orderbook_gap_hunt",
                "venue_id": "binance",
                "experimental_strategy": True,
                "non_active_strategy": True,
                "no_trade_only": True,
                "execution_policy": "NO_TRADE_ONLY",
            },
            "readiness": {
                "readiness_status": readiness_status,
                "readiness_pass": False,
                "recommended_default_decision": recommended,
                "required_missing_fields": [],
                "warnings": [],
                "metrics": {
                    "long_gap_pct": gross_gap_pct,
                    "short_gap_pct": -0.002,
                    "max_observed_gap_pct": gross_gap_pct,
                    "fee_slippage_buffer_pct": 0.2,
                    "estimated_net_gap_pct": net_gap_pct,
                    "liquidity_pass": True,
                    "freshness_pass": True,
                    "comparability_pass": True,
                },
            },
        },
    }


class MarkOrderbookGapHuntSamplingTests(unittest.TestCase):
    def test_sampling_exposes_mark_orderbook_gap_sample_fields(self) -> None:
        result = run_market_sampling(
            StaticPacketAdapter(_mark_packet(readiness_status="REJECT")),
            adapter_id="live_binance_mark_orderbook_gap_btcusdt",
            samples_requested=1,
            interval_seconds=0,
            now_fn=lambda: NOW,
        )

        self.assertEqual(result["schema_version"], "market_sampling_v1")
        self.assertEqual(result["adapter_id"], "live_binance_mark_orderbook_gap_btcusdt")
        self.assertFalse(result["council_recommended"])
        sample = result["samples"][0]
        self.assertEqual(sample["status"], "ok")
        self.assertEqual(sample["strategy_family"], "mark_orderbook_gap_hunt")
        self.assertEqual(sample["strategy_id"], "mark_orderbook_gap_hunt_v0")
        self.assertEqual(sample["candidate_count"], 1)
        self.assertEqual(sample["readiness_status"], "REJECT")
        self.assertFalse(sample["readiness_pass"])
        self.assertEqual(sample["recommended_default_decision"], "REJECT")
        self.assertEqual(sample["long_gap_pct"], 0.004)
        self.assertEqual(sample["short_gap_pct"], -0.002)
        self.assertEqual(sample["gross_gap_pct"], 0.004)
        self.assertEqual(sample["max_observed_gap_pct"], 0.004)
        self.assertEqual(sample["estimated_net_gap_pct"], -0.196)
        self.assertTrue(sample["liquidity_pass"])
        self.assertTrue(sample["freshness_pass"])
        self.assertTrue(sample["comparability_pass"])
        self.assertEqual(sample["required_missing_fields"], [])
        self.assertEqual(sample["mark_price"], 62413.6)
        self.assertEqual(sample["index_price"], 62444.55652174)
        self.assertEqual(sample["bid"], 62416.3)
        self.assertEqual(sample["ask"], 62416.4)
        self.assertTrue(sample["no_trade_only"])
        self.assertEqual(sample["execution_policy"], "NO_TRADE_ONLY")
        self.assertEqual(sample["best_candidate"]["readiness_status"], "REJECT")
        self.assertTrue(sample["best_candidate"]["comparability_pass"])

    def test_sampling_summary_exposes_readiness_counts_and_gap_counts(self) -> None:
        result = run_market_sampling(
            StaticPacketAdapter(_mark_packet(readiness_status="REJECT")),
            adapter_id="live_binance_mark_orderbook_gap_btcusdt",
            samples_requested=1,
            interval_seconds=0,
            now_fn=lambda: NOW,
        )

        summary = result["summary"]
        self.assertEqual(summary["samples_requested"], 1)
        self.assertEqual(summary["samples_ok"], 1)
        self.assertEqual(summary["samples_error"], 0)
        self.assertEqual(summary["candidate_seen_count"], 1)
        self.assertEqual(summary["positive_gross_gap_count"], 1)
        self.assertEqual(summary["positive_net_gap_count"], 0)
        self.assertEqual(summary["readiness_status_counts"], {"REJECT": 1})
        self.assertEqual(summary["watch_count"], 0)
        self.assertEqual(summary["reject_count"], 1)
        self.assertEqual(summary["need_data_count"], 0)
        self.assertEqual(summary["max_estimated_net_gap_pct"], -0.196)
        self.assertEqual(summary["avg_estimated_net_gap_pct"], -0.196)
        self.assertEqual(summary["max_gross_gap_pct"], 0.004)
        self.assertEqual(summary["avg_latency_ms"], 11)
        self.assertEqual(summary["max_latency_ms"], 11)
        self.assertEqual(summary["persistence_status"], "NO_PERSISTENT_EDGE")
        self.assertEqual(summary["recommended_default_decision"], "REJECT")
        self.assertFalse(result["council_recommended"])

    def test_watch_sampling_remains_analysis_only_without_alert_council_or_execution(self) -> None:
        result = run_market_sampling(
            StaticPacketAdapter(_mark_packet(readiness_status="WATCH", gross_gap_pct=0.5, net_gap_pct=0.3)),
            adapter_id="live_binance_mark_orderbook_gap_btcusdt",
            samples_requested=1,
            interval_seconds=0,
            now_fn=lambda: NOW,
        )

        sample = result["samples"][0]
        self.assertEqual(sample["readiness_status"], "WATCH")
        self.assertFalse(sample["readiness_pass"])
        self.assertFalse(result["council_recommended"])
        payload_text = json.dumps(result, sort_keys=True)
        self.assertNotIn("execution_allowed", payload_text)
        self.assertNotIn("council_auto_call", payload_text)
        self.assertNotIn("alert_trigger", payload_text)

    def test_sampling_does_not_call_network_or_env_with_mocked_adapter(self) -> None:
        with patch("socket.socket") as socket_factory, patch("os.getenv") as getenv:
            result = run_market_sampling(
                StaticPacketAdapter(_mark_packet()),
                adapter_id="live_binance_mark_orderbook_gap_btcusdt",
                samples_requested=1,
                interval_seconds=0,
                now_fn=lambda: NOW,
            )

        socket_factory.assert_not_called()
        getenv.assert_not_called()
        self.assertEqual(result["samples"][0]["status"], "ok")

    def test_mock_packet_fixture_is_valid_opportunity_packet_shape(self) -> None:
        packet = OpportunityPacket.model_validate(_mark_packet())

        self.assertEqual(packet.strategy_family, "mark_orderbook_gap_hunt")
        self.assertEqual(packet.candidates[0].candidate_type, "mark_orderbook_gap_observation")


if __name__ == "__main__":
    unittest.main()
