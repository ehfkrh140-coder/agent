# Funding Pure Parser Helper Planning v0 Handoff

## Summary

This PR is a docs-only parser-helper planning task for Funding Rate context. It creates the pure parser helper contract plan before any Funding Rate parser, adapter, packet builder, readiness, sampling, or endpoint work. Funding Rate remains context-only and `NO_TRADE_ONLY`.

## PR Review Evidence

- PR number: TBD by GitHub after PR creation.
- Branch name: `codex/funding-pure-parser-helper-plan-v0`.
- Base branch: local `work` branch at pre-task HEAD `2644a20`; no `origin` remote was configured locally, so reviewers must verify the GitHub PR base and Files changed view.
- Commit hash: TBD until commit is created; reviewers should compare the final GitHub commit hash with the validation evidence in the PR.
- Commit parent hash: pre-task HEAD `2644a20` with parent `a69760c56cdfb6013c42585a6325604366ded163`; this is not blocked parent `456b985`.
- GitHub PR Files changed reviewer checklist included: Yes.

## Branch Freshness Evidence

- `git fetch origin main` success: No.
- Exact failure reason: `fatal: 'origin' does not appear to be a git repository` and `fatal: Could not read from remote repository.`
- Fresh `origin/main` branch: Not available locally because no `origin` remote is configured.
- Reviewer caution: because fetch did not establish a fresh `origin/main` base, the GPT designer or human reviewer must inspect GitHub PR Files changed and commit parent more strictly before merge consideration.
- Fallback freshness checks: Passed before file edits; all required latest review-gate, handoff, and Funding Rate fixture files existed in the checkout.
- Blocked HEAD/parent check: current pre-task HEAD was `2644a20`, not `70a1e23`; its listed parent was `a69760c56cdfb6013c42585a6325604366ded163`, not `456b985`.

## Expected vs Actual Files Changed

Expected Files Changed:

- `docs/funding_rate_pure_parser_helper_plan.md`
- `docs/pr_handoffs/funding_pure_parser_helper_plan_2026_06_11.md`

Actual staged files from `git diff --cached --name-only` after staging:

- `docs/funding_rate_pure_parser_helper_plan.md`
- `docs/pr_handoffs/funding_pure_parser_helper_plan_2026_06_11.md`

Comparison result: Expected Files Changed and staged files match exactly. Reviewers must still confirm GitHub PR Files changed matches exactly.

## GitHub PR Files Changed Reviewer Checklist

- [ ] GitHub Files changed matches Expected Files Changed exactly.
- [ ] Changed files are only `docs/funding_rate_pure_parser_helper_plan.md` and this handoff file.
- [ ] No fixture JSON was modified.
- [ ] No Python test code was modified.
- [ ] No `src/`, `config/`, `configs/`, `tools/`, or runtime/data source code changed.
- [ ] No generated packet or sampling JSON was created or committed.
- [ ] No previous docs, handoffs, fixture changes, or review-gate docs reappeared in the PR diff.

## Inputs Reviewed

Repository documents reviewed:

- `AGENTS.md`
- `docs/AI_Council_Project_Handoff_v5_Spot_Futures_Depth_VWAP_Dashboard_2026-06-10.md`
- `docs/codex_pr_review_gate.md`
- `docs/merge_gate.md`
- `docs/strategy_module_boundaries.md`
- `docs/funding_rate_context_strategy.md`
- `docs/funding_rate_mocked_fixture_contract.md`
- `docs/pr_handoffs/funding_public_source_research_finalization_2026_06_11.md`
- `docs/pr_handoffs/funding_mocked_fixture_contract_2026_06_11.md`
- `docs/pr_handoffs/funding_mocked_required_fixture_files_2026_06_11.md`
- `docs/pr_handoffs/funding_optional_edge_fixture_files_2026_06_11.md`
- `docs/strategy_evidence_dashboard.md`
- `docs/no_trade_policy.md`
- `docs/pr_handoffs/README.md`
- `docs/rollback_policy.md`
- `docs/task_checklist.md`
- `docs/agent_workflow.md`

Fixture files confirmed present and inspected read-only:

- `tests/fixtures/market_data/funding_rate/binance_usdm_funding_rate_history_normal.json`
- `tests/fixtures/market_data/funding_rate/bybit_linear_funding_history_normal.json`
- `tests/fixtures/market_data/funding_rate/okx_funding_rate_history_normal.json`
- `tests/fixtures/market_data/funding_rate/binance_usdm_funding_info_interval_cap_floor.json`
- `tests/fixtures/market_data/funding_rate/bybit_linear_instruments_info_funding_interval.json`
- `tests/fixtures/market_data/funding_rate/bybit_inverse_funding_history_normal.json`
- `tests/fixtures/market_data/funding_rate/okx_current_funding_rate_normal.json`
- `tests/fixtures/market_data/funding_rate/missing_required_funding_rate.json`
- `tests/fixtures/market_data/funding_rate/missing_optional_interval.json`
- `tests/fixtures/market_data/funding_rate/string_numeric_parsing.json`
- `tests/fixtures/market_data/funding_rate/positive_funding_rate.json`
- `tests/fixtures/market_data/funding_rate/negative_funding_rate.json`
- `tests/fixtures/market_data/funding_rate/zero_funding_rate.json`
- `tests/fixtures/market_data/funding_rate/high_absolute_funding_context.json`
- `tests/fixtures/market_data/funding_rate/timestamp_data_age_clock_skew_watch.json`
- `tests/fixtures/market_data/funding_rate/varying_funding_interval.json`
- `tests/fixtures/market_data/funding_rate/okx_predicted_vs_realized_semantics.json`

## Current Baseline Preservation

The active baseline remains `cross_exchange_spot_spread_v1`. This PR does not change `mark_orderbook_gap_hunt_v0`, `spot_futures_basis_v0`, `funding_rate_context_v0`, active strategy config, registry state, readiness semantics, dashboard interpretation, or any runtime behavior.

## Why Planning Before Parser Implementation

Parser implementation should not start before the project agrees on parser status naming, source semantics, required versus optional missing-field handling, warnings, normalized observation fields, and context-only guardrails. Planning first prevents parser success from being misread as readiness success and prevents predicted/current funding values from being collapsed into executable signals.

## Parser Helper Contract Summary

- Pure helper boundary: validate provided raw payloads, extract source-specific fields, plan numeric/timestamp parsing, populate missing-field lists and warnings, tag source semantics, and emit draft normalized funding observations.
- Out-of-boundary work: HTTP calls, credentials, account data, execution, readiness, Council recommendations, packet builder mutation, sampling, and dashboard generation.
- Normalized shape: venue/source provenance, source semantics, instrument identity, funding values and timestamps, parser diagnostics, optional interval/cap/floor, predicted/realized fields, and reference-only mark/premium context.
- Parser statuses: `OK`, `OK_WITH_WARNINGS`, `NEED_SOURCE_FIELDS`, `INVALID_SOURCE_SHAPE`, `INVALID_NUMERIC_FIELD`, `INVALID_TIMESTAMP_FIELD`, `UNSUPPORTED_SOURCE`, and `UNSUPPORTED_VENUE`.
- Source semantics: historical charge records, settled historical context, OKX historical context, interval/cap/floor context, instrument interval/cap/floor context, current predicted context, predicted-vs-realized semantics context, timestamp watch context, and high-absolute-funding context.

## Fixture-to-Parser Matrix Summary

The plan maps every existing Funding Rate required, optional, and edge fixture to future parser expectations. Normal Binance, Bybit, and OKX histories should parse as `OK`; missing required funding rate should produce `NEED_SOURCE_FIELDS`; optional missing interval should not fail the parser; high absolute and timestamp contexts should remain warnings; sign fixtures preserve values without directional permission; OKX predicted/current/realized fields must not be collapsed.

## Context vs Signal Guardrail

Funding parser output is not standalone `WATCH`, standalone `ENTER`, active promotion evidence, short permission, long permission, venue selection, alert authorization, or execution permission. Funding values are context, diagnostics, and regime information only. Parser warnings are review context, not trade instructions.

## Existing System Preservation Gate

- 기존 public adapter → parser → OpportunityPacket → readiness → sampling → handoff → dashboard → Council manual review 흐름을 보존하는가? Yes. This PR is docs-only and does not modify the flow.
- active baseline `cross_exchange_spot_spread_v1` behavior를 바꾸지 않는가? Yes. No active baseline files or behavior changed.
- 기존 experimental strategy status / readiness semantics / dashboard interpretation을 바꾸지 않는가? Yes. No registry, readiness, or dashboard files changed.
- Funding Rate를 기존 공통 모듈에 강제로 섞지 않고 parser-helper planning으로만 유지하는가? Yes. The plan is documentation-only.
- Context-only 정보와 executable signal을 분리하는가? Yes. The guardrail is explicit throughout the plan.
- generated packet/sampling JSON을 만들거나 commit하지 않는가? Yes. No generated JSON was created or committed.
- private API / credential / order / alert / Council auto-call을 추가하지 않는가? Yes. No executable surface was added.
- readiness 변경 없이 docs-only planning으로 유지하는가? Yes. No readiness files changed.
- endpoint 호출 없이 기존 mocked fixture와 docs만 검토했는가? Yes. Fixtures and docs were inspected read-only; no endpoint was called.

## No-Trade Compliance

`NO_TRADE_ONLY` is preserved. This PR does not add private APIs, credentials, account/balance/position lookups, orders, transfers, withdrawals, deposits, auto-trading, alert execution, Council auto-calls, endpoint calls, active strategy promotion, or executable signal wording.

## Behavior Unchanged

No `src/`, `tests/`, `config/`, `configs/`, `tools/`, `data/`, or `tests/fixtures/` file was modified. Runtime behavior is unchanged because this PR only adds planning documentation and handoff evidence.

## Generated Artifact Policy

No generated packet or sampling JSON was created or committed under `data/generated_packets` or `data/market_samples`.

## Files Changed

Expected and actual changed files are exactly:

- `docs/funding_rate_pure_parser_helper_plan.md`
- `docs/pr_handoffs/funding_pure_parser_helper_plan_2026_06_11.md`

## Validation

- `git status --short --branch`: passed; output showed branch `codex/funding-pure-parser-helper-plan-v0` and only the two expected staged docs:
  - `A  docs/funding_rate_pure_parser_helper_plan.md`
  - `A  docs/pr_handoffs/funding_pure_parser_helper_plan_2026_06_11.md`
- `git rev-parse --short HEAD`: passed; pre-commit HEAD was `2644a20`.
- `git show --no-patch --format='%h %P %s' HEAD`: passed; output was `2644a20 a69760c56cdfb6013c42585a6325604366ded163 d22de93c96885934ac74a2c85bd6c9875f5b162a Merge pull request #186 from ehfkrh140-coder/codex/summarize-project-status-and-propose-next-steps-5mhkk9`.
- `git fetch origin main`: not available in this workspace because no `origin` remote is configured; exact output was `fatal: 'origin' does not appear to be a git repository` and `fatal: Could not read from remote repository.`
- Fallback freshness checks: passed; `HEAD_BLOCK_CHECK=PASS`, `PARENT_BLOCK_CHECK=PASS`, and the current checkout was not blocked HEAD `70a1e23` or blocked parent `456b985`.
- Required latest docs/fixtures existence check: passed; output was `REQUIRED_FILE_MISSING_COUNT=0`.
- `git diff --cached --name-only`: passed; output listed only:
  - `docs/funding_rate_pure_parser_helper_plan.md`
  - `docs/pr_handoffs/funding_pure_parser_helper_plan_2026_06_11.md`
- Expected Files Changed comparison: passed; `EXPECTED_COMPARE=PASS`.
- `git diff --cached --name-only -- src tests config configs tools data/generated_packets data/market_samples`: passed; output was empty.
- `git diff --cached --name-only -- tests/fixtures`: passed; output was empty.
- `find data/generated_packets data/market_samples -type f -name '*.json'`: no generated JSON files were listed for this task; the command also reported that `data/generated_packets` and `data/market_samples` do not exist in this checkout.
- `git diff --check --cached`: passed with no output.
- `python -m unittest discover -s tests`: passed; output ended with `Ran 531 tests in 15.781s` and `OK`.

## Merge Recommendation

Codex does not assert this PR is mergeable. GPT designer or human reviewer must inspect GitHub PR Files changed, commit parent, validation evidence, and no-trade guardrails before deciding whether to merge. If GitHub Files changed differs from Expected Files Changed, merge must remain on hold.

## Next Recommended Step

The next PR should be Funding Pure Parser Helper Implementation v0. It should remain public-read-only, context-only, fixture-driven, and no-trade-first, with parser behavior tested against the approved mocked fixtures before any venue wrapper, packet extension, readiness, sampling, or dashboard work.
