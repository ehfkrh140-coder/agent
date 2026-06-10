from __future__ import annotations

import ast
import copy
import unittest
from pathlib import Path

from src.market_data.packet_builder import OpportunityPacketBuilder
from src.market_data.spot_futures_basis_packet_builder import build_spot_futures_basis_opportunity_packet

CREATED_AT_UTC = "2026-06-05T00:00:00Z"


def _source_bundle() -> dict:
    return {
        "strategy_family": "spot_futures_basis",
        "strategy_id": "spot_futures_basis_v0",
        "status": "experimental_non_active_no_trade_only",
        "source_venue_id": "binance",
        "comparison_type": "same_exchange_spot_perp_basis",
        "assumptions": ["analysis-only packet", "no trading behavior", "WATCH is not ENTER"],
        "spot_observation": {
            "venue_id": "binance",
            "venue_name": "Binance Spot",
            "symbol": "BTCUSDT",
            "base_asset": "BTC",
            "quote_asset": "USDT",
            "best_bid": 99.0,
            "best_bid_qty": 1.0,
            "best_ask": 100.0,
            "best_ask_qty": 1.0,
            "bid_qty_unit": "base_asset",
            "ask_qty_unit": "base_asset",
            "depth_bids": [["99", "1"], ["98", "2"], ["97", "3"]],
            "depth_asks": [["100", "1"], ["101", "2"], ["102", "3"]],
            "parser_normalized_status": "OK",
            "required_missing_fields": [],
            "raw_endpoint_ids": ["mock_spot_depth"],
        },
        "perp_observation": {
            "venue_id": "binance",
            "venue_name": "Binance USDⓈ-M Futures",
            "symbol": "BTCUSDT",
            "base_asset": "BTC",
            "quote_asset": "USDT",
            "settlement_asset": "USDT",
            "margin_asset": "USDT",
            "contract_type": "PERPETUAL",
            "best_bid": 101.0,
            "best_bid_qty": 1.0,
            "best_ask": 102.0,
            "best_ask_qty": 1.0,
            "mark_price": 101.5,
            "index_price": 101.4,
            "funding_rate": 0.01,
            "bid_qty_unit": "base_asset",
            "ask_qty_unit": "base_asset",
            "depth_bids": [["101", "1"], ["100", "2"], ["99", "3"]],
            "depth_asks": [["102", "1"], ["103", "2"], ["104", "3"]],
            "parser_normalized_status": "OK",
            "required_missing_fields": [],
            "raw_endpoint_ids": ["mock_perp_depth"],
        },
    }


def _readiness() -> dict:
    return {
        "readiness_status": "WATCH",
        "recommended_default_decision": "WATCH",
        "readiness_pass": True,
        "no_trade_only": True,
        "execution_policy": "NO_TRADE_ONLY",
        "required_missing_fields": [],
        "warnings": ["WATCH is not ENTER"],
        "assumptions": [
            "public no-key endpoints only",
            "analysis-only packet",
            "no trading behavior",
            "WATCH is not ENTER",
            "WATCH does not trigger Council auto-call, alert, or execution",
        ],
        "metrics": {
            "readiness_status": "WATCH",
            "recommended_default_decision": "WATCH",
            "readiness_pass": True,
            "spot_bid": 99.0,
            "spot_ask": 100.0,
            "perp_bid": 101.0,
            "perp_ask": 102.0,
            "spot_mid": 99.5,
            "perp_mid": 101.5,
            "mid_basis_pct": 2.01005025,
            "long_spot_short_perp_gross_pct": 1.0,
            "long_perp_short_spot_gross_pct": -2.94117647,
            "selected_direction": "long_spot_short_perp",
            "selected_gross_basis_pct": 1.0,
            "fee_slippage_buffer_pct": 0.2,
            "estimated_net_basis_pct": 0.8,
            "parser_normalized_status": "OK",
            "comparability_pass": True,
            "freshness_pass": True,
            "liquidity_pass": True,
        },
    }


class SpotFuturesBasisVwapContextTest(unittest.TestCase):
    def test_packet_builder_default_path_remains_behavior_unchanged_and_validates(self) -> None:
        packet = build_spot_futures_basis_opportunity_packet(
            _source_bundle(),
            _readiness(),
            created_at_utc=CREATED_AT_UTC,
            packet_id="default_packet",
        )
        self.assertNotIn("depth_vwap_context", packet["extensions"])
        self.assertNotIn("depth_vwap_context", packet["candidates"][0]["extensions"])
        validated = OpportunityPacketBuilder().build(packet)
        self.assertEqual("default_packet", validated.packet_id)

    def test_packet_builder_with_explicit_target_size_adds_packet_extension_context(self) -> None:
        packet = build_spot_futures_basis_opportunity_packet(
            _source_bundle(),
            _readiness(),
            created_at_utc=CREATED_AT_UTC,
            target_size="2",
        )
        context = packet["extensions"]["depth_vwap_context"]
        self.assertEqual("diagnostics_only", context["behavior"])
        self.assertTrue(context["no_trade_only"])
        self.assertEqual("2", context["target_size"])
        self.assertIn("long_spot_short_perp", context["directions"])
        OpportunityPacketBuilder().build(packet)

    def test_candidate_extension_depth_vwap_context_is_present_with_context_only_true(self) -> None:
        packet = build_spot_futures_basis_opportunity_packet(
            _source_bundle(),
            _readiness(),
            created_at_utc=CREATED_AT_UTC,
            target_size="2",
        )
        candidate_context = packet["candidates"][0]["extensions"]["depth_vwap_context"]
        self.assertTrue(candidate_context["context_only"])
        self.assertTrue(candidate_context["directions"]["long_spot_short_perp"]["context_only"])
        self.assertTrue(candidate_context["directions"]["long_perp_short_spot"]["context_only"])

    def test_decision_metrics_unchanged_after_adding_vwap_context(self) -> None:
        bundle = _source_bundle()
        readiness = _readiness()
        baseline = build_spot_futures_basis_opportunity_packet(
            copy.deepcopy(bundle),
            copy.deepcopy(readiness),
            created_at_utc=CREATED_AT_UTC,
        )
        with_context = build_spot_futures_basis_opportunity_packet(
            copy.deepcopy(bundle),
            copy.deepcopy(readiness),
            created_at_utc=CREATED_AT_UTC,
            target_size="2",
        )
        baseline_candidate = baseline["candidates"][0]
        context_candidate = with_context["candidates"][0]
        for field in (
            "readiness_status",
            "recommended_default_decision",
            "estimated_net_basis_pct",
            "readiness_pass",
        ):
            self.assertEqual(baseline_candidate["metrics"][field], context_candidate["metrics"][field])
        self.assertEqual(baseline_candidate["required_missing_fields"], context_candidate["required_missing_fields"])

    def test_watch_no_trade_path_preserves_watch_is_not_enter_and_no_execution(self) -> None:
        packet = build_spot_futures_basis_opportunity_packet(
            _source_bundle(),
            _readiness(),
            created_at_utc=CREATED_AT_UTC,
            target_size="2",
        )
        candidate = packet["candidates"][0]
        self.assertEqual("WATCH", candidate["metrics"]["recommended_default_decision"])
        self.assertNotEqual("ENTER", candidate["metrics"]["recommended_default_decision"])
        self.assertTrue(candidate["extensions"]["no_trade_only"])
        self.assertEqual("NO_TRADE_ONLY", candidate["extensions"]["execution_policy"])
        self.assertIn("WATCH is not ENTER", candidate["assumptions"])
        self.assertIn("VWAP context is not execution permission", candidate["assumptions"])

    def test_generated_json_not_created(self) -> None:
        self.assertFalse(Path("data/generated_packets/spot_futures_basis_vwap_context.json").exists())
        self.assertFalse(Path("data/market_samples/spot_futures_basis_vwap_context.json").exists())

    def test_context_tests_do_not_import_forbidden_runtime_modules(self) -> None:
        source = Path(__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
        forbidden = (
            "src.market_data.adapters",
            "src.market_data.parsers",
            "src.strategy",
            "src.market_data.sampling",
            "requests",
            "aiohttp",
            "httpx",
        )
        self.assertTrue(all(not any(fragment in module for fragment in forbidden) for module in imported_modules))


if __name__ == "__main__":
    unittest.main()
