# USDT/KRW Multi-Source Data Availability Matrix v0

## Overview
This document is a planning-only data availability matrix for `stablecoin_krw_premium` / `usdt_krw_kimchi_premium_v0`. It separates domestic executable/reference venues, global USDT reference venues, and USD/KRW FX reference sources before any experimental scaffolding. It does not confirm pair availability, implement public probes, add live adapters, or authorize trading.

## Strategy link
- Strategy card: [`docs/strategy_task_cards/usdt_krw_kimchi_premium.md`](../strategy_task_cards/usdt_krw_kimchi_premium.md)
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

FX sources are candidates only. The next public probe must verify response shape, timestamp availability, update frequency, reliability, and key requirements.

## Domestic executable/reference venues

| venue | role | pair_to_check | pair_availability_status | public_ticker_candidate | public_orderbook_candidate | public_market_list_candidate | timestamp_available | depth_available | fee_source | implementation_status | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Upbit | domestic USDT/KRW bid/ask/depth; possible future execution-candidate venue, read-only now | `KRW-USDT` or documented equivalent | unknown_until_public_probe | candidate_source; BTC/KRW public adapter exists but USDT/KRW not verified | candidate_source; BTC/KRW orderbook adapter exists but USDT/KRW not verified | candidate_source | unknown_until_public_probe | unknown_until_public_probe | manual placeholder only | already_supported_for_BTC_KRW_public_adapter; USDT/KRW not_implemented | Do not confirm tradability in this document; next public probe checks pair availability. |
| Bithumb | domestic USDT/KRW bid/ask/depth; possible future execution-candidate venue, read-only now | `USDT_KRW` or documented equivalent | unknown_until_public_probe | candidate_source; BTC/KRW public adapter exists but USDT/KRW not verified | candidate_source; BTC/KRW orderbook adapter exists but USDT/KRW not verified | candidate_source | unknown_until_public_probe | unknown_until_public_probe | manual placeholder only | already_supported_for_BTC_KRW_public_adapter; USDT/KRW not_implemented | Do not confirm tradability in this document; next public probe checks pair availability. |
| Coinone | domestic USDT/KRW bid/ask/depth candidate, read-only now | documented USDT/KRW symbol candidate | unknown_until_public_probe | public ticker docs candidate | public orderbook docs candidate | public market docs candidate | unknown_until_public_probe | unknown_until_public_probe | manual placeholder only | candidate_source; not_implemented | Public ticker/orderbook/market docs must be reviewed by a later probe card. |
| Korbit | domestic USDT/KRW bid/ask/depth candidate, read-only now | documented USDT/KRW symbol candidate | unknown_until_public_probe | candidate_source | candidate_source | candidate_source | unknown_until_public_probe | unknown_until_public_probe | manual placeholder only | unknown_until_public_probe; not_implemented | Availability and public response shape are unknown until a later public probe. |

## Global USDT reference venues

| venue | reference_pair_candidates | ticker_candidate | orderbook_candidate | timestamp_available | depth_available | depeg_reference_role | implementation_status | notes |
|---|---|---|---|---|---|---|---|---|
| Binance | `USDT/USD`, `USDT/USDC`, `USDC/USDT`, documented equivalents | candidate_source | candidate_source | unknown_until_public_probe | unknown_until_public_probe | Reference midpoint and depeg cross-check only | candidate_source | Not an execution target here; use public ticker/orderbook only. |
| Bybit | `USDT/USD`, `USDT/USDC`, `USDC/USDT`, documented equivalents | candidate_source | candidate_source | unknown_until_public_probe | unknown_until_public_probe | Reference midpoint and depeg cross-check only | existing_public_adapter_for_derivatives_but_spot_usdt_reference_not_implemented | Existing public adapter is derivatives-oriented; spot USDT reference is not implemented. |
| OKX | `USDT/USD`, `USDT/USDC`, `USDC/USDT`, documented equivalents | candidate_source | candidate_source | unknown_until_public_probe | unknown_until_public_probe | Reference midpoint and depeg cross-check only | candidate_source | Not an execution target here; use public ticker/orderbook only. |

## USD/KRW FX reference sources

| source | role | requires_api_key | update_frequency_known | timestamp_available | reliability_level | implementation_status | notes |
|---|---|---|---|---|---|---|---|
| Frankfurter or no-key public FX candidate | public USD/KRW FX candidate for fair-value calculation | unknown_until_public_probe | unknown_until_public_probe | unknown_until_public_probe | candidate_source | candidate_source; not_implemented | Do not assume suitability; probe response shape and timestamp first. |
| official FX source candidate | higher-reliability official USD/KRW reference candidate | unknown_until_public_probe | unknown_until_public_probe | unknown_until_public_probe | candidate_official_reference | candidate_source; not_implemented | Source policy must determine update frequency, timestamp and licensing constraints. |
| other public market FX source candidate | additional public USD/KRW reference candidate | unknown_until_public_probe | unknown_until_public_probe | unknown_until_public_probe | candidate_secondary_reference | candidate_source; not_implemented | Use only public/no-private data; next probe compares shape and staleness metadata. |

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

No pair availability is confirmed by this document.

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

This work does not implement the public probe. It only prepares the matrix for that later documentation/probe task.

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
