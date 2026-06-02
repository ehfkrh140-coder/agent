# USDT/KRW Public Probe Review and Source Decision v0

## Overview
This document reviews the user-observed `USDT/KRW Public Probe v0` results. It is retained as a planning and source-decision document only: it does not add live adapters, persistent adapters, OpportunityPacket builder support, readiness rules, scenario JSON, private API access, account/balance lookup, orders, transfers, or auto-trading.

Correction note: User clarified FX is out of scope. This review is retained as historical planning, but near-term strategy uses domestic USDT/KRW and global USDT reference only. The near-term strategy is now `tether_cross_market_premium` / `usdt_krw_global_reference_v0`, not the earlier FX-based Kimchi Premium / FX Basis interpretation.

## Probe input summary
Domestic results:
- Upbit: ok / available
- Bithumb: ok / unknown
- Coinone: skipped / unknown
- Korbit: skipped / unknown

Global results:
- Binance: ok / available
- Bybit: ok / available
- OKX: ok / available

FX results retained as historical context only:
- Frankfurter/no-key public FX candidate: ok / unknown
- official FX source candidate: skipped / unknown
- other public FX candidate: skipped / unknown

## Source result table

| source | role | probe_status | pair_availability | planning note |
|---|---|---|---|---|
| Upbit | domestic_usdt_krw | ok | available | Primary domestic v0 candidate for USDT/KRW bid/ask/depth, subject to `Tether Cross-Market Public Probe Alignment v0`. |
| Bithumb | domestic_usdt_krw | ok | unknown | Secondary domestic v0 candidate; re-check Bithumb USDT/KRW pair availability before scaffolding. |
| Coinone | future_domestic_expansion | skipped | unknown | Future expansion only; not v0. |
| Korbit | future_domestic_expansion | skipped | unknown | Future expansion only; not v0. |
| Binance | global_usdt_reference | ok | available | Candidate global USDT reference source. Prefer use as part of a multi-source median/reference set, not as an execution venue. |
| Bybit | global_usdt_reference | ok | available | Candidate global USDT reference source. Prefer use as part of a multi-source median/reference set, not as an execution venue. |
| OKX | global_usdt_reference | ok | available | Candidate global USDT reference source. Prefer use as part of a multi-source median/reference set, not as an execution venue. |
| Frankfurter/no-key public FX candidate | deferred_fx_reference | ok | unknown | Historical FX source unresolved; no longer required for near-term strategy. |
| official FX source candidate | deferred_fx_reference | skipped | unknown | Historical FX source unresolved; no longer required for near-term strategy. |
| other public FX candidate | deferred_fx_reference | skipped | unknown | Historical FX source unresolved; no longer required for near-term strategy. |

## Domestic source decision
Domestic v0 primary candidate: Upbit USDT/KRW, because the probe showed Upbit `ok / available`.

Domestic v0 secondary candidate: Bithumb USDT/KRW remains required for the near-term domestic spread concept, but probe output is `ok / unknown`; pair availability must be re-checked in the next public probe alignment card.

Coinone and Korbit are future domestic expansion candidates only, not v0.

## Global USDT reference decision
Global v0 reference candidates are Binance, Bybit, and OKX. They should be used first as a multi-source reference/depeg-health basket, preferably via median or other source-robust aggregation after response-shape comparability is reviewed.

Global reference venues are not automatic execution venues. Only public ticker/orderbook/reference data is allowed.

## FX reference decision
FX v0 source is not needed for the near-term strategy.

The earlier FX source work showed unresolved USD/KRW candidates, but the user clarified that USD/KRW FX is out of scope. Do not continue FX cadence work as the next step for the current user-intended strategy. Do not calculate `fair_usdt_krw_price`, and do not calculate `premium_pct` against USD/KRW in current scope.

## Current blocker
The previous FX blocker no longer blocks near-term work because FX is no longer a required source. The current blocker is alignment of the public probe results with the reframed source set:
- Confirm Upbit `USDT/KRW` remains available.
- Re-check Bithumb `USDT/KRW` pair availability.
- Confirm Binance/Bybit/OKX global reference symbols are comparable enough for a depeg/reference basket.
- Remove FX from the required path.

## Recommended v0 source set
Proposed future source set for `tether_cross_market_premium`:

`domestic_usdt_krw_price` / domestic spread source:
- Upbit `USDT/KRW` bid/ask/depth as primary confirmed domestic source.
- Bithumb `USDT/KRW` bid/ask/depth as required domestic counterpart after re-check.

`global_usdt_reference_health`:
- Median of Binance, Bybit, and OKX global USDT reference mids if shapes and symbols are sufficiently comparable.

`usd_krw_reference_rate`:
- Out of current scope; not required.

## Next gate
Next card: `Tether Cross-Market Public Probe Alignment v0`

Purpose:
- Reuse existing probe outputs where possible.
- Confirm Upbit `USDT/KRW`.
- Re-check Bithumb `USDT/KRW` pair availability.
- Keep Binance/Bybit/OKX global references.
- Remove FX from the required path.
- No adapter yet.
- No trading.

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
