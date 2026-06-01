from __future__ import annotations

import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
