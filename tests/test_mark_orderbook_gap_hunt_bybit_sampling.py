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


def _bybit_mark_packet(
    *, readiness_status: str = "REJECT", gross_gap_pct: float = 0.006219574093567398, net_gap_pct: float = -0.1937804259064326, data_age_ms: int = -6647
) -> dict:
    return {
        "schema_version": "opportunity_packet_v0",
        "packet_id": f"bybit_btcusdt_mark_orderbook_gap_{readiness_status.lower()}",
        "created_at_utc": "2026-06-04T00:00:00+00:00",
        "asset": "BTC",
        "quote": "USDT",
        "signal_type": "mark_orderbook_gap_hunt",
        "strategy_family": "mark_orderbook_gap_hunt",
        "strategy_id": "mark_orderbook_gap_hunt_v0",
        "observations": [
            {
                "observation_id": "bybit_btcusdt_mark_orderbook_gap",
                "venue_id": "bybit",
                "venue_name": "Bybit Derivatives V5",
                "market_symbol": "BTCUSDT",
                "instrument_type": "linear_perpetual",
                "mark_price": 63991.52,
                "index_price": 64014.24,
                "bid": 63995.50,
                "ask": 63995.60,
                "bid_size": 1.25,
                "ask_size": 0.75,
                "data_quality": {
                    "timestamps_available": True,
                    "max_data_age_ms": data_age_ms,
                    "latency_ms": 13,
                    "source": "bybit_public_v5_linear",
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
                "candidate_id": "bybit_btcusdt_mark_orderbook_gap_candidate",
                "candidate_type": "mark_orderbook_gap_observation",
                "strategy_family": "mark_orderbook_gap_hunt",
                "strategy_id": "mark_orderbook_gap_hunt_v0",
                "source_observation_id": "bybit_btcusdt_mark_orderbook_gap",
                "source_venue_id": "bybit",
                "direction": "analysis_only_mark_orderbook_gap_observation",
                "gross_gap_pct": gross_gap_pct,
                "estimated_net_gap_pct": net_gap_pct,
                "long_gap_pct": gross_gap_pct,
                "short_gap_pct": -0.001,
                "liquidity_pass": True,
                "freshness_pass": True,
                "gap_pass": readiness_status == "WATCH",
                "guard_pass": True,
                "metrics": {
                    "readiness_status": readiness_status,
                    "recommended_default_decision": readiness_status,
                    "readiness_pass": False,
                    "comparability_pass": True,
                    "fee_slippage_buffer_pct": 0.2,
                    "estimated_net_gap_pct": net_gap_pct,
                    "max_observed_gap_pct": gross_gap_pct,
                    "parser_normalized_status": "OK",
                    "net_gap_pass": net_gap_pct > 0,
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
            "detector_name": "bybit_mark_orderbook_gap_hunt_adapter",
            "detector_version": "v0",
            "generated_from": "public_bybit_v5_linear_ticker_orderbook_instruments_info",
        },
        "extensions": {
            "adapter_metadata": {
                "adapter_id": "live_bybit_mark_orderbook_gap_btcusdt",
                "adapter_type": "bybit_mark_orderbook_gap_hunt",
                "venue_id": "bybit",
                "category": "linear",
                "experimental_strategy": True,
                "non_active_strategy": True,
                "no_trade_only": True,
                "execution_policy": "NO_TRADE_ONLY",
            },
            "parser_output": {
                "parser_mode": "bybit_linear",
                "normalized_status": "OK",
                "data_age_ms": data_age_ms,
            },
            "diagnostics": [
                {"parser_stage": "ticker", "http_status": 200, "retCode": 0, "retMsg": "OK"},
                {"parser_stage": "orderbook", "http_status": 200, "retCode": 0, "retMsg": "OK"},
                {"parser_stage": "metadata", "http_status": 200, "retCode": 0, "retMsg": "OK"},
            ],
            "readiness": {
                "readiness_status": readiness_status,
                "readiness_pass": False,
                "recommended_default_decision": readiness_status,
                "required_missing_fields": [],
                "warnings": [],
                "metrics": {
                    "long_gap_pct": gross_gap_pct,
                    "short_gap_pct": -0.001,
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


class BybitMarkOrderbookGapHuntSamplingTests(unittest.TestCase):
    def test_sampling_pipeline_consumes_bybit_mark_orderbook_gap_packet(self) -> None:
        result = run_market_sampling(
            StaticPacketAdapter(_bybit_mark_packet()),
            adapter_id="live_bybit_mark_orderbook_gap_btcusdt",
            samples_requested=1,
            interval_seconds=0,
            now_fn=lambda: NOW,
        )

        self.assertEqual(result["schema_version"], "market_sampling_v1")
        self.assertEqual(result["adapter_id"], "live_bybit_mark_orderbook_gap_btcusdt")
        self.assertFalse(result["council_recommended"])
        sample = result["samples"][0]
        self.assertEqual(sample["sample_index"], 1)
        self.assertEqual(sample["status"], "ok")
        self.assertIsNone(sample["error"])
        self.assertEqual(sample["strategy_family"], "mark_orderbook_gap_hunt")
        self.assertEqual(sample["strategy_id"], "mark_orderbook_gap_hunt_v0")
        self.assertEqual(sample["candidate_count"], 1)
        self.assertEqual(sample["readiness_status"], "REJECT")
        self.assertFalse(sample["readiness_pass"])
        self.assertEqual(sample["recommended_default_decision"], "REJECT")
        self.assertEqual(sample["venue_id"], "bybit")
        self.assertEqual(sample["market_symbol"], "BTCUSDT")
        self.assertEqual(sample["parser_normalized_status"], "OK")
        self.assertEqual(sample["diagnostics_count"], 3)
        self.assertEqual(sample["data_age_ms"], -6647)
        self.assertTrue(sample["timestamp_data_age_watch"])
        self.assertTrue(sample["negative_data_age_observed"])
        self.assertEqual(sample["gross_gap_pct"], 0.006219574093567398)
        self.assertEqual(sample["estimated_net_gap_pct"], -0.1937804259064326)
        self.assertTrue(sample["liquidity_pass"])
        self.assertTrue(sample["freshness_pass"])
        self.assertTrue(sample["comparability_pass"])
        self.assertEqual(sample["required_missing_fields"], [])
        self.assertEqual(sample["mark_price"], 63991.52)
        self.assertEqual(sample["index_price"], 64014.24)
        self.assertEqual(sample["bid"], 63995.50)
        self.assertEqual(sample["ask"], 63995.60)
        self.assertTrue(sample["no_trade_only"])
        self.assertEqual(sample["execution_policy"], "NO_TRADE_ONLY")

    def test_bybit_sampling_summary_counts_readiness_gaps_and_data_age_watch(self) -> None:
        result = run_market_sampling(
            StaticPacketAdapter(_bybit_mark_packet()),
            adapter_id="live_bybit_mark_orderbook_gap_btcusdt",
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
        self.assertEqual(summary["max_estimated_net_gap_pct"], -0.1937804259064326)
        self.assertEqual(summary["avg_estimated_net_gap_pct"], -0.1937804259064326)
        self.assertEqual(summary["max_gross_gap_pct"], 0.006219574093567398)
        self.assertEqual(summary["avg_latency_ms"], 13)
        self.assertEqual(summary["max_latency_ms"], 13)
        self.assertEqual(summary["persistence_status"], "NO_PERSISTENT_EDGE")
        self.assertEqual(summary["recommended_default_decision"], "REJECT")
        self.assertEqual(summary["timestamp_data_age_watch_count"], 1)
        self.assertTrue(summary["negative_data_age_observed"])
        self.assertFalse(result["council_recommended"])

    def test_negative_data_age_is_not_clamped_or_reinterpreted(self) -> None:
        result = run_market_sampling(
            StaticPacketAdapter(_bybit_mark_packet(data_age_ms=-6647)),
            adapter_id="live_bybit_mark_orderbook_gap_btcusdt",
            samples_requested=1,
            interval_seconds=0,
            now_fn=lambda: NOW,
        )

        sample = result["samples"][0]
        self.assertEqual(sample["data_age_ms"], -6647)
        self.assertTrue(sample["timestamp_data_age_watch"])
        self.assertEqual(sample["readiness_status"], "REJECT")
        self.assertTrue(sample["freshness_pass"])
        self.assertEqual(result["summary"]["timestamp_data_age_watch_count"], 1)

    def test_watch_remains_analysis_only_without_alert_council_or_execution(self) -> None:
        result = run_market_sampling(
            StaticPacketAdapter(_bybit_mark_packet(readiness_status="WATCH", net_gap_pct=0.3)),
            adapter_id="live_bybit_mark_orderbook_gap_btcusdt",
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

    def test_bybit_sampling_uses_mocked_adapter_without_network_or_env(self) -> None:
        with patch("socket.socket") as socket_factory, patch("os.getenv") as getenv:
            result = run_market_sampling(
                StaticPacketAdapter(_bybit_mark_packet()),
                adapter_id="live_bybit_mark_orderbook_gap_btcusdt",
                samples_requested=1,
                interval_seconds=0,
                now_fn=lambda: NOW,
            )

        socket_factory.assert_not_called()
        getenv.assert_not_called()
        self.assertEqual(result["samples"][0]["status"], "ok")

    def test_mocked_bybit_packet_is_valid_opportunity_packet_shape(self) -> None:
        packet = OpportunityPacket.model_validate(_bybit_mark_packet())

        self.assertEqual(packet.strategy_family, "mark_orderbook_gap_hunt")
        self.assertEqual(packet.candidates[0].candidate_type, "mark_orderbook_gap_observation")
        self.assertEqual(packet.observations[0].venue_id, "bybit")


if __name__ == "__main__":
    unittest.main()
