from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from src.market_data.persistence import summarize_persistence
from src.market_data.sampling import run_market_sampling


class FakeAdapter:
    def __init__(self, snapshots_or_errors: list[Any]) -> None:
        self.items = list(snapshots_or_errors)
        self.calls = 0

    def fetch_snapshot(self) -> dict[str, Any]:
        item = self.items[self.calls]
        self.calls += 1
        if isinstance(item, Exception):
            raise item
        return item


class MarketDataSamplingTests(unittest.TestCase):
    def test_sampler_records_five_fake_packets_without_sleep(self):
        adapter = FakeAdapter([snapshot_with_candidate(net_gap=0.3, net_pass=True, ready=True) for _ in range(5)])
        sleeps: list[float] = []

        result = run_market_sampling(
            adapter,
            adapter_id="fake_spot",
            samples_requested=5,
            interval_seconds=0,
            sleep_fn=sleeps.append,
        )

        self.assertEqual(len(result["samples"]), 5)
        self.assertEqual(result["summary"]["samples_ok"], 5)
        self.assertEqual(result["summary"]["persistence_status"], "PERSISTENT_READY_EDGE")
        self.assertTrue(result["council_recommended"])
        self.assertEqual(sleeps, [])

    def test_sampler_records_partial_errors_and_continues(self):
        adapter = FakeAdapter(
            [
                snapshot_with_candidate(net_gap=-0.1, net_pass=False, ready=False),
                RuntimeError("temporary public API failure"),
                snapshot_with_candidate(net_gap=-0.2, net_pass=False, ready=False),
            ]
        )

        result = run_market_sampling(adapter, adapter_id="fake_spot", samples_requested=3, interval_seconds=0, max_errors=3)

        self.assertEqual(result["summary"]["samples_ok"], 2)
        self.assertEqual(result["summary"]["samples_error"], 1)
        self.assertEqual(result["samples"][1]["status"], "error")
        self.assertIn("temporary public API failure", result["samples"][1]["error"])
        self.assertEqual(result["summary"]["persistence_status"], "NO_PERSISTENT_EDGE")

    def test_max_errors_sets_sample_errors(self):
        adapter = FakeAdapter([RuntimeError("e1"), RuntimeError("e2"), RuntimeError("e3")])

        result = run_market_sampling(adapter, adapter_id="fake_spot", samples_requested=3, interval_seconds=0, max_errors=1)

        self.assertEqual(len(result["samples"]), 2)
        self.assertEqual(result["summary"]["persistence_status"], "SAMPLE_ERRORS")
        self.assertFalse(result["council_recommended"])

    def test_persistence_no_candidate(self):
        summary = summarize_persistence(
            [ok_sample(best_candidate=None), ok_sample(best_candidate=None)],
            adapter_id="fake_spot",
            samples_requested=2,
        )

        self.assertEqual(summary["persistence_status"], "NO_CANDIDATE")
        self.assertEqual(summary["recommended_default_decision"], "REJECT")

    def test_persistence_no_persistent_edge_when_net_gap_never_passes(self):
        summary = summarize_persistence(
            [ok_sample(candidate("upbit", "bithumb", -0.1, False)), ok_sample(candidate("upbit", "bithumb", -0.2, False))],
            adapter_id="fake_spot",
            samples_requested=2,
        )

        self.assertEqual(summary["persistence_status"], "NO_PERSISTENT_EDGE")
        self.assertEqual(summary["positive_net_gap_count"], 0)

    def test_persistence_some_net_gap_pass_is_persistent_net_gap(self):
        summary = summarize_persistence(
            [ok_sample(candidate("upbit", "bithumb", 0.3, True)), ok_sample(candidate("upbit", "bithumb", -0.1, False))],
            adapter_id="fake_spot",
            samples_requested=2,
        )

        self.assertEqual(summary["persistence_status"], "PERSISTENT_NET_GAP")
        self.assertEqual(summary["positive_net_gap_count"], 1)
        self.assertFalse(summary["readiness_pass_count"])

    def test_persistence_ready_edge_requires_consecutive_ready(self):
        summary = summarize_persistence(
            [
                ok_sample(candidate("upbit", "bithumb", 0.3, True), readiness_pass=True),
                ok_sample(candidate("upbit", "bithumb", 0.4, True), readiness_pass=True),
            ],
            adapter_id="fake_spot",
            samples_requested=2,
        )

        self.assertEqual(summary["persistence_status"], "PERSISTENT_READY_EDGE")
        self.assertEqual(summary["readiness_pass_count"], 2)

    def test_direction_counts_and_latency_distribution(self):
        summary = summarize_persistence(
            [
                ok_sample(candidate("upbit", "bithumb", -0.1, False), latency={"max_latency_ms": 10}),
                ok_sample(candidate("bithumb", "upbit", -0.2, False), latency={"max_latency_ms": 30}),
                ok_sample(candidate("upbit", "bithumb", -0.3, False), latency={"max_latency_ms": 20}),
            ],
            adapter_id="fake_spot",
            samples_requested=3,
        )

        self.assertEqual(summary["direction_counts"], {"upbit_to_bithumb": 2, "bithumb_to_upbit": 1})
        self.assertEqual(summary["avg_latency_ms"], 20)
        self.assertEqual(summary["max_latency_ms"], 30)

    def test_output_json_schema_is_stable(self):
        result = run_market_sampling(
            FakeAdapter([snapshot_with_candidate(net_gap=-0.1, net_pass=False, ready=False)]),
            adapter_id="fake_spot",
            samples_requested=1,
            interval_seconds=0,
        )

        self.assertEqual(result["schema_version"], "market_sampling_v1")
        self.assertIn("samples", result)
        self.assertIn("summary", result)
        self.assertIn("council_recommended", result)
        self.assertEqual(result["samples"][0]["best_candidate"]["source_vwap_ask"], 100_000_000)
        json.dumps(result)

    def test_sample_tool_writes_output_without_live_network(self):
        with tempfile.TemporaryDirectory() as td:
            output_path = Path(td) / "sample.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    "tools/sample_market_data.py",
                    "--adapter",
                    "replay_cross_exchange_spot_spread",
                    "--samples",
                    "1",
                    "--interval",
                    "0",
                    "--output",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("Market sampling saved", completed.stdout)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "market_sampling_v1")
            self.assertEqual(len(payload["samples"]), 1)
            self.assertIn("persistence_status", payload["summary"])


def snapshot_with_candidate(*, net_gap: float, net_pass: bool, ready: bool) -> dict[str, Any]:
    target_bid = 100_650_000 if net_pass or ready else 100_050_000
    return {
        "packet_id": f"fake_{net_gap}_{net_pass}_{ready}",
        "created_at_utc": "2026-05-30T00:00:00+00:00",
        "asset": "BTC",
        "quote": "KRW",
        "strategy_family": "cross_exchange_spot_spread",
        "strategy_id": "cross_exchange_spot_spread_v1",
        "thresholds": {"min_notional": 1_000_000, "min_net_gap_pct": 0.2, "max_data_age_ms": 3000, "safety_buffer_pct": 0.05},
        "observations": [
            spot_observation("upbit", ask=100_000_000, bid=99_990_000, ask_size=0.6, bid_size=0.4),
            spot_observation("bithumb", ask=100_700_000, bid=target_bid, ask_size=0.3, bid_size=0.5),
        ],
    }


def spot_observation(venue_id: str, *, ask: float, bid: float, ask_size: float, bid_size: float) -> dict[str, Any]:
    # net_gap arguments are represented by thresholds/fees in builder tests; for sampling fake adapter
    # all positive top-of-book spreads build a candidate and readiness derives from its computed VWAP metrics.
    fee_pct = 0.05
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
        "timestamp_utc": "2026-05-30T00:00:00+00:00",
        "fees": {"trading_fee_pct": fee_pct, "fee_source": "test"},
        "liquidity": {
            "orderbook_depth_available": True,
            "volume_available": True,
            "estimated_executable_notional": min(ask * ask_size, bid * bid_size),
            "estimated_slippage_pct": 0.0,
            "depth_levels": [{"level": 1, "bid_price": bid, "bid_size": bid_size, "ask_price": ask, "ask_size": ask_size}],
        },
        "data_quality": {"timestamps_available": True, "max_data_age_ms": 500, "latency_ms": 10 if venue_id == "upbit" else 30, "is_realtime": False},
        "health": {"api_status_known": True, "api_ok": True},
    }


def candidate(source: str, target: str, net_gap: float, net_pass: bool) -> dict[str, Any]:
    return {
        "candidate_id": f"{source}_to_{target}",
        "source_venue_id": source,
        "target_venue_id": target,
        "gross_gap_pct": max(net_gap, 0.01),
        "estimated_net_gap_pct": net_gap,
        "net_gap_pass": net_pass,
        "liquidity_pass": True,
        "freshness_pass": True,
    }


def ok_sample(best_candidate: dict[str, Any] | None, *, readiness_pass: bool = False, latency: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "status": "ok",
        "best_candidate": best_candidate,
        "candidate_count": 1 if best_candidate else 0,
        "readiness_pass": readiness_pass,
        "latency": latency or {"max_latency_ms": 10},
    }


if __name__ == "__main__":
    unittest.main()
