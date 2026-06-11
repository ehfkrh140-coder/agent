# Funding Venue Parser Wrapper Planning v0 Handoff

## Summary

This PR is a docs-only Funding Rate venue parser wrapper planning task. It defines how future venue-specific wrappers may safely call the existing pure Funding Rate parser helper while preserving provenance, keeping output context-only, and avoiding readiness, adapter, packet, sampling, dashboard, or execution changes.

## PR Review Evidence

- PR number: TBD by GitHub after PR creation.
- Branch name: `work` in this Codex workspace; intended GitHub PR branch should be created from main by the PR workflow.
- Base branch: `main`.
- Commit hash: Final commit hash is not embedded because adding it would require a self-referential amend; reviewers should confirm with `git rev-parse --short HEAD` and GitHub PR commit view.
- Commit parent hash: `9a999da`.
- GitHub PR Files changed reviewer checklist included: Yes.

## Correction Note

Before merge review, the source semantics names in `docs/funding_rate_venue_parser_wrapper_plan.md` were aligned with the pure helper `_SOURCE_SEMANTICS` mapping. The corrected planning table now uses `historical_funding_charge_record`, `interval_cap_floor_context`, `settled_historical_funding_context`, `instrument_interval_cap_floor_context`, `historical_funding_context`, and `current_predicted_funding_context` exactly as the source-of-truth helper mapping defines them.

## Branch Freshness Evidence

- `git fetch origin main` success 여부: Failed after adding `origin` remote for verification.
- Exact failure reason: `fatal: unable to access 'https://github.com/ehfkrh140-coder/agent.git/': CONNECT tunnel failed, response 403`.
- Origin remote absent fallback: Initial `git remote -v` output was empty. The workspace then added `origin` as `https://github.com/ehfkrh140-coder/agent.git` only for freshness verification, but network fetch failed with the 403 error above.
- Fallback freshness checks performed: Yes. Required post-PR #189 files were present, pre-edit status was clean, current HEAD was `9a999da`, and log showed PR #189 merge followed by the pure parser helper implementation commit in history.
- PR #189 pure parser helper implementation 존재 확인 여부: Yes. `src/market_data/funding_rate_parser.py`, `tests/test_funding_rate_parser.py`, and `docs/pr_handoffs/funding_pure_parser_helper_implementation_2026_06_11.md` were present.
- #187 planning docs 존재 확인 여부: Yes. `docs/funding_rate_pure_parser_helper_plan.md` and `docs/pr_handoffs/funding_pure_parser_helper_plan_2026_06_11.md` were present.
- Blocked HEAD / blocked parent가 아닌지 확인 여부: No branch switch was performed. The workspace HEAD is `9a999da`, which is the local merge commit containing PR #189 evidence. Because `origin/main` could not be fetched, GitHub PR Files changed must be treated as the final source of truth before merge.
- Main 기준 작업 여부: Work was performed from the current clean checkout that already contains the PR #189 pure helper files expected on main after merge. No previous PR files were recreated or modified.
- Fresh `origin/main` 직접 fetch 불가 시 주의: Because fresh `origin/main` could not be fetched in this environment, the reviewer must more strictly verify GitHub PR Files changed against Expected Files Changed before any merge decision.

## Expected vs Actual Files Changed

Expected Files Changed:

- `docs/funding_rate_venue_parser_wrapper_plan.md`
- `docs/pr_handoffs/funding_venue_parser_wrapper_plan_2026_06_11.md`

Actual `git diff --cached --name-only` result after staging:

- `docs/funding_rate_venue_parser_wrapper_plan.md`
- `docs/pr_handoffs/funding_venue_parser_wrapper_plan_2026_06_11.md`

Comparison result:

- Passed. Actual staged files exactly match Expected Files Changed.

## GitHub PR Files Changed Reviewer Checklist

After PR creation, reviewer must confirm:

- GitHub Files changed matches Expected Files Changed exactly.
- Changed files are only `docs/funding_rate_venue_parser_wrapper_plan.md` and `docs/pr_handoffs/funding_venue_parser_wrapper_plan_2026_06_11.md`.
- `src/market_data/funding_rate_parser.py` was not modified.
- `tests/test_funding_rate_parser.py` was not modified.
- Fixture JSON was not modified.
- Config/registry files were not modified.
- No generated packet/sampling JSON was added.
- No private API, order, alert, or Council auto-call related change was added.

## Inputs Reviewed

Repository documents reviewed before writing:

- `docs/AI_Council_Project_Handoff_v5_Spot_Futures_Depth_VWAP_Dashboard_2026-06-10.md`
- `docs/codex_pr_review_gate.md`
- `docs/merge_gate.md`
- `docs/strategy_module_boundaries.md`
- `docs/funding_rate_context_strategy.md`
- `docs/funding_rate_mocked_fixture_contract.md`
- `docs/funding_rate_pure_parser_helper_plan.md`
- `docs/pr_handoffs/funding_public_source_research_finalization_2026_06_11.md`
- `docs/pr_handoffs/funding_mocked_fixture_contract_2026_06_11.md`
- `docs/pr_handoffs/funding_mocked_required_fixture_files_2026_06_11.md`
- `docs/pr_handoffs/funding_optional_edge_fixture_files_2026_06_11.md`
- `docs/pr_handoffs/funding_pure_parser_helper_plan_2026_06_11.md`
- `docs/pr_handoffs/funding_pure_parser_helper_implementation_2026_06_11.md`
- `docs/strategy_evidence_dashboard.md`
- `AGENTS.md`
- `docs/no_trade_policy.md`
- `docs/pr_handoffs/README.md`
- `docs/rollback_policy.md`
- `docs/task_checklist.md`
- `docs/agent_workflow.md`

Read-only implementation/test references reviewed and not modified:

- `src/market_data/funding_rate_parser.py`
- `tests/test_funding_rate_parser.py`

## Current Baseline Preservation

The active baseline remains `cross_exchange_spot_spread_v1`. This PR does not modify active strategy behavior, experimental strategy status, readiness semantics, dashboard interpretation, configs, registries, adapters, packet builders, or sampling collectors.

## Why Planning Before Wrapper Implementation

Planning comes before wrapper implementation because the wrapper boundary must be explicit before any orchestration code exists. The project needs agreement on wrapper responsibility, `wrapper_status`, provenance handling, `category_hint` policy, source/venue mismatch handling, and future adapter relationship before adding code that could otherwise be misread as endpoint readiness, live-data permission, or readiness evidence.

## Wrapper Boundary Summary

Candidate wrapper responsibilities:

- Select venue/source labels for the pure helper.
- Preserve payload provenance metadata.
- Call the pure helper with caller-provided payloads.
- Wrap parser results in a context-only envelope.
- Add wrapper-level diagnostics for source mismatch, category mismatch, or empty payload.
- Define future adapter-to-helper contract.

Explicitly out of boundary:

- HTTP requests.
- Authentication.
- Account data.
- Order execution.
- Readiness decisions.
- Packet builder mutation.
- Sampling persistence.
- Dashboard updates.
- Council recommendations.
- Active promotion.

## Proposed Wrapper API Summary

Planning-only wrapper API candidates:

- `parse_binance_usdm_funding_rate_history(payload)`.
- `parse_binance_usdm_funding_info(payload)`.
- `parse_bybit_v5_funding_history(payload, *, category_hint=None)`.
- `parse_bybit_v5_instruments_info(payload, *, category_hint=None)`.
- `parse_okx_funding_rate_history(payload)`.
- `parse_okx_current_funding_rate(payload)`.

Each candidate maps to fixed venue/source labels and calls the pure helper without adding endpoint calls, credentials, readiness mutation, or execution semantics.

## Wrapper Output Envelope Summary

Draft wrapper envelope fields:

- `wrapper_status`.
- `venue`.
- `source_endpoint`.
- `source_semantics`.
- `parser_result`.
- `wrapper_warnings`.
- `provenance`.
- `input_record_count`.
- `parsed_record_count`.
- `context_only`.
- `readiness_effect`.

The default readiness effect must be `none` or `unchanged`; v0 planning recommends `readiness_effect="unchanged"`.

## Relationship to Pure Helper

The wrapper is a thin-layer candidate above the pure helper. It may call `parse_funding_rate_payload(payload, venue=..., source_endpoint=...)` in a future implementation, but this PR does not modify `src/market_data/funding_rate_parser.py` or its tests.

## Relationship to Adapter / Packet / Readiness / Sampling / Dashboard

This PR does not add or modify adapters, packet/candidate builders, readiness policy, sampling collectors, generated artifacts, dashboards, alerts, or Council automation. Future wrapper results may be considered for packet/candidate extensions only in a separate planning and implementation sequence.

## Future Wrapper Test Matrix

Future implementation tests should verify:

- Binance history wrapper calls pure helper with correct venue/source.
- Binance `fundingInfo` wrapper calls pure helper with correct venue/source.
- Bybit funding history wrapper preserves category.
- Bybit instruments-info wrapper handles category hint.
- OKX history wrapper preserves historical semantics.
- OKX current wrapper preserves predicted/current/settled separation.
- Wrapper output has `context_only=True`.
- Wrapper output has `readiness_effect="unchanged"`.
- Wrapper output has no order/alert/execution keys.
- Unsupported wrapper input returns wrapper-level diagnostic without exception where safe.
- Wrapper does not import network/private libraries.
- Wrapper does not read files or environment variables.

## Context vs Signal Guardrail

Funding wrapper output is not standalone `WATCH`, standalone `ENTER`, active promotion evidence, readiness success, alert authorization, Council instruction, order direction, venue preference, or execution permission. Parser success, parser warnings, wrapper success, wrapper warnings, and parsed record counts remain context/diagnostics only.

## Existing System Preservation Gate

- 기존 public adapter → parser → OpportunityPacket → readiness → sampling → handoff → dashboard → Council manual review 흐름을 보존하는가? Yes. This PR only adds wrapper planning docs and does not modify the existing pipeline.
- active baseline `cross_exchange_spot_spread_v1` behavior를 바꾸지 않는가? Yes. No active baseline code, config, or registry was modified.
- 기존 experimental strategy status / readiness semantics / dashboard interpretation을 바꾸지 않는가? Yes. No strategy status, readiness, or dashboard files were modified.
- Funding Rate를 기존 공통 모듈에 강제로 섞지 않고 wrapper planning으로만 유지하는가? Yes. No common runtime module was modified.
- Context-only 정보와 executable signal을 분리하는가? Yes. The planning document explicitly states wrapper output is context-only and not `WATCH`, `ENTER`, or execution permission.
- generated packet/sampling JSON을 만들거나 commit하지 않는가? Yes. No generated JSON was created or committed.
- private API / credential / order / alert / Council auto-call을 추가하지 않는가? Yes. This is docs-only and adds none of those surfaces.
- readiness 변경 없이 docs-only planning으로 유지하는가? Yes. Readiness remains unchanged.
- endpoint 호출 없이 existing docs/source/tests만 검토했는가? Yes. No Funding Rate endpoint or live market-data endpoint was called.

## No-Trade Compliance

`NO_TRADE_ONLY` is preserved. This PR adds no private endpoints, API keys, secrets, tokens, account/balance/position lookup, order/cancel/transfer/withdraw/deposit behavior, auto-trading, alert execution, Council auto-call, active strategy promotion, endpoint calls, live response copy/paste, packet builder mutation, readiness mutation, sampling collector, dashboard automation, or generated artifacts.

## Behavior Unchanged

`src/`, `tests/`, `config/`, `configs/`, `tools/`, `data/`, and `tests/fixtures/` were not modified. Runtime behavior is unchanged because this PR only adds documentation and handoff evidence.

## Generated Artifact Policy

No generated JSON was created or committed under `data/generated_packets` or `data/market_samples`.

## Files Changed

Expected and actual changed files must be exactly:

- `docs/funding_rate_venue_parser_wrapper_plan.md`
- `docs/pr_handoffs/funding_venue_parser_wrapper_plan_2026_06_11.md`

## Validation

- `git status --short --branch`: passed; staged status showed only the two expected added docs files on `work`.
- `git diff --cached --name-only`: passed; output listed exactly `docs/funding_rate_venue_parser_wrapper_plan.md` and `docs/pr_handoffs/funding_venue_parser_wrapper_plan_2026_06_11.md`.
- Expected Files Changed comparison: passed; actual staged files exactly matched Expected Files Changed.
- `git diff --cached --name-only -- src tests config configs tools data/generated_packets data/market_samples`: passed; output was empty.
- `git diff --cached --name-only -- tests/fixtures`: passed; output was empty.
- `find data/generated_packets data/market_samples -type f -name '*.json'`: passed with no generated JSON found; this checkout reports both directories do not exist.
- `git diff --check --cached`: passed with no output.
- `python -m unittest discover -s tests`: passed; output ended with `Ran 555 tests in 16.460s` and `OK`.

## Conflict Resolution Evidence

No conflict occurred.

Conflict files: none.

Resolution basis: Not applicable. No merge, rebase, or branch switch was performed, and only the Expected Files Changed were created.

GitHub Files changed confirmation requirement: Reviewer must confirm GitHub Files changed exactly matches Expected Files Changed before any merge decision.

## Merge Recommendation

Codex does not assert this PR is mergeable. GPT designer or human reviewer must inspect GitHub PR Files changed, Expected Files Changed, validation evidence, no-trade compliance, and the planning boundary before deciding whether to merge. If GitHub PR Files changed differs from Expected Files Changed, merge must remain on hold.

## Next Recommended Step

The next PR should be Funding Venue Parser Wrapper Implementation v0. That future PR must remain public-read-only, context-only, fixture-driven, no-trade-first, and must not add private APIs, credentials, order behavior, readiness changes, packet builder mutation, sampling collectors, dashboards, alerts, Council auto-call, or active promotion.
