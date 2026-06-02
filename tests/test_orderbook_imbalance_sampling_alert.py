from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from src.market_data.persistence import summarize_persistence
from src.market_data.sampling import run_market_sampling
from src.notifications.alert_rules import evaluate_alert
from src.notifications.formatters import format_console_alert
from src.storage.opportunity_journal import append_journal_record, build_journal_record


class FakeAdapter:
    def __init__(self, snapshots: list[dict[str, Any]]) -> None:
        self.snapshots = snapshots
        self.calls = 0

    def fetch_snapshot(self) -> dict[str, Any]:
        item = self.snapshots[self.calls]
        self.calls += 1
        return item


class OrderbookImbalanceSamplingAlertTests(unittest.TestCase):
    def test_sampling_extracts_orderbook_imbalance_metrics_without_net_gap(self):
        result = run_market_sampling(
            FakeAdapter([orderbook_snapshot("bid")]),
            adapter_id="replay_orderbook_imbalance",
            samples_requested=1,
            interval_seconds=0,
        )

        sample = result["samples"][0]
        candidate = sample["best_candidate"]
        self.assertEqual(sample["strategy_family"], "orderbook_imbalance")
        self.assertEqual(candidate["candidate_type"], "orderbook_imbalance_signal")
        self.assertEqual(candidate["imbalance_side"], "BID_HEAVY")
        self.assertGreater(candidate["imbalance_ratio"], 1.5)
        self.assertIn("bid_depth_notional", candidate)
        self.assertIn("ask_depth_notional", candidate)
        self.assertIsNone(candidate["estimated_net_gap_pct"])
        self.assertFalse(sample["readiness_pass"])
        self.assertFalse(result["council_recommended"])
        self.assertIsNone(result["council_input_file"])

    def test_no_imbalance_summary(self):
        summary = summarize_persistence(
            [ok_orderbook_sample("BALANCED", False), ok_orderbook_sample("BALANCED", False)],
            adapter_id="fake_orderbook",
            samples_requested=2,
        )

        self.assertEqual(summary["persistence_status"], "NO_IMBALANCE")
        self.assertEqual(summary["balanced_count"], 2)
        self.assertFalse(summary["council_recommended"])
        self.assertIsNone(summary["council_input_file"])

    def test_non_persistent_imbalance_summary(self):
        summary = summarize_persistence(
            [ok_orderbook_sample("BID_HEAVY", True), ok_orderbook_sample("BALANCED", False)],
            adapter_id="fake_orderbook",
            samples_requested=2,
        )

        self.assertEqual(summary["persistence_status"], "NO_PERSISTENT_IMBALANCE")
        self.assertEqual(summary["imbalance_pass_count"], 1)

    def test_persistent_bid_heavy_summary(self):
        summary = summarize_persistence(
            [ok_orderbook_sample("BID_HEAVY", True), ok_orderbook_sample("BID_HEAVY", True), ok_orderbook_sample("BALANCED", False)],
            adapter_id="fake_orderbook",
            samples_requested=3,
        )

        self.assertEqual(summary["persistence_status"], "PERSISTENT_BID_HEAVY")
        self.assertEqual(summary["bid_heavy_count"], 2)
        self.assertEqual(summary["recommended_default_decision"], "WATCH")
        self.assertFalse(summary["council_recommended"])

    def test_persistent_ask_heavy_summary(self):
        summary = summarize_persistence(
            [ok_orderbook_sample("ASK_HEAVY", True), ok_orderbook_sample("ASK_HEAVY", True)],
            adapter_id="fake_orderbook",
            samples_requested=2,
        )

        self.assertEqual(summary["persistence_status"], "PERSISTENT_ASK_HEAVY")
        self.assertEqual(summary["ask_heavy_count"], 2)
        self.assertFalse(summary["council_recommended"])

    def test_alternating_bid_ask_summary_is_mixed(self):
        summary = summarize_persistence(
            [ok_orderbook_sample("BID_HEAVY", True), ok_orderbook_sample("ASK_HEAVY", True), ok_orderbook_sample("BID_HEAVY", True)],
            adapter_id="fake_orderbook",
            samples_requested=3,
        )

        self.assertEqual(summary["persistence_status"], "MIXED_IMBALANCE")
        self.assertFalse(summary["council_recommended"])
        self.assertIsNone(summary["council_input_file"])

    def test_orderbook_alert_rules_and_formatter(self):
        bid_payload = sampling_payload("PERSISTENT_BID_HEAVY")
        ask_payload = sampling_payload("PERSISTENT_ASK_HEAVY")
        no_payload = sampling_payload("NO_IMBALANCE")

        bid_alert = evaluate_alert(bid_payload)
        ask_alert = evaluate_alert(ask_payload)
        no_alert = evaluate_alert(no_payload)
        message = format_console_alert(bid_payload, bid_alert)

        self.assertTrue(bid_alert["should_alert"])
        self.assertEqual(bid_alert["alert_level"], "WATCH")
        self.assertEqual(bid_alert["recommended_action"], "REVIEW_JOURNAL")
        self.assertTrue(ask_alert["should_alert"])
        self.assertEqual(ask_alert["alert_level"], "WATCH")
        self.assertFalse(no_alert["should_alert"])
        self.assertIn("experimental orderbook_imbalance BTC/KRW", message)
        self.assertIn("non_active=true", message)
        self.assertIn("council_recommended=false", message)
        self.assertIn("bid_heavy_count=2", message)

    def test_orderbook_journal_record_appends_strategy_fields(self):
        payload = sampling_payload("PERSISTENT_BID_HEAVY")
        record = build_journal_record(payload, sampling_output="/tmp/orderbook_sample.json")

        self.assertEqual(record["strategy_family"], "orderbook_imbalance")
        self.assertEqual(record["imbalance_seen_count"], 2)
        self.assertEqual(record["bid_heavy_count"], 2)
        self.assertEqual(record["sampling_output"], "/tmp/orderbook_sample.json")
        self.assertFalse(record["council_recommended"])
        self.assertIsNone(record["council_input_file"])

        with tempfile.TemporaryDirectory() as td:
            journal_path = Path(td) / "journal.jsonl"
            append_journal_record(payload, journal_path=journal_path, sampling_output="/tmp/orderbook_sample.json")
            saved = json.loads(journal_path.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(saved["persistence_status"], "PERSISTENT_BID_HEAVY")
        self.assertEqual(saved["strategy_family"], "orderbook_imbalance")


def sampling_payload(status: str) -> dict[str, Any]:
    return {
        "schema_version": "market_sampling_v1",
        "adapter_id": "replay_orderbook_imbalance",
        "samples_requested": 3,
        "samples": [{"opportunity_packet": {"asset": "BTC", "quote": "KRW", "strategy_family": "orderbook_imbalance"}}],
        "summary": {
            "adapter_id": "replay_orderbook_imbalance",
            "strategy_family": "orderbook_imbalance",
            "samples_requested": 3,
            "samples_ok": 3,
            "samples_error": 0,
            "candidate_seen_count": 3,
            "imbalance_seen_count": 2 if status != "NO_IMBALANCE" else 0,
            "bid_heavy_count": 2 if status == "PERSISTENT_BID_HEAVY" else 0,
            "ask_heavy_count": 2 if status == "PERSISTENT_ASK_HEAVY" else 0,
            "balanced_count": 1 if status != "NO_IMBALANCE" else 3,
            "imbalance_pass_count": 2 if status != "NO_IMBALANCE" else 0,
            "experimental_watch_count": 2 if status != "NO_IMBALANCE" else 0,
            "readiness_pass_count": 0,
            "direction_counts": {"bid_heavy_orderbook_signal": 2} if status == "PERSISTENT_BID_HEAVY" else {},
            "max_imbalance_ratio": 3.25 if status != "NO_IMBALANCE" else None,
            "avg_imbalance_ratio": 2.12 if status != "NO_IMBALANCE" else None,
            "persistence_status": status,
            "recommended_default_decision": "WATCH" if status != "NO_IMBALANCE" else "REJECT",
            "council_recommended": False,
            "council_input_file": None,
        },
        "council_recommended": False,
        "council_input_file": None,
        "sampling_output_file": "data/market_samples/replay_orderbook_imbalance_sample.json",
    }


def ok_orderbook_sample(side: str, imbalance_pass: bool) -> dict[str, Any]:
    return {
        "status": "ok",
        "strategy_family": "orderbook_imbalance",
        "readiness_status": "WATCH" if imbalance_pass else "REJECT",
        "readiness_pass": False,
        "best_candidate": orderbook_candidate(side, imbalance_pass),
        "candidate_count": 1,
        "latency": {"max_latency_ms": 12},
    }


def orderbook_candidate(side: str, imbalance_pass: bool) -> dict[str, Any]:
    direction = {
        "BID_HEAVY": "bid_heavy_orderbook_signal",
        "ASK_HEAVY": "ask_heavy_orderbook_signal",
        "BALANCED": "balanced_orderbook_signal",
    }[side]
    return {
        "candidate_id": f"{side.lower()}_candidate",
        "candidate_type": "orderbook_imbalance_signal",
        "source_venue_id": "upbit",
        "direction": direction,
        "estimated_net_gap_pct": None,
        "imbalance_side": side,
        "imbalance_ratio": 2.0 if imbalance_pass else 1.0,
        "bid_depth_notional": 2_000_000 if side == "BID_HEAVY" else 1_000_000,
        "ask_depth_notional": 2_000_000 if side == "ASK_HEAVY" else 1_000_000,
        "spread_pct": 0.01,
        "depth_levels_used": 2,
        "liquidity_pass": True,
        "freshness_pass": True,
        "imbalance_pass": imbalance_pass,
    }


def orderbook_snapshot(side: str) -> dict[str, Any]:
    bid_size, ask_size = {
        "bid": (0.5, 0.1),
        "ask": (0.1, 0.5),
        "balanced": (0.2, 0.2),
    }[side]
    return {
        "packet_id": f"orderbook_{side}",
        "created_at_utc": "2026-06-02T00:00:00+00:00",
        "asset": "BTC",
        "quote": "KRW",
        "strategy_family": "orderbook_imbalance",
        "strategy_id": "orderbook_imbalance_v0",
        "thresholds": {"imbalance_ratio_threshold": 1.5, "max_data_age_ms": 3000, "target_notional": 1_000_000},
        "observations": [spot_observation("upbit", bid_size=bid_size, ask_size=ask_size)],
    }


def spot_observation(venue_id: str, *, bid_size: float, ask_size: float) -> dict[str, Any]:
    return {
        "observation_id": f"{venue_id}_btc_krw_orderbook",
        "venue_id": venue_id,
        "venue_name": venue_id.title(),
        "market_symbol": "BTC/KRW",
        "instrument_type": "spot",
        "region": "KR",
        "last_price": 99_995_000,
        "bid": 99_990_000,
        "ask": 100_000_000,
        "bid_size": bid_size,
        "ask_size": ask_size,
        "timestamp_utc": "2026-06-02T00:00:00+00:00",
        "liquidity": {
            "orderbook_depth_available": True,
            "volume_available": True,
            "depth_levels": [
                {"level": 1, "bid_price": 99_990_000, "bid_size": bid_size, "ask_price": 100_000_000, "ask_size": ask_size},
                {"level": 2, "bid_price": 99_980_000, "bid_size": bid_size, "ask_price": 100_010_000, "ask_size": ask_size},
            ],
        },
        "data_quality": {"timestamps_available": True, "max_data_age_ms": 500, "latency_ms": 10, "is_realtime": False},
        "health": {"api_status_known": True, "api_ok": True},
    }


if __name__ == "__main__":
    unittest.main()
