# Tether Cross-Market Premium Strategy Card v0

## Task name
Tether Cross-Market Experimental Scaffolding v0

## Strategy family
- `strategy_family`: `tether_cross_market_premium`
- `strategy_id`: `usdt_krw_global_reference_v0`
- Status: `experimental` / scaffolding only
- Priority: `P1`
- Execution policy: `NO_TRADE_ONLY`
- Active: `false`
- Experimental: `true`
- Codex must not promote this strategy to active by itself.

## Goal
Define a read-only experimental scaffolding plan that observes domestic `USDT/KRW` markets on Korean exchanges and compares that state with global public USDT reference health. The near-term goal is not FX-based kimchi premium, not auto-trading, and not an execution workflow. It is a planning card for detecting domestic Tether cross-market spread, premium-state, and depeg/reference-health conditions with public data only.

## Current status
- Experimental scaffolding only; not active and still `NO_TRADE_ONLY`.
- Active strategy remains `cross_exchange_spot_spread_v1`.
- Domestic v0 venues are Upbit and Bithumb only.
- Upbit `USDT/KRW` is the confirmed primary domestic public source from the prior probe (`ok / available`).
- Bithumb `USDT/KRW` is rechecked as available for the manual experimental path, but live adapters are still not added.
- Coinone and Korbit are future domestic expansion, not v0.
- Global reference v0 venues are Binance, Bybit, and OKX.
- Overseas venues can be expanded later only by separate strategy task cards and public probe review first.
- This scaffolding adds manual scenario JSON, formula helpers, evaluate-only readiness rules, and replay packet-builder support; it does not add a live adapter, persistent adapter, OpportunityPacket live builder, Council handoff, private API, order, transfer, balance lookup, or auto-trading.

## Probe alignment status
- Prior probe result: Upbit `domestic_usdt_krw` was `ok / available`; treat it as the confirmed primary domestic public source for planning.
- Bithumb `domestic_usdt_krw` has been rechecked for the manual experimental path; domestic executable-spread scaffolding remains manual/evaluate-only and non-active.
- Bithumb must remain confirmed before any future live domestic cross-exchange executable spread implementation; if it becomes unknown, use the Upbit-only domestic reference fallback instead of executable spread implementation.
- Prior probe result: Coinone and Korbit were `skipped / unknown`; they are future domestic expansion only, not v0.
- Prior probe result: Binance, Bybit, and OKX `global_usdt_reference` were `ok / available`; keep them as the initial global USDT reference basket.
- FX candidates are out-of-scope for current strategy and must not block the no-FX Tether cross-market path.

## Strategy concept

### A. Domestic USDT/KRW executable spread
- Compare Upbit `USDT/KRW` ask vs Bithumb `USDT/KRW` bid.
- Compare Bithumb `USDT/KRW` ask vs Upbit `USDT/KRW` bid.
- This is directly comparable because both markets are KRW quoted.
- This can reuse `cross_exchange_spot_spread_v1` style logic conceptually with `asset=USDT`, but this card does not implement that logic.
- Evaluation must use executable bid/ask/depth, fees, slippage, timestamps, and persistence, not last-price-only differences.

### B. Domestic USDT/KRW premium state
- Observe Upbit/Bithumb `USDT/KRW` mid/bid/ask levels.
- Calculate planning metrics such as:
  - `domestic_best_bid`
  - `domestic_best_ask`
  - `domestic_median_mid`
  - `domestic_weighted_mid`
  - `domestic_venue_count_available`
- This is a domestic Tether market-state signal, not a USD/KRW fair-value calculation.

### C. Global USDT reference health
- Use Binance / Bybit / OKX as the initial global USDT reference basket.
- Candidate public pairs include `USDT/USD`, `USDT/USDC`, `USDC/USDT`, or documented equivalents.
- Global references are used for USDT reference/depeg health, not KRW conversion.
- Global venues can be expanded later only through a new task card and public probe first.
- Overseas exchanges are not automatically execution venues.
- Future overseas venues can be added only after a new task card and public probe.

### Explicit de-scope from FX-based interpretation
- This strategy does not require USD/KRW FX.
- This strategy does not calculate `fair_usdt_krw_price`.
- `fair_usdt_krw_price` is not used in the current user-intended strategy.
- Do not calculate `premium_pct` against USD/KRW in current scope.
- The deferred FX-basis card is retained only as historical/future planning context.

## Data required

### Domestic public data for v0
- Upbit `USDT/KRW` pair availability.
- Bithumb `USDT/KRW` pair availability.
- Public ticker.
- Public orderbook.
- `bid`.
- `ask`.
- `bid_size`.
- `ask_size`.
- `depth_levels`.
- `timestamp` / `timestamp_utc`.
- `latency` / `latency_ms`.
- `data_age` / `data_quality.max_data_age_ms`.
- Manual fee placeholder.
- Public venue health or maintenance status if available.

### Global public reference data for v0
- Binance public `USDT/USD`, `USDT/USDC`, `USDC/USDT`, or equivalent ticker/orderbook candidate.
- Bybit public `USDT/USD`, `USDT/USDC`, `USDC/USDT`, or equivalent ticker/orderbook candidate.
- OKX public `USDT/USD`, `USDT/USDC`, `USDC/USDT`, or equivalent ticker/orderbook candidate.
- `bid`.
- `ask`.
- `mid`.
- `timestamp`.
- `latency`.
- `depeg_flag` / depeg threshold metadata.
- Reference reliability metadata.
- `global_reference_venue_count`.

## Data forbidden
- Private API.
- API key / secret / token.
- No account/balance lookup.
- Order placement.
- Order cancellation.
- No withdrawal/deposit/transfer.
- KRW deposit/withdrawal implementation.
- Bank account / fiat transfer implementation.
- Auto-trading.
- Council decision to trade conversion.
- Scraping / browser automation.

## OpportunityPacket shape
This is a draft only; no OpportunityPacket builder is added in this task.

Top-level draft:
- `asset`: `USDT`
- `quote`: `KRW`
- `strategy_family`: `tether_cross_market_premium`
- `strategy_id`: `usdt_krw_global_reference_v0`
- `signal_type`: `tether_cross_market_premium`

Observation examples:
- `domestic_usdt_krw_observation`
- `domestic_usdt_krw_spread_observation`
- `global_usdt_reference_observation`

Candidate type examples:
- `domestic_usdt_cross_exchange_spread_signal`
- `domestic_usdt_premium_state_signal`
- `global_usdt_depeg_health_signal`

Candidate metric examples:
- `source_venue`
- `target_venue`
- `source_ask`
- `target_bid`
- `gross_gap_pct`
- `estimated_net_gap_pct`
- `domestic_best_bid`
- `domestic_best_ask`
- `domestic_median_mid`
- `domestic_weighted_mid`
- `domestic_venue_count_available`
- `global_usdt_mid`
- `global_usdt_depeg_pct`
- `global_usdt_depeg_flag`
- `global_reference_venue_count`
- `liquidity_pass`
- `freshness_pass`
- `global_reference_health_pass`

## Formula draft

Domestic cross-exchange spread:

```text
source_ask = domestic venue A USDT/KRW ask
target_bid = domestic venue B USDT/KRW bid

gross_gap_pct =
(target_bid - source_ask) / source_ask * 100

estimated_net_gap_pct =
gross_gap_pct
- source_fee_pct
- target_fee_pct
- estimated_slippage_pct
- safety_buffer_pct
```

Domestic premium state:

```text
domestic_mid =
(domestic_best_bid + domestic_best_ask) / 2

domestic_median_mid =
median(per_venue_mid)

domestic_weighted_mid =
weighted average by executable depth or notional
```

Global USDT health:

```text
global_usdt_mid =
median(global_reference_mid_prices)

global_usdt_depeg_pct =
(global_usdt_mid - 1.0) * 100

global_usdt_depeg_flag =
abs(global_usdt_depeg_pct) >= threshold
```

Important: do not calculate `premium_pct` against USD/KRW in current scope, and do not use `fair_usdt_krw_price` for this near-term strategy.

## Readiness rules
Readiness is implemented only as experimental evaluate-only scaffolding. It is non-active, never execution-capable, and always keeps `readiness_pass=false` for this strategy.

### NEED_DATA
- Upbit/Bithumb `USDT/KRW` pair availability unknown.
- Domestic bid/ask/depth missing.
- Domestic timestamp/latency missing.
- Global reference unavailable.
- Global reference symbols not comparable.
- Fees missing.

### REJECT
- Domestic net spread <= 0 after fees/buffer/slippage.
- Insufficient domestic depth.
- Stale domestic data.
- Global USDT depeg flag active.
- Only last_price based signal.
- Unstable direction.

### WATCH
- Domestic bid/ask/depth fresh.
- Domestic net spread positive after fees/buffer/slippage.
- Global USDT reference healthy.
- Persistence observed.
- Still read-only/non-execution signal.

### ENTER
- Forbidden as an execution instruction.
- If present in a future schema, it is an analysis-stage label only.

## Manual scenarios
Manual scenario JSON added for evaluate-only scaffolding:
- `tether_cross_market_missing_bithumb_need_data`
- `tether_cross_market_missing_global_reference_need_data`
- `tether_cross_market_domestic_spread_positive_watch`
- `tether_cross_market_high_fee_reject`
- `tether_cross_market_depeg_risk_reject`
- `tether_cross_market_last_price_only_need_data`
- `tether_cross_market_balanced_no_spread_reject`

## Allowed files for future implementation
Future task cards may allow only explicitly scoped files. Typical future scopes may include docs, config, tests, and then public probe alignment before any adapter or readiness work.

## Forbidden files/actions
- Do not implement live adapters in this card.
- Do not implement persistent adapters in this card.
- Do not implement OpportunityPacket builders in this card.
- Do not implement active/live readiness or Council handoff in this card.
- Scenario JSON is manual/evaluate-only and must not be treated as live market data.
- Do not use private APIs, credentials, account/balance lookup, orders, transfers, withdrawals, KRW/bank transfer flows, auto-trading, or Council automatic calls.

## Tests
Documentation/guardrail tests must verify:
- This card exists.
- It says no FX is required.
- It fixes domestic v0 venues to Upbit and Bithumb.
- It starts global references with Binance, Bybit, and OKX and says they are expandable.
- It includes the domestic spread formula.
- It includes global depeg health formulas.
- It says `fair_usdt_krw_price` is not used.
- Registry marks the strategy `experimental` and `NO_TRADE_ONLY` while keeping it non-active.
- Active strategy remains `cross_exchange_spot_spread_v1`.

## Manual smoke
`python tools/run_strategy_scenarios.py --strategy tether_cross_market_premium --evaluate-only`

Replay packet builder smoke:

```text
python tools/collect_market_data.py --adapter replay_tether_cross_market_premium --output data/generated_packets/replay_tether_cross_market_packet.json
python main.py --council --opportunity-file data/generated_packets/replay_tether_cross_market_packet.json --dry-run-context
```

## Success criteria
- Strategy direction is corrected away from FX-based Kimchi Premium.
- Near-term Tether strategy compares domestic `USDT/KRW` state and global USDT reference health.
- Domestic v0 venues are fixed to Upbit/Bithumb.
- Overseas references are expandable starting from Binance/Bybit/OKX.
- Formula helper and evaluate-only readiness scaffolding are added without live adapters or execution paths.
- No private API or trade behavior is added.

## Next gate
Next card: `Tether Cross-Market Evaluate-Only Review v0`

Purpose:
- Review manual scenario outcomes and readiness warnings.
- Keep Upbit/Bithumb as domestic v0 venues and Binance/Bybit/OKX as global reference venues.
- Add no adapter yet.
- Add no OpportunityPacket live builder.
- Add no Council handoff.
- Do no trading.

Alternative if Bithumb remains unknown: `Tether Cross-Market Upbit-Only Domestic Reference Scaffolding v0`. This alternative is analysis-only, is not executable domestic spread, and still has no trade behavior.

## Non-goals
- No FX-based `fair_usdt_krw_price` calculation.
- No USD/KRW FX source requirement.
- No active strategy change.
- Experimental but non-active; no active promotion.
- No runtime/auth/prompt change.
- No order, balance, transfer, withdrawal, KRW deposit/withdrawal, bank account, private API, or auto-trading workflow.
