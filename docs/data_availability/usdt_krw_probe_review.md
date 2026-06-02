# USDT/KRW Public Probe Review and FX Source Decision v0

## Overview
This document reviews the user-observed `USDT/KRW Public Probe v0` results for the future `stablecoin_krw_premium` / `usdt_krw_kimchi_premium_v0` strategy. It is a planning and source-decision document only: it does not add live adapters, persistent adapters, OpportunityPacket builder support, readiness rules, scenario JSON, private API access, account/balance lookup, orders, transfers, or auto-trading.

The core user-intended strategy remains Mode B: `USDT/KRW Kimchi Premium / FX Basis`. Mode B requires a reliable public `USD/KRW` reference before experimental scaffolding can start.

## Probe input summary
The review is based on the user's local read-only probe results from `tools/probe_usdt_krw_sources.py`. The probe checked candidate sources from `configs/usdt_krw_probe_sources.yaml` and recorded only public-source availability/shape status.

Domestic results:
- Upbit: ok / available
- Bithumb: ok / unknown
- Coinone: skipped / unknown
- Korbit: skipped / unknown

Global results:
- Binance: ok / available
- Bybit: ok / available
- OKX: ok / available

FX results:
- Frankfurter/no-key public FX candidate: ok / unknown
- official FX source candidate: skipped / unknown
- other public FX candidate: skipped / unknown

## Source result table

| source | role | probe status | pair/reference availability | review interpretation |
|---|---|---:|---:|---|
| Upbit | domestic_usdt_krw | ok | available | Primary domestic v0 candidate for USDT/KRW bid/ask/depth, subject to future read-only fixture/scaffolding checks. |
| Bithumb | domestic_usdt_krw | ok | unknown | Secondary domestic candidate; public response shape did not prove USDT/KRW availability sufficiently for v0 primary use. |
| Coinone | domestic_usdt_krw | skipped | unknown | Candidate remains unconfirmed; no implementation until a later public-source review. |
| Korbit | domestic_usdt_krw | skipped | unknown | Candidate remains unconfirmed; no implementation until a later public-source review. |
| Binance | global_usdt_reference | ok | available | Candidate global USDT reference source. Prefer use as part of a multi-source median/reference set, not as an execution venue. |
| Bybit | global_usdt_reference | ok | available | Candidate global USDT reference source. Prefer use as part of a multi-source median/reference set, not as an execution venue. |
| OKX | global_usdt_reference | ok | available | Candidate global USDT reference source. Prefer use as part of a multi-source median/reference set, not as an execution venue. |
| Frankfurter/no-key public FX candidate | fx_reference | ok | unknown | FX source unresolved; response did not establish a reliable USD/KRW rate and timestamp basis for Mode B. |
| official FX source candidate | fx_reference | skipped | unknown | FX source unresolved; candidate needs no-key public endpoint review. |
| other public FX candidate | fx_reference | skipped | unknown | FX source unresolved; candidate needs no-key public endpoint review. |

## Domestic source decision
Domestic v0 primary candidate: Upbit USDT/KRW, because the probe showed Upbit `ok / available`.

Domestic secondary candidates: Bithumb, Coinone, and Korbit remain candidates but are not confirmed. Bithumb returned `ok / unknown`, while Coinone and Korbit remained `skipped / unknown`. They must not be treated as available domestic inputs until a later public-data check proves pair availability and response shape.

Upbit availability does not make the strategy active, does not create execution permission, and does not authorize orders or transfers. It only identifies a likely public domestic source for a future read-only experimental scaffolding card.

## Global USDT reference decision
Global v0 reference candidates: Binance, Bybit, and OKX, because the probe showed all three as `ok / available`.

The preferred future reference is a median or multi-source reference across Binance, Bybit, and OKX if their response shapes and symbols are sufficiently comparable. These sources are reference/depeg-check inputs only; they are not execution venues for this strategy in the current phase.

## FX reference decision
FX v0 source: not finalized.

The Frankfurter/no-key public FX candidate returned `ok / unknown`, and the official/other FX candidates remained `skipped / unknown`. Therefore, the USD/KRW FX reference is unresolved. Do not convert any FX candidate into a confirmed source without evidence of a reliable public USD/KRW rate, timestamp, freshness behavior, and no-key/no-private compliance.

Mode B cannot become experimental until USD/KRW FX source is confirmed.

## Current blocker
The current blocker is the unresolved `usd_krw_reference_rate` source. Without `usd_krw_reference_rate`, `fair_usdt_krw_price` cannot be calculated reliably, and `premium_mid_pct`, `premium_sell_pct`, `premium_buy_pct`, or `estimated_net_premium_pct` would be incomplete or misleading.

This blocks `stablecoin_krw_premium` from experimental scaffolding even though Upbit and the global USDT reference candidates have useful probe results.

## Recommended v0 source set
Proposed future source set after the FX blocker is resolved:

`domestic_usdt_krw_price`:
- Upbit USDT/KRW bid/ask/depth as the primary v0 domestic source.

`global_usdt_usd_reference`:
- Median of Binance, Bybit, and OKX global USDT reference values if shapes are sufficiently comparable; in short, use a median of Binance, Bybit, OKX only after shape comparability is reviewed.

`usd_krw_reference_rate`:
- Unresolved; requires FX source probe hardening.

Without `usd_krw_reference_rate`, `fair_usdt_krw_price` cannot be calculated reliably; fair_usdt_krw_price cannot be calculated reliably from domestic/global crypto data alone.

## Next gate
Next card: `USDT/KRW FX Reference Probe Hardening v0`

Purpose:
- Improve FX source candidates.
- Confirm whether a no-key USD/KRW public reference can provide reliable rate and timestamp metadata.
- Preserve no-private, no-key, and no-scraping rules.
- Do not implement the full strategy yet.
- Do not add live adapters, persistent adapters, OpportunityPacket builder support, readiness code, or scenario JSON.

## No-trade compliance
- No private API.
- No API key / secret / token.
- No account/balance lookup.
- No order placement or order cancellation.
- No withdrawal/deposit/transfer.
- No KRW deposit/withdrawal or bank account / fiat transfer implementation.
- No auto-trading.
- No Council automatic call.
- No Council decision to trade conversion.
