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
            "deferred/superseded",
            "superseded by [`tether_cross_market_premium`](tether_cross_market_premium.md)",
            "USD/KRW FX reference is out of current scope",
            "`fair_usdt_krw_price` is not used in the current user-intended strategy",
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
            "Tether Cross-Market Bithumb USDT/KRW Recheck v0",
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
        self.assertIn("Tether Cross-Market Bithumb USDT/KRW Recheck v0", playbook)
        self.assertIn("orderbook_imbalance experimental path continues", playbook)
        self.assertIn("tether_cross_market_premium requires Bithumb USDT/KRW public re-check", playbook)
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
            "deferred/out-of-scope",
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
            "gross_gap_pct",
            "estimated_net_gap_pct",
            "global_usdt_depeg_flag",
            "domestic_median_mid",
            "global_usdt_median",
            "single venue distortion",
            "stale FX reference",
            "Tether Cross-Market Bithumb USDT/KRW Recheck v0",
            "Tether Cross-Market Upbit-Only Domestic Reference Scaffolding v0",
            "No private API",
            "No account/balance lookup",
            "No withdrawal/deposit/transfer",
            "Tether Cross-Market Bithumb USDT/KRW Recheck v0",
        ]:
            self.assertIn(phrase, text)

        card = Path("docs/strategy_task_cards/usdt_krw_kimchi_premium.md").read_text(encoding="utf-8")
        self.assertIn("docs/data_availability/usdt_krw_multi_source_matrix.md", card)
        self.assertIn("Tether Cross-Market Bithumb USDT/KRW Recheck", card)

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
            "FX is out of scope",
            "near-term strategy uses domestic USDT/KRW and global USDT reference only",
            "Domestic v0 primary candidate: Upbit USDT/KRW",
            "Median of Binance, Bybit, and OKX",
            "usd_krw_reference_rate",
            "Out of current scope; not required",
            "Tether Cross-Market Bithumb USDT/KRW Recheck v0",
            "Tether Cross-Market Upbit-Only Domestic Reference Scaffolding v0",
            "No private API",
            "No account/balance lookup",
            "No withdrawal/deposit/transfer",
        ]:
            self.assertIn(phrase, text)

        matrix = Path("docs/data_availability/usdt_krw_multi_source_matrix.md").read_text(encoding="utf-8")
        self.assertIn("docs/data_availability/usdt_krw_probe_review.md", matrix)
        self.assertIn("probe_available_for_USDT_KRW", matrix)
        self.assertIn("probe_unknown_needs_recheck", matrix)
        self.assertIn("probe_available_for_reference", matrix)
        self.assertIn("FX: `deferred_out_of_scope_for_current_strategy`; deferred/out-of-scope for current strategy", matrix)

        card = Path("docs/strategy_task_cards/usdt_krw_kimchi_premium.md").read_text(encoding="utf-8")
        self.assertIn("docs/data_availability/usdt_krw_probe_review.md", card)
        self.assertIn("superseded for near-term implementation", card)
        self.assertIn("Tether Cross-Market Bithumb USDT/KRW Recheck", card)

        registry = yaml.safe_load(Path("configs/strategy_registry.yaml").read_text(encoding="utf-8"))
        stablecoin = next(item for item in registry["strategies"] if item["strategy_family"] == "stablecoin_krw_premium")
        active = [item for item in registry["strategies"] if item.get("status") == "active"]
        self.assertEqual(stablecoin["status"], "future")
        self.assertEqual(stablecoin["execution_policy"], "NO_TRADE_ONLY")
        self.assertEqual([item["strategy_id"] for item in active], ["cross_exchange_spot_spread_v1"])



    def test_tether_cross_market_premium_reframe_is_future_no_fx_read_only(self):
        card_path = Path("docs/strategy_task_cards/tether_cross_market_premium.md")
        self.assertTrue(card_path.exists(), str(card_path))
        card = card_path.read_text(encoding="utf-8")

        for phrase in [
            "tether_cross_market_premium",
            "usdt_krw_global_reference_v0",
            "NO_TRADE_ONLY",
            "This strategy does not require USD/KRW FX",
            "This strategy does not calculate `fair_usdt_krw_price`",
            "fair_usdt_krw_price` is not used",
            "Domestic v0 venues are Upbit and Bithumb only",
            "Upbit `USDT/KRW` is the confirmed primary domestic public source",
            "Bithumb `USDT/KRW` remains the domestic v0 secondary candidate",
            "Coinone and Korbit are future domestic expansion, not v0",
            "Binance / Bybit / OKX",
            "Global reference v0 venues are Binance, Bybit, and OKX",
            "Global venues can be expanded later only through a new task card and public probe first",
            "gross_gap_pct =",
            "(target_bid - source_ask) / source_ask * 100",
            "global_usdt_depeg_pct =",
            "global_usdt_depeg_flag =",
            "do not calculate `premium_pct` against USD/KRW",
            "Tether Cross-Market Bithumb USDT/KRW Recheck v0",
            "Tether Cross-Market Upbit-Only Domestic Reference Scaffolding v0",
            "No private API",
            "No account/balance lookup",
            "No withdrawal/deposit/transfer",
        ]:
            self.assertIn(phrase, card)

        deferred = Path("docs/strategy_task_cards/usdt_krw_kimchi_premium.md").read_text(encoding="utf-8")
        self.assertIn("Deferred/superseded note", deferred)
        self.assertIn("superseded by [`tether_cross_market_premium`](tether_cross_market_premium.md)", deferred)
        self.assertIn("USD/KRW FX reference is out of current scope", deferred)

        registry = yaml.safe_load(Path("configs/strategy_registry.yaml").read_text(encoding="utf-8"))
        strategies = registry["strategies"]
        tether = next(item for item in strategies if item["strategy_family"] == "tether_cross_market_premium")
        stablecoin = next(item for item in strategies if item["strategy_family"] == "stablecoin_krw_premium")
        active = [item for item in strategies if item.get("status") == "active"]

        self.assertEqual(tether["strategy_id"], "usdt_krw_global_reference_v0")
        self.assertEqual(tether["status"], "future")
        self.assertEqual(tether["execution_policy"], "NO_TRADE_ONLY")
        self.assertIn("not active", " ".join(tether["readiness_rules"]))
        self.assertEqual(stablecoin["status"], "future")
        self.assertNotEqual(stablecoin.get("status"), "active")
        self.assertIn("superseded_for_near_term_by_tether_cross_market_premium", " ".join(stablecoin["readiness_rules"]))
        self.assertEqual([item["strategy_id"] for item in active], ["cross_exchange_spot_spread_v1"])

        probe_config = yaml.safe_load(Path("configs/usdt_krw_probe_sources.yaml").read_text(encoding="utf-8"))
        by_id = {source["source_id"]: source for source in probe_config["sources"]}
        self.assertTrue(by_id["upbit"]["enabled_for_probe"])
        self.assertTrue(by_id["bithumb"]["enabled_for_probe"])
        self.assertFalse(by_id["coinone"]["enabled_for_probe"])
        self.assertFalse(by_id["korbit"]["enabled_for_probe"])
        for source_id in ["binance", "bybit", "okx"]:
            self.assertTrue(by_id[source_id]["enabled_for_probe"])
        self.assertTrue(by_id["frankfurter_or_no_key_public_fx_candidate"]["enabled_for_probe"])
        self.assertFalse(by_id["official_fx_source_candidate"]["enabled_for_probe"])
        self.assertIn("out_of_scope_for_tether_cross_market", " ".join(probe_config["notes"]))
        self.assertIn("out_of_scope_for_tether_cross_market", " ".join(by_id["frankfurter_or_no_key_public_fx_candidate"]["notes"]))

    def test_pr_trust_framework_docs_and_template_exist(self):
        required_paths = [
            ".github/pull_request_template.md",
            "docs/pr_review_policy.md",
            "docs/merge_gate.md",
            "docs/rollback_policy.md",
            "docs/task_checklist.md",
            "docs/agent_workflow.md",
        ]
        for path in required_paths:
            self.assertTrue(Path(path).exists(), path)

        template = Path(".github/pull_request_template.md").read_text(encoding="utf-8")
        for phrase in [
            "작업 목적",
            "변경 파일 목록",
            "영향 범위",
            "테스트 결과",
            "예상 리스크",
            "롤백 방법",
            "사람이 반드시 확인해야 하는 항목",
            "No-trade compliance",
            "Did this PR modify src?",
            "Did this PR modify tools?",
            "Did this PR modify prompts?",
            "Did this PR modify configs?",
            "Did this PR change active strategy?",
            "private API / API key / balance / order / transfer / auto-trading",
            "What files should the reviewer inspect first?",
            "How to rollback?",
        ]:
            self.assertIn(phrase, template)

    def test_pr_review_policy_merge_gate_and_rollback_cover_required_guardrails(self):
        review = Path("docs/pr_review_policy.md").read_text(encoding="utf-8")
        for phrase in [
            "trusted without reading every line",
            "PRs must be small and scoped",
            "purpose, affected files, tests, risks, and rollback",
            "runtime/auth/prompts/strategy_current/private API is high-risk",
            "docs-only",
            "config-only",
            "test-only",
            "probe",
            "adapter",
            "readiness",
            "strategy/scenario",
            "runtime/LLM",
            "execution/private API",
        ]:
            self.assertIn(phrase, review)

        merge_gate = Path("docs/merge_gate.md").read_text(encoding="utf-8")
        for phrase in [
            "Tests pass",
            "Existing behavior is preserved",
            "Docs are updated",
            "Impact scope is declared",
            "Failure handling exists",
            "No unrelated files changed",
            "No no-trade violation",
            "Rollback method is documented",
            "User approval is present for high-risk categories",
            "Unexplained refactor",
            "Private API/key/order/balance/transfer additions",
            "Active strategy change without explicit user approval",
            "Missing rollback plan",
        ]:
            self.assertIn(phrase, merge_gate)

        rollback = Path("docs/rollback_policy.md").read_text(encoding="utf-8")
        for phrase in [
            "Prefer a revert PR over force push",
            "docs-only PR",
            "Config PR",
            "Code PR",
            "verify `active_strategy` remains `cross_exchange_spot_spread_v1`",
            "Runtime/Gemini rollback",
            "Generated data files should not be treated as source rollback",
        ]:
            self.assertIn(phrase, rollback)

    def test_task_checklist_agent_workflow_and_agents_require_pr_evidence(self):
        checklist = Path("docs/task_checklist.md").read_text(encoding="utf-8")
        for phrase in [
            "Before starting",
            "Task type",
            "Allowed files",
            "Forbidden files",
            "Expected tests",
            "Manual smoke needed?",
            "Rollback path",
            "Human approval needed?",
            "After completing",
            "No-trade confirmation",
        ]:
            self.assertIn(phrase, checklist)

        workflow = Path("docs/agent_workflow.md").read_text(encoding="utf-8")
        for phrase in [
            "User: product owner and final approver",
            "Codex: implementation worker",
            "GPT/reviewer: design and risk reviewer",
            "Codex must provide evidence",
            "User should not need to read every line of code",
            "Human final approval is required",
            "strategy changes",
            "active promotion",
            "runtime/auth changes",
            "execution/private API",
            "merge approval",
        ]:
            self.assertIn(phrase, workflow)

        agents = Path("AGENTS.md").read_text(encoding="utf-8")
        for phrase in [
            ".github/pull_request_template.md",
            "purpose, files changed, impact, tests, risks, rollback, and no-trade compliance",
            "rollback/no-trade evidence",
            "high-risk",
            "must not claim it is safe-to-merge without explicit human review",
        ]:
            self.assertIn(phrase, agents)

        no_trade = Path("docs/no_trade_policy.md").read_text(encoding="utf-8")
        self.assertIn("Private exchange endpoints", no_trade)
        active = Path("docs/active_strategy.md").read_text(encoding="utf-8")
        self.assertIn("cross_exchange_spot_spread_v1", active)


if __name__ == "__main__":
    unittest.main()
