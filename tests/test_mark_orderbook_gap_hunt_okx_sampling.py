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


class SequencePacketAdapter:
    def __init__(self, packets: list[dict]) -> None:
        self.packets = [copy.deepcopy(packet) for packet in packets]
        self.index = 0

    def fetch_snapshot(self) -> dict:
        packet = self.packets[self.index]
        self.index += 1
        return copy.deepcopy(packet)


def _okx_mark_packet(
    *,
    readiness_status: str = "REJECT",
    gross_gap_pct: float = 0.0050201590762907295,
    net_gap_pct: float = -0.19497984092370926,
    data_age_ms: int = -7578,
    index_price: float | None = None,
    assumptions: list[str] | None = None,
) -> dict:
    return {
        "schema_version": "opportunity_packet_v0",
        "packet_id": f"okx_btc_usdt_swap_mark_orderbook_gap_{readiness_status.lower()}",
        "created_at_utc": "2026-06-04T00:00:00+00:00",
        "asset": "BTC",
        "quote": "USDT",
        "signal_type": "mark_orderbook_gap_hunt",
        "strategy_family": "mark_orderbook_gap_hunt",
        "strategy_id": "mark_orderbook_gap_hunt_v0",
        "observations": [
            {
                "observation_id": "okx_btc_usdt_swap_mark_orderbook_gap",
                "venue_id": "okx",
                "venue_name": "OKX",
                "market_symbol": "BTC-USDT-SWAP",
                "instrument_type": "linear_swap",
                "mark_price": 63743.0,
                "index_price": index_price,
                "bid": 63739.7,
                "ask": 63739.8,
                "bid_size": 66.94,
                "ask_size": 99.34,
                "data_quality": {
                    "timestamps_available": True,
                    "max_data_age_ms": data_age_ms,
                    "latency_ms": 17,
                    "source": "okx_public_swap",
                    "is_realtime": True,
                },
                "liquidity": {
                    "orderbook_depth_available": True,
                    "volume_available": False,
                    "depth_levels": [],
                },
                "extensions": {
                    "parser_normalized_status": "OK",
                    "parser_mode": "okx_swap",
                    "instType": "SWAP",
                    "instId": "BTC-USDT-SWAP",
                    "bid_size_unit": "contracts",
                    "ask_size_unit": "contracts",
                },
            }
        ],
        "candidates": [
            {
                "candidate_id": "okx_btc_usdt_swap_mark_orderbook_gap_candidate",
                "candidate_type": "mark_orderbook_gap_observation",
                "strategy_family": "mark_orderbook_gap_hunt",
                "strategy_id": "mark_orderbook_gap_hunt_v0",
                "source_observation_id": "okx_btc_usdt_swap_mark_orderbook_gap",
                "source_venue_id": "okx",
                "direction": "analysis_only_mark_orderbook_gap_observation",
                "gross_gap_pct": gross_gap_pct,
                "estimated_net_gap_pct": net_gap_pct,
                "long_gap_pct": gross_gap_pct,
                "short_gap_pct": -0.000156829385697254,
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
                "assumptions": assumptions
                or [
                    "mark price is not executable",
                    "WATCH is analysis-only",
                    "public no-key endpoints only",
                    "analysis-only packet",
                    "no private API",
                    "no trading behavior",
                    "timestamp/data_age policy unchanged",
                ],
            }
        ],
        "detector_metadata": {
            "detector_name": "okx_mark_orderbook_gap_hunt_adapter",
            "detector_version": "v0",
            "generated_from": "public_okx_mark_price_books_instruments",
        },
        "extensions": {
            "adapter_metadata": {
                "adapter_id": "live_okx_mark_orderbook_gap_btc_usdt_swap",
                "adapter_type": "okx_mark_orderbook_gap_hunt",
                "venue_id": "okx",
                "instType": "SWAP",
                "instId": "BTC-USDT-SWAP",
                "experimental_strategy": True,
                "non_active_strategy": True,
                "no_trade_only": True,
                "execution_policy": "NO_TRADE_ONLY",
            },
            "parser_output": {
                "parser_mode": "okx_swap",
                "normalized_status": "OK",
                "data_age_ms": data_age_ms,
            },
            "diagnostics": [
                {"parser_stage": "mark-price", "http_status": 200, "code": "0", "msg": ""},
                {"parser_stage": "books", "http_status": 200, "code": "0", "msg": ""},
                {"parser_stage": "instruments", "http_status": 200, "code": "0", "msg": ""},
            ],
            "readiness": {
                "readiness_status": readiness_status,
                "readiness_pass": False,
                "recommended_default_decision": readiness_status,
                "required_missing_fields": [],
                "warnings": [],
                "metrics": {
                    "long_gap_pct": gross_gap_pct,
                    "short_gap_pct": -0.000156829385697254,
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


class OkxMarkOrderbookGapHuntSamplingTests(unittest.TestCase):
    def test_sampling_pipeline_consumes_mocked_okx_mark_orderbook_gap_packet(self) -> None:
        result = run_market_sampling(
            StaticPacketAdapter(_okx_mark_packet()),
            adapter_id="live_okx_mark_orderbook_gap_btc_usdt_swap",
            samples_requested=1,
            interval_seconds=0,
            now_fn=lambda: NOW,
        )

        self.assertEqual(result["schema_version"], "market_sampling_v1")
        self.assertEqual(result["adapter_id"], "live_okx_mark_orderbook_gap_btc_usdt_swap")
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
        self.assertEqual(sample["venue_id"], "okx")
        self.assertEqual(sample["market_symbol"], "BTC-USDT-SWAP")
        self.assertEqual(sample["parser_normalized_status"], "OK")
        self.assertEqual(sample["diagnostics_count"], 3)
        self.assertEqual(sample["gross_gap_pct"], 0.0050201590762907295)
        self.assertEqual(sample["estimated_net_gap_pct"], -0.19497984092370926)
        self.assertTrue(sample["liquidity_pass"])
        self.assertTrue(sample["freshness_pass"])
        self.assertTrue(sample["comparability_pass"])
        self.assertEqual(sample["required_missing_fields"], [])
        self.assertEqual(sample["mark_price"], 63743.0)
        self.assertIsNone(sample["index_price"])
        self.assertTrue(sample["index_price_null_observed"])
        self.assertEqual(sample["bid"], 63739.7)
        self.assertEqual(sample["ask"], 63739.8)
        self.assertTrue(sample["no_trade_only"])
        self.assertEqual(sample["execution_policy"], "NO_TRADE_ONLY")

    def test_okx_sampling_summary_counts_readiness_gaps_and_watch_items(self) -> None:
        result = run_market_sampling(
            StaticPacketAdapter(_okx_mark_packet()),
            adapter_id="live_okx_mark_orderbook_gap_btc_usdt_swap",
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
        self.assertEqual(summary["max_estimated_net_gap_pct"], -0.19497984092370926)
        self.assertEqual(summary["avg_estimated_net_gap_pct"], -0.19497984092370926)
        self.assertEqual(summary["max_gross_gap_pct"], 0.0050201590762907295)
        self.assertEqual(summary["avg_latency_ms"], 17)
        self.assertEqual(summary["max_latency_ms"], 17)
        self.assertEqual(summary["persistence_status"], "NO_PERSISTENT_EDGE")
        self.assertEqual(summary["recommended_default_decision"], "REJECT")
        self.assertEqual(summary["timestamp_data_age_watch_count"], 1)
        self.assertTrue(summary["negative_data_age_observed"])
        self.assertEqual(summary["index_price_null_count"], 1)
        self.assertTrue(summary["index_price_null_observed"])
        self.assertEqual(summary["stale_assumption_wording_count"], 0)
        self.assertFalse(summary["stale_assumption_wording_observed"])
        self.assertFalse(result["council_recommended"])

    def test_three_sample_okx_summary_fields_are_under_summary_key(self) -> None:
        result = run_market_sampling(
            SequencePacketAdapter(
                [
                    _okx_mark_packet(data_age_ms=124),
                    _okx_mark_packet(data_age_ms=98),
                    _okx_mark_packet(data_age_ms=131),
                ]
            ),
            adapter_id="live_okx_mark_orderbook_gap_btc_usdt_swap",
            samples_requested=3,
            interval_seconds=0,
            now_fn=lambda: NOW,
        )

        self.assertNotIn("samples_ok", result)
        summary = result["summary"]
        self.assertEqual(result["samples_requested"], 3)
        self.assertEqual(summary["samples_requested"], 3)
        self.assertEqual(summary["samples_ok"], 3)
        self.assertEqual(summary["samples_error"], 0)
        self.assertEqual(summary["candidate_seen_count"], 3)
        self.assertEqual(summary["positive_gross_gap_count"], 3)
        self.assertEqual(summary["positive_net_gap_count"], 0)
        self.assertEqual(summary["readiness_status_counts"], {"REJECT": 3})
        self.assertEqual(summary["watch_count"], 0)
        self.assertEqual(summary["reject_count"], 3)
        self.assertEqual(summary["need_data_count"], 0)
        self.assertEqual(summary["max_estimated_net_gap_pct"], -0.19497984092370926)
        self.assertEqual(summary["avg_estimated_net_gap_pct"], -0.19497984092370926)
        self.assertEqual(summary["max_gross_gap_pct"], 0.0050201590762907295)
        self.assertEqual(summary["avg_latency_ms"], 17)
        self.assertEqual(summary["max_latency_ms"], 17)
        self.assertEqual(summary["persistence_status"], "NO_PERSISTENT_EDGE")
        self.assertEqual(summary["recommended_default_decision"], "REJECT")
        self.assertFalse(result["council_recommended"])
        self.assertEqual(summary["timestamp_data_age_watch_count"], 0)
        self.assertFalse(summary["negative_data_age_observed"])
        self.assertEqual(summary["index_price_null_count"], 3)
        self.assertTrue(summary["index_price_null_observed"])
        self.assertEqual(summary["stale_assumption_wording_count"], 0)
        self.assertFalse(summary["stale_assumption_wording_observed"])
        self.assertEqual([sample["status"] for sample in result["samples"]], ["ok", "ok", "ok"])
        self.assertEqual([sample["readiness_status"] for sample in result["samples"]], ["REJECT", "REJECT", "REJECT"])
        self.assertEqual([sample["venue_id"] for sample in result["samples"]], ["okx", "okx", "okx"])
        self.assertEqual(
            [sample["market_symbol"] for sample in result["samples"]],
            ["BTC-USDT-SWAP", "BTC-USDT-SWAP", "BTC-USDT-SWAP"],
        )
        self.assertEqual([sample["parser_normalized_status"] for sample in result["samples"]], ["OK", "OK", "OK"])
        self.assertEqual([sample["data_age_ms"] for sample in result["samples"]], [124, 98, 131])
        self.assertEqual([sample["index_price"] for sample in result["samples"]], [None, None, None])
        self.assertEqual([sample["index_price_null_observed"] for sample in result["samples"]], [True, True, True])
        self.assertEqual([sample["timestamp_data_age_watch"] for sample in result["samples"]], [False, False, False])
        self.assertEqual([sample["stale_assumption_wording_observed"] for sample in result["samples"]], [False, False, False])
        self.assertEqual([sample["no_trade_only"] for sample in result["samples"]], [True, True, True])
        self.assertEqual(
            [sample["execution_policy"] for sample in result["samples"]],
            ["NO_TRADE_ONLY", "NO_TRADE_ONLY", "NO_TRADE_ONLY"],
        )

    def test_negative_data_age_is_surfaced_without_clamping_or_reinterpretation(self) -> None:
        result = run_market_sampling(
            StaticPacketAdapter(_okx_mark_packet(data_age_ms=-7578)),
            adapter_id="live_okx_mark_orderbook_gap_btc_usdt_swap",
            samples_requested=1,
            interval_seconds=0,
            now_fn=lambda: NOW,
        )

        sample = result["samples"][0]
        self.assertEqual(sample["data_age_ms"], -7578)
        self.assertTrue(sample["timestamp_data_age_watch"])
        self.assertTrue(sample["negative_data_age_observed"])
        self.assertTrue(sample["freshness_pass"])
        self.assertEqual(result["summary"]["timestamp_data_age_watch_count"], 1)

    def test_index_price_none_is_surfaced_without_okx_reference_policy_change(self) -> None:
        result = run_market_sampling(
            StaticPacketAdapter(_okx_mark_packet(index_price=None)),
            adapter_id="live_okx_mark_orderbook_gap_btc_usdt_swap",
            samples_requested=1,
            interval_seconds=0,
            now_fn=lambda: NOW,
        )

        sample = result["samples"][0]
        self.assertIsNone(sample["index_price"])
        self.assertTrue(sample["index_price_null_observed"])
        self.assertEqual(sample["required_missing_fields"], [])
        self.assertEqual(sample["parser_normalized_status"], "OK")
        self.assertTrue(result["summary"]["index_price_null_observed"])

    def test_stale_assumption_wording_regression_guard_distinguishes_future_packets(self) -> None:
        future_result = run_market_sampling(
            StaticPacketAdapter(_okx_mark_packet()),
            adapter_id="live_okx_mark_orderbook_gap_btc_usdt_swap",
            samples_requested=1,
            interval_seconds=0,
            now_fn=lambda: NOW,
        )
        stale_result = run_market_sampling(
            StaticPacketAdapter(_okx_mark_packet(assumptions=["no config registration in this PR"])),
            adapter_id="live_okx_mark_orderbook_gap_btc_usdt_swap",
            samples_requested=1,
            interval_seconds=0,
            now_fn=lambda: NOW,
        )

        self.assertFalse(future_result["samples"][0]["stale_assumption_wording_observed"])
        self.assertFalse(future_result["summary"]["stale_assumption_wording_observed"])
        self.assertTrue(stale_result["samples"][0]["stale_assumption_wording_observed"])
        self.assertTrue(stale_result["summary"]["stale_assumption_wording_observed"])

    def test_watch_remains_analysis_only_without_alert_council_or_execution(self) -> None:
        result = run_market_sampling(
            StaticPacketAdapter(_okx_mark_packet(readiness_status="WATCH", net_gap_pct=0.3)),
            adapter_id="live_okx_mark_orderbook_gap_btc_usdt_swap",
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

    def test_okx_sampling_uses_mocked_adapter_without_network_or_env(self) -> None:
        with patch("socket.socket") as socket_factory, patch("os.getenv") as getenv:
            result = run_market_sampling(
                StaticPacketAdapter(_okx_mark_packet()),
                adapter_id="live_okx_mark_orderbook_gap_btc_usdt_swap",
                samples_requested=1,
                interval_seconds=0,
                now_fn=lambda: NOW,
            )

        socket_factory.assert_not_called()
        getenv.assert_not_called()
        self.assertEqual(result["samples"][0]["status"], "ok")

    def test_mocked_okx_packet_is_valid_opportunity_packet_shape(self) -> None:
        packet = OpportunityPacket.model_validate(_okx_mark_packet())

        self.assertEqual(packet.strategy_family, "mark_orderbook_gap_hunt")
        self.assertEqual(packet.candidates[0].candidate_type, "mark_orderbook_gap_observation")
        self.assertEqual(packet.observations[0].venue_id, "okx")
        self.assertEqual(packet.observations[0].market_symbol, "BTC-USDT-SWAP")


if __name__ == "__main__":
    unittest.main()
