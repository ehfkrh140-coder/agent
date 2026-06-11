# Funding Rate Context Strategy Planning v0 Handoff

## Summary

This PR is a docs-only planning update for `funding_rate_context_v0`. It designs public-read-only source options, common source-contract fields, context-only semantics, fixture planning, parser/adapter planning, dashboard semantics, and no-trade guardrails before any implementation work.

This PR does not implement Funding Rate endpoints, parsers, adapters, packet builders, readiness logic, sampling collectors, dashboard automation, alerts, Council auto-call, execution, registry/config changes, or active promotion.

## Inputs Reviewed

The following repository documents were reviewed:

- `docs/AI_Council_Project_Handoff_v5_Spot_Futures_Depth_VWAP_Dashboard_2026-06-10.md`
- `docs/strategy_module_boundaries.md`
- `docs/pr_handoffs/strategy_module_boundary_map_2026_06_10.md`
- `docs/pr_handoffs/next_experimental_strategy_selection_2026_06_10.md`
- `docs/strategy_evidence_dashboard.md`
- `AGENTS.md`
- `docs/no_trade_policy.md`
- `docs/pr_handoffs/README.md`
- `docs/merge_gate.md`
- `docs/rollback_policy.md`
- `docs/task_checklist.md`
- `docs/agent_workflow.md`

Official public documentation consulted for source-option planning only:

- Binance USDⓈ-M Futures funding history: <https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History>
- Binance USDⓈ-M Futures funding info: <https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-Info>
- Bybit V5 funding history: <https://bybit-exchange.github.io/docs/v5/market/history-fund-rate>
- Bybit V5 instruments info: <https://bybit-exchange.github.io/docs/v5/market/instrument>
- OKX public data REST API docs: <https://www.okx.com/docs-v5/en/>
- OKX funding formula/change-log notes: <https://www.okx.com/docs-v5/log_en/>

No endpoint was called.

Operational note: a fresh `origin/main` branch was attempted first, but this environment could not fetch GitHub because the network request failed with `CONNECT tunnel failed, response 403`. Work proceeded on a scoped branch from the available repository state, and this limitation is recorded here for reviewer awareness.

## Current Baseline Preservation

This planning update does not change the current baseline or existing strategy behavior.

- Active baseline remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains experimental / non-active / `NO_TRADE_ONLY` with Binance / Bybit / OKX baseline complete.
- `spot_futures_basis_v0` remains proposed / experimental / non-active / `NO_TRADE_ONLY` with Binance + Bybit baseline complete and OKX deferred.
- `usdt_krw_global_reference_v0` remains experimental / non-active / `NO_TRADE_ONLY`.
- `orderbook_imbalance_v0` remains experimental / non-active / `NO_TRADE_ONLY`.
- Depth/VWAP remains diagnostics-only context and does not change readiness.
- `funding_rate_context_v0` remains planning / proposed / experimental / non-active and unimplemented.

No active strategy behavior, execution policy, config, registry, source code, tests, tools, generated data, or runtime behavior is changed by this PR.

## Why Funding Rate Starts as Context

Funding Rate starts as context because it describes perpetual-market regime, crowding, and carry pressure, but it is not an executable price or an instruction to trade.

A funding rate can be positive, negative, zero, capped, floored, predicted, realized, stale, or unusually large in absolute value. Those states may help reviewers understand derivatives-market conditions, but they do not prove spot/futures edge, fill feasibility, persistence, or safe execution.

Therefore:

- Funding Rate is not an entry signal.
- Funding Rate is not a standalone `WATCH` trigger.
- Funding Rate is not a standalone `ENTER` trigger.
- Funding Rate is not active-promotion evidence.
- Funding Rate starts only as context / diagnostics / regime information.
- Funding Rate may only be reviewed as auxiliary context for `spot_futures_basis_v0`, `mark_orderbook_gap_hunt_v0`, or future derivatives-oriented strategy families.

## Public Source Candidates

Planning-only public source candidates:

| venue | source candidates | planning summary |
| --- | --- | --- |
| Binance USDⓈ-M Futures | `GET /fapi/v1/fundingRate`; `GET /fapi/v1/fundingInfo` | Funding history provides `symbol`, `fundingRate`, `fundingTime`, and `markPrice`; funding info provides adjusted cap/floor and `fundingIntervalHours` context. Funding info should remain interval/cap/floor context, not a trade signal. |
| Bybit V5 | `GET /v5/market/funding/history`; `GET /v5/market/instruments-info` | Funding history provides `category`, `symbol`, `fundingRate`, and `fundingRateTimestamp`; `category` must distinguish `linear` vs `inverse`. Instruments info is a candidate for funding interval and cap/floor context. |
| OKX | `GET /api/v5/public/funding-rate`; `GET /api/v5/public/funding-rate-history` | Current funding and history must separate predicted/current funding, realized/settled funding, `fundingTime`, `nextFundingTime`, premium, method, and formula semantics. Do not assume a fixed 8h interval. |

No public endpoint was called in this PR.

## Common Source Contract Summary

`docs/funding_rate_context_strategy.md` drafts a normalized funding context contract and plugin/context placement with these candidate fields:

- Core identity: `venue`, `instrument_id`, `instrument_type`, `symbol_normalized`.
- Funding values: `funding_rate`, `realized_funding_rate`, `predicted_funding_rate`, `funding_cap`, `funding_floor`.
- Time and interval fields: `funding_rate_timestamp_ms`, `funding_interval_hours`, `next_funding_time_ms`, `source_payload_timestamp_ms`, `local_observed_at_ms`, `data_age_ms`, `clock_skew_warning`.
- Reference/context fields: `mark_price_reference`, `premium_index_reference`.
- Source and parser metadata: `source_endpoint`, `source_semantics`, `parser_status`, `required_missing_fields`, `optional_missing_fields`, `warnings`.

This is documentation only. No code field, schema, parser, model, runtime plugin, packet extension, or sampling field is added by this PR. The plugin metadata remains a planning draft with `NO_TRADE_ONLY`, `standalone_signal_allowed=false`, `readiness_changes_allowed=false`, `alert_allowed=false`, and `private_api_allowed=false`.

## Venue Semantics Summary

- Binance `fundingRate` history and `markPrice` must be treated as funding record context; the mark price is not executable. `fundingInfo` is interval/cap/floor context only.
- Bybit `category` is required and must preserve `linear` vs `inverse` product semantics. Funding interval is investigated through `instruments-info` rather than assumed.
- OKX current funding and history fields require explicit separation between predicted/current funding, realized/settled funding, funding timestamps, next funding timestamps, premium, method, and formula type.
- Funding interval must be derived from explicit venue fields or timestamp differences. It must not be globally hard-coded to 8 hours.

## Context vs Signal Guardrail

Funding Rate is context-only.

It must not automatically change:

- Readiness status.
- `recommended_default_decision`.
- Estimated net gap, spread, or basis.
- Persistence status.
- Council recommendation.
- Dashboard interpretation.
- Active strategy status.
- Alert behavior.
- Execution behavior.

High absolute funding can be a watch context for humans, but it is not a standalone `WATCH`, not `ENTER`, not active-promotion evidence, and not an instruction to submit orders.

## Existing System Preservation Gate

| Gate question | Answer | Evidence / decision |
| --- | --- | --- |
| Does this preserve the existing public adapter → parser → OpportunityPacket → readiness → sampling → handoff → dashboard → Council manual review flow? | Yes. | This PR only plans how funding context could later enter the existing flow; it adds no runtime path. |
| Does this avoid changing active baseline `cross_exchange_spot_spread_v1` behavior? | Yes. | No config, registry, source, or active strategy file is modified. |
| Does this avoid changing existing experimental strategy status, readiness semantics, or dashboard interpretation? | Yes. | Existing strategies remain non-active; readiness and dashboard semantics are unchanged. |
| Does this keep Funding Rate as a plugin/context candidate instead of forcing it into common modules? | Yes. | The planning doc maps Funding Rate to source-contract and diagnostics/context layers first, with future plugin-like integration only after separate PRs. |
| Does this separate context-only information from executable signal? | Yes. | Funding Rate is explicitly not an entry signal, standalone `WATCH` / `ENTER` trigger, alert trigger, execution trigger, or active-promotion evidence. |
| Does this avoid generated JSON creation or commit? | Yes. | This PR creates no generated packet or market-sampling JSON and records no raw smoke artifacts. |
| Does this avoid private API, credentials, orders, alerts, or Council auto-call? | Yes. | The source plan is public-read-only and docs-only; no private endpoint, secret, account lookup, order, alert, execution, or Council auto-call is added. |
| Does this remain planning-only with no readiness change? | Yes. | No readiness code or readiness semantics are changed; future funding-readiness impact would require separate explicit policy approval. |

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

Runtime behavior is unchanged. This PR only adds planning documentation.

No files under `src/`, `tests/`, `config/`, `configs/`, `tools/`, `data/generated_packets/`, or `data/market_samples/` were modified. No registry/config/active strategy file was modified. The active strategy remains `cross_exchange_spot_spread_v1`; all experimental and future strategies remain non-active unless a separate approved PR changes status.

## Generated Artifact Policy

No generated packet JSON or market-sampling JSON was created or committed. Generated JSON remains a smoke artifact and is not source-of-truth for dashboard or handoff evidence.

## Files Changed

- Added `docs/funding_rate_context_strategy.md`.
- Added `docs/pr_handoffs/funding_rate_context_strategy_planning_2026_06_10.md`.

## Validation

Validation commands required for this docs-only PR:

- `git status --short --branch`
- `git diff --name-only`
- `git diff --name-only -- src tests config configs tools data/generated_packets data/market_samples`
- `find data/generated_packets data/market_samples -type f -name '*.json'`
- `git diff --check`
- `python -m unittest discover -s tests`

Validation result summary:

- Fresh `origin/main` branch creation was attempted but could not complete because GitHub fetch failed in this environment with `CONNECT tunnel failed, response 403`.
- Work was performed on `docs/funding-rate-context-planning-v0` from the available repository state.
- Only allowed docs files were changed.
- Forbidden source/test/config/tool/generated-data paths were not modified.
- No generated JSON artifact was created or committed.
- `git diff --check` passed.
- Full unittest discovery passed: `Ran 531 tests in 15.236s`, `OK`.

## Next Recommended Step

Recommended next PR: `Funding Public Source Research Finalization v0`.

Reason: before fixture contracts or parser wrappers, reviewers should first finalize the official public source choices, exact field semantics, pagination/rate-limit assumptions, and whether Binance `fundingInfo`, Bybit `instruments-info`, and OKX current/history endpoints are required or optional context sources.

That next PR must remain public-read-only / context-only / no-trade-first. It must not call live endpoints, add private API, implement adapters/parsers/packet builders/readiness/sampling collectors, create generated JSON, trigger alerts, call Council automatically, or promote any strategy.
