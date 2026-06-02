# USDT/KRW Kimchi Premium Strategy Card v0

## Task name
USDT/KRW Kimchi Premium Strategy Card v0

## Strategy family
- `strategy_family`: `stablecoin_krw_premium`
- `strategy_id`: `usdt_krw_kimchi_premium_v0`
- First implementation target: `USDT/KRW`
- Long-term expansion: other stablecoins such as `USDC/KRW` may be considered only after a separate read-only data requirement review.
- Current status: `future`
- Active strategy: no. The active strategy remains `cross_exchange_spot_spread_v1`.
- Execution policy: `NO_TRADE_ONLY`

## Goal
Design a read-only, no-trade future strategy for reading USDT/KRW kimchi premium or reverse-premium conditions. This is not auto-trading, not an execution strategy, and not a request to place orders, transfer funds, query balances, or use private APIs.

## Current status
- Status: `future`
- Priority: `P1`
- Not active and not experimental yet.
- Codex must not promote this strategy to active by itself.
- No live adapter, no scenario JSON, no readiness implementation, no Council handoff, and no automated execution is included in this card.
- Data availability matrix: [`docs/data_availability/usdt_krw_multi_source_matrix.md`](../data_availability/usdt_krw_multi_source_matrix.md).
- experimental scaffolding requires Multi-Source Data Availability Matrix and Public Probe first.

## Strategy concept

### Mode A: Domestic USDT/KRW executable spread
- Example: compare an Upbit `USDT/KRW` source ask with a Bithumb `USDT/KRW` target bid.
- Candidate evaluation must use source ask / target bid, not last_price-only differences.
- Requires fee, VWAP, orderbook depth, timestamp, latency, and repeated persistence checks.
- This is similar to `cross_exchange_spot_spread_v1` but with `asset=USDT` and `quote=KRW`.
- Mode A is a domestic exchange-to-exchange USDT spread and is only a lower-level or supporting observation for kimchi premium analysis.

### Mode B: USDT/KRW Kimchi Premium / FX Basis
- Compare domestic `USDT/KRW` public bid/ask/depth with a fair KRW value derived from public `USD/KRW` reference rates and optional global `USDT/USD` references.
- If domestic USDT/KRW is above the fair reference, the signal is premium.
- If domestic USDT/KRW is below the fair reference, the signal is discount or reverse premium.
- Requires FX source reliability, timestamp alignment, stale FX risk controls, and USDT depeg risk checks.
- Mode B is the user-intended core strategy: read the USDT/KRW kimchi premium or reverse premium as a public-data analysis signal.

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

## Formula draft

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

## Readiness rules

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
Documentation tests should verify this card exists, is read-only/no-trade, is not auto-trading, distinguishes Mode A and Mode B, identifies Mode B as the user-intended core strategy, includes forbidden data/actions, includes formulas, and leaves the active strategy unchanged.

## Manual smoke
None. This is a documentation-only strategy card.

## Success criteria
- `stablecoin_krw_premium` / `usdt_krw_kimchi_premium_v0` is documented as a future read-only strategy.
- The card clearly separates domestic USDT spread observation from USDT/KRW kimchi premium / FX basis analysis.
- No active strategy change occurs.
- No adapter, private API, or trading implementation is added.
- The next card can be `USDT/KRW Data Availability Check v0`.

## Non-goals
- Do not implement data availability checks in this card.
- Do not implement live or replay adapters.
- Do not add scenario JSON files.
- Do not implement readiness code.
- Do not implement Council handoff or Council automatic calls.
- Do not implement auto-trading or execution.
