from __future__ import annotations

import copy
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.market_data.sampling import run_market_sampling

ADAPTER_ID = "mock_depth_vwap_sampling_context"
CREATED_AT = "2026-06-05T00:00:00Z"


class FakeAdapter:
    def __init__(self, snapshots: list[dict[str, Any]]):
        self.snapshots = [copy.deepcopy(snapshot) for snapshot in snapshots]
        self.calls = 0

    def fetch_snapshot(self) -> dict[str, Any]:
        snapshot = self.snapshots[self.calls % len(self.snapshots)]
        self.calls += 1
        return copy.deepcopy(snapshot)


def _noop_sleep(_seconds: float) -> None:
    return None


def _now() -> datetime:
    return datetime(2026, 6, 5, tzinfo=timezone.utc)


def _depth_vwap_context(
    *,
    target_size: Any | None = "2",
    target_notional: Any | None = None,
    insufficient_depth: bool = False,
    behavior: str = "diagnostics_only",
    warnings: list[str] | None = None,
    ask_slippage: Any = 0.01,
    bid_slippage: Any = 0.02,
) -> dict[str, Any]:
    warnings = list(warnings or [])
    return {
        "behavior": behavior,
        "no_trade_only": True,
        "execution_policy": "NO_TRADE_ONLY",
        "target_size": target_size,
        "target_notional": target_notional,
        "spot": {
            "ask_vwap_result": {"side": "ask", "slippage_pct": ask_slippage, "insufficient_depth": insufficient_depth},
            "bid_vwap_result": {"side": "bid", "slippage_pct": bid_slippage, "insufficient_depth": False},
            "depth_available": True,
            "ask_levels_available": 3,
            "bid_levels_available": 3,
            "warnings": ["spot_depth_context"],
        },
        "perp": {
            "ask_vwap_result": {"side": "ask", "slippage_pct": 0.03, "insufficient_depth": False},
            "bid_vwap_result": {"side": "bid", "slippage_pct": 0.04, "insufficient_depth": insufficient_depth},
            "depth_available": True,
            "ask_levels_available": 3,
            "bid_levels_available": 3,
            "warnings": ["perp_depth_context"],
        },
        "directions": {
            "long_spot_short_perp": {
                "spot_vwap_ask": 100.5,
                "perp_vwap_bid": 101.0,
                "depth_coverage_pct": 100,
                "insufficient_depth": insufficient_depth,
                "context_only": True,
                "warnings": ["direction_context"],
            },
            "long_perp_short_spot": {
                "perp_vwap_ask": 102.5,
                "spot_vwap_bid": 99.0,
                "depth_coverage_pct": 100,
                "insufficient_depth": False,
                "context_only": True,
            },
        },
        "warnings": warnings,
    }


def _packet(
    packet_id: str,
    *,
    context: Any | None = None,
    context_location: str = "candidate",
    readiness_status: str = "REJECT",
    recommended_default_decision: str = "REJECT",
    readiness_pass: bool = False,
    estimated_net_gap_pct: float = -0.5,
    gross_gap_pct: float = 1.0,
) -> dict[str, Any]:
    candidate_extensions = {"no_trade_only": True, "execution_policy": "NO_TRADE_ONLY"}
    packet_extensions = {
        "no_trade_only": True,
        "execution_policy": "NO_TRADE_ONLY",
        "adapter_metadata": {"no_trade_only": True, "execution_policy": "NO_TRADE_ONLY"},
        "readiness": {
            "readiness_status": readiness_status,
            "recommended_default_decision": recommended_default_decision,
            "readiness_pass": readiness_pass,
            "required_missing_fields": [],
            "warnings": [],
        },
    }
    if context is not None and context_location == "candidate":
        candidate_extensions["depth_vwap_context"] = copy.deepcopy(context)
    if context is not None and context_location == "packet":
        packet_extensions["depth_vwap_context"] = copy.deepcopy(context)
    return {
        "schema_version": "opportunity_packet_v0",
        "packet_id": packet_id,
        "created_at_utc": CREATED_AT,
        "asset": "BTC",
        "quote": "USDT",
        "signal_type": "spot_futures_basis",
        "strategy_family": "spot_futures_basis",
        "strategy_id": "spot_futures_basis_v0",
        "observations": [
            {
                "observation_id": f"{packet_id}_spot",
                "venue_id": "mock_venue",
                "venue_name": "Mock Venue",
                "market_symbol": "BTCUSDT",
                "bid": 99.0,
                "ask": 100.0,
                "extensions": {"parser_normalized_status": "OK"},
            }
        ],
        "candidates": [
            {
                "candidate_id": f"{packet_id}_candidate",
                "candidate_type": "spot_futures_basis_observation",
                "strategy_family": "spot_futures_basis",
                "strategy_id": "spot_futures_basis_v0",
                "source_venue_id": "mock_spot",
                "target_venue_id": "mock_perp",
                "direction": "long_spot_short_perp",
                "gross_gap_pct": gross_gap_pct,
                "estimated_net_gap_pct": estimated_net_gap_pct,
                "liquidity_pass": True,
                "freshness_pass": True,
                "guard_pass": True,
                "metrics": {
                    "readiness_status": readiness_status,
                    "readiness_pass": readiness_pass,
                    "recommended_default_decision": recommended_default_decision,
                    "parser_normalized_status": "OK",
                    "estimated_net_basis_pct": estimated_net_gap_pct,
                },
                "required_missing_fields": [],
                "assumptions": ["WATCH is not ENTER", "no trading behavior"],
                "extensions": candidate_extensions,
            }
        ],
        "detector_metadata": {"detector_name": "mock_depth_vwap_sampling_context"},
        "extensions": packet_extensions,
    }


def _sample(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    return run_market_sampling(
        FakeAdapter(snapshots),
        adapter_id=ADAPTER_ID,
        samples_requested=len(snapshots),
        interval_seconds=0,
        output_path=None,
        also_save_packets=False,
        sleep_fn=_noop_sleep,
        now_fn=_now,
    )


class DepthVwapSamplingContextTest(unittest.TestCase):
    def test_sampling_summary_counts_depth_vwap_context_seen_count(self) -> None:
        result = _sample([_packet("seen_1", context=_depth_vwap_context()), _packet("seen_2", context=_depth_vwap_context())])
        self.assertEqual(2, result["summary"]["depth_vwap_context_seen_count"])

    def test_sampling_summary_counts_depth_vwap_context_missing_count_when_absent(self) -> None:
        result = _sample([_packet("seen", context=_depth_vwap_context()), _packet("missing")])
        self.assertEqual(1, result["summary"]["depth_vwap_context_missing_count"])

    def test_behavior_counts_include_diagnostics_only(self) -> None:
        result = _sample([_packet("seen", context=_depth_vwap_context())])
        self.assertEqual(1, result["summary"]["depth_vwap_context_behavior_counts"].get("diagnostics_only"))

    def test_insufficient_depth_count_is_aggregated(self) -> None:
        result = _sample([
            _packet("ok", context=_depth_vwap_context()),
            _packet("insufficient", context=_depth_vwap_context(insufficient_depth=True)),
        ])
        self.assertEqual(1, result["summary"]["depth_vwap_insufficient_depth_count"])

    def test_target_size_seen_count_is_aggregated(self) -> None:
        result = _sample([_packet("size", context=_depth_vwap_context(target_size="2"))])
        self.assertEqual(1, result["summary"]["depth_vwap_target_size_seen_count"])

    def test_target_notional_seen_count_is_aggregated(self) -> None:
        result = _sample([_packet("notional", context=_depth_vwap_context(target_size=None, target_notional="200"))])
        self.assertEqual(1, result["summary"]["depth_vwap_target_notional_seen_count"])

    def test_warning_counts_are_aggregated(self) -> None:
        result = _sample([_packet("warnings", context=_depth_vwap_context(warnings=["top_level_warning"]))])
        counts = result["summary"]["depth_vwap_warning_counts"]
        self.assertEqual(1, counts.get("top_level_warning"))
        self.assertEqual(1, counts.get("spot_depth_context"))
        self.assertEqual(1, counts.get("perp_depth_context"))
        self.assertEqual(1, counts.get("direction_context"))

    def test_max_and_avg_ask_slippage_summary_works(self) -> None:
        result = _sample([
            _packet("ask_1", context=_depth_vwap_context(ask_slippage="0.01")),
            _packet("ask_2", context=_depth_vwap_context(ask_slippage="0.03")),
        ])
        self.assertEqual(0.03, result["summary"]["max_depth_vwap_ask_slippage_pct"])
        self.assertAlmostEqual(0.025, result["summary"]["avg_depth_vwap_ask_slippage_pct"])

    def test_max_and_avg_bid_slippage_summary_works(self) -> None:
        result = _sample([
            _packet("bid_1", context=_depth_vwap_context(bid_slippage="0.02")),
            _packet("bid_2", context=_depth_vwap_context(bid_slippage="0.06")),
        ])
        self.assertEqual(0.06, result["summary"]["max_depth_vwap_bid_slippage_pct"])
        self.assertAlmostEqual(0.04, result["summary"]["avg_depth_vwap_bid_slippage_pct"])

    def test_per_sample_depth_vwap_context_seen_fields_are_present(self) -> None:
        sample = _sample([_packet("seen", context=_depth_vwap_context())])["samples"][0]
        self.assertTrue(sample["depth_vwap_context_seen"])
        self.assertFalse(sample["depth_vwap_insufficient_depth"])
        self.assertEqual("diagnostics_only", sample["depth_vwap_context_behavior"])
        self.assertEqual("2", sample["depth_vwap_target_size"])
        self.assertIsNone(sample["depth_vwap_target_notional"])
        self.assertIsInstance(sample["depth_vwap_warnings"], list)

    def test_per_sample_missing_context_fields_are_safe(self) -> None:
        sample = _sample([_packet("missing")])["samples"][0]
        self.assertFalse(sample["depth_vwap_context_seen"])
        self.assertFalse(sample["depth_vwap_insufficient_depth"])
        self.assertIsNone(sample["depth_vwap_context_behavior"])
        self.assertEqual([], sample["depth_vwap_warnings"])
        self.assertIsNone(sample["depth_vwap_target_size"])
        self.assertIsNone(sample["depth_vwap_target_notional"])

    def test_readiness_status_unchanged(self) -> None:
        sample = _sample([_packet("readiness", context=_depth_vwap_context(), readiness_status="REJECT")])["samples"][0]
        self.assertEqual("REJECT", sample["readiness_status"])
        self.assertEqual("REJECT", sample["best_candidate"]["readiness_status"])

    def test_recommended_default_decision_unchanged(self) -> None:
        sample = _sample([_packet("decision", context=_depth_vwap_context(), recommended_default_decision="REJECT")])["samples"][0]
        self.assertEqual("REJECT", sample["recommended_default_decision"])
        self.assertEqual("REJECT", sample["best_candidate"]["recommended_default_decision"])

    def test_estimated_net_gap_pct_unchanged(self) -> None:
        sample = _sample([_packet("net", context=_depth_vwap_context(), estimated_net_gap_pct=-0.7)])["samples"][0]
        self.assertEqual(-0.7, sample["estimated_net_gap_pct"])
        self.assertEqual(-0.7, sample["best_candidate"]["estimated_net_gap_pct"])

    def test_positive_net_gap_count_unchanged(self) -> None:
        baseline = _sample([_packet("base")])
        with_context = _sample([_packet("ctx", context=_depth_vwap_context())])
        self.assertEqual(baseline["summary"]["positive_net_gap_count"], with_context["summary"]["positive_net_gap_count"])
        self.assertEqual(0, with_context["summary"]["positive_net_gap_count"])

    def test_readiness_pass_count_unchanged(self) -> None:
        baseline = _sample([_packet("base", readiness_pass=False)])
        with_context = _sample([_packet("ctx", context=_depth_vwap_context(), readiness_pass=False)])
        self.assertEqual(baseline["summary"]["readiness_pass_count"], with_context["summary"]["readiness_pass_count"])
        self.assertEqual(0, with_context["summary"]["readiness_pass_count"])

    def test_persistence_status_and_council_recommended_unchanged(self) -> None:
        baseline = _sample([_packet("base")])
        with_context = _sample([_packet("ctx", context=_depth_vwap_context())])
        self.assertEqual(baseline["summary"]["persistence_status"], with_context["summary"]["persistence_status"])
        self.assertEqual(baseline["council_recommended"], with_context["council_recommended"])

    def test_no_private_account_order_execution_fields_introduced(self) -> None:
        result = _sample([_packet("guard", context=_depth_vwap_context())])
        self._assert_no_forbidden_fields(result)

    def test_generated_json_paths_not_created_or_referenced(self) -> None:
        before_packets = set(Path("data/generated_packets").glob("*.json"))
        before_samples = set(Path("data/market_samples").glob("*.json"))
        result = _sample([_packet("generated", context=_depth_vwap_context())])
        self.assertIsNone(result["sampling_output_file"])
        self.assertEqual(before_packets, set(Path("data/generated_packets").glob("*.json")))
        self.assertEqual(before_samples, set(Path("data/market_samples").glob("*.json")))

    def test_existing_no_context_sampling_behavior_remains_safe(self) -> None:
        result = _sample([_packet("missing")])
        summary = result["summary"]
        self.assertEqual(1, summary["samples_ok"])
        self.assertEqual(0, summary["samples_error"])
        self.assertEqual(1, summary["candidate_seen_count"])
        self.assertEqual(1, summary["readiness_status_counts"].get("REJECT"))
        self.assertEqual(1, summary["reject_count"])
        self.assertEqual(0, summary["watch_count"])
        self.assertEqual(0, summary["need_data_count"])
        self.assertEqual(0, summary["depth_vwap_context_seen_count"])
        self.assertEqual(1, summary["depth_vwap_context_missing_count"])

    def test_watch_path_remains_watch_is_not_enter_and_no_execution(self) -> None:
        result = _sample([
            _packet(
                "watch",
                context=_depth_vwap_context(),
                readiness_status="WATCH",
                recommended_default_decision="WATCH",
                readiness_pass=False,
            )
        ])
        sample = result["samples"][0]
        self.assertEqual("WATCH", sample["readiness_status"])
        self.assertEqual("WATCH", sample["recommended_default_decision"])
        self.assertNotEqual("ENTER", sample["recommended_default_decision"])
        self.assertEqual("NO_TRADE_ONLY", sample["execution_policy"])
        self.assertFalse(result["council_recommended"])

    def test_malformed_depth_vwap_context_does_not_crash_and_records_warning(self) -> None:
        result = _sample([_packet("malformed", context="not_a_context")])
        sample = result["samples"][0]
        self.assertFalse(sample["depth_vwap_context_seen"])
        self.assertIn("depth_vwap_context_malformed", sample["depth_vwap_warnings"])
        self.assertEqual(0, result["summary"]["depth_vwap_context_seen_count"])
        self.assertEqual(1, result["summary"]["depth_vwap_context_missing_count"])
        self.assertEqual(1, result["summary"]["depth_vwap_warning_counts"].get("depth_vwap_context_malformed"))

    def test_packet_level_context_lookup_is_supported(self) -> None:
        result = _sample([_packet("packet_context", context=_depth_vwap_context(), context_location="packet")])
        self.assertTrue(result["samples"][0]["depth_vwap_context_seen"])
        self.assertEqual(1, result["summary"]["depth_vwap_context_seen_count"])

    def _assert_no_forbidden_fields(self, value: Any) -> None:
        forbidden = (
            "apiKey",
            "secret",
            "token",
            "account",
            "balance",
            "position",
            "orderId",
            "clientOrderId",
            "cancel",
            "withdraw",
            "deposit",
            "transfer",
            "privateKey",
            "execution_enabled",
            "auto_trade",
        )
        allowed = {"execution_policy", "imbalance_side", "imbalance_ratio", "imbalance_pass"}
        if isinstance(value, dict):
            for key, nested in value.items():
                if key not in allowed:
                    key_text = str(key)
                    for fragment in forbidden:
                        self.assertNotIn(fragment.lower(), key_text.lower(), key)
                self._assert_no_forbidden_fields(nested)
        elif isinstance(value, list):
            for item in value:
                self._assert_no_forbidden_fields(item)


if __name__ == "__main__":
    unittest.main()
