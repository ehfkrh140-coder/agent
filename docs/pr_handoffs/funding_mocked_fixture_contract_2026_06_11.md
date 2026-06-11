# Funding Mocked Fixture Contract v0 Handoff

## Summary

This PR is a docs-only mocked fixture contract for `funding_rate_context_v0`. It defines future fixture filenames, pseudo raw payload shapes, required/optional normalized output expectations, parser outcome expectations, warning expectations, future parser test matrix, and context-only guardrails.

This PR does not create fixture JSON files. It does not implement endpoints, adapters, parsers, packet builders, readiness, sampling collectors, generated JSON, alerts, Council auto-call, execution, registry/config changes, or active promotion.

## Inputs Reviewed

Repository documents reviewed:

- `docs/AI_Council_Project_Handoff_v5_Spot_Futures_Depth_VWAP_Dashboard_2026-06-10.md`
- `docs/strategy_module_boundaries.md`
- `docs/pr_handoffs/strategy_module_boundary_map_2026_06_10.md`
- `docs/pr_handoffs/next_experimental_strategy_selection_2026_06_10.md`
- `docs/funding_rate_context_strategy.md`
- `docs/pr_handoffs/funding_rate_context_strategy_planning_2026_06_10.md`
- `docs/pr_handoffs/funding_public_source_research_finalization_2026_06_11.md`
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

This fixture-contract planning update does not change the current baseline or existing strategy behavior.

- Active baseline remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains experimental / non-active / `NO_TRADE_ONLY` with Binance / Bybit / OKX baseline complete.
- `spot_futures_basis_v0` remains proposed / experimental / non-active / `NO_TRADE_ONLY` with Binance + Bybit baseline complete and OKX deferred.
- `usdt_krw_global_reference_v0` remains experimental / non-active / `NO_TRADE_ONLY`.
- `orderbook_imbalance_v0` remains experimental / non-active / `NO_TRADE_ONLY`.
- Depth/VWAP remains diagnostics-only context and does not change readiness.
- `funding_rate_context_v0` remains planning / proposed / experimental / non-active and unimplemented.

No active strategy behavior, execution policy, config, registry, source code, tests, tools, generated data, fixtures, or runtime behavior is changed by this PR.

## Why This Step Comes Before Fixture JSON

The fixture contract comes before fixture JSON so the future fixture-files PR can stay narrow and deterministic. This PR defines:

- Expected fixture filenames and directory policy.
- Required, optional, and edge fixture scope.
- Pseudo raw payload shapes by venue/source.
- Required and optional normalized output expectations.
- Parser status, missing field, and warning expectations.
- Numeric, timestamp, interval, and predicted-vs-realized semantics.
- Context-only and no-trade guardrails.

Without this contract, fixture JSON could accidentally encode live payload assumptions, widen v0 source scope, or imply signal/readiness behavior.

## Fixture Contract Summary

The contract recommends future path `tests/fixtures/market_data/funding_rate/` but creates no files under `tests/fixtures`. It divides future fixtures into:

- Required fixtures for minimum v0 source coverage.
- Optional context fixtures for interval/cap/floor/product/current-predicted context.
- Edge case fixtures for missing fields, numeric parsing, sign coverage, high absolute funding, timestamp watch, varying intervals, and OKX predicted-vs-realized semantics.

## Required Fixture Set

Required future fixture candidates:

- `binance_usdm_funding_rate_history_normal.json`
- `bybit_linear_funding_history_normal.json`
- `okx_funding_rate_history_normal.json`

These represent the finalized `required_primary` sources from Funding Public Source Research Finalization v0: Binance funding history, Bybit funding history, and OKX funding history.

## Optional Fixture Set

Optional context fixture candidates:

- `binance_usdm_funding_info_interval_cap_floor.json`
- `bybit_linear_instruments_info_funding_interval.json`
- `bybit_inverse_funding_history_normal.json`
- `okx_current_funding_rate_normal.json`

These do not block minimum v0 fixture coverage. They provide interval, cap/floor, product metadata, inverse category coverage, current/predicted funding, next funding time, premium, or settlement context.

## Edge Case Fixture Set

Edge case fixture candidates:

- `missing_required_funding_rate.json`
- `missing_optional_interval.json`
- `string_numeric_parsing.json`
- `positive_funding_rate.json`
- `negative_funding_rate.json`
- `zero_funding_rate.json`
- `high_absolute_funding_context.json`
- `timestamp_data_age_clock_skew_watch.json`
- `varying_funding_interval.json`
- `okx_predicted_vs_realized_semantics.json`

These fixtures should validate parser expectations without implying `WATCH`, `ENTER`, active promotion, alerts, Council auto-call, or execution.

## Normalized Output Expectations

Required v0 fields expected from normal required fixtures:

- `venue`
- `instrument_id`
- `instrument_type`
- `symbol_normalized`
- `funding_rate`
- `funding_rate_timestamp_ms`
- `source_endpoint`
- `source_semantics`
- `parser_status`
- `required_missing_fields`

Optional or venue-specific fields:

- `funding_interval_hours`
- `next_funding_time_ms`
- `realized_funding_rate`
- `predicted_funding_rate`
- `funding_cap`
- `funding_floor`
- `mark_price_reference`
- `premium_index_reference`
- `optional_missing_fields`
- `warnings`

Deferred fields for this contract:

- `local_observed_at_ms`
- `data_age_ms`
- `clock_skew_warning`
- `source_payload_timestamp_ms`

Missing required_v0 fields should produce a future failure or `NEED_SOURCE_FIELDS`-style parser status. Missing optional fields should not fail the parser.

## Future Parser Test Matrix

Future parser tests should cover:

- Required Binance history normal fixture parses to parser status OK.
- Required Bybit linear history normal fixture parses to parser status OK.
- Required OKX history normal fixture parses to parser status OK.
- Missing required fundingRate creates `required_missing_fields`.
- Missing optional interval does not fail parser.
- String numeric values parse deterministically.
- Positive / negative / zero funding parse without direction recommendation.
- High absolute funding creates warning/context but no `ENTER`.
- OKX predicted vs realized fields remain separate.
- Timestamp edge fixture preserves timestamp warning expectations.
- Varying interval fixture does not assume 8h hard-code.

No tests are added by this PR.

## Context vs Signal Guardrail

Funding fixtures are context-only test inputs.

- Fixture existence is not a trading signal.
- Fixture existence is not active-promotion evidence.
- Fixture existence is not Council execution permission.
- Funding Rate is not standalone `WATCH`.
- Funding Rate is not standalone `ENTER`.
- Positive funding is not short permission.
- Negative funding is not long permission.
- High absolute funding may be human watch context, but it is not `ENTER`.
- Parser success must not change readiness, `recommended_default_decision`, Council recommendation, active status, alert behavior, or execution behavior.

## Existing System Preservation Gate

| Gate question | Answer | Evidence / decision |
| --- | --- | --- |
| Does this preserve the existing public adapter → parser → OpportunityPacket → readiness → sampling → handoff → dashboard → Council manual review flow? | Yes. | This PR only documents a fixture contract and adds no runtime behavior. |
| Does this avoid changing active baseline `cross_exchange_spot_spread_v1` behavior? | Yes. | No config, registry, source, active strategy, or runtime file is modified. |
| Does this avoid changing existing experimental strategy status, readiness semantics, or dashboard interpretation? | Yes. | Existing strategies remain non-active; readiness and dashboard semantics are unchanged. |
| Does this keep Funding Rate as a fixture-contract / diagnostics-context candidate rather than forcing it into common modules? | Yes. | The contract only scopes future mocked fixture files and parser expectations. |
| Does this separate context-only information from executable signal? | Yes. | Funding fixture data remains context-only and cannot trigger `WATCH`, `ENTER`, alerts, execution, or promotion. |
| Does this avoid fixture JSON creation or commit? | Yes. | No files under `tests/fixtures` were created or modified. |
| Does this avoid generated JSON creation or commit? | Yes. | No generated packet or market-sampling JSON was created or committed. |
| Does this avoid private API, credentials, orders, alerts, or Council auto-call? | Yes. | This PR is docs-only and does not add private endpoints, secrets, account lookup, orders, alerts, execution, or Council auto-call. |
| Does this remain fixture-contract docs-only with no readiness change? | Yes. | No readiness code or semantics were changed. |
| Was this based on existing official-docs research with no endpoint calls? | Yes. | It uses prior source-finalization docs and calls no exchange endpoints. |

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
- Funding Rate fixture JSON.
- Funding Rate adapter, parser, packet-builder, readiness, or sampling collector implementation.
- VWAP-adjusted readiness implementation.

## Behavior Unchanged

Runtime behavior is unchanged. This PR only adds planning documentation.

No files under `src/`, `tests/`, `config/`, `configs/`, `tools/`, `data/generated_packets/`, `data/market_samples/`, or `tests/fixtures/` were modified. No registry/config/active strategy file was modified. The active strategy remains `cross_exchange_spot_spread_v1`; all experimental and future strategies remain non-active unless a separate approved PR changes status.

## Generated Artifact Policy

No fixture JSON and no generated packet or market-sampling JSON was created or committed. Generated JSON remains a smoke artifact and is not source-of-truth for dashboard or handoff evidence.

## Files Changed

Expected and actual changed files:

- `docs/funding_rate_mocked_fixture_contract.md`
- `docs/pr_handoffs/funding_mocked_fixture_contract_2026_06_11.md`

No other files are part of this PR.

## Validation

Validation commands required for this docs-only PR:

- `git status --short --branch`
- `git diff --cached --name-only`
- Expected Files Changed comparison
- `git diff --cached --name-only -- src tests config configs tools data/generated_packets data/market_samples`
- `find data/generated_packets data/market_samples -type f -name '*.json'`
- `find tests/fixtures -path '*funding*' -type f`
- `git diff --check --cached`
- `python -m unittest discover -s tests`

Validation result summary:

- Fresh `origin/main` branch creation was attempted but could not complete because GitHub fetch failed in this environment with `CONNECT tunnel failed, response 403`.
- Work was performed on `docs/funding-mocked-fixture-contract-v0` from the available repository state.
- Expected Files Changed matched staged files exactly.
- Forbidden source/test/config/tool/generated-data paths were not modified.
- No funding fixture JSON was created under `tests/fixtures`.
- No generated JSON artifact was created or committed.
- `git diff --check --cached` passed.
- Full unittest discovery passed: `Ran 531 tests in 15.508s`, `OK`.

## Next Recommended Step

Recommended next PR: `Funding Mocked Fixture Files v0`.

The next PR should add only deterministic mocked fixture JSON files under the agreed fixture path. It must remain public-read-only / context-only / no-trade-first. It must not call live endpoints, add private API, implement adapters/parsers/packet builders/readiness/sampling collectors, create generated market samples, trigger alerts, call Council automatically, or promote any strategy.
