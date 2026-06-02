from __future__ import annotations

import unittest
from pathlib import Path

import yaml


class ProjectGuardrailsDocsTests(unittest.TestCase):
    def test_required_guardrail_docs_exist(self):
        for path in [
            "AGENTS.md",
            "docs/no_trade_policy.md",
            "docs/active_strategy.md",
            "docs/roadmap.md",
            "docs/codex_task_template.md",
            "docs/architecture_status.md",
        ]:
            self.assertTrue(Path(path).exists(), path)

    def test_agents_mentions_repo_workflow_and_active_strategy(self):
        text = Path("AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("git status", text)
        self.assertIn("origin", text)
        self.assertIn("cross_exchange_spot_spread_v1", text)
        self.assertIn("mark_orderbook_gap", text)
        self.assertIn("python -m unittest discover -s tests", text)
        self.assertIn("API keys", text)
        self.assertIn("order", text.lower())

    def test_no_trade_policy_blocks_private_and_execution_actions(self):
        text = Path("docs/no_trade_policy.md").read_text(encoding="utf-8")

        for phrase in [
            "Read-only public market data",
            "Private exchange endpoints",
            "API keys",
            "Account or balance lookup",
            "Order placement",
            "Withdrawal",
            "transfer",
            "Auto-trading",
            "analysis only",
        ]:
            self.assertIn(phrase, text)

    def test_active_strategy_doc_names_required_and_unneeded_fields(self):
        text = Path("docs/active_strategy.md").read_text(encoding="utf-8")

        self.assertIn("cross_exchange_spot_spread_v1", text)
        self.assertIn("source ask", text)
        self.assertIn("target bid", text)
        self.assertIn("VWAP", text)
        self.assertIn("Upbit and Bithumb", text)
        self.assertIn("KRW", text)
        self.assertIn("spot", text)
        for phrase in ["mark_price", "index_price", "leverage", "funding_rate", "open_interest"]:
            self.assertIn(phrase, text)

    def test_roadmap_lists_completed_and_next_todo_items(self):
        text = Path("docs/roadmap.md").read_text(encoding="utf-8")

        for phrase in [
            "Single Round Council v1",
            "OpportunityPacket v0",
            "Upbit/Bithumb public adapter",
            "VWAP/slippage evaluator",
            "Council handoff/journal",
            "Alert/notification v1",
            "Market Watch Runner v1",
            "Scheduler / Watch Loop v1",
            "Paper Decision Journal / Backtest-lite v1",
            "read-only by default",
            "currently forbidden",
        ]:
            self.assertIn(phrase, text)

    def test_task_template_contains_expected_sections(self):
        text = Path("docs/codex_task_template.md").read_text(encoding="utf-8")

        for heading in [
            "## Task name",
            "## Goal",
            "## Current state",
            "## Allowed files",
            "## Forbidden files",
            "## Implementation requirements",
            "## Tests",
            "## Manual smoke",
            "## Success criteria",
            "## Non-goals",
        ]:
            self.assertIn(heading, text)

    def test_architecture_status_lists_current_flow_and_missing_execution(self):
        text = Path("docs/architecture_status.md").read_text(encoding="utf-8")

        for phrase in [
            "public market data",
            "OpportunityPacket",
            "VWAP/readiness",
            "sampling/persistence",
            "handoff/journal",
            "alert",
            "optional manual Council",
            "Execution engine",
            "Private account data",
            "Balance lookup",
            "Order placement",
            "Withdrawal",
            "Auto trading",
        ]:
            self.assertIn(phrase, text)


    def test_strategy_expansion_playbook_exists_and_defines_statuses(self):
        text = Path("docs/strategy_expansion_playbook.md").read_text(encoding="utf-8")

        for phrase in [
            "future",
            "experimental",
            "active_candidate",
            "active",
            "archived",
            "cross_exchange_spot_spread_v1",
            "mark_orderbook_gap",
        ]:
            self.assertIn(phrase, text)

    def test_strategy_expansion_playbook_lists_promotion_steps_and_no_trade_policy(self):
        text = Path("docs/strategy_expansion_playbook.md").read_text(encoding="utf-8")

        for step in [
            "Step 1: Strategy brief",
            "Step 2: Data requirement matrix",
            "Step 3: OpportunityPacket mapping",
            "Step 4: Manual scenario fixtures",
            "Step 5: Readiness rules",
            "Step 6: Replay/evaluate tests",
            "Step 7: Public read-only adapter",
            "Step 8: Sampling/persistence",
            "Step 9: Alert/journal integration",
            "Step 10: Optional manual Council smoke",
            "Step 11: active_candidate review",
            "Step 12: active promotion",
        ]:
            self.assertIn(step, text)
        for forbidden in [
            "private API",
            "API key / secret / token",
            "balance/account lookup",
            "order placement/cancel",
            "withdrawal/deposit/transfer",
            "auto-trading",
            "Council decision to trade conversion",
        ]:
            self.assertIn(forbidden, text)

    def test_strategy_expansion_backlog_and_recommended_order_are_documented(self):
        text = Path("docs/strategy_expansion_playbook.md").read_text(encoding="utf-8")

        for strategy in [
            "kimchi_premium",
            "reverse_premium",
            "spot_futures_basis",
            "funding_rate",
            "orderbook_imbalance",
            "trade_flow_momentum",
            "volatility_breakout",
            "mean_reversion",
            "liquidation_open_interest",
            "news_event",
            "onchain",
            "grid",
            "market_making",
        ]:
            self.assertIn(strategy, text)
        self.assertIn("existing Upbit/Bithumb orderbook depth makes this the safest next candidate", text)
        self.assertIn("domestic/global prices and FX or USDT-KRW reference", text)
        self.assertIn("requires public derivatives data", text)
        self.assertIn("combines spot and futures data", text)

    def test_strategy_task_cards_are_documentation_only(self):
        paths = [
            Path("docs/strategy_task_cards/TEMPLATE.md"),
            Path("docs/strategy_task_cards/orderbook_imbalance.md"),
            Path("docs/strategy_task_cards/kimchi_premium.md"),
            Path("docs/strategy_task_cards/funding_rate.md"),
        ]
        for path in paths:
            self.assertTrue(path.exists(), str(path))
            text = path.read_text(encoding="utf-8")
            self.assertIn("## Task name", text)
            self.assertIn("## Strategy family", text)
            self.assertIn("## Goal", text)
            self.assertIn("## Data required", text)
            self.assertIn("## Data forbidden", text)
            self.assertIn("## OpportunityPacket shape", text)
            self.assertIn("## Readiness rules", text)
            self.assertIn("## Scenarios", text)
            self.assertIn("## Allowed files", text)
            self.assertIn("## Forbidden files", text)
            self.assertIn("## Tests", text)
            self.assertIn("## Manual smoke", text)
            self.assertIn("## Success criteria", text)
            self.assertIn("## Non-goals", text)
            self.assertIn("Do not implement", text)

    def test_active_strategy_remains_cross_exchange_spot_spread_v1_in_docs(self):
        active = Path("docs/active_strategy.md").read_text(encoding="utf-8")
        playbook = Path("docs/strategy_expansion_playbook.md").read_text(encoding="utf-8")
        roadmap = Path("docs/roadmap.md").read_text(encoding="utf-8")

        self.assertIn("cross_exchange_spot_spread_v1", active)
        self.assertIn("Active strategy remains `cross_exchange_spot_spread_v1`", playbook)
        self.assertIn("Codex must not change the active strategy by itself", playbook)
        self.assertIn("Strategy expansion one-by-one using `docs/strategy_expansion_playbook.md`", roadmap)

    def test_usdt_krw_kimchi_premium_strategy_card_is_future_read_only(self):
        path = Path("docs/strategy_task_cards/usdt_krw_kimchi_premium.md")
        self.assertTrue(path.exists(), str(path))
        text = path.read_text(encoding="utf-8")

        for phrase in [
            "stablecoin_krw_premium",
            "usdt_krw_kimchi_premium_v0",
            "read-only",
            "no-trade",
            "not auto-trading",
            "Mode A: Domestic USDT/KRW executable spread",
            "Mode B: USDT/KRW Kimchi Premium / FX Basis",
            "Mode B is the user-intended core strategy",
            "## Data forbidden",
            "private API",
            "API key / secret / token",
            "account/balance lookup",
            "order placement",
            "withdrawal/deposit/transfer",
            "bank account / fiat transfer",
            "auto-trading",
            "fair_usdt_krw_price = usd_krw_reference_rate * global_usdt_usd_reference",
            "premium_pct = ((domestic_usdt_krw_price - fair_usdt_krw_price) / fair_usdt_krw_price) * 100",
            "USDT/KRW Data Availability Check v0",
        ]:
            self.assertIn(phrase, text)

    def test_stablecoin_krw_premium_registry_entry_is_future_and_active_strategy_unchanged(self):
        registry = yaml.safe_load(Path("configs/strategy_registry.yaml").read_text(encoding="utf-8"))
        strategies = registry["strategies"]
        stablecoin = next(item for item in strategies if item["strategy_family"] == "stablecoin_krw_premium")
        active = [item for item in strategies if item.get("status") == "active"]

        self.assertEqual(stablecoin["strategy_id"], "usdt_krw_kimchi_premium_v0")
        self.assertEqual(stablecoin["status"], "future")
        self.assertEqual(stablecoin["execution_policy"], "NO_TRADE_ONLY")
        self.assertIn("not active", " ".join(stablecoin["readiness_rules"]))
        self.assertEqual([item["strategy_id"] for item in active], ["cross_exchange_spot_spread_v1"])

    def test_stablecoin_krw_premium_is_in_playbook_and_catalog_backlog(self):
        playbook = Path("docs/strategy_expansion_playbook.md").read_text(encoding="utf-8")
        catalog = Path("docs/strategy_catalog.md").read_text(encoding="utf-8")

        for text in [playbook, catalog]:
            self.assertIn("stablecoin_krw_premium", text)
            self.assertIn("usdt_krw_kimchi_premium", text)
        self.assertIn("USDT/KRW Data Availability Check v0", playbook)
        self.assertIn("orderbook_imbalance experimental path continues", playbook)
        self.assertIn("funding_rate and spot_futures_basis remain later", playbook)

    def test_usdt_krw_multi_source_matrix_exists_and_keeps_strategy_future(self):
        path = Path("docs/data_availability/usdt_krw_multi_source_matrix.md")
        self.assertTrue(path.exists(), str(path))
        text = path.read_text(encoding="utf-8")

        for phrase in [
            "## Overview",
            "## Strategy link",
            "## Source role model",
            "## Domestic executable/reference venues",
            "## Global USDT reference venues",
            "## USD/KRW FX reference sources",
            "## Recommended premium formulas",
            "## Aggregation rules",
            "## Data availability matrix",
            "## Data risks",
            "## Next implementation gate",
            "## No-trade compliance",
            "Upbit",
            "Bithumb",
            "Coinone",
            "Korbit",
            "Binance",
            "Bybit",
            "OKX",
            "public FX API candidate",
            "official FX source candidate",
            "no-key public source candidate",
            "A. Domestic USDT/KRW venues",
            "B. Global USDT reference venues",
            "C. USD/KRW FX reference sources",
            "fair_usdt_krw_price",
            "premium_mid_pct",
            "premium_sell_pct",
            "premium_buy_pct",
            "per_venue_premium_pct",
            "domestic_median_mid_premium_pct",
            "global_usdt_usd_median",
            "single venue distortion",
            "stale FX reference",
            "No private API",
            "No account/balance lookup",
            "No withdrawal/deposit/transfer",
            "USDT/KRW Public Probe v0",
        ]:
            self.assertIn(phrase, text)

        card = Path("docs/strategy_task_cards/usdt_krw_kimchi_premium.md").read_text(encoding="utf-8")
        self.assertIn("docs/data_availability/usdt_krw_multi_source_matrix.md", card)
        self.assertIn("experimental scaffolding requires Multi-Source Data Availability Matrix and Public Probe first", card)

        registry = yaml.safe_load(Path("configs/strategy_registry.yaml").read_text(encoding="utf-8"))
        stablecoin = next(item for item in registry["strategies"] if item["strategy_family"] == "stablecoin_krw_premium")
        active = [item for item in registry["strategies"] if item.get("status") == "active"]
        self.assertEqual(stablecoin["status"], "future")
        self.assertEqual(stablecoin["execution_policy"], "NO_TRADE_ONLY")
        self.assertEqual([item["strategy_id"] for item in active], ["cross_exchange_spot_spread_v1"])


    def test_usdt_krw_probe_review_documents_source_decision_and_fx_blocker(self):
        path = Path("docs/data_availability/usdt_krw_probe_review.md")
        self.assertTrue(path.exists(), str(path))
        text = path.read_text(encoding="utf-8")

        for phrase in [
            "## Overview",
            "## Probe input summary",
            "## Source result table",
            "## Domestic source decision",
            "## Global USDT reference decision",
            "## FX reference decision",
            "## Current blocker",
            "## Recommended v0 source set",
            "## Next gate",
            "## No-trade compliance",
            "Upbit: ok / available",
            "Bithumb: ok / unknown",
            "Coinone: skipped / unknown",
            "Korbit: skipped / unknown",
            "Binance: ok / available",
            "Bybit: ok / available",
            "OKX: ok / available",
            "Frankfurter/no-key public FX candidate: ok / unknown",
            "FX source unresolved",
            "Mode B cannot become experimental until USD/KRW FX source is confirmed",
            "Domestic v0 primary candidate: Upbit USDT/KRW",
            "median of Binance, Bybit, OKX",
            "usd_krw_reference_rate",
            "fair_usdt_krw_price cannot be calculated reliably",
            "USDT/KRW FX Reference Probe Hardening v0",
            "No private API",
            "No account/balance lookup",
            "No withdrawal/deposit/transfer",
        ]:
            self.assertIn(phrase, text)

        matrix = Path("docs/data_availability/usdt_krw_multi_source_matrix.md").read_text(encoding="utf-8")
        self.assertIn("docs/data_availability/usdt_krw_probe_review.md", matrix)
        self.assertIn("probe_available_for_USDT_KRW", matrix)
        self.assertIn("probe_unknown", matrix)
        self.assertIn("probe_available_for_reference", matrix)
        self.assertIn("FX reference remains unresolved", matrix)

        card = Path("docs/strategy_task_cards/usdt_krw_kimchi_premium.md").read_text(encoding="utf-8")
        self.assertIn("docs/data_availability/usdt_krw_probe_review.md", card)
        self.assertIn("Experimental scaffolding is blocked until a reliable public `USD/KRW` FX source is confirmed", card)

        registry = yaml.safe_load(Path("configs/strategy_registry.yaml").read_text(encoding="utf-8"))
        stablecoin = next(item for item in registry["strategies"] if item["strategy_family"] == "stablecoin_krw_premium")
        active = [item for item in registry["strategies"] if item.get("status") == "active"]
        self.assertEqual(stablecoin["status"], "future")
        self.assertEqual(stablecoin["execution_policy"], "NO_TRADE_ONLY")
        self.assertEqual([item["strategy_id"] for item in active], ["cross_exchange_spot_spread_v1"])


if __name__ == "__main__":
    unittest.main()
