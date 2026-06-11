# Funding Pure Parser Helper Implementation v0 Handoff

## Summary

이번 PR은 Funding Rate pure parser helper implementation + unit tests 작업입니다. `docs/funding_rate_pure_parser_helper_plan.md`의 계약을 바탕으로 caller-provided mocked/public Funding Rate payload를 deterministic normalized context observation으로 변환하는 pure helper와 fixture-driven unittest coverage를 추가했습니다. Adapter, packet builder, readiness, sampling, dashboard, endpoint 호출, live response copy/paste, fixture 수정은 포함하지 않습니다.

## PR Review Evidence

- PR number: TBD by GitHub after PR creation.
- Branch name: `codex/funding-pure-parser-helper-implementation-v0`.
- Base branch: local `work` checkout at pre-task HEAD `1c7868f`; no `origin` remote is configured in this Codex workspace, so fallback freshness checks were used.
- Commit hash: created after validation by Codex; reviewer should compare GitHub commit view with this handoff and PR Files changed.
- Commit parent hash: pre-task parent `2644a20427543162424b1d1aef5aaf5b6708005e`; this is not blocked parent `456b985`.
- GitHub PR Files changed reviewer checklist included: Yes.

## Branch Freshness Evidence

- `git fetch origin main` success: No.
- Exact failure reason: `fatal: 'origin' does not appear to be a git repository` and `fatal: Could not read from remote repository.`
- Origin remote fallback: Per task instruction, origin absence did not automatically stop work. Fallback freshness checks were performed before edits.
- PR #187 planning docs existence: Passed; both `docs/funding_rate_pure_parser_helper_plan.md` and `docs/pr_handoffs/funding_pure_parser_helper_plan_2026_06_11.md` exist in the checkout.
- Required Funding Rate fixture existence: Passed; all required/optional/edge Funding Rate fixture JSON files listed in the task exist in the checkout.
- Blocked HEAD / blocked parent: Passed; pre-task HEAD was `1c7868f`, not blocked HEAD `70a1e23`; parent was `2644a20427543162424b1d1aef5aaf5b6708005e`, not blocked parent `456b985`.
- Working tree before edits: Passed; `git status --short --branch` showed clean branch `## work` before creating the implementation branch.
- Reviewer caution: because fresh `origin/main` could not be fetched directly, GPT designer or human reviewer must inspect GitHub PR Files changed and commit parent more strictly before merge consideration.

## Expected vs Actual Files Changed

Expected Files Changed:

- `src/market_data/funding_rate_parser.py`
- `tests/test_funding_rate_parser.py`
- `docs/pr_handoffs/funding_pure_parser_helper_implementation_2026_06_11.md`

Actual staged files from `git diff --cached --name-only`:

- `docs/pr_handoffs/funding_pure_parser_helper_implementation_2026_06_11.md`
- `src/market_data/funding_rate_parser.py`
- `tests/test_funding_rate_parser.py`

Comparison result: Same three files, no extra staged files. Reviewers must still confirm GitHub PR Files changed matches Expected Files Changed exactly; if not, merge is on hold.

## GitHub PR Files Changed Reviewer Checklist

- [ ] GitHub Files changed matches Expected Files Changed exactly.
- [ ] Changed files are only `src/market_data/funding_rate_parser.py`, `tests/test_funding_rate_parser.py`, and this handoff file.
- [ ] Fixture JSON files were not modified.
- [ ] Config/registry files were not modified.
- [ ] No generated packet/sampling JSON was created or committed.
- [ ] No private API / order / alert / Council auto-call related change exists.

## Inputs Reviewed

Repository documents reviewed:

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
- `docs/strategy_evidence_dashboard.md`
- `AGENTS.md`
- `docs/no_trade_policy.md`
- `docs/pr_handoffs/README.md`
- `docs/rollback_policy.md`
- `docs/task_checklist.md`
- `docs/agent_workflow.md`

Implementation style references reviewed:

- `src/market_data/depth_vwap.py`
- `tests/test_depth_vwap.py`

Fixture files used by tests, read-only:

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

The active baseline remains `cross_exchange_spot_spread_v1`. Existing experimental strategies, Funding Rate planning status, readiness semantics, dashboard interpretation, configs, registries, adapters, packet builders, and sampling collectors were not modified.

## Implementation Summary

- Added `src/market_data/funding_rate_parser.py`, a pure helper module with public API `parse_funding_rate_payload(payload, *, venue: str, source_endpoint: str) -> dict[str, Any]`.
- The helper accepts caller-provided payload objects only and returns plain dict/list output with `Decimal`, `int`, `str`, `None`, and diagnostic lists.
- Supported venue/source pairs cover Binance USD-M funding history and funding info, Bybit V5 funding history and instruments-info, OKX funding-rate history and current funding-rate, plus edge/mixed context sources for OKX predicted-vs-realized, timestamp watch, high-absolute funding, string numeric parsing, and varying interval coverage.
- OKX `settFundingRate` is mapped to `realized_funding_rate` for current funding context in this v0 implementation; `nextFundingRate` remains `predicted_funding_rate`, and `fundingRate` remains the current source funding rate.
- The helper does not create dataclasses, pydantic models, enums, external dependencies, network clients, file readers, config lookups, registry lookups, generated artifacts, or adapter behavior.

## Parser Status Behavior

- `OK`: Required fields parsed with no warnings. This is parser health only, not trade permission.
- `OK_WITH_WARNINGS`: Required fields parsed and context warnings are present, such as high absolute funding, timestamp watch, optional interval missing, string numeric non-signal, or predicted-vs-realized non-collapse warnings. This is not `WATCH` or `ENTER`.
- `NEED_SOURCE_FIELDS`: Required source fields such as `instrument_id`, `funding_rate`, or `funding_rate_timestamp_ms` are missing. Missing data is context only.
- `INVALID_SOURCE_SHAPE`: Top-level payload shape does not match the selected source parser.
- `INVALID_NUMERIC_FIELD`: A required or present numeric field cannot be parsed as finite `Decimal`.
- `INVALID_TIMESTAMP_FIELD`: A required or present timestamp field cannot be parsed as integer milliseconds.
- `UNSUPPORTED_SOURCE`: Venue is known but source endpoint is not supported by v0.
- `UNSUPPORTED_VENUE`: Venue is outside v0 support.

All statuses have readiness effect `none / readiness unchanged`.

## Source Semantics Mapping

Implemented mappings:

- `binance_usdm` + `binance_usdm_funding_rate_history` → `historical_funding_charge_record`
- `binance_usdm` + `binance_usdm_funding_info` → `interval_cap_floor_context`
- `bybit` + `bybit_v5_funding_history` → `settled_historical_funding_context`
- `bybit` + `bybit_v5_instruments_info` → `instrument_interval_cap_floor_context`
- `okx` + `okx_funding_rate_history` → `historical_funding_context`
- `okx` + `okx_current_funding_rate` → `current_predicted_funding_context`
- `okx` + `okx_predicted_vs_realized_semantics` → `predicted_vs_realized_semantics_context`
- `bybit` + `timestamp_watch_context` → `timestamp_watch_context`
- `okx` + `high_abs_funding_context` → `high_abs_funding_context`
- edge helpers for string numeric parsing and varying interval fixture coverage remain context-only.

## Fixture Coverage

- Required normal fixtures: Binance history, Bybit linear funding history, and OKX funding history parse to `OK`, produce two observations, use `Decimal` funding rates, integer timestamps, and expected `source_semantics`.
- Optional fixtures: Binance funding info parses cap/floor/interval context; Bybit instruments-info converts minutes to hours; Bybit inverse history preserves `inverse`; OKX current funding keeps current/predicted/settled fields distinct.
- Edge fixtures: missing required funding rate, missing optional interval, string numeric parsing, positive/negative/zero funding, high absolute funding, timestamp watch, varying interval, and OKX predicted-vs-realized semantics are covered.
- Invalid synthetic cases: unsupported venue/source, invalid source shape, invalid numeric field, and invalid timestamp field are covered without live calls.

## Context vs Signal Guardrail

Funding parser output is not standalone `WATCH`, standalone `ENTER`, active promotion evidence, short permission, long permission, alert authorization, or execution permission. Positive funding, negative funding, zero funding, high absolute funding, parser success, and parser warnings remain context/diagnostics only.

## Safety / Purity Guardrail

The helper imports only standard-library `decimal` and `typing` modules plus `__future__` annotations. It does not import network libraries, private API clients, credential/config/registry helpers, filesystem path helpers, subprocess/socket modules, or pydantic. It does not perform file I/O, network I/O, endpoint calls, environment lookup, generated artifact creation, config lookup, registry lookup, account lookup, order placement, alert execution, or Council auto-call.

## Existing System Preservation Gate

- 기존 public adapter → parser → OpportunityPacket → readiness → sampling → handoff → dashboard → Council manual review 흐름을 보존하는가? Yes. No existing pipeline module was modified.
- active baseline `cross_exchange_spot_spread_v1` behavior를 바꾸지 않는가? Yes. No active baseline file or behavior changed.
- 기존 experimental strategy status / readiness semantics / dashboard interpretation을 바꾸지 않는가? Yes. No registry, readiness, or dashboard file changed.
- Funding Rate를 기존 공통 모듈에 강제로 섞지 않고 pure helper로만 추가했는가? Yes. One new pure helper module was added under `src/market_data/`.
- Context-only 정보와 executable signal을 분리하는가? Yes. Output contains parser/context fields only and tests assert forbidden execution/trade keys are absent.
- generated packet/sampling JSON을 만들거나 commit하지 않는가? Yes.
- private API / credential / order / alert / Council auto-call을 추가하지 않는가? Yes.
- readiness 변경 없이 parser-helper-only로 유지하는가? Yes.
- endpoint 호출 없이 mocked fixture와 caller-provided payload만 사용했는가? Yes. Tests read static fixtures and pass payload objects to the helper.

## No-Trade Compliance

`NO_TRADE_ONLY` is preserved. This PR adds no private endpoints, API keys, secrets, tokens, account/balance/position lookup, order/cancel/transfer/withdraw/deposit behavior, auto-trading, alert execution, Council auto-call, active strategy promotion, endpoint call, live response copy/paste, packet builder mutation, readiness mutation, or sampling collector.

## Behavior Unchanged

Adapter, packet builder, candidate builder, readiness, sampling, dashboard, config, registry, fixture JSON, generated data, and active strategy behavior are unchanged. Runtime strategy behavior is unchanged unless a future caller explicitly imports the pure helper; no existing caller was modified.

## Generated Artifact Policy

No generated JSON was created or committed under `data/generated_packets` or `data/market_samples`. Tests assert `data/generated_packets/funding_rate_parser.json` and `data/market_samples/funding_rate_parser.json` do not exist, and the parser source does not reference those generated artifact directories.

## Files Changed

Expected and actual changed files are exactly:

- `src/market_data/funding_rate_parser.py`
- `tests/test_funding_rate_parser.py`
- `docs/pr_handoffs/funding_pure_parser_helper_implementation_2026_06_11.md`

## Validation

- `git status --short --branch`: passed; pre-edit status was clean `## work`, and staged status later showed only expected changes on `codex/funding-pure-parser-helper-implementation-v0`.
- `git diff --cached --name-only`: passed; output listed only the three expected files.
- Expected Files Changed comparison: passed; staged files exactly matched the expected set.
- `git diff --cached --name-only -- config configs tools data/generated_packets data/market_samples`: passed; output was empty.
- `git diff --cached --name-only -- tests/fixtures`: passed; output was empty.
- `find data/generated_packets data/market_samples -type f -name '*.json'`: no generated JSON files for this task were listed; this checkout reports the directories do not exist.
- `git diff --check --cached`: passed with no output.
- `python -m unittest tests.test_funding_rate_parser`: passed; `Ran 24 tests` and `OK`.
- `python -m unittest discover -s tests`: passed; output ended with `Ran 555 tests in 22.642s` and `OK`.

## Merge Recommendation

Codex does not assert this PR is mergeable. GPT designer or human reviewer must inspect GitHub PR Files changed, commit parent, validation evidence, and no-trade guardrails before deciding whether to merge. If GitHub Files changed differs from Expected Files Changed, merge must remain on hold.

## Next Recommended Step

The next PR should be Funding Venue Parser Wrapper Planning v0 rather than wrapper implementation, because wrapper boundaries should be reviewed before adding any source-specific orchestration around the pure helper. The next PR must remain public-read-only, context-only, fixture-driven, no-trade-first, and must not add endpoint calls, credentials, private APIs, readiness changes, packet builder mutation, sampling collectors, dashboards, alerts, or active promotion.
