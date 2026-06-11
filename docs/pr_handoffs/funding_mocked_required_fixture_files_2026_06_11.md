# Funding Mocked Required Fixture Files v0 Handoff

## Summary

This PR adds only the three required deterministic mocked Funding Rate fixture JSON files agreed in `docs/funding_rate_mocked_fixture_contract.md`, plus this handoff evidence file.

This PR does not add optional fixtures, edge fixtures, parser code, adapter code, packet builder code, readiness code, sampling collectors, generated market samples, live endpoint calls, alerts, Council auto-call, execution behavior, registry/config changes, or active promotion.

## Inputs Reviewed

Repository documents reviewed:

- `docs/AI_Council_Project_Handoff_v5_Spot_Futures_Depth_VWAP_Dashboard_2026-06-10.md`
- `docs/strategy_module_boundaries.md`
- `docs/pr_handoffs/strategy_module_boundary_map_2026_06_10.md`
- `docs/pr_handoffs/next_experimental_strategy_selection_2026_06_10.md`
- `docs/funding_rate_context_strategy.md`
- `docs/pr_handoffs/funding_rate_context_strategy_planning_2026_06_10.md`
- `docs/pr_handoffs/funding_public_source_research_finalization_2026_06_11.md`
- `docs/funding_rate_mocked_fixture_contract.md`
- `docs/pr_handoffs/funding_mocked_fixture_contract_2026_06_11.md`
- `docs/strategy_evidence_dashboard.md`
- `AGENTS.md`
- `docs/no_trade_policy.md`
- `docs/pr_handoffs/README.md`
- `docs/merge_gate.md`
- `docs/rollback_policy.md`
- `docs/task_checklist.md`
- `docs/agent_workflow.md`

Operational note: a fresh `origin/main` branch was attempted first, but this environment could not fetch GitHub because the network request failed with `CONNECT tunnel failed, response 403`. Work proceeded on a scoped branch from the available repository state, and this limitation is recorded here for reviewer awareness.

## Current Baseline Preservation

This required-fixture update does not change the current baseline or existing strategy behavior.

- Active baseline remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains experimental / non-active / `NO_TRADE_ONLY` with Binance / Bybit / OKX baseline complete.
- `spot_futures_basis_v0` remains proposed / experimental / non-active / `NO_TRADE_ONLY` with Binance + Bybit baseline complete and OKX deferred.
- `usdt_krw_global_reference_v0` remains experimental / non-active / `NO_TRADE_ONLY`.
- `orderbook_imbalance_v0` remains experimental / non-active / `NO_TRADE_ONLY`.
- Depth/VWAP remains diagnostics-only context and does not change readiness.
- `funding_rate_context_v0` remains planning / proposed / experimental / non-active and parser-unimplemented.

No active strategy behavior, execution policy, config, registry, source code, test code, tools, generated data, or runtime behavior is changed by this PR.

## Why Required Fixtures First

Required normal fixtures come before optional and edge fixtures because they provide the narrowest deterministic coverage for the finalized `required_primary` public source candidates:

- Binance funding history.
- Bybit linear funding history.
- OKX funding history.

Starting with these three normal fixtures keeps the first fixture-files PR small, reviewable, and aligned with the minimum v0 source contract. Optional context fixtures and edge fixtures are intentionally deferred so they do not broaden scope before parser expectations are reviewed.

## Files Added

- `tests/fixtures/market_data/funding_rate/binance_usdm_funding_rate_history_normal.json`
- `tests/fixtures/market_data/funding_rate/bybit_linear_funding_history_normal.json`
- `tests/fixtures/market_data/funding_rate/okx_funding_rate_history_normal.json`
- `docs/pr_handoffs/funding_mocked_required_fixture_files_2026_06_11.md`

No optional fixture files and no edge fixture files were added.

## Fixture Data Policy

The fixture data is deterministic fake data.

- No live endpoint was called.
- No live exchange response was copied.
- No private API, API key, account endpoint, balance endpoint, position endpoint, order endpoint, or execution endpoint was used.
- Values are small, fixed, and human-readable.
- Timestamps are fixed values, not live current timestamps.
- `fundingRate` and price/reference values are string numerics where expected.
- Each fixture includes at least two records so future parsers can test list iteration.
- These are static test fixtures, not generated packet/sampling artifacts.

## Binance Fixture Summary

Fixture: `tests/fixtures/market_data/funding_rate/binance_usdm_funding_rate_history_normal.json`

- Represented endpoint: Binance USDⓈ-M Futures `GET /fapi/v1/fundingRate`.
- Shape: top-level array/list of funding history records.
- Required raw fields included per record: `symbol`, `fundingRate`, `fundingTime`, `markPrice`.
- Record count: 2 deterministic fake records.
- Expected future normalized required_v0 fields: `venue`, `instrument_id`, `instrument_type`, `symbol_normalized`, `funding_rate`, `funding_rate_timestamp_ms`, `source_endpoint`, `source_semantics`, `parser_status`, `required_missing_fields`.
- Expected source semantics: `historical_funding_charge_record`.
- Guardrail: `markPrice` is funding-record attached mark reference, not executable price.

## Bybit Fixture Summary

Fixture: `tests/fixtures/market_data/funding_rate/bybit_linear_funding_history_normal.json`

- Represented endpoint: Bybit V5 `GET /v5/market/funding/history`.
- Shape: Bybit V5 response-style object with `retCode`, `retMsg`, `result.category`, `result.list`, and `time`.
- Category: `linear`; category must not be collapsed with inverse products.
- Required raw fields included per record: `symbol`, `fundingRate`, `fundingRateTimestamp`.
- Record count: 2 deterministic fake records.
- Expected future normalized required_v0 fields: `venue`, `instrument_id`, `instrument_type`, `symbol_normalized`, `funding_rate`, `funding_rate_timestamp_ms`, `source_endpoint`, `source_semantics`, `parser_status`, `required_missing_fields`.
- Expected source semantics: `settled_historical_funding_context`.
- Guardrail: `linear` category and funding sign are context only, not direction recommendation.

## OKX Fixture Summary

Fixture: `tests/fixtures/market_data/funding_rate/okx_funding_rate_history_normal.json`

- Represented endpoint: OKX `GET /api/v5/public/funding-rate-history`.
- Shape: OKX public API response-style object with `code`, `msg`, and `data` list.
- Required raw fields included per record: `instType`, `instId`, `fundingRate`, `fundingTime`.
- Optional raw fields included per record: `realizedRate`, `method`, `formulaType`.
- Record count: 2 deterministic fake records.
- Expected future normalized required_v0 fields: `venue`, `instrument_id`, `instrument_type`, `symbol_normalized`, `funding_rate`, `funding_rate_timestamp_ms`, `source_endpoint`, `source_semantics`, `parser_status`, `required_missing_fields`.
- Expected source semantics: `historical_funding_context`.
- Guardrail: `fundingRate` and `realizedRate` must not be collapsed; both are context only.

## JSON Validation Evidence

Commands run and results:

- `python -m json.tool tests/fixtures/market_data/funding_rate/binance_usdm_funding_rate_history_normal.json` → passed (`binance json.tool: OK`).
- `python -m json.tool tests/fixtures/market_data/funding_rate/bybit_linear_funding_history_normal.json` → passed (`bybit json.tool: OK`).
- `python -m json.tool tests/fixtures/market_data/funding_rate/okx_funding_rate_history_normal.json` → passed (`okx json.tool: OK`).
- Python `json.load` validation for all 3 fixtures passed:
  - `tests/fixtures/market_data/funding_rate/binance_usdm_funding_rate_history_normal.json: json.load OK (list)`
  - `tests/fixtures/market_data/funding_rate/bybit_linear_funding_history_normal.json: json.load OK (dict)`
  - `tests/fixtures/market_data/funding_rate/okx_funding_rate_history_normal.json: json.load OK (dict)`

## Test Evidence Standard

GitHub Checks / CI: independent verification unavailable in this local Codex PR creation environment.

Codex/local validation commands were run and recorded in this handoff. Full unittest discovery was run locally with `python -m unittest discover -s tests` and passed.

## Context vs Signal Guardrail

Funding fixtures are context-only static test data.

- Funding fixture existence is not a trading signal.
- Funding fixture existence is not active-promotion evidence.
- Funding fixture existence is not Council execution permission.
- Funding Rate is not standalone `WATCH`.
- Funding Rate is not standalone `ENTER`.
- Positive funding values are not short permission.
- Negative funding values are not long permission.
- JSON validity is not readiness success and not a trade signal.
- Future parser success is not readiness success or trade signal unless a separate explicitly approved policy changes that boundary.
- Fixtures must not trigger alerts, Council auto-call, orders, transfers, withdrawals, deposits, auto-trading, or execution.

## Existing System Preservation Gate

| Gate question | Answer | Evidence / decision |
| --- | --- | --- |
| Does this preserve the existing public adapter → parser → OpportunityPacket → readiness → sampling → handoff → dashboard → Council manual review flow? | Yes. | This PR only adds static required fixture JSON and a handoff document; it adds no runtime flow. |
| Does this avoid changing active baseline `cross_exchange_spot_spread_v1` behavior? | Yes. | No config, registry, source, active strategy, or runtime file is modified. |
| Does this avoid changing existing experimental strategy status, readiness semantics, or dashboard interpretation? | Yes. | Existing strategies remain non-active; readiness and dashboard semantics are unchanged. |
| Does this keep Funding Rate as required mocked fixture data rather than forcing it into common modules? | Yes. | Only static fixture files are added; no parser/model/common module is touched. |
| Does this separate context-only information from executable signal? | Yes. | Fixture values are documented as context only and not direction recommendations. |
| Did this avoid optional/edge fixtures in this PR? | Yes. | Only the 3 required normal fixtures were added. |
| Does this avoid generated packet/sampling JSON creation or commit? | Yes. | `data/generated_packets` and `data/market_samples` were not modified. |
| Does this avoid private API, credentials, orders, alerts, or Council auto-call? | Yes. | No private endpoint, secret, account lookup, order, alert, execution, or Council auto-call was added. |
| Does this remain fixture-files-only with no readiness change? | Yes. | No readiness code or semantics were changed. |
| Was this deterministic mocked data with no endpoint calls? | Yes. | Fixture values are fixed fake values; no live endpoint was called. |

## No-Trade Compliance

`NO_TRADE_ONLY` is preserved.

This PR adds no:

- Private API.
- API key, secret, token, OAuth token, bot token, or webhook secret.
- Account, balance, or position lookup.
- Order placement or cancellation.
- Withdrawal, deposit, or transfer behavior.
- Auto-trading or execution engine.
- Alert execution.
- Council auto-call.
- Council decision to trade conversion.
- Active strategy promotion.
- Funding Rate endpoint calls.
- Funding Rate adapter, parser, packet-builder, readiness, or sampling collector implementation.
- VWAP-adjusted readiness implementation.

## Behavior Unchanged

Runtime behavior is unchanged.

No files under `src/`, `config/`, `configs/`, `tools/`, `data/generated_packets/`, or `data/market_samples/` were modified. No test Python code was modified. The only `tests/` changes are the 3 allowed static fixture JSON files under `tests/fixtures/market_data/funding_rate/`.

The active strategy remains `cross_exchange_spot_spread_v1`; all experimental and future strategies remain non-active unless a separate approved PR changes status.

## Generated Artifact Policy

No generated packet JSON or market-sampling JSON was created or committed under `data/generated_packets` or `data/market_samples`.

The 3 JSON files in this PR are deterministic static test fixtures under `tests/fixtures/market_data/funding_rate/`. They are not generated packet/sampling artifacts and are not live endpoint outputs.

## Files Changed

Expected and actual changed files:

- `tests/fixtures/market_data/funding_rate/binance_usdm_funding_rate_history_normal.json`
- `tests/fixtures/market_data/funding_rate/bybit_linear_funding_history_normal.json`
- `tests/fixtures/market_data/funding_rate/okx_funding_rate_history_normal.json`
- `docs/pr_handoffs/funding_mocked_required_fixture_files_2026_06_11.md`

No other files are part of this PR.

## Validation

Validation commands required for this PR:

- `git status --short --branch`
- `git diff --cached --name-only`
- Expected Files Changed comparison
- `python -m json.tool tests/fixtures/market_data/funding_rate/binance_usdm_funding_rate_history_normal.json`
- `python -m json.tool tests/fixtures/market_data/funding_rate/bybit_linear_funding_history_normal.json`
- `python -m json.tool tests/fixtures/market_data/funding_rate/okx_funding_rate_history_normal.json`
- Python `json.load` validation for all 3 fixtures
- `git diff --cached --name-only -- src config configs tools data/generated_packets data/market_samples`
- `git diff --cached --name-only -- tests`
- `find data/generated_packets data/market_samples -type f -name '*.json'`
- `find tests/fixtures/market_data/funding_rate -type f -name '*.json' | sort`
- `git diff --check --cached`
- `python -m unittest discover -s tests`

Validation result summary:

- Fresh `origin/main` branch creation was attempted but could not complete because GitHub fetch failed in this environment with `CONNECT tunnel failed, response 403`.
- Work was performed on `docs/funding-mocked-required-fixture-files-v0` from the available repository state.
- Expected Files Changed set matched staged files exactly: `Expected Files Changed set match: True`.
- `python -m json.tool` passed for all 3 fixture JSON files.
- Python `json.load` passed for all 3 fixture JSON files.
- Forbidden source/config/tool/generated-data paths were not modified.
- `git diff --cached --name-only -- tests` contained only the 3 allowed fixture JSON files.
- `find data/generated_packets data/market_samples -type f -name '*.json'` produced no generated JSON files.
- `find tests/fixtures/market_data/funding_rate -type f -name '*.json' | sort` listed exactly the 3 required fixture files.
- `git diff --check --cached` passed.
- Full unittest discovery passed: `Ran 531 tests in 14.940s`, `OK`.

## Next Recommended Step

Recommended next PR: `Funding Optional / Edge Fixture Files v0`.

Reason: after required normal fixtures exist, the next narrow fixture-only step should add optional context and edge fixtures defined in `docs/funding_rate_mocked_fixture_contract.md`. Parser implementation should still wait until fixture coverage is reviewed.

The next PR must remain public-read-only / context-only / no-trade-first. It must not call live endpoints, copy live responses, add private API, implement adapters/parsers/packet builders/readiness/sampling collectors, create generated market samples, trigger alerts, call Council automatically, or promote any strategy.
