from __future__ import annotations

import unittest

from src.market_data.registry import build_adapter, load_market_data_config
from src.market_data.sampling import run_market_sampling


class TetherCrossMarketSamplingTests(unittest.TestCase):
    def test_replay_sampling_exposes_tether_best_candidate_metrics(self) -> None:
        config = load_market_data_config()
        adapter = build_adapter("replay_tether_cross_market_premium", config)

        result = run_market_sampling(
            adapter,
            adapter_id="replay_tether_cross_market_premium",
            samples_requested=1,
            interval_seconds=0,
        )

        self.assertEqual(result["schema_version"], "market_sampling_v1")
        self.assertEqual(result["adapter_id"], "replay_tether_cross_market_premium")
        self.assertEqual(result["samples_requested"], 1)
        self.assertEqual(result["summary"]["samples_ok"], 1)
        sample = result["samples"][0]
        self.assertEqual(sample["status"], "ok")
        self.assertEqual(sample["strategy_family"], "tether_cross_market_premium")
        self.assertEqual(sample["readiness_status"], "WATCH")
        self.assertEqual(sample["recommended_default_decision"], "WATCH")
        self.assertIsNone(sample["successful_global_reference_count"])
        self.assertIsNone(sample["failed_global_reference_venues"])
        self.assertIn("opportunity_packet", sample)

        best = sample["best_candidate"]
        self.assertEqual(best["candidate_type"], "tether_domestic_spread_signal")
        self.assertEqual(best["global_reference_pass"], True)
        self.assertEqual(best["global_reference_venue_count"], 3)
        self.assertEqual(best["global_usdt_depeg_flag"], False)
        self.assertEqual(best["global_usdt_depeg_pct"], 0.0)
        self.assertEqual(best["global_usdt_mid"], 1.0)
        self.assertEqual(best["net_gap_pass"], True)
        self.assertEqual(best["domestic_best_bid"], 1400.0)
        self.assertEqual(best["domestic_best_ask"], 1390.0)
        self.assertEqual(best["domestic_mid"], 1395.0)
        self.assertGreater(best["estimated_net_gap_pct"], 0)


if __name__ == "__main__":
    unittest.main()
