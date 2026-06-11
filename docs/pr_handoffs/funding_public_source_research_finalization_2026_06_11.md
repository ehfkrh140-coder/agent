# Funding Public Source Research Finalization v0 Handoff

## Summary

This PR is a docs-only official-source research finalization for `funding_rate_context_v0`. It finalizes the public source candidates, classifies each source as `required_primary` or `optional_context`, narrows the minimum v0 source contract, documents predicted-vs-realized semantics, records funding interval and pagination/rate-limit policy, and recommends the next fixture contract PR.

This PR does not call endpoints, implement adapters, implement parsers, implement packet builders, change readiness, add sampling collectors, generate JSON, change configs/registry, trigger alerts, call Council automatically, or promote any strategy.

## Inputs Reviewed

Repository documents reviewed:

- `docs/AI_Council_Project_Handoff_v5_Spot_Futures_Depth_VWAP_Dashboard_2026-06-10.md`
- `docs/strategy_module_boundaries.md`
- `docs/pr_handoffs/strategy_module_boundary_map_2026_06_10.md`
- `docs/pr_handoffs/next_experimental_strategy_selection_2026_06_10.md`
- `docs/funding_rate_context_strategy.md`
- `docs/pr_handoffs/funding_rate_context_strategy_planning_2026_06_10.md`
- `docs/strategy_evidence_dashboard.md`
- `AGENTS.md`
- `docs/no_trade_policy.md`
- `docs/pr_handoffs/README.md`
- `docs/merge_gate.md`
- `docs/rollback_policy.md`
- `docs/task_checklist.md`
- `docs/agent_workflow.md`

Official exchange documentation reviewed for source research only:

- Binance USDⓈ-M Futures — Get Funding Rate History, `GET /fapi/v1/fundingRate`.
- Binance USDⓈ-M Futures — Get Funding Info, `GET /fapi/v1/fundingInfo`.
- Bybit V5 Market — Get Funding Rate History, `GET /v5/market/funding/history`.
- Bybit V5 Market — Get Instruments Info, `GET /v5/market/instruments-info`.
- OKX Public Data REST API — Get funding rate, `GET /api/v5/public/funding-rate`.
- OKX Public Data REST API — Get funding rate history, `GET /api/v5/public/funding-rate-history`.

No exchange endpoint was called. The official docs were used only as documentation references.

Operational note: a fresh `origin/main` branch was attempted first, but this environment could not fetch GitHub because the network request failed with `CONNECT tunnel failed, response 403`. Work proceeded on a scoped branch from the available repository state, and this limitation is recorded here for reviewer awareness.

## Current Baseline Preservation

This research finalization does not change the current baseline or existing strategy behavior.

- Active baseline remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains experimental / non-active / `NO_TRADE_ONLY` with Binance / Bybit / OKX baseline complete.
- `spot_futures_basis_v0` remains proposed / experimental / non-active / `NO_TRADE_ONLY` with Binance + Bybit baseline complete and OKX deferred.
- `usdt_krw_global_reference_v0` remains experimental / non-active / `NO_TRADE_ONLY`.
- `orderbook_imbalance_v0` remains experimental / non-active / `NO_TRADE_ONLY`.
- Depth/VWAP remains diagnostics-only context and does not change readiness.
- `funding_rate_context_v0` remains planning / proposed / experimental / non-active and unimplemented.

No active strategy behavior, execution policy, config, registry, source code, tests, tools, generated data, or runtime behavior is changed by this PR.

## Why This Step Comes Before Fixtures

This step comes before fixture creation because fixture contracts should not guess source semantics. Before writing deterministic mocked payloads, reviewers need agreement on:

- Which official public sources are required vs optional.
- Which fields are required for minimum v0 parser fixtures.
- Whether interval/cap/floor/current funding context blocks minimum fixtures.
- How predicted/current funding differs from historical/realized/settled funding.
- How pagination and rate-limit assumptions should shape future collectors without calling live endpoints.
- Which warnings should preserve ambiguity instead of silently coercing venue semantics.

This keeps the next fixture PR narrow, public-read-only, context-only, deterministic, and no-trade compliant.

## Public Source Finalization Summary

- Binance `GET /fapi/v1/fundingRate` is finalized as `required_primary` for minimum funding history fixtures.
- Binance `GET /fapi/v1/fundingInfo` is finalized as `optional_context` for cap/floor/interval context.
- Bybit `GET /v5/market/funding/history` is finalized as `required_primary` for minimum funding history fixtures.
- Bybit `GET /v5/market/instruments-info` is finalized as `optional_context` for funding interval, product metadata, and cap/floor context.
- OKX `GET /api/v5/public/funding-rate-history` is finalized as `required_primary` for minimum OKX historical funding fixtures.
- OKX `GET /api/v5/public/funding-rate` is finalized as `optional_context` for current/predicted funding, next funding time, interval delta, cap/floor, settlement, and premium context.

## Source Classification Decision Table

| classification | sources | reason |
| --- | --- | --- |
| `required_primary` | Binance `GET /fapi/v1/fundingRate`; Bybit `GET /v5/market/funding/history`; OKX `GET /api/v5/public/funding-rate-history` | These are the narrow official public history sources needed to create minimum v0 fixtures for each venue. |
| `optional_context` | Binance `GET /fapi/v1/fundingInfo`; Bybit `GET /v5/market/instruments-info`; OKX `GET /api/v5/public/funding-rate` | These add interval, cap/floor, product metadata, current/predicted, settlement, premium, or next-funding context, but should not block minimum history fixtures. |
| `deferred_research` | Premium-index endpoints, mark-price endpoints, open-interest/long-short/liquidation sources, broader derivatives-flow sources | Useful later but outside the narrow funding source finalization scope. |
| `rejected_for_now` | Private/account/order/position endpoints, private funding-fee account history, execution/trade endpoints, alert/webhook integrations, third-party aggregated vendor APIs | They violate or complicate the public-read-only, no-trade-first, official-docs-only scope for v0. |

## Minimum v0 Source Contract

Required v0 fields:

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

Optional v0 fields:

- `optional_missing_fields`
- `warnings`
- `funding_interval_hours`
- `source_payload_timestamp_ms`

Venue-specific optional fields:

- `next_funding_time_ms`
- `realized_funding_rate`
- `predicted_funding_rate`
- `funding_cap`
- `funding_floor`
- `mark_price_reference`
- `premium_index_reference`

Deferred fields:

- `local_observed_at_ms`
- `data_age_ms`
- `clock_skew_warning`

Rejected for now: none of the drafted normalized fields are rejected for now, but private/account/execution-derived fields remain rejected outside this contract.

## Predicted vs Realized Funding Policy

- In v0, normalized `funding_rate` means the primary funding value emitted by the selected source record and must always be interpreted with `source_semantics`.
- Predicted/current funding and realized/settled funding remain separate optional fields when a source exposes both.
- Ambiguous venue history semantics should be preserved in `warnings`; parsers must not silently coerce predicted/current/settled/realized meanings.
- OKX current endpoint: `fundingRate` / `nextFundingRate` are current/predicted context candidates, while `settFundingRate` is settlement context.
- OKX history endpoint: `realizedRate` and `fundingRate` stay separate until fixture/parser naming is finalized.
- Bybit funding history `fundingRate` is treated as settled historical context for v0 planning, with a warning hook for ambiguity.
- Binance funding history `fundingRate` is treated as funding-fee charge record context at `fundingTime`; `markPrice` remains funding-record attached mark reference only.

## Funding Interval Policy

- Do not hard-code 8 hours across all venues or symbols.
- Binance `fundingInfo.fundingIntervalHours` is optional context.
- Bybit `instruments-info.fundingInterval` is optional context and should be converted from minutes to hours when used.
- OKX current `fundingTime` / `nextFundingTime` delta can be used as optional interval context.
- Missing interval should not fail v0 normal history fixtures; record it in `optional_missing_fields` or `warnings`.
- `funding_interval_hours` is not required in minimum v0 fixtures.

## Pagination and Rate-Limit Notes

- Binance `GET /fapi/v1/fundingRate`: `startTime` and `endTime` are inclusive; `limit` defaults to 100 and maxes at 1000; no time params returns recent records; results are ascending; rate-limit is shared 500/5min/IP with funding info.
- Binance `GET /fapi/v1/fundingInfo`: no request parameters documented; request weight 0; shares 500/5min/IP with funding history.
- Bybit `GET /v5/market/funding/history`: `limit` range 1-200, default 200; passing only `startTime` returns an error; only `endTime` returns up to 200 records up to `endTime`; neither returns 200 records up to current time.
- Bybit `GET /v5/market/instruments-info`: default returns 500 entries; `limit` range 1-1000; linear symbols can exceed 500 and require cursor/`nextPageCursor` pagination.
- OKX `GET /api/v5/public/funding-rate`: current point-in-time endpoint; no history pagination; official public-data rate-limit detail should be rechecked before implementation.
- OKX `GET /api/v5/public/funding-rate-history`: uses `before`, `after`, and `limit`; pagination should be based on `fundingTime`; history window and exact rate-limit wording should be rechecked before implementation.

## Fixture Contract Recommendation

Required fixture candidates for next PR:

- `binance_usdm_funding_rate_history_normal.json`
- `bybit_linear_funding_history_normal.json`
- `okx_funding_rate_history_normal.json`

Optional context fixture candidates:

- `binance_usdm_funding_info_interval_cap_floor.json`
- `bybit_linear_instruments_info_funding_interval.json`
- `bybit_inverse_funding_history_normal.json`
- `okx_current_funding_rate_normal.json`

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

The next PR should create mocked fixtures only, not live source outputs or generated JSON.

## Context vs Signal Guardrail

Funding Rate is context-only.

- Funding Rate is not an entry signal.
- Funding Rate is not a standalone `WATCH` trigger.
- Funding Rate is not a standalone `ENTER` trigger.
- Funding Rate is not active-promotion evidence.
- Positive funding is not short permission.
- Negative funding is not long permission.
- High absolute funding may be watch context for humans, but it is not `ENTER`.
- Funding Rate must not trigger alerts, Council auto-call, orders, transfers, withdrawals, deposits, auto-trading, or execution.
- Funding Rate must not change readiness without a separate approved policy PR.

## Existing System Preservation Gate

| Gate question | Answer | Evidence / decision |
| --- | --- | --- |
| Does this preserve the existing public adapter → parser → OpportunityPacket → readiness → sampling → handoff → dashboard → Council manual review flow? | Yes. | This PR only finalizes official source research and does not add runtime behavior. |
| Does this avoid changing active baseline `cross_exchange_spot_spread_v1` behavior? | Yes. | No config, registry, source, or active strategy file is modified. |
| Does this avoid changing existing experimental strategy status, readiness semantics, or dashboard interpretation? | Yes. | Existing strategies remain non-active; readiness and dashboard semantics are unchanged. |
| Does this keep Funding Rate as a source-contract / diagnostics-context candidate rather than forcing it into common modules? | Yes. | The finalization narrows sources and fields for future fixtures only. |
| Does this separate context-only information from executable signal? | Yes. | Funding Rate remains context / diagnostics / regime information only. |
| Does this avoid generated JSON creation or commit? | Yes. | No generated packet or market-sampling JSON was created or committed. |
| Does this avoid private API, credentials, orders, alerts, or Council auto-call? | Yes. | The sources are official public docs candidates only; no private endpoint, credential, order, alert, execution, or Council auto-call was added. |
| Does this remain research-finalization docs-only with no readiness change? | Yes. | No readiness code or semantics were changed. |
| Was this official-docs research only, with no endpoint calls? | Yes. | Official documentation was reviewed; no exchange endpoint was called. |

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

Runtime behavior is unchanged. This PR only updates planning documentation.

No files under `src/`, `tests/`, `config/`, `configs/`, `tools/`, `data/generated_packets/`, or `data/market_samples/` were modified. No registry/config/active strategy file was modified. The active strategy remains `cross_exchange_spot_spread_v1`; all experimental and future strategies remain non-active unless a separate approved PR changes status.

## Generated Artifact Policy

No generated packet JSON or market-sampling JSON was created or committed. Generated JSON remains a smoke artifact and is not source-of-truth for dashboard or handoff evidence.

## Files Changed

Expected and actual changed files:

- `docs/funding_rate_context_strategy.md`
- `docs/pr_handoffs/funding_public_source_research_finalization_2026_06_11.md`

No other files are part of this PR.

## Validation

Validation commands required for this docs-only PR:

- `git status --short --branch`
- `git diff --cached --name-only`
- `git diff --cached --name-only -- src tests config configs tools data/generated_packets data/market_samples`
- `find data/generated_packets data/market_samples -type f -name '*.json'`
- `git diff --check --cached`
- `python -m unittest discover -s tests`

Validation result summary:

- Fresh `origin/main` branch creation was attempted but could not complete because GitHub fetch failed in this environment with `CONNECT tunnel failed, response 403`.
- Work was performed on `docs/funding-public-source-research-finalization-v0` from the available repository state.
- Expected Files Changed matched staged files exactly.
- Forbidden source/test/config/tool/generated-data paths were not modified.
- No generated JSON artifact was created or committed.
- `git diff --check --cached` passed.
- Full unittest discovery passed: `Ran 531 tests in 15.321s`, `OK`.

## Next Recommended Step

Recommended next PR: `Funding Mocked Fixture Contract v0`.

The next PR should add only deterministic mocked fixture contracts for the required/optional/edge fixture candidates, and it must remain public-read-only / context-only / no-trade-first. It must not call live endpoints, add private API, implement adapters/parsers/packet builders/readiness/sampling collectors, create generated market samples, trigger alerts, call Council automatically, or promote any strategy.
