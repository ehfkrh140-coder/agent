from __future__ import annotations

import unittest

from src.market_data.vwap import (
    compute_buy_vwap_from_asks,
    compute_executable_notional,
    compute_sell_vwap_from_bids,
    compute_slippage_pct,
)


class VwapCalculationTests(unittest.TestCase):
    def test_buy_vwap_consumes_multiple_ask_levels(self):
        depth = [
            {"ask_price": 100.0, "ask_size": 5.0},
            {"ask_price": 110.0, "ask_size": 10.0},
        ]

        result = compute_buy_vwap_from_asks(depth, 1_000.0)

        self.assertTrue(result["fully_filled"])
        self.assertEqual(result["filled_notional"], 1_000.0)
        self.assertEqual(result["levels_consumed"], 2)
        self.assertAlmostEqual(result["vwap_price"], 104.7619047619)
        self.assertAlmostEqual(result["slippage_pct"], 4.7619047619)

    def test_sell_vwap_consumes_multiple_bid_levels(self):
        depth = [
            {"bid_price": 100.0, "bid_size": 5.0},
            {"bid_price": 90.0, "bid_size": 10.0},
        ]

        result = compute_sell_vwap_from_bids(depth, 1_000.0)

        self.assertTrue(result["fully_filled"])
        self.assertEqual(result["filled_notional"], 1_000.0)
        self.assertEqual(result["levels_consumed"], 2)
        self.assertAlmostEqual(result["vwap_price"], 94.7368421053)
        self.assertAlmostEqual(result["slippage_pct"], 5.2631578947)

    def test_depth_shortfall_marks_not_fully_filled(self):
        depth = [{"ask_price": 100.0, "ask_size": 2.0}]

        result = compute_buy_vwap_from_asks(depth, 1_000.0)

        self.assertFalse(result["fully_filled"])
        self.assertEqual(result["filled_notional"], 200.0)
        self.assertEqual(compute_executable_notional(depth, "buy"), 200.0)

    def test_slippage_pct_uses_side_specific_degradation(self):
        self.assertAlmostEqual(compute_slippage_pct(100.0, 101.0, "buy"), 1.0)
        self.assertAlmostEqual(compute_slippage_pct(100.0, 99.0, "sell"), 1.0)
        self.assertEqual(compute_slippage_pct(100.0, 99.0, "buy"), 0.0)


if __name__ == "__main__":
    unittest.main()
