# Strategy Expansion Playbook v1

This playbook defines how future strategies move from registry/catalog ideas into safe, testable, read-only experimental work. It does not promote any strategy to active status and does not authorize private APIs, orders, balances, withdrawals, transfers, or auto-trading.

## Current baseline
- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap` remains experimental/disabled.
- `orderbook_imbalance` has experimental scaffolding only; remaining unscaffolded strategies stay future backlog items until they pass the promotion steps below.
- Every strategy starts read-only and public-data-only unless a future gated phase explicitly changes the policy.

## 1. Strategy state definitions

### future
A strategy idea exists in docs/registry but has no implementation commitment. It may have notes, assumptions, and a rough data list. It must not change active runtime behavior.

### experimental
A strategy has a brief, data requirement matrix, OpportunityPacket mapping, manual scenarios, readiness rules, and unit/evaluate-only tests. It remains read-only, cannot become the default active strategy, and must not trigger Council handoff or alerts as if it were active unless explicitly scoped.

### active_candidate
A strategy is technically complete enough for review but is not active. It must be compared against the current active strategy, checked for no-trade compliance, and validated through replay/evaluate-only and manual smoke tests. It still cannot replace `cross_exchange_spot_spread_v1` without explicit user approval.

### active
A strategy is the current production analysis focus. Today, the only active strategy is `cross_exchange_spot_spread_v1`. Codex must not change the active strategy by itself.

### archived
A strategy is retained for historical context but is not maintained or used in active workflows. Archived strategies must not be revived without a new task card and user approval.

## 2. Strategy promotion steps

### Step 1: Strategy brief
Document the strategy purpose, market assumption, why it is useful, expected signal, and why it is safe to evaluate read-only.

### Step 2: Data requirement matrix
List required data, optional data, forbidden/private data, and whether the strategy can be evaluated with public-only sources. The matrix must explicitly reject private endpoints, API keys, account/balance lookup, order data, withdrawals, transfers, and auto-trading inputs.

### Step 3: OpportunityPacket mapping
Define which values belong in `observations`, which values belong in `candidates`, and how to use `metrics`, `thresholds`, `guards`, and `extensions`. The mapping must remain forward-compatible and must not introduce fixed exchange_a/exchange_b structures.

### Step 4: Manual scenario fixtures
Before live data, create manual scenario designs for:
- missing-data / NEED_DATA
- positive / WATCH
- high-fee / REJECT
- stale-data / REJECT
- low-liquidity / REJECT

### Step 5: Readiness rules
Define deterministic rules for `NEED_DATA`, `REJECT`, and `WATCH`. `ENTER` is forbidden as an execution instruction; if retained in schema language, it means only an analysis-stage candidate label. Define the exact `readiness_pass` conditions.

### Step 6: Replay/evaluate tests
Validate replay/evaluate-only behavior before any live work. Required checks include `tools/run_strategy_scenarios.py --evaluate-only`, scenario schema validation, and proving `expected_behavior` never enters agent context.

### Step 7: Public read-only adapter
Implement a live adapter only if required and explicitly allowed by the task. The adapter must use public GET/read-only endpoints only, no private API, no API key, and no auth headers. Unit tests must use mocks/fixtures only. Live smoke tests are manual and must be optional.

### Step 8: Sampling/persistence
Add repeated sampling only after packet building and readiness are deterministic. Define persistent edge criteria, including `PERSISTENT_READY_EDGE`, minimum consecutive ready samples, direction stability, latency and data-age tolerances.

### Step 9: Alert/journal integration
Add journal fields and alert rules only after persistence is defined. Alerts must remain console/file based unless a future task explicitly permits another channel. Handoff must only occur when a strategy-specific `PERSISTENT_READY_EDGE` is confirmed.

### Step 10: Optional manual Council smoke
Council smoke is manual only. Do not implement automatic Council invocation. Do not convert Council output into execution, orders, transfers, or account actions.

### Step 11: active_candidate review
Compare the strategy against the existing active strategy, check for conflicting assumptions, verify no-trade policy compliance, document operational risks, and confirm that `cross_exchange_spot_spread_v1` is not broken.

### Step 12: active promotion
Codex must not promote a strategy to active by itself. Active promotion requires explicit user approval and must not break the existing active strategy, scenarios, readiness checks, sampling outputs, handoff packet schema, or alert behavior.

## 3. Stage-wide forbidden actions

The following are forbidden at every stage:
- private API
- API key / secret / token
- balance/account lookup
- order placement/cancel
- withdrawal/deposit/transfer
- auto-trading
- Council decision to trade conversion

## 4. Minimum deliverables before experimental status

A strategy cannot move from future to experimental until it has:
- strategy brief doc
- data requirement matrix
- OpportunityPacket mapping
- manual scenario designs
- readiness rules
- unit tests
- evaluate-only test
- no-trade compliance notes

## 5. Future strategy backlog

### stablecoin_krw_premium / usdt_krw_kimchi_premium
- Purpose: Read USDT/KRW kimchi premium or reverse-premium by comparing domestic USDT/KRW public bid/ask/depth with fair USD/KRW or global USDT/USD reference pricing.
- Likely public data required: domestic USDT/KRW bid/ask/depth, public USD/KRW reference, optional global USDT/USD reference, timestamp alignment, source reliability, fees, liquidity and depeg-risk metadata. This includes domestic/global prices and FX or USDT-KRW reference assumptions that must be resolved before implementation.
- First safe implementation step: `USDT/KRW Data Availability Check v0` to document Upbit/Bithumb pair availability and reference-source candidates; no live adapter changes initially.
- Why not active yet: FX/reference reliability, timestamp alignment and depeg-risk controls are unresolved; this is a future read-only strategy, not auto-trading.

### kimchi_premium
- Purpose: Compare domestic KRW crypto prices against global USD/USDT-referenced prices to detect premium or discount regimes.
- Likely public data required: domestic spot bid/ask/depth, global spot bid/ask/depth, public FX or USDT/KRW reference, timestamps, fees, liquidity.
- First safe implementation step: data requirement matrix and FX/USDT-KRW source policy; no live adapter changes initially.
- Why not active yet: requires reliable currency conversion and multi-market normalization beyond current active KRW spot-spread flow.

### reverse_premium
- Purpose: Detect cases where domestic KRW prices are below global reference prices after conversion and costs.
- Likely public data required: same as kimchi premium plus direction-specific fees, liquidity and stale-data checks.
- First safe implementation step: share a premium/discount OpportunityPacket mapping with kimchi premium.
- Why not active yet: conversion reliability, transfer assumptions, and venue comparability are unresolved and must remain read-only.

### spot_futures_basis
- Purpose: Compare spot price against futures/perpetual reference to observe basis without trading it.
- Likely public data required: spot bid/ask/depth, futures/perp bid/ask/mark/index, contract metadata, timestamps, fees.
- First safe implementation step: brief and data matrix after funding-rate public data assumptions are documented.
- Why not active yet: combines spot and derivatives data and must remain separate from active spot-only strategy.

### funding_rate
- Purpose: Monitor public funding rates and next funding times for derivative markets.
- Likely public data required: funding rate, next funding time, mark/index price, open interest if public, venue health, timestamps.
- First safe implementation step: derivatives-only OpportunityPacket mapping and manual missing/stale scenarios.
- Why not active yet: active strategy is spot-only; funding decisions require separate readiness and risk framing.

### orderbook_imbalance
- Purpose: Measure bid/ask depth imbalance as a market pressure signal using existing public orderbook depth.
- Likely public data required: multi-level bid/ask prices and sizes, spread, depth notional, timestamp, latency and venue health.
- First safe implementation step: experimental scaffolding with registry metadata, manual scenarios and non-active readiness rules.
- Why not active yet: imbalance is a signal, not an executable spread; readiness_pass remains false to avoid Council handoff confusion.

### trade_flow_momentum
- Purpose: Observe public trade prints or tick data to estimate short-term aggressive buy/sell flow.
- Likely public data required: public recent trades, side/inference if available, price, size, timestamp, latency.
- First safe implementation step: determine whether public trade side data is available and reliable without private endpoints.
- Why not active yet: trade side inference can be noisy and needs a dedicated data-quality model.

### volatility_breakout
- Purpose: Detect public price/volume expansion beyond recent ranges as a watch signal.
- Likely public data required: candles/trades, rolling highs/lows, volume, bid/ask spread, timestamps.
- First safe implementation step: offline fixture-only indicator brief and no-trade readiness definitions.
- Why not active yet: needs historical window handling and should not create execution prompts.

### mean_reversion
- Purpose: Identify stretched price moves that may revert, only as an analysis signal.
- Likely public data required: public candles, rolling averages, volatility bands, liquidity and timestamp metadata.
- First safe implementation step: define statistical assumptions and stale-data safeguards.
- Why not active yet: requires historical modeling and backtest-lite validation before even experimental live sampling.

### liquidation_open_interest
- Purpose: Monitor public liquidation/open-interest signals for derivatives stress.
- Likely public data required: public liquidation feed if available, open interest, mark/index price, funding, timestamps.
- First safe implementation step: verify public availability and exchange-specific semantics.
- Why not active yet: derivatives-only and not compatible with active spot KRW spread workflow.

### news_event
- Purpose: Track public news/event metadata as context for market moves.
- Likely public data required: public news/event feeds, timestamps, source credibility metadata, affected assets.
- First safe implementation step: document source policy and hallucination/verification requirements.
- Why not active yet: unstructured data risk is high and needs separate validation rules.

### onchain
- Purpose: Use public blockchain metrics as context for asset flows or network stress.
- Likely public data required: public chain metrics, exchange-labeled flows if available, timestamps, source provenance.
- First safe implementation step: define accepted public data providers and provenance requirements.
- Why not active yet: provider trust, latency, and interpretation risks are unresolved.

### grid
- Purpose: Analyze grid-like range structure for research without placing any grid orders.
- Likely public data required: public candles, bid/ask spread, volatility, liquidity, fees.
- First safe implementation step: no-trade research brief and offline scenarios only.
- Why not active yet: grid is execution-adjacent and must not be implemented as an order strategy.

### market_making
- Purpose: Study spread/liquidity conditions that market makers monitor, without quoting or orders.
- Likely public data required: bid/ask depth, spread, volatility, fees, latency, inventory assumptions explicitly excluded.
- First safe implementation step: analysis-only data matrix that forbids inventory, balances and order placement.
- Why not active yet: true market making requires private account state and orders, both forbidden.

## 6. Strategy task-card template

See `docs/strategy_task_cards/TEMPLATE.md`. A strategy task card must include:
- Task name
- Strategy family
- Goal
- Current status
- Data required
- Data forbidden
- OpportunityPacket shape
- Readiness rules
- Scenarios
- Allowed files
- Forbidden files
- Tests
- Manual smoke
- Success criteria
- Non-goals

## 7. Initial task-card drafts

Initial future/experimental preparation drafts live under `docs/strategy_task_cards/`:
- `orderbook_imbalance.md`
- `kimchi_premium.md`
- `funding_rate.md`

These are documentation-only planning cards. They do not authorize code, config, live adapter, readiness, or scenario implementation.

## 8. Recommended implementation order

1. `orderbook_imbalance` — existing Upbit/Bithumb orderbook depth makes this the safest next candidate.
2. `stablecoin_krw_premium` / `usdt_krw_kimchi_premium` — requires `USDT/KRW Data Availability Check v0` before experimental scaffolding.
3. `kimchi_premium` — broader domestic/global premium work still requires data requirements and FX/reference policy first.
4. `funding_rate` — requires public derivatives data and must remain separate from the active spot strategy.
5. `spot_futures_basis` — combines spot and futures data, so it should follow funding-rate groundwork.

The orderbook_imbalance experimental path continues; stablecoin_krw_premium requires data availability checks before experimental scaffolding; funding_rate and spot_futures_basis remain later. All other strategies remain future backlog items until a dedicated task card promotes them through the playbook.
