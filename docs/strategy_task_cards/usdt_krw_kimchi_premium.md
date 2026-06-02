# USDT/KRW Kimchi Premium Strategy Card v0

> Deferred/superseded note: the previous FX-based Kimchi Premium / FX Basis interpretation is deferred. The user clarified that USD/KRW FX reference is out of current scope, `fair_usdt_krw_price` is not used in the current user-intended strategy, and near-term implementation is superseded by [`tether_cross_market_premium`](tether_cross_market_premium.md). This card is retained as archived/deferred future planning only; it is not active and not experimental.


## Task name
USDT/KRW Kimchi Premium Strategy Card v0

## Strategy family
- `strategy_family`: `stablecoin_krw_premium`
- `strategy_id`: `usdt_krw_kimchi_premium_v0`
- First implementation target: `USDT/KRW`
- Long-term expansion: other stablecoins such as `USDC/KRW` may be considered only after a separate read-only data requirement review.
- Current status: `future` / deferred for near-term implementation
- Active strategy: no. The active strategy remains `cross_exchange_spot_spread_v1`.
- Execution policy: `NO_TRADE_ONLY`

## Goal
Preserve a read-only, no-trade future planning record for the older FX-based USDT/KRW kimchi premium or reverse-premium interpretation. This card is now deferred/superseded for near-term work by `tether_cross_market_premium`; it is not auto-trading, not an execution strategy, and not a request to place orders, transfer funds, query balances, or use private APIs.

## Current status
- Status: `future` / deferred.
- Priority: `P1` historical planning.
- Not active and not experimental yet.
- Superseded for near-term implementation by [`tether_cross_market_premium`](tether_cross_market_premium.md).
- USD/KRW FX reference is out of current scope for the user-intended near-term strategy.
- `fair_usdt_krw_price` is not used in the current user-intended strategy.
- Codex must not promote this strategy to active by itself.
- No live adapter, no scenario JSON, no readiness implementation, no Council handoff, and no automated execution is included in this card.
- Data availability matrix: [`docs/data_availability/usdt_krw_multi_source_matrix.md`](../data_availability/usdt_krw_multi_source_matrix.md).
- Public probe review: [`docs/data_availability/usdt_krw_probe_review.md`](../data_availability/usdt_krw_probe_review.md).
- experimental scaffolding requires Multi-Source Data Availability Matrix and Public Probe first.
- Experimental scaffolding for this FX-based interpretation is deferred; near-term scaffolding should use the Tether Cross-Market Public Probe Alignment path instead of FX cadence work.

## Strategy concept

### Mode A: Domestic USDT/KRW executable spread
- Example: compare an Upbit `USDT/KRW` source ask with a Bithumb `USDT/KRW` target bid.
- Candidate evaluation must use source ask / target bid, not last_price-only differences.
- Requires fee, VWAP, orderbook depth, timestamp, latency, and repeated persistence checks.
- This is similar to `cross_exchange_spot_spread_v1` but with `asset=USDT` and `quote=KRW`.
- Mode A is a domestic exchange-to-exchange USDT spread and is only a lower-level or supporting observation for kimchi premium analysis.

### Mode B: USDT/KRW Kimchi Premium / FX Basis (deferred)
- This was the earlier interpretation: compare domestic `USDT/KRW` public bid/ask/depth with a fair KRW value derived from public `USD/KRW` reference rates and optional global `USDT/USD` references.
- The user clarified that this FX-based interpretation is not the current near-term target.
- USD/KRW FX reference is out of current scope.
- `fair_usdt_krw_price` is not used in the current user-intended strategy.
- Near-term implementation is superseded by `tether_cross_market_premium`, which monitors domestic `USDT/KRW` and global USDT reference health without KRW FX conversion.

## Data required

### Mode A required public data
- Upbit `USDT/KRW` ticker/orderbook or pair availability confirmation.
- Bithumb `USDT/KRW` ticker/orderbook or pair availability confirmation.
- `bid`
- `ask`
- `bid_size`
- `ask_size`
- `depth_levels`
- trading fee placeholder
- `timestamp_utc`
- `data_quality.max_data_age_ms`
- `latency_ms`
- venue health
- pair availability

### Mode B required public data
- domestic `USDT/KRW` bid/ask/depth from one or more Korean venues
- public `USD/KRW` reference rate
- optional global `USDT/USD` reference
- optional global USDT orderbook/reference venue
- FX timestamp
- USDT reference timestamp
- timestamp alignment metadata
- source reliability metadata
- trading fee placeholder
- depth/VWAP/liquidity
- `data_quality.max_data_age_ms`
- `latency_ms`
- depeg/risk flag if available from public data

## Data forbidden
- private API
- API key / secret / token
- account/balance lookup
- order placement
- order cancel
- withdrawal/deposit/transfer
- bank account / fiat transfer
- KRW deposit/withdrawal implementation
- auto-trading
- Council decision to trade conversion

## OpportunityPacket shape

Top-level draft:
- `asset`: `USDT`
- `quote`: `KRW`
- `strategy_family`: `stablecoin_krw_premium`
- `strategy_id`: `usdt_krw_kimchi_premium_v0`
- `signal_type`: `stablecoin_krw_premium`

Observation examples:
- `domestic_usdt_krw_observation`
- `fx_reference_observation`
- `global_usdt_reference_observation`

Candidate type examples:
- `usdt_krw_premium_signal`
- `usdt_krw_discount_signal`
- `domestic_usdt_cross_exchange_spread_signal`

Candidate metrics draft:
- `domestic_usdt_krw_price`
- `reference_usd_krw_rate`
- `global_usdt_usd_price`
- `fair_usdt_krw_price`
- `premium_absolute_krw`
- `premium_pct`
- `discount_pct`
- `source_ask`
- `target_bid`
- `vwap_price`
- `fee_pct`
- `safety_buffer_pct`
- `estimated_net_premium_pct`
- `fx_source`
- `fx_timestamp_utc`
- `reference_timestamp_utc`
- `timestamp_diff_ms`
- `data_age_ms`
- `depeg_risk_flag`
- `liquidity_pass`
- `freshness_pass`
- `premium_pass`

## Formula draft (historical/deferred FX interpretation)

The formulas below are retained only for historical/future FX-basis planning. They are not used in the current user-intended near-term strategy. The current strategy must not calculate `fair_usdt_krw_price` or `premium_pct` against USD/KRW.

Mode B fair value:

```text
fair_usdt_krw_price = usd_krw_reference_rate * global_usdt_usd_reference
```

Mode B premium:

```text
premium_pct = ((domestic_usdt_krw_price - fair_usdt_krw_price) / fair_usdt_krw_price) * 100
```

Mode B net premium estimate:

```text
estimated_net_premium_pct =
premium_pct
- domestic_trading_fee_pct
- estimated_slippage_pct
- safety_buffer_pct
```

Mode A domestic spread:

```text
gross_spread = target_bid - source_ask
gross_spread_pct = gross_spread / source_ask * 100
```

Mode A estimated net gap:

```text
estimated_net_gap_pct =
gross_spread_pct
- source_fee_pct
- target_fee_pct
- estimated_slippage_pct
- safety_buffer_pct
```

## Readiness rules (historical/deferred FX interpretation)

### NEED_DATA
- `USDT/KRW` pair availability unknown
- domestic bid/ask/depth missing
- fees missing
- timestamp or data_age missing
- `USD/KRW` reference missing for Mode B
- global `USDT/USD` reference missing if required
- FX timestamp stale
- timestamp diff too large
- depeg/risk reference unavailable when required

### REJECT
- `estimated_net_premium_pct <= 0`
- insufficient depth
- stale domestic market data
- stale FX/reference data
- unstable direction
- premium exists but only last_price based
- depeg/risk flag active
- reference source unreliable

### WATCH
- public bid/ask/depth fresh
- FX/reference fresh
- `premium_pct` positive and `estimated_net_premium_pct` above threshold
- liquidity sufficient
- persistence observed
- no private data required
- still non-execution signal only

### ENTER
- Forbidden as an execution instruction.
- If present in a schema, `ENTER` is an analysis-stage label only and must not be converted into an order, transfer, or automated trade.

## Manual scenarios

These scenario names are historical/deferred drafts. Do not add scenario JSON for this card unless a future user-approved task reactivates the FX-based interpretation.

Scenario JSON files are not part of this card. Draft scenario names for a later experimental scaffolding card:
- `usdt_krw_premium_missing_fx_need_data`
- `usdt_krw_premium_missing_depth_need_data`
- `usdt_krw_premium_positive_watch`
- `usdt_krw_premium_high_fee_reject`
- `usdt_krw_premium_stale_fx_reject`
- `usdt_krw_premium_depeg_risk_reject`
- `usdt_krw_discount_watch_or_reject`
- `usdt_krw_domestic_spread_positive_watch`

## Allowed files for future implementation
Future task cards may allow only carefully scoped documentation, fixtures, config metadata, and tests first. Any later public adapter work must be read-only, mock/fixture tested, and separately approved.

## Forbidden files/actions
- Do not implement live adapters in this card.
- Do not modify `src/`, `tools/`, `prompts/`, or `configs/strategy_current.yaml` in this card.
- Do not add private endpoints, API keys, secrets, tokens, account lookup, balance lookup, orders, order cancel, withdrawal, deposit, transfer, fiat/bank transfer, auto-trading, or Council auto-call behavior.

## Tests
Documentation tests should verify this card exists, is read-only/no-trade, is not auto-trading, is marked deferred/superseded for near-term implementation, keeps the old Mode A / deferred Mode B distinction for historical context, and leaves the active strategy unchanged.

## Manual smoke
None. This is a documentation-only strategy card.

## Success criteria
- `stablecoin_krw_premium` / `usdt_krw_kimchi_premium_v0` is documented as a future read-only strategy.
- The card clearly marks USDT/KRW kimchi premium / FX basis analysis as deferred historical planning.
- No active strategy change occurs.
- No adapter, private API, or trading implementation is added.
- The multi-source matrix is linked at [`docs/data_availability/usdt_krw_multi_source_matrix.md`](../data_availability/usdt_krw_multi_source_matrix.md).
- Experimental scaffolding requires the Multi-Source Data Availability Matrix and `USDT/KRW Public Probe v0` report first.
- Probe review is linked at [`docs/data_availability/usdt_krw_probe_review.md`](../data_availability/usdt_krw_probe_review.md).
- Experimental scaffolding for this FX-based interpretation is deferred; near-term scaffolding should use the Tether Cross-Market Public Probe Alignment path instead of FX cadence work.
- The near-term next implementation gate is `Tether Cross-Market Public Probe Alignment v0`; FX cadence work is no longer required for the current user-intended strategy.

## Non-goals
- Do not treat the public probe report as a live adapter or execution readiness check.
- Do not implement persistent data availability adapters in this card.
- Do not implement live or replay adapters.
- Do not add scenario JSON files.
- Do not implement readiness code.
- Do not implement Council handoff or Council automatic calls.
- Do not implement auto-trading or execution.
