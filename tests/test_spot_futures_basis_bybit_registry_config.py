import unittest
from pathlib import Path
from typing import Any

from src.market_data.adapters.spot_futures_basis import BybitSpotFuturesBasisAdapter
from src.market_data.registry import build_adapter, list_adapters, load_market_data_config


ADAPTER_ID = "live_bybit_spot_futures_basis_btcusdt"
BINANCE_ADAPTER_ID = "live_binance_spot_futures_basis_btcusdt"
HANDOFF_PATH = Path("docs/pr_handoffs/spot_futures_basis_bybit_registry_config_no_activation_2026_06_05.md")
FORBIDDEN_KEY_SUBSTRINGS = (
    "apiKey",
    "secret",
    "token",
    "credential",
    "account",
    "balance",
    "position",
    "orderId",
    "clientOrderId",
    "order",
    "cancel",
    "withdraw",
    "deposit",
    "transfer",
    "privateKey",
    "execution_enabled",
    "auto_trade",
    "alert_enabled",
    "council_auto_call",
)
ALLOWED_KEYS_WITH_FORBIDDEN_SUBSTRINGS = {"orderbook_limit", "orderbook_path", "orderbook_depth_available"}


def _config() -> dict[str, Any]:
    return load_market_data_config()


def _bybit_adapter_config() -> dict[str, Any]:
    return _config()["adapters"][ADAPTER_ID]


def _find_forbidden_keys(value: Any, *, path: str = "") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}" if path else key_text
            normalized_key = key_text.replace("orderbook", "public_book")
            if key_text not in ALLOWED_KEYS_WITH_FORBIDDEN_SUBSTRINGS:
                for forbidden in FORBIDDEN_KEY_SUBSTRINGS:
                    if forbidden.lower() in normalized_key.lower():
                        findings.append(child_path)
                        break
            findings.extend(_find_forbidden_keys(child, path=child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_find_forbidden_keys(child, path=f"{path}[{index}]"))
    return findings


class SpotFuturesBasisBybitRegistryConfigTest(unittest.TestCase):
    def test_config_contains_bybit_spot_futures_basis_adapter_disabled_no_trade(self):
        adapter_config = _bybit_adapter_config()

        self.assertEqual("bybit_spot_futures_basis", adapter_config["type"])
        self.assertIs(adapter_config["enabled"], False)
        self.assertIs(adapter_config["experimental"], True)
        self.assertIs(adapter_config["experimental_strategy"], True)
        self.assertIs(adapter_config["non_active_strategy"], True)
        self.assertIs(adapter_config["no_trade_only"], True)
        self.assertEqual("NO_TRADE_ONLY", adapter_config["execution_policy"])
        self.assertEqual("spot_futures_basis", adapter_config["strategy_family"])
        self.assertEqual("spot_futures_basis_v0", adapter_config["strategy_id"])
        self.assertEqual("bybit", adapter_config["source_venue_id"])
        self.assertEqual("spot", adapter_config["spot_category"])
        self.assertEqual("linear", adapter_config["perp_category"])

    def test_registry_builds_bybit_spot_futures_basis_adapter_without_live_fetch(self):
        config = _config()
        adapter = build_adapter(ADAPTER_ID, config)

        self.assertIsInstance(adapter, BybitSpotFuturesBasisAdapter)
        self.assertEqual(ADAPTER_ID, adapter.adapter_id)
        self.assertEqual("bybit_spot_futures_basis", adapter.adapter_type)
        self.assertEqual("BTCUSDT", adapter.spot_symbol)
        self.assertEqual("BTCUSDT", adapter.perp_symbol)
        self.assertEqual("spot", adapter.spot_category)
        self.assertEqual("linear", adapter.perp_category)

    def test_list_adapters_includes_bybit_spot_futures_basis_adapter(self):
        config = _config()

        self.assertIn(ADAPTER_ID, list_adapters(config))

    def test_bybit_spot_futures_basis_config_has_no_private_or_execution_keys(self):
        adapter_config = _bybit_adapter_config()

        self.assertEqual([], _find_forbidden_keys(adapter_config))
        for forbidden_key in (
            "private_api_required",
            "credentials",
            "api_key",
            "secret",
            "token",
            "account",
            "balance",
            "position",
            "order",
            "execution_enabled",
            "auto_trade",
            "alert_enabled",
            "council_auto_call",
        ):
            self.assertNotIn(forbidden_key, adapter_config)

    def test_existing_active_strategy_unchanged(self):
        config = _config()
        adapters = config["adapters"]

        self.assertIn("live_upbit_bithumb_spot_spread", adapters)
        active_adapter = adapters["live_upbit_bithumb_spot_spread"]
        self.assertIs(active_adapter["enabled"], True)
        self.assertEqual("cross_exchange_spot_spread", active_adapter["strategy_family"])
        self.assertEqual("cross_exchange_spot_spread_v1", active_adapter["strategy_id"])
        self.assertIs(adapters[ADAPTER_ID]["enabled"], False)
        self.assertIs(adapters[BINANCE_ADAPTER_ID]["enabled"], False)

    def test_bybit_collect_path_not_claimed_yet(self):
        text = HANDOFF_PATH.read_text(encoding="utf-8")

        self.assertIn("user-local collect smoke was not executed in this PR", text)
        self.assertIn("collect smoke not executed", text)
        self.assertIn("user-local collect smoke next", text)
        self.assertIn("Generated packet JSON must not be committed", text)

    def test_okx_deferred_no_okx_spot_futures_config_entry_added(self):
        config = _config()
        adapters = config["adapters"]

        for adapter_id, adapter_config in adapters.items():
            self.assertNotIn("live_okx_spot_futures_basis", adapter_id)
            if adapter_config.get("strategy_family") == "spot_futures_basis":
                self.assertNotEqual("okx", adapter_config.get("source_venue_id"))


if __name__ == "__main__":
    unittest.main()
