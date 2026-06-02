# USDT/KRW Multi-Source Data Availability Matrix v0

## Overview
This document is a planning-only data availability matrix for `stablecoin_krw_premium` / `usdt_krw_kimchi_premium_v0`. It separates domestic executable/reference venues, global USDT reference venues, and USD/KRW FX reference sources before any experimental scaffolding. The read-only public probe has now been reviewed in [`docs/data_availability/usdt_krw_probe_review.md`](usdt_krw_probe_review.md); this matrix still does not add live adapters, persistent adapters, OpportunityPackets, or trading authorization.

## Strategy link
- Strategy card: [`docs/strategy_task_cards/usdt_krw_kimchi_premium.md`](../strategy_task_cards/usdt_krw_kimchi_premium.md)
- Probe review: [`docs/data_availability/usdt_krw_probe_review.md`](usdt_krw_probe_review.md)
- Strategy family: `stablecoin_krw_premium`
- Strategy id: `usdt_krw_kimchi_premium_v0`
- Status: `future`
- Execution policy: `NO_TRADE_ONLY`
- Active strategy remains `cross_exchange_spot_spread_v1`.

## Source role model

### A. Domestic USDT/KRW venues
Role:
- Observe domestic `USDT/KRW` bid/ask/depth.
- Calculate domestic premium values.
- May become execution-candidate venues in a future gated phase, but current use is read-only only.

Candidates:
- Upbit
- Bithumb
- Coinone
- Korbit

### B. Global USDT reference venues
Role:
- Check `USDT/USD`, `USDT/USDC`, or similar reference values.
- Detect possible USDT depeg conditions.
- Provide global reference support for domestic kimchi premium calculations.

Candidates:
- Binance
- Bybit
- OKX

Global references are not execution venues for this strategy in the current phase. Only public ticker/orderbook candidates are allowed; private/account/order endpoints are forbidden.

### C. USD/KRW FX reference sources
Role:
- Provide fair `USD/KRW` reference rates.
- Support `fair_usdt_krw_price` calculation.

Candidates:
- public FX API candidate
- official FX source candidate
- no-key public source candidate if available

FX sources are candidates only. The hardened public probe must verify response shape, timestamp availability, update frequency, reliability, and key requirements. A Mode B FX source must provide both a USD/KRW rate and timestamp/freshness metadata; rate-only responses are not suitable.

## Domestic executable/reference venues

| venue | role | pair_to_check | pair_availability_status | public_ticker_candidate | public_orderbook_candidate | public_market_list_candidate | timestamp_available | depth_available | fee_source | implementation_status | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Upbit | domestic USDT/KRW bid/ask/depth; possible future execution-candidate venue, read-only now | `KRW-USDT` or documented equivalent | probe_available_for_USDT_KRW | probe_available_for_USDT_KRW | probe_available_for_USDT_KRW | probe_available_for_USDT_KRW | probe_available_for_USDT_KRW | probe_available_for_USDT_KRW | manual placeholder only | already_supported_for_BTC_KRW_public_adapter; USDT/KRW future probe candidate only | User local probe result was ok / available; this is a primary v0 domestic source candidate, not an active/execution source. |
| Bithumb | domestic USDT/KRW bid/ask/depth; possible future execution-candidate venue, read-only now | `USDT_KRW` or documented equivalent | probe_unknown | probe_unknown | probe_unknown | candidate_source | probe_unknown | probe_unknown | manual placeholder only | already_supported_for_BTC_KRW_public_adapter; USDT/KRW not_implemented | User local probe result was ok / unknown; keep as secondary candidate only. |
| Coinone | domestic USDT/KRW bid/ask/depth candidate, read-only now | documented USDT/KRW symbol candidate | skipped_unknown | public ticker docs candidate | public orderbook docs candidate | public market docs candidate | unknown_until_future_probe | unknown_until_future_probe | manual placeholder only | candidate_source; not_implemented | User local probe result was skipped / unknown; no availability is confirmed. |
| Korbit | domestic USDT/KRW bid/ask/depth candidate, read-only now | documented USDT/KRW symbol candidate | skipped_unknown | candidate_source | candidate_source | candidate_source | unknown_until_future_probe | unknown_until_future_probe | manual placeholder only | candidate_source; not_implemented | User local probe result was skipped / unknown; no availability is confirmed. |

## Global USDT reference venues

| venue | reference_pair_candidates | ticker_candidate | orderbook_candidate | timestamp_available | depth_available | depeg_reference_role | implementation_status | notes |
|---|---|---|---|---|---|---|---|---|
| Binance | `USDT/USD`, `USDT/USDC`, `USDC/USDT`, documented equivalents | probe_available_for_reference | candidate_source | probe_available_for_reference | unknown_until_future_probe | Reference midpoint and depeg cross-check only | probe_available_for_reference | User local probe result was ok / available; use only as one global reference candidate. |
| Bybit | `USDT/USD`, `USDT/USDC`, `USDC/USDT`, documented equivalents | probe_available_for_reference | candidate_source | probe_available_for_reference | unknown_until_future_probe | Reference midpoint and depeg cross-check only | existing_public_adapter_for_derivatives_but_spot_usdt_reference_not_implemented; probe_available_for_reference | User local probe result was ok / available; use only as one global reference candidate. |
| OKX | `USDT/USD`, `USDT/USDC`, `USDC/USDT`, documented equivalents | probe_available_for_reference | candidate_source | probe_available_for_reference | unknown_until_future_probe | Reference midpoint and depeg cross-check only | probe_available_for_reference | User local probe result was ok / available; use only as one global reference candidate. |

## USD/KRW FX reference sources

| source | role | requires_api_key | update_frequency_known | timestamp_available | reliability_level | implementation_status | notes |
|---|---|---|---|---|---|---|---|
| Frankfurter or no-key public FX candidate | public USD/KRW FX candidate for fair-value calculation | no_key_candidate_but_unresolved | probe_unknown | probe_unknown | unresolved_candidate_source | unresolved; not_implemented | User local probe result was ok / unknown; do not use as confirmed FX source yet. |
| official FX source candidate | higher-reliability official USD/KRW reference candidate | unknown_until_fx_probe_hardening | unknown_until_fx_probe_hardening | unknown_until_fx_probe_hardening | candidate_official_reference | unresolved; not_implemented | User local probe result was skipped / unknown; source policy must determine update frequency, timestamp and licensing constraints. |
| other public market FX source candidate | additional public USD/KRW reference candidate | unknown_until_fx_probe_hardening | unknown_until_fx_probe_hardening | unknown_until_fx_probe_hardening | candidate_secondary_reference | unresolved; not_implemented | User local probe result was skipped / unknown; use only public/no-private data. |

## Recommended premium formulas

```text
fair_usdt_krw_price =
usd_krw_reference_rate * global_usdt_usd_reference
```

```text
domestic_mid =
(domestic_best_bid + domestic_best_ask) / 2
```

```text
premium_mid_pct =
(domestic_mid - fair_usdt_krw_price) / fair_usdt_krw_price * 100
```

```text
premium_sell_pct =
(domestic_best_bid - fair_usdt_krw_price) / fair_usdt_krw_price * 100
```

```text
premium_buy_pct =
(domestic_best_ask - fair_usdt_krw_price) / fair_usdt_krw_price * 100
```

```text
estimated_net_premium_pct =
premium_sell_pct
- domestic_fee_pct
- estimated_slippage_pct
- safety_buffer_pct
```

## Aggregation rules
When multiple domestic venues are available, calculate all of the following rather than relying on one venue:
- `per_venue_premium_pct`
- `domestic_best_bid_premium_pct`
- `domestic_best_ask_premium_pct`
- `domestic_median_mid_premium_pct`
- `domestic_weighted_mid_premium_pct`
- `venue_count_available`
- `source_reliability_score`

For global USDT references, calculate:
- `global_usdt_usd_mid`
- `global_usdt_usd_median`
- `global_usdt_depeg_flag`
- `global_reference_venue_count`

Aggregation must preserve source-level timestamps, reliability metadata, and venue counts so a single source cannot silently dominate the signal.

## Data availability matrix
This planning matrix intentionally marks most USDT/KRW and FX fields as `unknown_until_public_probe`. The next card must verify:
- domestic pair availability for Upbit, Bithumb, Coinone and Korbit;
- public ticker, orderbook and market-list response shapes;
- timestamp availability and staleness metadata;
- global USDT reference pair availability for Binance, Bybit and OKX;
- FX source response shape, key requirements and timestamp availability.

Probe review status: Upbit is `probe_available_for_USDT_KRW`; Bithumb is `probe_unknown`; Coinone and Korbit remain `skipped_unknown`; Binance, Bybit and OKX are `probe_available_for_reference`; FX reference remains unresolved. See [`docs/data_availability/usdt_krw_probe_review.md`](usdt_krw_probe_review.md).

## Data risks
- single venue distortion
- last_price-only premium illusion
- stale FX reference
- crypto timestamp vs FX timestamp mismatch
- USDT depeg
- shallow domestic orderbook
- exchange-specific maintenance
- public API outage
- manual fee placeholder risk
- liquidity fragmentation across venues
- regional restriction / Travel Rule / fiat transfer constraints are out of scope and must not be implemented

## Next implementation gate
Next card: `USDT/KRW Public Probe v0`

Purpose:
- Use actual public endpoint calls to verify pair availability and response shape.
- Check Upbit, Bithumb, Coinone and Korbit domestic candidates.
- Check Binance, Bybit and OKX global candidates.
- Check FX source candidates.
- Use no private API.
- Do no trading.
- Add no persistent adapter yet.

`USDT/KRW Public Probe v0` results are reviewed in [`docs/data_availability/usdt_krw_probe_review.md`](usdt_krw_probe_review.md). FX hardening adds suitability fields for rate + timestamp/freshness detection because Mode B cannot become experimental until a reliable USD/KRW FX source is confirmed. The probe is not a persistent adapter, does not create OpportunityPackets, and does not change strategy status.

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
