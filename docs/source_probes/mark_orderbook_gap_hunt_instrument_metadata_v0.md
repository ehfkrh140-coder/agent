# Mark-Orderbook Gap Hunt Instrument Metadata v0

## Purpose

Document public instrument metadata source candidates and mocked parser planning for `Mark-Orderbook Gap Hunt v0`. The prior public endpoint probes confirmed that mark price, orderbook, and top-of-book fields can be returned from user-local normal-network public endpoints, but they did not prove unit, contract size, lot size, notional, funding, fee, or slippage correctness.

This document is planning only. It does not implement runtime adapters, parser code, config registration, sampling, alerts, notification, Council auto-call, active strategy promotion, execution, private APIs, credentials, account/balance lookup, order/cancel, withdrawal/deposit/transfer, generated packets, or generated sampling outputs.

## Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains proposed / experimental-planning / inactive.
- Execution policy remains `NO_TRADE_ONLY`.
- Mark price is not executable and cannot be treated as an order price.
- Bid/ask and mark price are not enough for readiness unless instrument metadata confirms size unit, contract size, lot size, notional formula, freshness, and comparability.
- If metadata or comparability is missing, the correct decision state is `NEED_DATA`.

## Why instrument metadata is needed

The user-local endpoint evidence confirmed that public mark and orderbook/top-of-book responses exist. However, a mark/orderbook gap strategy cannot safely estimate opportunity quality until the parser understands what one unit of bid/ask size means.

Instrument metadata is required to answer:

- Is the product linear, inverse, swap, or futures?
- What is the base/quote/settle currency?
- What is one orderbook size unit?
- Is size expressed in base asset, contracts, lots, or another venue-specific unit?
- What is the contract value or multiplier?
- What is the minimum order size, quantity step, and tick size?
- How should bid/ask notional be calculated?
- Are mark response and orderbook response for the exact same instrument?
- Are funding and fee/slippage assumptions relevant to the estimated net gap?

Until these questions are resolved, the strategy may observe fields but must not classify them as `WATCH` or `COUNCIL_REVIEW_CANDIDATE`.

## Instrument metadata source matrix

| Venue | Candidate metadata endpoint | Candidate params | Public/no-key expectation | Fields to inspect | Remaining question |
| --- | --- | --- | --- | --- | --- |
| Binance USDⓈ-M Futures | `GET /fapi/v1/exchangeInfo` | optional `symbol=BTCUSDT` if supported by the endpoint behavior; otherwise filter response by symbol | Public market-data REST; no key expected | `symbol`, `pair`, `contractType`, `status`, `baseAsset`, `quoteAsset`, `marginAsset`, `pricePrecision`, `quantityPrecision`, `filters`, `PRICE_FILTER.tickSize`, `LOT_SIZE.minQty`, `LOT_SIZE.maxQty`, `LOT_SIZE.stepSize`, `MARKET_LOT_SIZE`, `MIN_NOTIONAL.notional` | Confirm quantity unit and selected-symbol notional formula for USDⓈ-M futures |
| Bybit Derivatives V5 | `GET /v5/market/instruments-info` | `category=linear` or `category=inverse`; `symbol=BTCUSDT` | Public market-data REST; no key expected | `category`, `symbol`, `contractType`, `status`, `baseCoin`, `quoteCoin`, `settleCoin`, `priceScale`, `priceFilter.tickSize`, `lotSizeFilter.minNotionalValue`, `lotSizeFilter.minOrderQty`, `lotSizeFilter.maxOrderQty`, `lotSizeFilter.qtyStep`, `fundingInterval` | Confirm size unit and notional convention by product type |
| OKX derivatives | `GET /api/v5/public/instruments` | `instType=SWAP` or `FUTURES`; `instId=BTC-USDT-SWAP` if supported by endpoint behavior | Public market-data REST; no key expected | `instType`, `instId`, `uly`, `instFamily`, `ctVal`, `ctMult`, `ctValCcy`, `settleCcy`, `tickSz`, `lotSz`, `minSz`, `state` | Confirm contract value, multiplier, lot size, size unit, and notional formula |

## Venue-specific metadata planning

### Binance USDⓈ-M Futures

Candidate metadata endpoint:

```text
GET /fapi/v1/exchangeInfo
```

Fields to inspect:

- `symbol`
- `pair`
- `contractType`
- `status`
- `baseAsset`
- `quoteAsset`
- `marginAsset`
- `pricePrecision`
- `quantityPrecision`
- `filters`
- `PRICE_FILTER.tickSize`
- `LOT_SIZE.minQty`
- `LOT_SIZE.maxQty`
- `LOT_SIZE.stepSize`
- `MARKET_LOT_SIZE`
- `MIN_NOTIONAL.notional`

Parser planning notes:

- Match `exchangeInfo.symbol` exactly to the mark/depth `symbol`.
- Treat inactive or non-trading symbols as `NEED_DATA` or `REJECT`, depending on final parser semantics.
- Extract tick size, minimum quantity, maximum quantity, quantity step, and minimum notional from filters.
- Keep quantity unit and notional formula as `NEED_DATA` until official examples or user-local metadata evidence confirm the rule for the selected symbol.

### Bybit Derivatives V5

Candidate metadata endpoint:

```text
GET /v5/market/instruments-info
```

Candidate params:

- `category=linear` or `category=inverse`
- `symbol=BTCUSDT`

Fields to inspect:

- `category`
- `symbol`
- `contractType`
- `status`
- `baseCoin`
- `quoteCoin`
- `settleCoin`
- `priceScale`
- `priceFilter.tickSize`
- `lotSizeFilter.minNotionalValue`
- `lotSizeFilter.minOrderQty`
- `lotSizeFilter.maxOrderQty`
- `lotSizeFilter.qtyStep`
- `fundingInterval`

Parser planning notes:

- Match `category` and `symbol` exactly to ticker/orderbook responses.
- Separate linear and inverse products; do not assume shared size or notional rules.
- Parse `priceFilter` and `lotSizeFilter` into normalized tick size, quantity step, min order size, max order size, and min notional fields.
- Keep size unit and product-specific notional convention as `NEED_DATA` until metadata evidence and examples are reviewed.

### OKX derivatives

Candidate metadata endpoint:

```text
GET /api/v5/public/instruments
```

Candidate params:

- `instType=SWAP` or `instType=FUTURES`
- `instId=BTC-USDT-SWAP` if supported by endpoint behavior

Fields to inspect:

- `instType`
- `instId`
- `uly`
- `instFamily`
- `ctVal`
- `ctMult`
- `ctValCcy`
- `settleCcy`
- `tickSz`
- `lotSz`
- `minSz`
- `state`

Parser planning notes:

- Match `instType` and `instId` exactly to mark/books/ticker responses.
- Treat `ctVal`, `ctMult`, `ctValCcy`, and `settleCcy` as required for notional planning.
- Parse `tickSz`, `lotSz`, and `minSz` into normalized tick size, lot size, and minimum order size.
- Keep contract value, multiplier, size unit, and notional formula as `NEED_DATA` until instrument metadata evidence is captured.

## Mocked parser fixture planning

A future parser test PR should add mocked response examples before any runtime adapter implementation. The minimum fixture set should include:

1. Binance mark response example.
2. Binance depth response example.
3. Binance `exchangeInfo` response excerpt for the same symbol.
4. Bybit ticker response example.
5. Bybit orderbook response example.
6. Bybit `instruments-info` response excerpt for the same category/symbol.
7. OKX mark-price response example.
8. OKX books or ticker response example.
9. OKX instruments response excerpt for the same `instType`/`instId`.

Fixture requirements:

- Include one valid same-instrument case per venue.
- Include one missing-metadata case that must return `NEED_DATA`.
- Include one instrument-mismatch case that must return `NEED_DATA`.
- Include one unknown-size-unit or unknown-notional case that must return `NEED_DATA`.
- Include one stale timestamp or excessive-latency case that must return `NEED_DATA` or `REJECT` according to final readiness rules.
- Use safe, synthetic, or truncated public examples only; do not include credentials or private/account data.

## Normalized parser output planning

A future parser should produce normalized planning fields such as:

- `venue_id`
- `instrument_id`
- `instrument_type`
- `mark_price`
- `index_price`
- `bid`
- `ask`
- `bid_size_raw`
- `ask_size_raw`
- `bid_size_unit`
- `ask_size_unit`
- `contract_size`
- `contract_multiplier`
- `lot_size`
- `min_order_size`
- `tick_size`
- `notional_formula`
- `bid_notional`
- `ask_notional`
- `timestamp`
- `data_age_ms`
- `freshness_pass`
- `comparability_pass`
- `required_missing_fields`

No parser code is added in this PR. These names are planning targets only and may be refined in a later mocked-parser PR.

## Decision criteria impact

- If metadata is missing, readiness state is `NEED_DATA`.
- If mark/orderbook instrument IDs do not match, readiness state is `NEED_DATA`.
- If size unit or notional formula is unknown, readiness state is `NEED_DATA`.
- If metadata is known but the gap is not positive after fee/slippage/buffer assumptions, readiness state is `REJECT`.
- `WATCH` is only possible after metadata and comparability are confirmed.
- `COUNCIL_REVIEW_CANDIDATE` requires repeated `WATCH`, persistence, and sufficient public data quality. It is still not an order instruction.
- `EXECUTION_CANDIDATE` remains forbidden in the current project phase.

## Future execution / API note

The long-term project may eventually include a shared execution/risk engine after multiple strategy decision structures are defined. That future work must be common/shared rather than strategy-specific ad hoc order code.

Future execution/API work requires separate task cards and explicit human review, including:

- credential isolation;
- dry-run and paper-trading phase;
- kill switch;
- risk limits;
- order-state machine;
- audit logs;
- rollback plan;
- no-trade policy transition plan if the project ever leaves `NO_TRADE_ONLY`.

This PR does not implement execution, API keys, private API, account/balance lookup, order placement, cancellation, withdrawal, deposit, transfer, or Council decision-to-trade conversion.

## Explicit deferrals

This planning PR explicitly defers:

- runtime adapter implementation;
- config adapter registration;
- parser implementation;
- sampling implementation;
- alert/notification expansion;
- Council auto-call;
- Council decision to trade conversion;
- active strategy promotion;
- execution/private API;
- API key/secret/token;
- auth/private headers;
- account/balance lookup;
- order/cancel;
- withdrawal/deposit/transfer;
- generated packet JSON;
- generated sampling JSON;
- live network smoke as a merge requirement.

## Next recommended step

Open a separate `Mark-Orderbook Gap Hunt User-Local Instrument Metadata Evidence v0` or `Mark-Orderbook Gap Hunt Mocked Parser Fixture Planning v0` PR. That task should remain public-read-only/no-key and should record safe metadata previews or mocked fixtures before runtime adapter/config/parser implementation is considered.
