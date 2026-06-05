from __future__ import annotations

import copy
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.market_data.adapters.mark_orderbook_gap_hunt import (
    BinanceMarkOrderbookGapHuntAdapter,
    BybitMarkOrderbookGapHuntAdapter,
    OkxMarkOrderbookGapHuntAdapter,
)
from src.market_data.http_client import HttpJsonResponse

FIXTURE_DIR = Path("tests/fixtures/mark_orderbook_gap_hunt")
NOW = datetime.fromtimestamp(1780536387000 / 1000, tz=timezone.utc)


class FakeHttpClient:
    def __init__(self, responses: dict[str, dict | None]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str, dict]] = []

    def get_json(self, base_url: str, path: str, params: dict | None = None) -> HttpJsonResponse:
        request_params = dict(params or {})
        self.calls.append((base_url, path, request_params))
        if path not in self.responses:
            raise AssertionError(f"unexpected path: {path}")
        data = copy.deepcopy(self.responses[path])
        return HttpJsonResponse(
            data=data,
            elapsed_ms=7,
            url=f"{base_url}{path}",
            http_status=200,
            safe_response_preview=json.dumps(data)[:500],
        )


def _binance_responses() -> dict[str, dict]:
    fixture = json.loads((FIXTURE_DIR / "binance_valid_btcusdt.json").read_text(encoding="utf-8"))
    return {
        BinanceMarkOrderbookGapHuntAdapter.MARK_PRICE_PATH: fixture["mark_response"],
        BinanceMarkOrderbookGapHuntAdapter.ORDERBOOK_PATH: fixture["depth_response"],
        BinanceMarkOrderbookGapHuntAdapter.METADATA_PATH: fixture["metadata_response"],
    }


def _bybit_responses() -> dict[str, dict]:
    fixture = json.loads((FIXTURE_DIR / "bybit_valid_btcusdt_linear.json").read_text(encoding="utf-8"))
    return {
        BybitMarkOrderbookGapHuntAdapter.TICKER_PATH: fixture["ticker_response"],
        BybitMarkOrderbookGapHuntAdapter.ORDERBOOK_PATH: fixture["orderbook_response"],
        BybitMarkOrderbookGapHuntAdapter.METADATA_PATH: fixture["metadata_response"],
    }


def _okx_responses() -> dict[str, dict]:
    fixture = json.loads((FIXTURE_DIR / "okx_valid_btc_usdt_swap.json").read_text(encoding="utf-8"))
    return {
        OkxMarkOrderbookGapHuntAdapter.MARK_PRICE_PATH: fixture["mark_response"],
        OkxMarkOrderbookGapHuntAdapter.ORDERBOOK_PATH: fixture["books_response"],
        OkxMarkOrderbookGapHuntAdapter.METADATA_PATH: fixture["metadata_response"],
    }


def _config() -> dict[str, object]:
    return {
        "max_data_age_ms": 10_000,
        "fee_slippage_buffer_pct": "0.05",
        "min_net_gap_pct": "0",
        "liquidity_pass": True,
        "require_freshness": True,
        "size_or_notional_resolved": True,
    }


class MarkOrderbookGapHuntMetadataWordingTests(unittest.TestCase):
    def test_common_metadata_and_assumptions_remain_no_trade_only_for_all_venues(self) -> None:
        packets = [
            BinanceMarkOrderbookGapHuntAdapter(
                http_client=FakeHttpClient(_binance_responses()),
                now_fn=lambda: NOW,
                config=_config(),
            ).fetch_packet(),
            BybitMarkOrderbookGapHuntAdapter(
                http_client=FakeHttpClient(_bybit_responses()),
                now_fn=lambda: NOW,
                config=_config(),
            ).fetch_packet(),
            OkxMarkOrderbookGapHuntAdapter(
                http_client=FakeHttpClient(_okx_responses()),
                now_fn=lambda: NOW,
                config=_config(),
            ).fetch_packet(),
        ]

        stale_stage_phrases = (
            " ".join(("no", "config", "registration", "in", "this", "pr")),
            " ".join(("no", "registry", "integration", "in", "this", "pr")),
            " ".join(("this", "pr", "does", "not", "register", "adapter")),
            " ".join(("this", "pr", "does", "not", "integrate", "registry")),
        )
        for packet in packets:
            metadata = packet.extensions["adapter_metadata"]
            self.assertTrue(metadata["experimental_strategy"])
            self.assertTrue(metadata["non_active_strategy"])
            self.assertTrue(metadata["no_trade_only"])
            self.assertEqual(metadata["execution_policy"], "NO_TRADE_ONLY")

            assumptions = packet.extensions["assumptions"]
            assumptions_text = " | ".join(assumptions).lower()
            self.assertIn("public no-key endpoints only", assumptions)
            self.assertIn("analysis-only packet", assumptions)
            self.assertIn("no private api", assumptions_text)
            self.assertIn("no trading behavior", assumptions_text)
            self.assertIn("sampling integration is separate from packet generation", assumptions)
            self.assertIn("timestamp/data_age policy unchanged", assumptions)
            for phrase in stale_stage_phrases:
                self.assertNotIn(phrase, assumptions_text)

    def test_venue_specific_metadata_and_parser_outputs_are_not_hidden_by_common_wording(self) -> None:
        binance = BinanceMarkOrderbookGapHuntAdapter(
            http_client=FakeHttpClient(_binance_responses()),
            now_fn=lambda: NOW,
            config=_config(),
        ).fetch_packet()
        bybit = BybitMarkOrderbookGapHuntAdapter(
            http_client=FakeHttpClient(_bybit_responses()),
            now_fn=lambda: NOW - timedelta(seconds=10),
            config=_config(),
        ).fetch_packet()
        okx = OkxMarkOrderbookGapHuntAdapter(
            http_client=FakeHttpClient(_okx_responses()),
            now_fn=lambda: NOW,
            config=_config(),
        ).fetch_packet()

        self.assertEqual(binance.extensions["adapter_metadata"]["venue_id"], "binance")
        self.assertEqual(binance.extensions["parser_output"]["parser_mode"], "binance_usdm")
        self.assertEqual(binance.observations[0].market_symbol, "BTCUSDT")
        self.assertEqual(binance.observations[0].extensions["bid_size_unit"], "base_asset")

        self.assertEqual(bybit.extensions["adapter_metadata"]["venue_id"], "bybit")
        self.assertEqual(bybit.extensions["adapter_metadata"]["category"], "linear")
        self.assertEqual(bybit.extensions["parser_output"]["parser_mode"], "bybit_linear")
        self.assertEqual(bybit.observations[0].market_symbol, "BTCUSDT")
        self.assertLess(bybit.extensions["parser_output"]["data_age_ms"], 0)
        self.assertLess(bybit.observations[0].data_quality.max_data_age_ms, 0)

        self.assertEqual(okx.extensions["adapter_metadata"]["venue_id"], "okx")
        self.assertEqual(okx.extensions["adapter_metadata"]["instType"], "SWAP")
        self.assertEqual(okx.extensions["adapter_metadata"]["instId"], "BTC-USDT-SWAP")
        self.assertEqual(okx.extensions["parser_output"]["parser_mode"], "okx_swap")
        self.assertEqual(okx.observations[0].market_symbol, "BTC-USDT-SWAP")
        self.assertIsNone(okx.extensions["parser_output"]["index_price"])
        self.assertIsNone(okx.observations[0].index_price)
        self.assertEqual(okx.observations[0].extensions["bid_size_unit"], "contracts")

        for packet in (binance, bybit, okx):
            readiness = packet.extensions["readiness"]
            candidate = packet.candidates[0]
            self.assertEqual(candidate.metrics["readiness_status"], readiness["readiness_status"])
            self.assertEqual(
                candidate.metrics["recommended_default_decision"],
                readiness["recommended_default_decision"],
            )

    def test_diagnostics_common_envelope_and_venue_status_fields_are_preserved(self) -> None:
        binance = BinanceMarkOrderbookGapHuntAdapter(
            http_client=FakeHttpClient(_binance_responses()),
            now_fn=lambda: NOW,
            config=_config(),
        ).fetch_packet()
        bybit = BybitMarkOrderbookGapHuntAdapter(
            http_client=FakeHttpClient(_bybit_responses()),
            now_fn=lambda: NOW,
            config=_config(),
        ).fetch_packet()
        okx = OkxMarkOrderbookGapHuntAdapter(
            http_client=FakeHttpClient(_okx_responses()),
            now_fn=lambda: NOW,
            config=_config(),
        ).fetch_packet()

        expected_paths_and_params = {
            "binance": [
                (BinanceMarkOrderbookGapHuntAdapter.MARK_PRICE_PATH, {"symbol": "BTCUSDT"}, "mark_price"),
                (
                    BinanceMarkOrderbookGapHuntAdapter.ORDERBOOK_PATH,
                    {"symbol": "BTCUSDT", "limit": 5},
                    "orderbook",
                ),
                (BinanceMarkOrderbookGapHuntAdapter.METADATA_PATH, {}, "metadata"),
            ],
            "bybit": [
                (BybitMarkOrderbookGapHuntAdapter.TICKER_PATH, {"category": "linear", "symbol": "BTCUSDT"}, "ticker"),
                (
                    BybitMarkOrderbookGapHuntAdapter.ORDERBOOK_PATH,
                    {"category": "linear", "symbol": "BTCUSDT", "limit": 5},
                    "orderbook",
                ),
                (
                    BybitMarkOrderbookGapHuntAdapter.METADATA_PATH,
                    {"category": "linear", "symbol": "BTCUSDT"},
                    "metadata",
                ),
            ],
            "okx": [
                (
                    OkxMarkOrderbookGapHuntAdapter.MARK_PRICE_PATH,
                    {"instType": "SWAP", "instId": "BTC-USDT-SWAP"},
                    "mark_price",
                ),
                (
                    OkxMarkOrderbookGapHuntAdapter.ORDERBOOK_PATH,
                    {"instId": "BTC-USDT-SWAP", "sz": 5},
                    "orderbook",
                ),
                (
                    OkxMarkOrderbookGapHuntAdapter.METADATA_PATH,
                    {"instType": "SWAP", "instId": "BTC-USDT-SWAP"},
                    "metadata",
                ),
            ],
        }

        for venue_id, packet in (("binance", binance), ("bybit", bybit), ("okx", okx)):
            diagnostics = packet.extensions["diagnostics"]
            self.assertEqual(len(diagnostics), 3)
            for diagnostic, (endpoint, params, parser_stage) in zip(
                diagnostics, expected_paths_and_params[venue_id], strict=True
            ):
                self.assertEqual(diagnostic["endpoint"], endpoint)
                self.assertEqual(diagnostic["params"], params)
                self.assertEqual(diagnostic["parser_stage"], parser_stage)
                self.assertEqual(diagnostic["http_status"], 200)
                self.assertTrue(diagnostic["safe_response_preview"])
                self.assertEqual(diagnostic["elapsed_ms"], 7)
                self.assertTrue(diagnostic["url"].endswith(endpoint))

        for diagnostic in bybit.extensions["diagnostics"]:
            self.assertIn("retCode", diagnostic)
            self.assertIn("retMsg", diagnostic)

        for diagnostic in okx.extensions["diagnostics"]:
            self.assertIn("code", diagnostic)
            self.assertIn("msg", diagnostic)


    def test_venue_specific_boundaries_and_candidate_mapping_are_locked(self) -> None:
        binance = BinanceMarkOrderbookGapHuntAdapter(
            http_client=FakeHttpClient(_binance_responses()),
            now_fn=lambda: NOW,
            config=_config(),
        ).fetch_packet()
        bybit = BybitMarkOrderbookGapHuntAdapter(
            http_client=FakeHttpClient(_bybit_responses()),
            now_fn=lambda: NOW - timedelta(seconds=10),
            config=_config(),
        ).fetch_packet()
        okx = OkxMarkOrderbookGapHuntAdapter(
            http_client=FakeHttpClient(_okx_responses()),
            now_fn=lambda: NOW - timedelta(seconds=10),
            config=_config(),
        ).fetch_packet()

        self.assertEqual(binance.extensions["adapter_metadata"]["venue_id"], "binance")
        self.assertEqual(binance.extensions["parser_output"]["parser_mode"], "binance_usdm")
        self.assertEqual(binance.observations[0].market_symbol, "BTCUSDT")
        self.assertEqual(binance.observations[0].extensions["bid_size_unit"], "base_asset")
        self.assertEqual(binance.observations[0].extensions["ask_size_unit"], "base_asset")
        self.assertEqual(binance.extensions["parser_output"]["min_order_size"], "0.001")
        self.assertEqual(binance.extensions["parser_output"]["min_notional"], "50")
        self.assertEqual(binance.extensions["parser_output"]["parser_warnings"], [])

        self.assertEqual(bybit.extensions["adapter_metadata"]["venue_id"], "bybit")
        self.assertEqual(bybit.extensions["adapter_metadata"]["category"], "linear")
        self.assertEqual(bybit.extensions["parser_output"]["parser_mode"], "bybit_linear")
        self.assertEqual(bybit.observations[0].market_symbol, "BTCUSDT")
        self.assertEqual(bybit.observations[0].extensions["bid_size_unit"], "base_asset")
        self.assertEqual(bybit.observations[0].extensions["ask_size_unit"], "base_asset")
        self.assertIn("funding_interval=480", bybit.extensions["parser_output"]["parser_warnings"])
        self.assertIn("funding_interval=480", bybit.extensions["readiness"]["warnings"])
        self.assertLess(bybit.extensions["parser_output"]["data_age_ms"], 0)
        self.assertLess(bybit.observations[0].data_quality.max_data_age_ms, 0)

        self.assertEqual(okx.extensions["adapter_metadata"]["venue_id"], "okx")
        self.assertEqual(okx.extensions["adapter_metadata"]["instType"], "SWAP")
        self.assertEqual(okx.extensions["adapter_metadata"]["instId"], "BTC-USDT-SWAP")
        self.assertEqual(okx.extensions["parser_output"]["parser_mode"], "okx_swap")
        self.assertEqual(okx.observations[0].market_symbol, "BTC-USDT-SWAP")
        self.assertIsNone(okx.extensions["parser_output"]["index_price"])
        self.assertIsNone(okx.observations[0].index_price)
        self.assertEqual(okx.observations[0].extensions["bid_size_unit"], "contracts")
        self.assertEqual(okx.observations[0].extensions["ask_size_unit"], "contracts")
        self.assertEqual(okx.observations[0].extensions["contract_value"], "0.01")
        self.assertEqual(okx.observations[0].extensions["contract_multiplier"], "1")
        self.assertEqual(okx.observations[0].extensions["lot_size"], "0.01")
        self.assertEqual(okx.observations[0].extensions["min_order_size"], "0.01")
        self.assertLess(okx.extensions["parser_output"]["data_age_ms"], 0)
        self.assertLess(okx.observations[0].data_quality.max_data_age_ms, 0)

        expected_candidate_assumptions = [
            "mark price is not executable",
            "WATCH is analysis-only",
            "no private API",
            "no trading behavior",
        ]
        for packet in (binance, bybit, okx):
            metadata = packet.extensions["adapter_metadata"]
            self.assertTrue(metadata["no_trade_only"])
            self.assertEqual(metadata["execution_policy"], "NO_TRADE_ONLY")

            readiness = packet.extensions["readiness"]
            candidate = packet.candidates[0]
            self.assertEqual(candidate.metrics["readiness_status"], readiness["readiness_status"])
            self.assertEqual(candidate.metrics["recommended_default_decision"], readiness["recommended_default_decision"])
            self.assertEqual(candidate.metrics["readiness_pass"], readiness["readiness_pass"])
            self.assertEqual(str(candidate.gross_gap_pct), str(float(readiness["metrics"]["max_observed_gap_pct"])))
            self.assertEqual(str(candidate.estimated_net_gap_pct), str(float(readiness["metrics"]["estimated_net_gap_pct"])))
            self.assertEqual(candidate.required_missing_fields, readiness["required_missing_fields"])
            self.assertEqual(candidate.assumptions, expected_candidate_assumptions)
            self.assertIn("non_positive_estimated_net_gap", readiness["warnings"])



if __name__ == "__main__":
    unittest.main()
