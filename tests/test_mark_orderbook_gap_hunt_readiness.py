from __future__ import annotations

import copy
import inspect
import json
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from src.market_data.parsers.mark_orderbook_gap_hunt import parse_mark_orderbook_gap_snapshot
from src.strategy.mark_orderbook_gap_hunt_readiness import evaluate_mark_orderbook_gap_readiness

FIXTURE_DIR = Path("tests/fixtures/mark_orderbook_gap_hunt")


def _fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _binance_parser_output() -> dict:
    fixture = _fixture("binance_valid_btcusdt.json")
    return parse_mark_orderbook_gap_snapshot(
        venue_id="binance",
        parser_mode="binance_usdm",
        mark_response=fixture["mark_response"],
        orderbook_response=fixture["depth_response"],
        metadata_response=fixture["metadata_response"],
    )


class MarkOrderbookGapHuntReadinessTests(unittest.TestCase):
    def test_parser_need_data_maps_to_readiness_need_data(self) -> None:
        fixture = _fixture("binance_valid_btcusdt.json")
        parser_output = parse_mark_orderbook_gap_snapshot(
            venue_id="binance",
            parser_mode="binance_usdm",
            mark_response=None,
            orderbook_response=fixture["depth_response"],
            metadata_response=fixture["metadata_response"],
        )

        readiness = evaluate_mark_orderbook_gap_readiness(
            parser_output,
            fee_slippage_buffer_pct=Decimal("0.15"),
            liquidity_pass=True,
            require_freshness=False,
            size_or_notional_resolved=True,
        )

        self.assertEqual(readiness["readiness_status"], "NEED_DATA")
        self.assertFalse(readiness["readiness_pass"])
        self.assertIn("parser_normalized_status", readiness["required_missing_fields"])
        self.assertIn("mark_response", readiness["required_missing_fields"])

    def test_missing_mark_bid_or_ask_maps_to_need_data(self) -> None:
        for field_name in ["mark_price", "bid", "ask"]:
            with self.subTest(field_name=field_name):
                parser_output = _binance_parser_output()
                parser_output[field_name] = None

                readiness = evaluate_mark_orderbook_gap_readiness(
                    parser_output,
                    fee_slippage_buffer_pct=Decimal("0.15"),
                    liquidity_pass=True,
                    require_freshness=False,
                    size_or_notional_resolved=True,
                )

                self.assertEqual(readiness["readiness_status"], "NEED_DATA")
                self.assertIn(field_name, readiness["required_missing_fields"])

    def test_unresolved_size_or_missing_fee_maps_to_need_data(self) -> None:
        parser_output = _binance_parser_output()

        unresolved = evaluate_mark_orderbook_gap_readiness(
            parser_output,
            fee_slippage_buffer_pct=Decimal("0.15"),
            liquidity_pass=True,
            require_freshness=False,
            size_or_notional_resolved=False,
        )
        missing_fee = evaluate_mark_orderbook_gap_readiness(
            parser_output,
            fee_slippage_buffer_pct=None,
            liquidity_pass=True,
            require_freshness=False,
            size_or_notional_resolved=True,
        )

        self.assertEqual(unresolved["readiness_status"], "NEED_DATA")
        self.assertIn("size_or_notional_resolved", unresolved["required_missing_fields"])
        self.assertEqual(missing_fee["readiness_status"], "NEED_DATA")
        self.assertIn("fee_slippage_buffer_pct", missing_fee["required_missing_fields"])

    def test_require_freshness_gates_unknown_or_false_freshness(self) -> None:
        parser_output = _binance_parser_output()

        readiness = evaluate_mark_orderbook_gap_readiness(
            parser_output,
            fee_slippage_buffer_pct=Decimal("0.15"),
            liquidity_pass=True,
            require_freshness=True,
            size_or_notional_resolved=True,
        )

        self.assertEqual(readiness["readiness_status"], "NEED_DATA")
        self.assertIn("freshness_pass", readiness["required_missing_fields"])

    def test_no_positive_gross_gap_rejects(self) -> None:
        parser_output = _binance_parser_output()
        parser_output["mark_price"] = "100"
        parser_output["ask"] = "100.00"
        parser_output["bid"] = "99.90"

        readiness = evaluate_mark_orderbook_gap_readiness(
            parser_output,
            fee_slippage_buffer_pct=Decimal("0"),
            liquidity_pass=True,
            require_freshness=False,
            size_or_notional_resolved=True,
        )

        self.assertEqual(readiness["readiness_status"], "REJECT")
        self.assertFalse(readiness["readiness_pass"])
        self.assertIn("no_positive_gross_gap", readiness["warnings"])

    def test_positive_gross_gap_wiped_out_by_buffer_rejects(self) -> None:
        parser_output = _binance_parser_output()
        parser_output["mark_price"] = "100"
        parser_output["ask"] = "99.90"
        parser_output["bid"] = "99.80"

        readiness = evaluate_mark_orderbook_gap_readiness(
            parser_output,
            fee_slippage_buffer_pct=Decimal("0.20"),
            liquidity_pass=True,
            require_freshness=False,
            size_or_notional_resolved=True,
        )

        self.assertEqual(readiness["readiness_status"], "REJECT")
        self.assertIn("non_positive_estimated_net_gap", readiness["warnings"])
        self.assertLessEqual(Decimal(readiness["metrics"]["estimated_net_gap_pct"]), Decimal("0"))

    def test_liquidity_false_rejects(self) -> None:
        parser_output = _binance_parser_output()
        parser_output["mark_price"] = "100"
        parser_output["ask"] = "99.00"
        parser_output["bid"] = "98.80"

        readiness = evaluate_mark_orderbook_gap_readiness(
            parser_output,
            fee_slippage_buffer_pct=Decimal("0.20"),
            liquidity_pass=False,
            require_freshness=False,
            size_or_notional_resolved=True,
        )

        self.assertEqual(readiness["readiness_status"], "REJECT")
        self.assertIn("liquidity_insufficient", readiness["warnings"])

    def test_positive_net_gap_maps_to_watch_without_execution_council_or_alert(self) -> None:
        parser_output = _binance_parser_output()
        parser_output["mark_price"] = "100"
        parser_output["ask"] = "99.00"
        parser_output["bid"] = "98.80"

        readiness = evaluate_mark_orderbook_gap_readiness(
            parser_output,
            fee_slippage_buffer_pct=Decimal("0.20"),
            liquidity_pass=True,
            require_freshness=False,
            size_or_notional_resolved=True,
        )

        self.assertEqual(readiness["readiness_status"], "WATCH")
        self.assertFalse(readiness["readiness_pass"])
        self.assertGreater(Decimal(readiness["metrics"]["estimated_net_gap_pct"]), Decimal("0"))
        self.assertNotIn("execution_allowed", readiness)
        self.assertNotIn("council_auto_call", readiness)
        self.assertNotIn("alert_trigger", readiness)

    def test_min_net_gap_threshold_must_be_exceeded_for_watch(self) -> None:
        parser_output = _binance_parser_output()
        parser_output["mark_price"] = "100"
        parser_output["ask"] = "99.00"
        parser_output["bid"] = "98.80"

        readiness = evaluate_mark_orderbook_gap_readiness(
            parser_output,
            fee_slippage_buffer_pct=Decimal("0.20"),
            liquidity_pass=True,
            require_freshness=False,
            size_or_notional_resolved=True,
            min_net_gap_pct=Decimal("1.00"),
        )

        self.assertEqual(readiness["readiness_status"], "REJECT")
        self.assertIn("non_positive_estimated_net_gap", readiness["warnings"])

    def test_helper_does_not_mutate_parser_output(self) -> None:
        parser_output = _binance_parser_output()
        original = copy.deepcopy(parser_output)

        evaluate_mark_orderbook_gap_readiness(
            parser_output,
            fee_slippage_buffer_pct=Decimal("0.15"),
            liquidity_pass=True,
            require_freshness=False,
            size_or_notional_resolved=True,
        )

        self.assertEqual(parser_output, original)

    def test_helper_has_no_network_env_or_credential_side_effects(self) -> None:
        parser_output = _binance_parser_output()
        source = inspect.getsource(evaluate_mark_orderbook_gap_readiness)
        forbidden_source_terms = ["requests", "urllib", "http_client", "os.environ", "getenv"]
        for term in forbidden_source_terms:
            with self.subTest(term=term):
                self.assertNotIn(term, source)

        with patch("socket.socket") as socket_factory, patch("os.getenv") as getenv:
            readiness = evaluate_mark_orderbook_gap_readiness(
                parser_output,
                fee_slippage_buffer_pct=Decimal("0.15"),
                liquidity_pass=True,
                require_freshness=False,
                size_or_notional_resolved=True,
            )
        socket_factory.assert_not_called()
        getenv.assert_not_called()
        self.assertIn(readiness["readiness_status"], {"REJECT", "WATCH"})

    def test_watch_output_contains_no_private_auth_or_order_fields(self) -> None:
        parser_output = _binance_parser_output()
        parser_output["mark_price"] = "100"
        parser_output["ask"] = "99.00"
        parser_output["bid"] = "98.80"

        readiness = evaluate_mark_orderbook_gap_readiness(
            parser_output,
            fee_slippage_buffer_pct=Decimal("0.20"),
            liquidity_pass=True,
            require_freshness=False,
            size_or_notional_resolved=True,
        )
        text = json.dumps(readiness).lower()
        for phrase in [
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
        ]:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
