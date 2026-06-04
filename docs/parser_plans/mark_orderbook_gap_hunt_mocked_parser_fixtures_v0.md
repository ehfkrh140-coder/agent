# Mark-Orderbook Gap Hunt Mocked Parser Fixtures v0

## Purpose

Plan the mocked fixture groups and expected normalized parser outputs for a future `Mark-Orderbook Gap Hunt v0` parser test PR.

This document is planning only. It does not implement runtime adapters, parser code, config registration, tests, sampling, alerts, notification, Council auto-call, active strategy promotion, execution, private APIs, credentials, account/balance lookup, order/cancel, withdrawal/deposit/transfer, generated packets, or generated sampling outputs.

## Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains proposed / experimental-planning / inactive.
- Execution policy remains `NO_TRADE_ONLY`.
- User-local public endpoint evidence confirmed mark/orderbook/top-of-book field availability.
- User-local metadata evidence confirmed core instrument metadata field availability.
- Parser correctness, final notional formulas, fee/slippage/funding treatment, and readiness thresholds are still not implemented or proven.

## Fixture group summary

### Binance fixture group

Required mocked fixtures:

1. Binance mark response fixture from `GET /fapi/v1/premiumIndex`.
2. Binance depth response fixture from `GET /fapi/v1/depth`.
3. Binance `exchangeInfo` BTCUSDT metadata fixture from `GET /fapi/v1/exchangeInfo`.

Expected normalized output planning:

- `venue_id`: `binance`
- `instrument_id`: `BTCUSDT`
- `instrument_type`: `linear_perpetual` or equivalent planning label
- `mark_price`: parsed decimal from mark response
- `index_price`: parsed decimal from mark response
- `bid`: best bid price from depth
- `ask`: best ask price from depth
- `bid_size_raw`: best bid size from depth
- `ask_size_raw`: best ask size from depth
- `tick_size`: `0.10`
- `quantity_step`: `0.001`
- `min_order_size`: `0.001`
- `min_notional`: `50`
- `margin_asset`: `USDT`
- `comparability_pass`: `true` only when mark/depth/metadata all use the same `BTCUSDT` symbol and timestamps are acceptable
- `required_missing_fields`: `[]` for the valid same-instrument fixture

### Bybit fixture group

Required mocked fixtures:

1. Bybit ticker response fixture from `GET /v5/market/tickers`.
2. Bybit orderbook response fixture from `GET /v5/market/orderbook`.
3. Bybit `instruments-info` BTCUSDT metadata fixture from `GET /v5/market/instruments-info`.

Expected normalized output planning:

- `venue_id`: `bybit`
- `instrument_id`: `BTCUSDT`
- `instrument_type`: `linear_perpetual`
- `mark_price`: parsed decimal from ticker
- `index_price`: parsed decimal from ticker
- `bid`: best bid price from orderbook
- `ask`: best ask price from orderbook
- `bid_size_raw`: best bid size from orderbook
- `ask_size_raw`: best ask size from orderbook
- `tick_size`: `0.10`
- `quantity_step`: `0.001`
- `min_order_size`: `0.001`
- `min_notional`: `5`
- `settle_coin`: `USDT`
- `funding_interval`: `480`
- `comparability_pass`: `true` only when ticker/orderbook/metadata all use the same `category=linear` and `symbol=BTCUSDT`, and timestamps are acceptable
- `required_missing_fields`: `[]` for the valid same-instrument fixture

### OKX fixture group

Required mocked fixtures:

1. OKX mark-price response fixture from `GET /api/v5/public/mark-price`.
2. OKX books or ticker response fixture from `GET /api/v5/market/books` or `GET /api/v5/market/ticker`.
3. OKX instruments BTC-USDT-SWAP metadata fixture from `GET /api/v5/public/instruments`.

Expected normalized output planning:

- `venue_id`: `okx`
- `instrument_id`: `BTC-USDT-SWAP`
- `instrument_type`: `linear_swap`
- `mark_price`: parsed decimal from mark-price
- `bid`: best bid price from books or `bidPx` from ticker
- `ask`: best ask price from books or `askPx` from ticker
- `bid_size_raw`: best bid size from books or `bidSz` from ticker
- `ask_size_raw`: best ask size from books or `askSz` from ticker
- `contract_value`: `0.01`
- `contract_multiplier`: `1`
- `contract_value_currency`: `BTC`
- `settle_currency`: `USDT`
- `tick_size`: `0.1`
- `lot_size`: `0.01`
- `min_order_size`: `0.01`
- `comparability_pass`: `true` only when mark/books-or-ticker/metadata all use the same `instId=BTC-USDT-SWAP` and timestamps are acceptable
- `required_missing_fields`: `[]` for the valid same-instrument fixture

## Failure / NEED_DATA fixture cases

Future parser tests should separate valid same-instrument cases from failure/`NEED_DATA` cases.

Required failure cases:

- Missing mark response -> `NEED_DATA`.
- Missing orderbook or missing bid/ask -> `NEED_DATA`.
- Missing metadata -> `NEED_DATA`.
- Instrument mismatch, such as mark `BTCUSDT` but orderbook `ETHUSDT` -> `NEED_DATA`.
- Bybit category/type mismatch, such as ticker `linear` but orderbook `inverse` -> `NEED_DATA`.
- OKX `instId` mismatch between mark, books/ticker, and metadata -> `NEED_DATA`.
- Unknown size unit or missing `ctVal` / lot size -> `NEED_DATA`.
- Stale timestamp or excessive latency -> `NEED_DATA` or `REJECT` according to future readiness rules.
- Non-positive gap after fee/slippage/buffer -> `REJECT`.
- Positive mark-orderbook gap with metadata and comparability confirmed -> `WATCH` only, not execution.

Each failure fixture should also populate `required_missing_fields` or an equivalent diagnostic list so reviewers can see why the parser refused to classify the observation above `NEED_DATA`.

## Notional formula planning

No notional formula is implemented in this PR.

Planning assumptions to test later:

- Binance / Bybit linear candidate: approximate planning notional may be `price * quantity` if, and only if, quantity unit is confirmed as base asset amount.
- Keep Binance / Bybit notional as `NEED_DATA` until parser test fixtures explicitly confirm the base-quantity assumption and document source evidence.
- OKX: contract value and `ctValCcy` must be used. Planning notional needs an explicit formula using `price`, `size`, `ctVal`, `ctMult`, `ctValCcy`, and `settleCcy`.
- Keep OKX notional as `NEED_DATA` until the fixture rule is agreed and documented.

## Decision criteria mapping

- Missing metadata -> `NEED_DATA`.
- Instrument mismatch -> `NEED_DATA`.
- Size unit unknown -> `NEED_DATA`.
- Notional formula unknown -> `NEED_DATA`.
- Data is sufficient but no positive net gap after fee/slippage/buffer -> `REJECT`.
- Positive observation with complete metadata and comparability -> `WATCH`.
- Repeated `WATCH` with persistence may become `COUNCIL_REVIEW_CANDIDATE` in a future phase, but it is still not an order instruction.
- `EXECUTION_CANDIDATE` remains forbidden in the current project phase.

## Expected parser test assertions

A future parser test PR should assert at least:

- Valid fixture outputs normalize venue, instrument, mark, bid, ask, metadata, and comparability fields.
- Valid fixture outputs include `required_missing_fields: []`.
- Missing fixture sections return `NEED_DATA` and name the missing fields.
- Mismatched instruments return `NEED_DATA` and identify the mismatch.
- Unknown notional assumptions do not produce `WATCH`.
- `WATCH` never implies Council auto-call, active strategy promotion, or execution.

## Future execution / API note

The user direction is to defer alert/notification and execution/API work until multiple strategy decision structures are better defined. Any future execution/risk engine must be common/shared rather than strategy-specific ad hoc order code.

Future execution/API work requires separate task cards, credential isolation, dry-run/paper trading, a kill switch, risk limits, an order-state machine, audit logs, rollback planning, and explicit human review.

This PR does not implement that future execution track.

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

Open a separate `Mark-Orderbook Gap Hunt Mocked Parser Tests v0` PR only after this fixture plan is reviewed. That future task may add tests/fixtures, but runtime adapter/config/parser implementation should remain out of scope unless explicitly approved.
