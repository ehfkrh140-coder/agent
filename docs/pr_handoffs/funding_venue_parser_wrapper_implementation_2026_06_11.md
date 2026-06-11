# Funding Venue Parser Wrapper Implementation v0 Handoff

## Summary

This PR adds the first thin Funding Rate venue parser wrapper implementation plus unittest coverage. The wrapper module accepts caller-provided raw Funding Rate payload objects, selects fixed venue/source labels, delegates parsing to the existing pure helper, and returns a context-only envelope with provenance, wrapper warnings, record counts, and unchanged readiness effect.

This PR does not add adapters, endpoint calls, live payload collection, packet builders, candidate builders, readiness changes, sampling collectors, dashboards, config/registry changes, fixture changes, generated artifacts, or execution behavior.

## PR Review Evidence

- PR number: TBD by GitHub after PR creation.
- Branch name: `work` in this Codex workspace; intended GitHub PR branch should be created from main by the PR workflow.
- Base branch: `main`.
- Commit hash: TBD after commit; reviewer should confirm with GitHub PR commit view.
- Commit parent hash: `24d28f0` before this implementation commit.
- GitHub PR Files changed reviewer checklist included: Yes.

## Branch Freshness Evidence

- `git fetch origin main` success 여부: Not attempted because initial `git remote -v` output was empty and no `origin` remote was configured in this workspace.
- Exact failure reason: Not applicable; no origin remote was present.
- Origin remote absent fallback freshness checks 수행 여부: Yes. Required PR #191 planning docs and PR #189 pure parser implementation files were present, pre-edit status was clean, and the current checkout contained the wrapper planning handoff and source-semantics correction expected after PR #191.
- PR #191 wrapper planning docs 존재 확인 여부: Yes. `docs/funding_rate_venue_parser_wrapper_plan.md` and `docs/pr_handoffs/funding_venue_parser_wrapper_plan_2026_06_11.md` were present before implementation.
- PR #189 pure parser helper implementation 존재 확인 여부: Yes. `src/market_data/funding_rate_parser.py`, `tests/test_funding_rate_parser.py`, and `docs/pr_handoffs/funding_pure_parser_helper_implementation_2026_06_11.md` were present before implementation.
- Blocked HEAD / blocked parent가 아닌지 확인 여부: No branch switch was performed. Because this workspace has no origin remote and cannot directly verify fresh `origin/main`, GitHub PR Files changed must be treated as the final source of truth before merge.
- Fresh `origin/main` 직접 fetch 불가 시 주의: Reviewer must more strictly verify GitHub PR Files changed against Expected Files Changed and confirm PR #191 is merged into main before any merge decision.

## Expected vs Actual Files Changed

Expected Files Changed:

- `src/market_data/funding_rate_wrappers.py`
- `tests/test_funding_rate_wrappers.py`
- `docs/pr_handoffs/funding_venue_parser_wrapper_implementation_2026_06_11.md`

Actual `git diff --cached --name-only` result after staging:

- `docs/pr_handoffs/funding_venue_parser_wrapper_implementation_2026_06_11.md`
- `src/market_data/funding_rate_wrappers.py`
- `tests/test_funding_rate_wrappers.py`

Comparison result:

- Passed. Actual staged files are exactly the same three files as Expected Files Changed; `git diff --cached --name-only` prints them in path-sorted order.

## GitHub PR Files Changed Reviewer Checklist

After PR creation, reviewer must confirm:

- GitHub Files changed matches Expected Files Changed exactly.
- Changed files are only `src/market_data/funding_rate_wrappers.py`, `tests/test_funding_rate_wrappers.py`, and `docs/pr_handoffs/funding_venue_parser_wrapper_implementation_2026_06_11.md`.
- Existing parser helper `src/market_data/funding_rate_parser.py` was not modified.
- Existing parser tests `tests/test_funding_rate_parser.py` were not modified.
- Fixture JSON files were not modified.
- Config/registry files were not modified.
- No generated packet/sampling JSON was added.
- No private API, order, alert, or Council auto-call related change was added.

## Inputs Reviewed

Repository documents reviewed before implementation:

- `docs/AI_Council_Project_Handoff_v5_Spot_Futures_Depth_VWAP_Dashboard_2026-06-10.md`
- `docs/codex_pr_review_gate.md`
- `docs/merge_gate.md`
- `docs/strategy_module_boundaries.md`
- `docs/funding_rate_context_strategy.md`
- `docs/funding_rate_mocked_fixture_contract.md`
- `docs/funding_rate_pure_parser_helper_plan.md`
- `docs/funding_rate_venue_parser_wrapper_plan.md`
- `docs/pr_handoffs/funding_public_source_research_finalization_2026_06_11.md`
- `docs/pr_handoffs/funding_mocked_fixture_contract_2026_06_11.md`
- `docs/pr_handoffs/funding_mocked_required_fixture_files_2026_06_11.md`
- `docs/pr_handoffs/funding_optional_edge_fixture_files_2026_06_11.md`
- `docs/pr_handoffs/funding_pure_parser_helper_plan_2026_06_11.md`
- `docs/pr_handoffs/funding_pure_parser_helper_implementation_2026_06_11.md`
- `docs/pr_handoffs/funding_venue_parser_wrapper_plan_2026_06_11.md`
- `docs/strategy_evidence_dashboard.md`
- `AGENTS.md`
- `docs/no_trade_policy.md`
- `docs/pr_handoffs/README.md`
- `docs/rollback_policy.md`
- `docs/task_checklist.md`
- `docs/agent_workflow.md`

Read-only source/test references reviewed and not modified:

- `src/market_data/funding_rate_parser.py`
- `tests/test_funding_rate_parser.py`

Fixture JSON files read by new tests and not modified:

- `tests/fixtures/market_data/funding_rate/binance_usdm_funding_rate_history_normal.json`
- `tests/fixtures/market_data/funding_rate/binance_usdm_funding_info_interval_cap_floor.json`
- `tests/fixtures/market_data/funding_rate/bybit_linear_funding_history_normal.json`
- `tests/fixtures/market_data/funding_rate/bybit_inverse_funding_history_normal.json`
- `tests/fixtures/market_data/funding_rate/bybit_linear_instruments_info_funding_interval.json`
- `tests/fixtures/market_data/funding_rate/okx_funding_rate_history_normal.json`
- `tests/fixtures/market_data/funding_rate/okx_current_funding_rate_normal.json`

## Current Baseline Preservation

The active baseline remains `cross_exchange_spot_spread_v1`. Existing experimental strategy status, readiness semantics, dashboard interpretation, configs, registries, adapters, packet builders, sampling collectors, and generated data were not modified.

## Implementation Summary

Added `src/market_data/funding_rate_wrappers.py`, a pure thin wrapper layer with these public APIs:

- `parse_binance_usdm_funding_rate_history(payload, *, provenance=None)`
- `parse_binance_usdm_funding_info(payload, *, provenance=None)`
- `parse_bybit_v5_funding_history(payload, *, category_hint=None, provenance=None)`
- `parse_bybit_v5_instruments_info(payload, *, category_hint=None, provenance=None)`
- `parse_okx_funding_rate_history(payload, *, provenance=None)`
- `parse_okx_current_funding_rate(payload, *, provenance=None)`

Each public API calls `parse_funding_rate_payload(...)` with the correct fixed venue/source endpoint and returns an envelope containing `wrapper_status`, `venue`, `source_endpoint`, `source_semantics`, `parser_result`, `wrapper_warnings`, shallow-copied `provenance`, `input_record_count`, `parsed_record_count`, `context_only=True`, and `readiness_effect="unchanged"`.

Bybit `category_hint` is optional. If absent or matching payload `result.category`, no wrapper warning is added. If mismatched, `category_hint_mismatch` is added, wrapper status becomes `OK_WITH_WARNINGS`, and pure helper parsing continues against the caller-provided payload.

Empty payloads add `empty_payload` and use `WRAPPER_INPUT_EMPTY`. This status was chosen because it most clearly identifies wrapper-level orchestration input health. It remains diagnostic only and does not imply readiness or trade signal.

## Wrapper Status Behavior

- `OK`: wrapper orchestration saw recognizable non-empty input and no wrapper-level warnings.
- `OK_WITH_WARNINGS`: wrapper orchestration completed with diagnostic warnings, such as Bybit `category_hint_mismatch`.
- `WRAPPER_INPUT_EMPTY`: wrapper recognized an empty record container and added `empty_payload`.
- `WRAPPER_SOURCE_MISMATCH`: defined as a future explicit source/venue mismatch candidate; this v0 has fixed public APIs and does not expose a generic source-switching wrapper path.
- `WRAPPER_INVALID_INPUT`: wrapper could not compute an input record count for the expected venue payload shape.

All wrapper statuses are orchestration health labels only. They are not readiness success, `WATCH`, `ENTER`, alert permission, order permission, or execution permission.

## Source Semantics Mapping

Implemented mapping:

- `binance_usdm_funding_rate_history` → `historical_funding_charge_record`
- `binance_usdm_funding_info` → `interval_cap_floor_context`
- `bybit_v5_funding_history` → `settled_historical_funding_context`
- `bybit_v5_instruments_info` → `instrument_interval_cap_floor_context`
- `okx_funding_rate_history` → `historical_funding_context`
- `okx_current_funding_rate` → `current_predicted_funding_context`

These values match the existing pure helper source semantics mapping for the implemented wrapper endpoints.

## Fixture Coverage

New wrapper tests cover:

- Binance USD-M funding history fixture.
- Binance funding info cap/floor/interval fixture.
- Bybit linear funding history fixture.
- Bybit inverse funding history fixture for category mismatch diagnostics.
- Bybit linear instruments-info funding interval fixture.
- OKX funding-rate-history fixture.
- OKX current funding-rate fixture.

The tests read fixtures only; no fixture JSON was modified.

## Context vs Signal Guardrail

Funding wrapper output is not standalone `WATCH`, standalone `ENTER`, active promotion evidence, readiness success, alert authorization, Council instruction, order direction, venue preference, or execution permission. Parser success, parser warnings, wrapper success, wrapper warnings, record counts, category hints, and provenance remain context/diagnostics only.

## Safety / Purity Guardrail

The wrapper module uses only standard-library typing plus the existing pure helper import. It does not import network libraries, private API clients, `os`, `pathlib`, `subprocess`, `socket`, `urllib`, or `pydantic`. It does not perform file I/O, network I/O, endpoint calls, environment lookup, config lookup, registry lookup, generated artifact creation, account lookup, balance/position lookup, order/cancel/transfer/withdraw/deposit behavior, alert execution, or Council auto-call.

## Existing System Preservation Gate

- 기존 public adapter → parser → OpportunityPacket → readiness → sampling → handoff → dashboard → Council manual review 흐름을 보존하는가? Yes. Existing pipeline modules were not modified.
- active baseline `cross_exchange_spot_spread_v1` behavior를 바꾸지 않는가? Yes. No active baseline code, config, or registry was modified.
- 기존 experimental strategy status / readiness semantics / dashboard interpretation을 바꾸지 않는가? Yes. No readiness, status, or dashboard files were modified.
- Funding Rate를 기존 공통 모듈에 강제로 섞지 않고 wrapper-only로 추가했는가? Yes. One new wrapper module was added under `src/market_data/`.
- Context-only 정보와 executable signal을 분리하는가? Yes. Wrapper output has `context_only=True`, `readiness_effect="unchanged"`, and tests assert forbidden output keys are absent.
- generated packet/sampling JSON을 만들거나 commit하지 않는가? Yes. No generated JSON was created or committed.
- private API / credential / order / alert / Council auto-call을 추가하지 않는가? Yes. The wrapper has none of those surfaces.
- readiness 변경 없이 wrapper-only로 유지하는가? Yes. Readiness remains unchanged.
- endpoint 호출 없이 mocked fixture와 caller-provided payload만 사용했는가? Yes. Tests read static fixtures and pass payload objects to wrappers; wrappers call only the pure helper.

## No-Trade Compliance

`NO_TRADE_ONLY` is preserved. This PR adds no private endpoints, API keys, secrets, tokens, account/balance/position lookup, order/cancel/transfer/withdraw/deposit behavior, auto-trading, alert execution, Council auto-call, active strategy promotion, endpoint call, live response copy/paste, packet builder mutation, readiness mutation, sampling collector, dashboard automation, config/registry change, or generated artifact.

## Behavior Unchanged

Adapters, packet builders, candidate builders, readiness, sampling, dashboards, configs, registries, fixture JSON, generated data, active baseline behavior, and existing parser helper/tests were not modified. Runtime strategy behavior is unchanged unless a future caller explicitly imports the new wrapper module; no existing caller was modified.

## Generated Artifact Policy

No generated JSON was created or committed under `data/generated_packets` or `data/market_samples`. Tests assert `data/generated_packets/funding_rate_wrappers.json` and `data/market_samples/funding_rate_wrappers.json` do not exist, and the wrapper source does not reference those generated artifact directories.

## Conflict Resolution Evidence

No conflict occurred.

Conflict files: none.

Resolution method: Not applicable. No merge, rebase, or branch switch was performed, and only the Expected Files Changed were created.

GitHub Files changed confirmation requirement: Reviewer must confirm GitHub Files changed exactly matches Expected Files Changed before any merge decision.

## Files Changed

Expected and actual changed files must be exactly:

- `src/market_data/funding_rate_wrappers.py`
- `tests/test_funding_rate_wrappers.py`
- `docs/pr_handoffs/funding_venue_parser_wrapper_implementation_2026_06_11.md`

## Validation

- `git status --short --branch`: passed; staged status showed only the three expected added files on `work`.
- `git diff --cached --name-only`: passed; output listed `docs/pr_handoffs/funding_venue_parser_wrapper_implementation_2026_06_11.md`, `src/market_data/funding_rate_wrappers.py`, and `tests/test_funding_rate_wrappers.py`.
- Expected Files Changed comparison: passed; actual staged files were exactly the same three files as Expected Files Changed.
- `git diff --cached --name-only -- config configs tools data/generated_packets data/market_samples`: passed; output was empty.
- `git diff --cached --name-only -- tests/fixtures`: passed; output was empty.
- `git diff --cached --name-only -- src/market_data/funding_rate_parser.py tests/test_funding_rate_parser.py`: passed; output was empty.
- `find data/generated_packets data/market_samples -type f -name '*.json'`: passed with no generated JSON found; this checkout reports both directories do not exist.
- `git diff --check --cached`: passed with no output.
- `python -m unittest tests.test_funding_rate_wrappers`: passed; output ended with `Ran 17 tests in 0.015s` and `OK`.
- `python -m unittest discover -s tests`: passed; output ended with `Ran 572 tests in 21.218s` and `OK`.

## Merge Recommendation

Codex does not assert this PR is mergeable. GPT designer or human reviewer must inspect GitHub PR Files changed, Expected Files Changed, validation evidence, no-trade compliance, source semantics mapping, wrapper purity, and forbidden-path checks before deciding whether to merge. If GitHub PR Files changed differs from Expected Files Changed, merge must remain on hold.

## Next Recommended Step

The next PR should be Funding Adapter Public Source Planning v0. That future PR must remain public-read-only, context-only, fixture-driven, no-trade-first, and must not add private APIs, credentials, order behavior, readiness changes, packet builder mutation, sampling collectors, dashboards, alerts, Council auto-call, or active promotion.
