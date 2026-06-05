# Mark-Orderbook Gap Hunt Public Sources v0

## Purpose

Document candidate public, no-key market-data sources for the proposed `Mark-Orderbook Gap Hunt v0` strategy. This is source/probe planning only. It does not implement runtime adapters, parsers, config registration, sampling, alerts, Council auto-calls, execution, private APIs, credentials, account/balance lookup, orders, transfers, generated packets, or generated sampling outputs.

## Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains proposed / experimental-planning / inactive.
- Current project scope remains `NO_TRADE_ONLY`.
- Mark price is not executable. Any future strategy must compare mark price against executable bid/ask and validated orderbook size, unit, notional, fee/slippage, latency, freshness, and venue health.
- If derivative unit/contract size or mark-vs-orderbook comparability is unclear, the correct decision state is `NEED_DATA`.

## Reference URLs checked / recorded

Official or exchange-hosted documentation references to review again during the next probe PR:

- Binance USDⓈ-M Futures mark price: `https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Mark-Price`
- Binance USDⓈ-M Futures order book: `https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Order-Book`
- Bybit V5 tickers: `https://bybit-exchange.github.io/docs/v5/market/tickers`
- Bybit V5 orderbook: `https://bybit-exchange.github.io/docs/v5/market/orderbook`
- OKX public mark price: `https://www.okx.com/docs-v5/en/#public-data-rest-api-get-mark-price`
- OKX market books: `https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-order-book`
- OKX market ticker: `https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-ticker`

Codex workspace direct HTTP access to exchange documentation/endpoints may be blocked by the existing network tunnel `403 Forbidden`. Treat that as an environment limitation, not a code/config failure. This document records source candidates and response-shape expectations; it is not live endpoint evidence.

## Venue source matrix

| Venue | Product scope | Mark endpoint candidate | Orderbook / best bid-ask endpoint candidate | Public / no-key expectation | Symbol / instrument format | Primary fields to inspect | Unit / notional status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Binance USDⓈ-M Futures | Linear USDT/BUSD-margined futures/perpetuals | `GET /fapi/v1/premiumIndex` | `GET /fapi/v1/depth` | Public market-data REST; no key expected | Uppercase futures symbol such as `BTCUSDT` | `markPrice`, `indexPrice`, `lastFundingRate`, `time`; depth `bids`, `asks`, event/transaction timestamps if present | Price/qty arrays are available, but exact quantity unit and notional convention must be confirmed before implementation |
| Bybit Derivatives V5 | `linear` / `inverse` derivatives categories | `GET /v5/market/tickers` | `GET /v5/market/orderbook` | Public market-data REST; no key expected | `category=linear` or `category=inverse`, uppercase symbol such as `BTCUSDT` | Ticker `markPrice`, `indexPrice`, `bid1Price`, `ask1Price`, `bid1Size`, `ask1Size`, timestamp; orderbook `b`, `a`, `ts`, `cts`, `seq` | Size unit differs by product and must be confirmed with instrument metadata before notional calculation |
| OKX derivatives | `SWAP` / `FUTURES` derivatives | `GET /api/v5/public/mark-price` | `GET /api/v5/market/books`; optional `GET /api/v5/market/ticker` for top-of-book | Public market-data REST; no key expected | `instType=SWAP` or `FUTURES`, `instId` such as `BTC-USDT-SWAP` or `BTC-USD-...` futures | Mark `markPx`, `ts`, `instType`, `instId`; books `bids`, `asks`, `ts`; ticker `bidPx`, `bidSz`, `askPx`, `askSz`, `ts` | Contract size / lot size / quote/base meaning must be confirmed from instrument metadata before notional calculation |

## Endpoint / field findings

### Binance USDⓈ-M Futures

Candidate mark endpoint:

```text
GET /fapi/v1/premiumIndex
```

Fields to plan for:

- `symbol`
- `markPrice`
- `indexPrice`
- `lastFundingRate` / funding-related field
- `time`

Candidate orderbook endpoint:

```text
GET /fapi/v1/depth
```

Fields to plan for:

- `lastUpdateId`
- timestamp fields such as `E` / `T` when present in the futures depth response
- `bids` as arrays of `[price, quantity]`
- `asks` as arrays of `[price, quantity]`

Implementation blockers / `NEED_DATA` until confirmed:

- exact symbol universe and active contract filtering;
- quantity unit and notional rule for the selected USDⓈ-M instrument;
- whether the mark endpoint and depth endpoint refer to the exact same contract symbol;
- whether timestamps are aligned enough for mark-vs-orderbook comparison.

### Bybit Derivatives V5

Candidate ticker endpoint:

```text
GET /v5/market/tickers
```

Required params to plan for:

- `category=linear` or `category=inverse`
- `symbol=BTCUSDT` style uppercase symbol

Fields to plan for:

- `markPrice`
- `indexPrice`
- `bid1Price`
- `ask1Price`
- `bid1Size`
- `ask1Size`
- `fundingRate`
- `nextFundingTime`
- response timestamp / `time`

Candidate orderbook endpoint:

```text
GET /v5/market/orderbook
```

Fields to plan for:

- `s` symbol
- `b` bid levels, where each level is `[price, size]`
- `a` ask levels, where each level is `[price, size]`
- `ts` system-generated timestamp
- `cts` matching-engine timestamp
- `u` update ID
- `seq` cross sequence

Implementation blockers / `NEED_DATA` until confirmed:

- whether `linear` or `inverse` is in scope for v0;
- size unit by product type;
- notional calculation rule and contract multiplier if applicable;
- whether ticker top-of-book and orderbook best bid/ask match sufficiently for the same symbol;
- latency/freshness thresholds.

### OKX derivatives

Candidate mark endpoint:

```text
GET /api/v5/public/mark-price
```

Required params to plan for:

- `instType=SWAP` or `instType=FUTURES`
- optional / filtered `instId`, e.g. `BTC-USDT-SWAP`

Fields to plan for:

- `instType`
- `instId`
- `markPx`
- `ts`

Candidate orderbook endpoint:

```text
GET /api/v5/market/books
```

Fields to plan for:

- `asks`
- `bids`
- `ts`
- sequence/checksum fields if present in the response

Optional top-of-book/ticker endpoint:

```text
GET /api/v5/market/ticker
```

Fields to plan for:

- `instId`
- `bidPx`
- `bidSz`
- `askPx`
- `askSz`
- `ts`

Implementation blockers / `NEED_DATA` until confirmed:

- exact `instType` and `instId` set for v0;
- contract size, lot size, and notional rules for chosen derivatives instruments;
- whether `markPx` and books/ticker are same instrument and same settlement convention;
- whether size unit is contracts, base currency, or another unit;
- timestamp and latency consistency.

## Cross-venue comparability checks

A future implementation must not compare mark and orderbook data unless:

- mark and bid/ask are from the same venue and same instrument;
- instrument type is explicit (`linear`, `inverse`, `SWAP`, `FUTURES`, etc.);
- symbol / instrument ID maps unambiguously to one contract;
- size unit and contract multiplier are known;
- notional calculation is deterministic;
- mark timestamp and orderbook timestamp are fresh enough;
- orderbook depth is sufficient for the target notional;
- fee/slippage/buffer placeholders are defined before net-gap interpretation.

If any of these are unknown, classify as `NEED_DATA`, not `WATCH`.

## Live-network limitation

No live network smoke is required for this PR. Codex workspace network access to exchange sites/endpoints can fail with tunnel `403 Forbidden`; that should be recorded as an environment limitation, not a strategy or parser failure.

The next evidence step should be one of:

1. user-local public endpoint probe evidence with safe response previews; or
2. mocked parser planning based on official response examples.

Neither follow-up should add private API, credentials, account lookup, orders, transfers, alerts, Council auto-calls, active promotion, or execution.

## Explicit deferrals

This source/probe document explicitly defers:

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
