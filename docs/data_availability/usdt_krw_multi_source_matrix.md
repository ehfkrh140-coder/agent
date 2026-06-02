# USDT/KRW Multi-Source Data Availability Matrix v0

## Overview
This document is a planning-only data availability matrix for the near-term `tether_cross_market_premium` / `usdt_krw_global_reference_v0` strategy. The strategy has been reframed away from `USDT/KRW Kimchi Premium / FX Basis`: USD/KRW FX reference and `fair_usdt_krw_price` are deferred/out-of-scope for the current user-intended strategy. The matrix now separates domestic `USDT/KRW` venues from global USDT reference venues before any experimental scaffolding, live adapter, persistent adapter, OpportunityPacket builder, readiness code, or trading workflow.

Historical FX-basis planning for `stablecoin_krw_premium` / `usdt_krw_kimchi_premium_v0` is retained, but it is superseded for near-term implementation by `tether_cross_market_premium`.

## Strategy link
- Near-term strategy card: [`docs/strategy_task_cards/tether_cross_market_premium.md`](../strategy_task_cards/tether_cross_market_premium.md)
- Deferred FX-basis card: [`docs/strategy_task_cards/usdt_krw_kimchi_premium.md`](../strategy_task_cards/usdt_krw_kimchi_premium.md)
- Probe review: [`docs/data_availability/usdt_krw_probe_review.md`](usdt_krw_probe_review.md)
- Near-term strategy family: `tether_cross_market_premium`
- Near-term strategy_id: `usdt_krw_global_reference_v0`
- Status: future / planning only
- Execution policy: `NO_TRADE_ONLY`

## Source role model

### A. Domestic USDT/KRW venues
Roles:
- Observe domestic `USDT/KRW` bid/ask/depth.
- Calculate domestic cross-exchange spread and domestic premium-state metrics.
- Potential future execution candidates only after explicit separate approval; current use is read-only.

v0 candidates:
- Upbit
- Bithumb

Future domestic expansion candidates, not v0:
- Coinone
- Korbit

### B. Global USDT reference venues
Roles:
- Check `USDT/USD`, `USDT/USDC`, `USDC/USDT`, or documented equivalent public reference values.
- Detect possible USDT depeg/reference-health conditions.
- Support domestic signal interpretation as reference/depeg checks, not KRW conversion and not automatic execution venues.

Initial candidates:
- Binance
- Bybit
- OKX

Global venues can be expanded later only through a new task card and public probe first.

### C. USD/KRW FX reference sources (deferred/out-of-scope)
Roles in historical FX-basis planning only:
- Provide public USD/KRW reference for a future fair-value calculation if the FX-basis strategy is revived.
- Not required by the current `tether_cross_market_premium` strategy.
- Not part of the near-term implementation gate.

Deferred candidates:
- public FX API candidate
- official FX source candidate
- no-key public source candidate if available

FX sources must not be used for current strategy readiness. If revisited in a future task, a source must provide rate plus timestamp/freshness metadata without keys, private APIs, scraping, or browser automation.

## Domestic executable/reference venues

| venue | role | pair_to_check | pair_availability_status | public_ticker_candidate | public_orderbook_candidate | public_market_list_candidate | timestamp_available | depth_available | fee_source | implementation_status | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Upbit | v0 domestic `USDT/KRW` executable/reference venue | `USDT/KRW` | probe_available_for_USDT_KRW | public ticker candidate | public orderbook candidate | public market list candidate | probe_available_for_USDT_KRW | probe_available_for_USDT_KRW | manual fee placeholder | already_supported_for_BTC_KRW_public_adapter; USDT/KRW adapter not implemented | User local probe result was ok / available; confirm again in `Tether Cross-Market Public Probe Alignment v0`. |
| Bithumb | v0 domestic `USDT/KRW` executable/reference venue | `USDT/KRW` | probe_unknown | public ticker candidate | public orderbook candidate | public market list candidate | probe_unknown | probe_unknown | manual fee placeholder | already_supported_for_BTC_KRW_public_adapter; USDT/KRW adapter not implemented | User local probe result was ok / unknown; re-check Bithumb USDT/KRW pair availability before scaffolding. |
| Coinone | future domestic expansion candidate, not v0 | `USDT/KRW` or documented equivalent | skipped_unknown | public ticker/orderbook/market docs candidate | public ticker/orderbook/market docs candidate | public ticker/orderbook/market docs candidate | unknown_until_future_probe | unknown_until_future_probe | manual fee placeholder | not_implemented | Do not include in v0; future expansion requires task card and public probe. |
| Korbit | future domestic expansion candidate, not v0 | `USDT/KRW` or documented equivalent | skipped_unknown | candidate_source | candidate_source | candidate_source | unknown_until_future_probe | unknown_until_future_probe | manual fee placeholder | not_implemented | Do not include in v0; future expansion requires task card and public probe. |

## Global USDT reference venues

| venue | reference_pair_candidates | ticker_candidate | orderbook_candidate | timestamp_available | depth_available | depeg_reference_role | implementation_status | notes |
|---|---|---|---|---|---|---|---|---|
| Binance | `USDT/USD`, `USDT/USDC`, `USDC/USDT`, documented equivalents | probe_available_for_reference | probe_available_for_reference | probe_available_for_reference | unknown_until_future_probe | Reference midpoint and depeg cross-check only | candidate_source; probe_available_for_reference | User local probe result was ok / available; use only as one global reference candidate. |
| Bybit | `USDT/USD`, `USDT/USDC`, `USDC/USDT`, documented equivalents | probe_available_for_reference | probe_available_for_reference | probe_available_for_reference | unknown_until_future_probe | Reference midpoint and depeg cross-check only | existing_public_adapter_for_derivatives_but_spot_usdt_reference_not_implemented; probe_available_for_reference | User local probe result was ok / available; use only as one global reference candidate. |
| OKX | `USDT/USD`, `USDT/USDC`, `USDC/USDT`, documented equivalents | probe_available_for_reference | probe_available_for_reference | probe_available_for_reference | unknown_until_future_probe | Reference midpoint and depeg cross-check only | candidate_source; probe_available_for_reference | User local probe result was ok / available; use only as one global reference candidate. |

## USD/KRW FX reference sources
FX reference remains deferred/out-of-scope for the current strategy. The rows below are retained for historical planning only and must not block `tether_cross_market_premium` public probe alignment.

| source | role | requires_api_key | update_frequency_known | timestamp_available | reliability_level | implementation_status | notes |
|---|---|---|---|---|---|---|---|
| Frankfurter or no-key public FX candidate | deferred public USD/KRW FX candidate for historical fair-value planning | no_key_candidate_but_unresolved | probe_unknown | probe_unknown | unresolved_candidate_source | deferred; not_implemented | User local probe result was ok / unknown; not required for current strategy. |
| official FX source candidate | deferred official USD/KRW reference candidate | unknown_until_future_fx_task | unknown_until_future_fx_task | unknown_until_future_fx_task | candidate_official_reference | deferred; not_implemented | User clarified FX is out of scope; do not continue FX cadence for near-term strategy. |
| other public market FX source candidate | deferred additional public USD/KRW reference candidate | unknown_until_future_fx_task | unknown_until_future_fx_task | unknown_until_future_fx_task | candidate_secondary_reference | deferred; not_implemented | Use only if a future user-approved FX-basis task revives this path. |

## Recommended premium formulas
Current near-term formulas exclude USD/KRW FX and do not calculate `fair_usdt_krw_price`.

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

Domestic premium-state metrics:

```text
domestic_mid =
(domestic_best_bid + domestic_best_ask) / 2

domestic_median_mid =
median(per_venue_mid)

domestic_weighted_mid =
weighted average by executable depth or notional
```

Global USDT reference health:

```text
global_usdt_mid =
median(global_reference_mid_prices)

global_usdt_depeg_pct =
(global_usdt_mid - 1.0) * 100

global_usdt_depeg_flag =
abs(global_usdt_depeg_pct) >= threshold
```

Historical FX-basis formulas such as `fair_usdt_krw_price`, `premium_mid_pct`, `premium_sell_pct`, and `premium_buy_pct` are deferred and not used in current scope.

## Aggregation rules
When multiple domestic venues are available, calculate all of the following rather than relying on one venue:
- `per_venue_mid`
- `domestic_best_bid`
- `domestic_best_ask`
- `domestic_median_mid`
- `domestic_weighted_mid`
- `domestic_venue_count_available`
- `source_reliability_score`

For global USDT references, calculate:
- `global_usdt_mid`
- `global_usdt_median`
- `global_usdt_depeg_flag`
- `global_reference_venue_count`

Aggregation must preserve source-level timestamps, reliability metadata, and venue counts so a single source cannot silently dominate the signal.

## Data availability matrix
This planning matrix marks the near-term source set as:
- Domestic v0: Upbit is `probe_available_for_USDT_KRW`; Bithumb is `probe_unknown` and needs pair availability verification.
- Domestic future expansion: Coinone and Korbit remain `skipped_unknown` and are not v0.
- Global v0 reference: Binance, Bybit, and OKX are `probe_available_for_reference`.
- FX: deferred/out-of-scope for current strategy.

See [`docs/data_availability/usdt_krw_probe_review.md`](usdt_krw_probe_review.md) for the historical probe review and correction note.

## Data risks
- single venue distortion
- last_price-only premium illusion
- USDT depeg
- shallow domestic orderbook
- exchange-specific maintenance
- public API outage
- manual fee placeholder risk
- liquidity fragmentation across venues
- global reference symbol comparability risk
- regional restriction / Travel Rule / fiat transfer constraints are out of scope and must not be implemented
- stale FX reference and crypto timestamp vs FX timestamp mismatch are historical FX-basis risks only; FX is deferred for the current strategy

## Next implementation gate
Next card: `Tether Cross-Market Public Probe Alignment v0`

Purpose:
- Reuse probe outputs where possible.
- Confirm Upbit `USDT/KRW`.
- Re-check Bithumb `USDT/KRW` pair availability.
- Keep Binance/Bybit/OKX global references.
- Remove FX from the required path.
- Use no private API.
- Do no trading.
- Add no persistent adapter yet.

## No-trade compliance
- No private API.
- No API key / secret / token.
- No account/balance lookup.
- No order placement or order cancel.
- No withdrawal/deposit/transfer.
- No KRW deposit/withdrawal or bank account / fiat transfer implementation.
- No auto-trading.
- No Council automatic call.
- No Council decision to trade conversion.
