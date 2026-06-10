from __future__ import annotations

import ast
import inspect
import unittest
from decimal import Decimal
from pathlib import Path

from src.market_data.depth_vwap_context import (
    build_observation_vwap_context,
    build_spot_futures_basis_vwap_context,
    extract_depth_levels_from_observation,
)


ASKS = [["100", "1"], ["101", "2"], ["102", "3"]]
BIDS = [["99", "1"], ["98", "2"], ["97", "3"]]


def _observation_with_depth() -> dict:
    return {"depth": {"asks": ASKS, "bids": BIDS}}


def _source_bundle() -> dict:
    return {
        "spot_observation": {"depth": {"asks": ASKS, "bids": BIDS}},
        "perp_observation": {
            "depth_bids": [["100", "1"], ["99", "2"], ["98", "3"]],
            "depth_asks": [["101", "1"], ["102", "2"], ["103", "3"]],
        },
    }


class DepthVwapContextTest(unittest.TestCase):
    def test_extracts_levels_from_depth_asks_and_bids(self) -> None:
        observation = _observation_with_depth()
        ask = extract_depth_levels_from_observation(observation, side="ask")
        bid = extract_depth_levels_from_observation(observation, side="bid")
        self.assertEqual(ASKS, ask["levels"])
        self.assertEqual(BIDS, bid["levels"])
        self.assertTrue(ask["depth_available"])
        self.assertTrue(bid["depth_available"])

    def test_extracts_levels_from_orderbook_depth(self) -> None:
        observation = {"orderbook_depth": {"asks": ASKS, "bids": BIDS}}
        self.assertEqual(ASKS, extract_depth_levels_from_observation(observation, side="ask")["levels"])
        self.assertEqual(BIDS, extract_depth_levels_from_observation(observation, side="bid")["levels"])

    def test_extracts_levels_from_bid_levels_and_ask_levels(self) -> None:
        observation = {"ask_levels": ASKS, "bid_levels": BIDS}
        self.assertEqual(ASKS, extract_depth_levels_from_observation(observation, side="ask")["levels"])
        self.assertEqual(BIDS, extract_depth_levels_from_observation(observation, side="bid")["levels"])

    def test_missing_depth_returns_warning_without_exception(self) -> None:
        context = build_observation_vwap_context({}, target_size="1")
        self.assertFalse(context["depth_available"])
        self.assertTrue(context["warnings"])
        self.assertIn("ask:depth_ask_levels_not_found", context["warnings"])
        self.assertTrue(context["ask_vwap_result"]["insufficient_depth"])

    def test_target_size_computes_spot_ask_and_bid_context(self) -> None:
        context = build_observation_vwap_context(_observation_with_depth(), target_size="2")
        self.assertEqual("diagnostics_only", context["behavior"])
        self.assertEqual(Decimal("100.5"), context["ask_vwap_result"]["vwap"])
        self.assertEqual(Decimal("98.5"), context["bid_vwap_result"]["vwap"])
        self.assertEqual("2", context["target_size"])

    def test_target_notional_computes_context(self) -> None:
        context = build_observation_vwap_context(_observation_with_depth(), target_notional="150")
        self.assertIsNone(context["target_size"])
        self.assertEqual("150", context["target_notional"])
        self.assertIsNotNone(context["ask_vwap_result"]["vwap"])
        self.assertIsNotNone(context["bid_vwap_result"]["vwap"])

    def test_both_target_size_and_target_notional_prefers_size_with_warning(self) -> None:
        context = build_observation_vwap_context(_observation_with_depth(), target_size="2", target_notional="999")
        self.assertEqual("2", context["target_size"])
        self.assertIsNone(context["target_notional"])
        self.assertIn("target_size_preferred_over_target_notional", context["warnings"])

    def test_source_bundle_spot_perp_context_computes_both_directions(self) -> None:
        context = build_spot_futures_basis_vwap_context(_source_bundle(), target_size="2")
        self.assertEqual("diagnostics_only", context["behavior"])
        self.assertEqual("NO_TRADE_ONLY", context["execution_policy"])
        self.assertIn("long_spot_short_perp", context["directions"])
        self.assertIn("long_perp_short_spot", context["directions"])
        self.assertTrue(context["directions"]["long_spot_short_perp"]["context_only"])
        self.assertTrue(context["directions"]["long_perp_short_spot"]["context_only"])

    def test_insufficient_depth_propagates_into_direction_context(self) -> None:
        context = build_spot_futures_basis_vwap_context(_source_bundle(), target_size="100")
        self.assertTrue(context["directions"]["long_spot_short_perp"]["insufficient_depth"])
        self.assertTrue(context["directions"]["long_perp_short_spot"]["insufficient_depth"])

    def test_context_output_has_no_private_account_or_order_keys(self) -> None:
        context = build_spot_futures_basis_vwap_context(_source_bundle(), target_size="2")
        forbidden_key_fragments = ("api", "secret", "token", "private", "account", "balance", "position", "order", "cancel", "withdraw", "deposit", "transfer")
        self._assert_no_forbidden_key_fragments(context, forbidden_key_fragments)

    def test_module_structural_guardrail_no_network_file_env_imports(self) -> None:
        import src.market_data.depth_vwap_context as module

        source = inspect.getsource(module)
        tree = ast.parse(source)
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
        forbidden = {"requests", "aiohttp", "httpx", "socket", "urllib", "os", "pathlib"}
        self.assertTrue(forbidden.isdisjoint(imported_modules))
        self.assertNotIn("open(", source)
        self.assertNotIn("getenv", source)
        self.assertNotIn("environ", source)

    def test_no_generated_json_path_created_or_referenced(self) -> None:
        import src.market_data.depth_vwap_context as module

        source = inspect.getsource(module)
        self.assertNotIn("data/generated_packets", source)
        self.assertNotIn("data/market_samples", source)
        self.assertFalse(Path("data/generated_packets/depth_vwap_context.json").exists())
        self.assertFalse(Path("data/market_samples/depth_vwap_context.json").exists())

    def test_no_target_returns_depth_vwap_target_not_provided_warning(self) -> None:
        context = build_spot_futures_basis_vwap_context(_source_bundle())
        self.assertIn("depth_vwap_target_not_provided", context["warnings"])
        self.assertIsNone(context["spot"]["ask_vwap_result"])
        self.assertIsNone(context["perp"]["bid_vwap_result"])

    def test_vwap_context_is_diagnostics_only_and_no_trade_only(self) -> None:
        context = build_spot_futures_basis_vwap_context(_source_bundle(), target_size="2")
        self.assertEqual("diagnostics_only", context["behavior"])
        self.assertTrue(context["no_trade_only"])
        self.assertEqual("NO_TRADE_ONLY", context["execution_policy"])

    def _assert_no_forbidden_key_fragments(self, value, forbidden_key_fragments) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                key_text = str(key).lower()
                for forbidden in forbidden_key_fragments:
                    self.assertNotIn(forbidden, key_text, key)
                self._assert_no_forbidden_key_fragments(nested, forbidden_key_fragments)
        elif isinstance(value, list):
            for item in value:
                self._assert_no_forbidden_key_fragments(item, forbidden_key_fragments)


if __name__ == "__main__":
    unittest.main()
