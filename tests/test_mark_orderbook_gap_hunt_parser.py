from __future__ import annotations

import copy
import inspect
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from src.market_data.parsers.mark_orderbook_gap_hunt import (
    MarkOrderbookGapParserError,
    parse_mark_orderbook_gap_snapshot,
)

FIXTURE_DIR = Path("tests/fixtures/mark_orderbook_gap_hunt")


def _fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


class MarkOrderbookGapHuntProductionParserTests(unittest.TestCase):
    def test_binance_valid_fixture_returns_ok_normalized_snapshot(self) -> None:
        fixture = _fixture("binance_valid_btcusdt.json")

        parsed = parse_mark_orderbook_gap_snapshot(
            venue_id="binance",
            parser_mode="binance_usdm",
            mark_response=fixture["mark_response"],
            orderbook_response=fixture["depth_response"],
            metadata_response=fixture["metadata_response"],
        )

        expected = fixture["expected_normalized"]
        self.assertEqual(parsed["normalized_status"], "OK")
        self.assertEqual(parsed["venue_id"], expected["venue_id"])
        self.assertEqual(parsed["parser_mode"], "binance_usdm")
        self.assertEqual(parsed["instrument_id"], expected["instrument_id"])
        self.assertEqual(parsed["instrument_type"], expected["instrument_type"])
        self.assertEqual(parsed["mark_price"], expected["mark_price"])
        self.assertEqual(parsed["index_price"], expected["index_price"])
        self.assertEqual(parsed["bid"], expected["bid"])
        self.assertEqual(parsed["ask"], expected["ask"])
        self.assertEqual(parsed["bid_size_raw"], expected["bid_size_raw"])
        self.assertEqual(parsed["ask_size_raw"], expected["ask_size_raw"])
        self.assertEqual(parsed["tick_size"], expected["tick_size"])
        self.assertEqual(parsed["quantity_step"], expected["quantity_step"])
        self.assertEqual(parsed["min_order_size"], expected["min_order_size"])
        self.assertEqual(parsed["min_notional"], expected["min_notional"])
        self.assertEqual(parsed["margin_asset"], expected["margin_asset"])
        self.assertTrue(parsed["comparability_pass"])
        self.assertEqual(parsed["required_missing_fields"], [])
        self.assertNotEqual(parsed.get("execution_allowed"), True)

    def test_bybit_valid_fixture_returns_ok_normalized_snapshot(self) -> None:
        fixture = _fixture("bybit_valid_btcusdt_linear.json")

        parsed = parse_mark_orderbook_gap_snapshot(
            venue_id="bybit",
            parser_mode="bybit_linear",
            mark_response=None,
            ticker_response=fixture["ticker_response"],
            orderbook_response=fixture["orderbook_response"],
            metadata_response=fixture["metadata_response"],
        )

        expected = fixture["expected_normalized"]
        self.assertEqual(parsed["normalized_status"], "OK")
        self.assertEqual(parsed["venue_id"], expected["venue_id"])
        self.assertEqual(parsed["parser_mode"], "bybit_linear")
        self.assertEqual(parsed["instrument_id"], expected["instrument_id"])
        self.assertEqual(parsed["instrument_type"], expected["instrument_type"])
        self.assertEqual(parsed["mark_price"], expected["mark_price"])
        self.assertEqual(parsed["index_price"], expected["index_price"])
        self.assertEqual(parsed["bid"], expected["bid"])
        self.assertEqual(parsed["ask"], expected["ask"])
        self.assertEqual(parsed["bid_size_raw"], expected["bid_size_raw"])
        self.assertEqual(parsed["ask_size_raw"], expected["ask_size_raw"])
        self.assertEqual(parsed["tick_size"], expected["tick_size"])
        self.assertEqual(parsed["quantity_step"], expected["quantity_step"])
        self.assertEqual(parsed["min_order_size"], expected["min_order_size"])
        self.assertEqual(parsed["min_notional"], expected["min_notional"])
        self.assertEqual(parsed["settle_currency"], expected["settle_coin"])
        self.assertTrue(parsed["comparability_pass"])
        self.assertEqual(parsed["required_missing_fields"], [])
        self.assertNotEqual(parsed.get("execution_allowed"), True)

    def test_okx_valid_fixture_returns_ok_normalized_snapshot(self) -> None:
        fixture = _fixture("okx_valid_btc_usdt_swap.json")

        parsed = parse_mark_orderbook_gap_snapshot(
            venue_id="okx",
            parser_mode="okx_swap",
            mark_response=fixture["mark_response"],
            orderbook_response=fixture["books_response"],
            metadata_response=fixture["metadata_response"],
        )

        expected = fixture["expected_normalized"]
        self.assertEqual(parsed["normalized_status"], "OK")
        self.assertEqual(parsed["venue_id"], expected["venue_id"])
        self.assertEqual(parsed["parser_mode"], "okx_swap")
        self.assertEqual(parsed["instrument_id"], expected["instrument_id"])
        self.assertEqual(parsed["instrument_type"], expected["instrument_type"])
        self.assertEqual(parsed["mark_price"], expected["mark_price"])
        self.assertEqual(parsed["bid"], expected["bid"])
        self.assertEqual(parsed["ask"], expected["ask"])
        self.assertEqual(parsed["bid_size_raw"], expected["bid_size_raw"])
        self.assertEqual(parsed["ask_size_raw"], expected["ask_size_raw"])
        self.assertEqual(parsed["contract_value"], expected["contract_value"])
        self.assertEqual(parsed["contract_multiplier"], expected["contract_multiplier"])
        self.assertEqual(parsed["contract_value_currency"], expected["contract_value_currency"])
        self.assertEqual(parsed["settle_currency"], expected["settle_currency"])
        self.assertEqual(parsed["tick_size"], expected["tick_size"])
        self.assertEqual(parsed["lot_size"], expected["lot_size"])
        self.assertEqual(parsed["min_order_size"], expected["min_order_size"])
        self.assertTrue(parsed["comparability_pass"])
        self.assertEqual(parsed["required_missing_fields"], [])
        self.assertNotEqual(parsed.get("execution_allowed"), True)

    def test_missing_payloads_return_need_data(self) -> None:
        fixture = _fixture("binance_valid_btcusdt.json")

        cases = {
            "missing_mark": {"mark_response": None, "orderbook_response": fixture["depth_response"], "metadata_response": fixture["metadata_response"], "missing": "mark_response"},
            "missing_orderbook": {"mark_response": fixture["mark_response"], "orderbook_response": None, "metadata_response": fixture["metadata_response"], "missing": "orderbook_response"},
            "missing_metadata": {"mark_response": fixture["mark_response"], "orderbook_response": fixture["depth_response"], "metadata_response": None, "missing": "metadata_response"},
        }
        for name, kwargs in cases.items():
            with self.subTest(name=name):
                parsed = parse_mark_orderbook_gap_snapshot(
                    venue_id="binance",
                    parser_mode="binance_usdm",
                    mark_response=kwargs["mark_response"],
                    orderbook_response=kwargs["orderbook_response"],
                    metadata_response=kwargs["metadata_response"],
                )
                self.assertEqual(parsed["normalized_status"], "NEED_DATA")
                self.assertIn(kwargs["missing"], parsed["required_missing_fields"])
                self.assertFalse(parsed["comparability_pass"])

    def test_mismatch_and_unknown_metadata_return_need_data(self) -> None:
        binance = _fixture("binance_valid_btcusdt.json")
        bybit = _fixture("bybit_valid_btcusdt_linear.json")
        okx = _fixture("okx_valid_btc_usdt_swap.json")

        binance_bad = copy.deepcopy(binance)
        binance_bad["metadata_response"]["symbols"][0]["symbol"] = "ETHUSDT"
        binance_parsed = parse_mark_orderbook_gap_snapshot(
            venue_id="binance",
            parser_mode="binance_usdm",
            mark_response=binance_bad["mark_response"],
            orderbook_response=binance_bad["depth_response"],
            metadata_response=binance_bad["metadata_response"],
        )
        self.assertEqual(binance_parsed["normalized_status"], "NEED_DATA")
        self.assertIn("instrument_match", binance_parsed["required_missing_fields"])

        bybit_bad = copy.deepcopy(bybit)
        bybit_bad["metadata_response"]["result"]["category"] = "inverse"
        bybit_parsed = parse_mark_orderbook_gap_snapshot(
            venue_id="bybit",
            parser_mode="bybit_linear",
            mark_response=None,
            ticker_response=bybit_bad["ticker_response"],
            orderbook_response=bybit_bad["orderbook_response"],
            metadata_response=bybit_bad["metadata_response"],
        )
        self.assertEqual(bybit_parsed["normalized_status"], "NEED_DATA")
        self.assertIn("instrument_match", bybit_parsed["required_missing_fields"])

        okx_bad = copy.deepcopy(okx)
        okx_bad["metadata_response"]["data"][0]["instId"] = "ETH-USDT-SWAP"
        okx_parsed = parse_mark_orderbook_gap_snapshot(
            venue_id="okx",
            parser_mode="okx_swap",
            mark_response=okx_bad["mark_response"],
            orderbook_response=okx_bad["books_response"],
            metadata_response=okx_bad["metadata_response"],
        )
        self.assertEqual(okx_parsed["normalized_status"], "NEED_DATA")
        self.assertIn("instrument_match", okx_parsed["required_missing_fields"])

        okx_missing_contract = copy.deepcopy(okx)
        del okx_missing_contract["metadata_response"]["data"][0]["ctVal"]
        del okx_missing_contract["metadata_response"]["data"][0]["lotSz"]
        missing_contract_parsed = parse_mark_orderbook_gap_snapshot(
            venue_id="okx",
            parser_mode="okx_swap",
            mark_response=okx_missing_contract["mark_response"],
            orderbook_response=okx_missing_contract["books_response"],
            metadata_response=okx_missing_contract["metadata_response"],
        )
        self.assertEqual(missing_contract_parsed["normalized_status"], "NEED_DATA")
        self.assertIn("contract_value", missing_contract_parsed["required_missing_fields"])
        self.assertIn("lot_size", missing_contract_parsed["required_missing_fields"])

    def test_stale_timestamp_returns_need_data_when_threshold_can_be_evaluated(self) -> None:
        fixture = _fixture("binance_valid_btcusdt.json")

        parsed = parse_mark_orderbook_gap_snapshot(
            venue_id="binance",
            parser_mode="binance_usdm",
            mark_response=fixture["mark_response"],
            orderbook_response=fixture["depth_response"],
            metadata_response=fixture["metadata_response"],
            collected_at_utc="2030-06-04T00:00:00+00:00",
            max_data_age_ms=1,
        )

        self.assertEqual(parsed["normalized_status"], "NEED_DATA")
        self.assertFalse(parsed["freshness_pass"])
        self.assertIn("fresh_timestamp", parsed["required_missing_fields"])

    def test_parser_rejects_malformed_non_dict_payloads(self) -> None:
        fixture = _fixture("binance_valid_btcusdt.json")

        with self.assertRaises(MarkOrderbookGapParserError):
            parse_mark_orderbook_gap_snapshot(
                venue_id="binance",
                parser_mode="binance_usdm",
                mark_response=[],
                orderbook_response=fixture["depth_response"],
                metadata_response=fixture["metadata_response"],
            )

    def test_parser_has_no_network_env_or_credential_side_effects(self) -> None:
        fixture = _fixture("binance_valid_btcusdt.json")
        source = inspect.getsource(parse_mark_orderbook_gap_snapshot)
        forbidden_source_terms = ["requests", "urllib", "http_client", "os.environ", "getenv"]
        for term in forbidden_source_terms:
            with self.subTest(term=term):
                self.assertNotIn(term, source)

        with patch("socket.socket") as socket_factory, patch("os.getenv") as getenv:
            parsed = parse_mark_orderbook_gap_snapshot(
                venue_id="binance",
                parser_mode="binance_usdm",
                mark_response=fixture["mark_response"],
                orderbook_response=fixture["depth_response"],
                metadata_response=fixture["metadata_response"],
            )
        self.assertEqual(parsed["normalized_status"], "OK")
        socket_factory.assert_not_called()
        getenv.assert_not_called()
        self.assertNotIn("execution_allowed", parsed)
        self.assertNotIn("council_auto_call", parsed)
