from __future__ import annotations

import copy
import json
import unittest
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.market_data.parsers.mark_orderbook_gap_hunt import parse_mark_orderbook_gap_snapshot
from src.strategy.mark_orderbook_gap_hunt_readiness import evaluate_mark_orderbook_gap_readiness

FIXTURE_DIR = Path("tests/fixtures/mark_orderbook_gap_hunt")


def _fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    return Decimal(str(value))


def _evaluate_readiness_contract(
    parser_output: dict[str, Any],
    *,
    fee_slippage_buffer_pct: Decimal | str | None = "0.15",
    liquidity_pass: bool | None = True,
    require_freshness: bool = False,
    size_or_notional_resolved: bool = True,
) -> dict[str, Any]:
    return evaluate_mark_orderbook_gap_readiness(
        parser_output,
        fee_slippage_buffer_pct=fee_slippage_buffer_pct,
        liquidity_pass=liquidity_pass,
        require_freshness=require_freshness,
        size_or_notional_resolved=size_or_notional_resolved,
    )


def _binance_parser_output() -> dict[str, Any]:
    fixture = _fixture("binance_valid_btcusdt.json")
    return parse_mark_orderbook_gap_snapshot(
        venue_id="binance",
        parser_mode="binance_usdm",
        mark_response=fixture["mark_response"],
        orderbook_response=fixture["depth_response"],
        metadata_response=fixture["metadata_response"],
    )


class MarkOrderbookGapHuntReadinessContractTests(unittest.TestCase):
    def test_parser_need_data_maps_to_readiness_need_data(self) -> None:
        fixture = _fixture("binance_valid_btcusdt.json")
        parser_output = parse_mark_orderbook_gap_snapshot(
            venue_id="binance",
            parser_mode="binance_usdm",
            mark_response=None,
            orderbook_response=fixture["depth_response"],
            metadata_response=fixture["metadata_response"],
        )

        readiness = _evaluate_readiness_contract(parser_output)

        self.assertEqual(readiness["readiness_status"], "NEED_DATA")
        self.assertFalse(readiness["readiness_pass"])
        self.assertIn("parser_normalized_status", readiness["required_missing_fields"])
        self.assertIn("mark_response", readiness["required_missing_fields"])

    def test_missing_required_fields_maps_to_need_data(self) -> None:
        parser_output = _binance_parser_output()
        parser_output["bid"] = None

        readiness = _evaluate_readiness_contract(parser_output)

        self.assertEqual(readiness["readiness_status"], "NEED_DATA")
        self.assertIn("bid", readiness["required_missing_fields"])

    def test_unresolved_notional_or_fee_assumptions_map_to_need_data(self) -> None:
        parser_output = _binance_parser_output()

        unresolved_notional = _evaluate_readiness_contract(parser_output, size_or_notional_resolved=False)
        missing_fee = _evaluate_readiness_contract(parser_output, fee_slippage_buffer_pct=None)

        self.assertEqual(unresolved_notional["readiness_status"], "NEED_DATA")
        self.assertIn("size_or_notional_resolved", unresolved_notional["required_missing_fields"])
        self.assertEqual(missing_fee["readiness_status"], "NEED_DATA")
        self.assertIn("fee_slippage_buffer_pct", missing_fee["required_missing_fields"])

    def test_valid_parser_output_with_negative_or_zero_gap_rejects(self) -> None:
        parser_output = _binance_parser_output()
        parser_output["mark_price"] = "100"
        parser_output["ask"] = "100.00"
        parser_output["bid"] = "99.90"

        readiness = _evaluate_readiness_contract(parser_output, fee_slippage_buffer_pct="0")

        self.assertEqual(readiness["readiness_status"], "REJECT")
        self.assertFalse(readiness["readiness_pass"])
        self.assertIn("no_positive_gross_gap", readiness["warnings"])
        self.assertLessEqual(Decimal(readiness["metrics"]["max_observed_gap_pct"]), Decimal("0"))

    def test_positive_gross_gap_wiped_out_by_fee_buffer_rejects(self) -> None:
        parser_output = _binance_parser_output()
        parser_output["mark_price"] = "100"
        parser_output["ask"] = "99.90"
        parser_output["bid"] = "99.80"

        readiness = _evaluate_readiness_contract(parser_output, fee_slippage_buffer_pct="0.20")

        self.assertEqual(readiness["readiness_status"], "REJECT")
        self.assertFalse(readiness["readiness_pass"])
        self.assertIn("non_positive_estimated_net_gap", readiness["warnings"])
        self.assertEqual(readiness["metrics"]["max_observed_gap_pct"], "0.100")
        self.assertLessEqual(Decimal(readiness["metrics"]["estimated_net_gap_pct"]), Decimal("0"))

    def test_positive_net_gap_maps_to_watch_without_execution_or_council(self) -> None:
        parser_output = _binance_parser_output()
        parser_output["mark_price"] = "100"
        parser_output["ask"] = "99.00"
        parser_output["bid"] = "98.80"

        readiness = _evaluate_readiness_contract(parser_output, fee_slippage_buffer_pct="0.20")

        self.assertEqual(readiness["readiness_status"], "WATCH")
        self.assertFalse(readiness["readiness_pass"])
        self.assertEqual(readiness["recommended_default_decision"], "WATCH")
        self.assertGreater(Decimal(readiness["metrics"]["estimated_net_gap_pct"]), Decimal("0"))
        self.assertNotIn("execution_allowed", readiness)
        self.assertNotIn("council_auto_call", readiness)

    def test_liquidity_failure_rejects_even_with_positive_gap(self) -> None:
        parser_output = _binance_parser_output()
        parser_output["mark_price"] = "100"
        parser_output["ask"] = "99.00"
        parser_output["bid"] = "98.80"

        readiness = _evaluate_readiness_contract(parser_output, fee_slippage_buffer_pct="0.20", liquidity_pass=False)

        self.assertEqual(readiness["readiness_status"], "REJECT")
        self.assertIn("liquidity_insufficient", readiness["warnings"])
        self.assertFalse(readiness["readiness_pass"])

    def test_watch_output_contains_no_private_auth_or_order_fields(self) -> None:
        parser_output = _binance_parser_output()
        parser_output["mark_price"] = "100"
        parser_output["ask"] = "99.00"
        parser_output["bid"] = "98.80"

        readiness = _evaluate_readiness_contract(parser_output, fee_slippage_buffer_pct="0.20")
        text = json.dumps(readiness).lower()

        forbidden = [
            "api_key",
            "api_secret",
            "authorization",
            "bearer",
            "account",
            "balance",
            "order_id",
            "withdraw",
            "deposit",
            "transfer",
            "private",
        ]
        for phrase in forbidden:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, text)

    def test_readiness_helper_does_not_mutate_parser_output(self) -> None:
        parser_output = _binance_parser_output()
        original = copy.deepcopy(parser_output)

        _evaluate_readiness_contract(parser_output)

        self.assertEqual(parser_output, original)


if __name__ == "__main__":
    unittest.main()
