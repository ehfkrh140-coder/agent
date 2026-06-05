# Mark-Orderbook Gap Hunt Parser Contract v0

## Purpose

Define the future parser interface / contract for `Mark-Orderbook Gap Hunt v0` before production parser implementation.

This document is planning only. It does not implement a production parser, runtime adapter, config registration, sampling, alert/notification, Council auto-call, active strategy promotion, execution, private API, credentials, account/balance lookup, order/cancel, withdrawal/deposit/transfer, generated packet JSON, or generated sampling JSON.

## Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains proposed / experimental-planning / inactive.
- Execution policy remains `NO_TRADE_ONLY`.
- Mocked fixture tests now pin Binance / Bybit / OKX valid same-instrument planning outputs and failure / `NEED_DATA` / `REJECT` / `WATCH` cases.
- Public endpoint and metadata evidence exists from user-local normal-network probes, but parser correctness and final notional formulas are still not implemented.

## Parser input contract

A future production parser should accept one venue-specific input bundle per instrument observation.

Required input fields:

- `venue_id`: canonical venue identifier, such as `binance`, `bybit`, or `okx`.
- `parser_mode`: venue-specific parser mode. Initial planned modes:
  - `binance_usdm`
  - `bybit_linear`
  - `okx_swap`
- `raw_mark_or_ticker_response`: raw public mark-price or ticker response.
- `raw_orderbook_or_top_of_book_response`: raw public orderbook, depth, books, or ticker top-of-book response.
- `raw_instrument_metadata_response`: raw public instrument metadata response.
- `collected_at_utc`: UTC collection timestamp assigned by the caller.
- `latency_ms`: observed public request/collection latency for the bundle.
- `max_data_age_ms`: planning threshold input for freshness checks. This is a parser/readiness boundary input, not a hard-coded production threshold in this PR.

Parser inputs must be public read-only data. They must not include API keys, secrets, auth headers, account identifiers, balances, positions, order IDs, withdrawal/deposit identifiers, transfer IDs, or private endpoint payloads.

## Parser output contract

A future parser should return a normalized planning object with these fields where applicable. Missing or unknown values should be explicit `null` or listed in `required_missing_fields`; they should not be silently guessed.

Common identity and price fields:

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

Metadata and sizing fields:

- `tick_size`
- `quantity_step`
- `lot_size`
- `min_order_size`
- `min_notional`
- `contract_value`
- `contract_multiplier`
- `contract_value_currency`
- `settle_currency`
- `margin_asset`

Funding and timing fields:

- `funding_rate`
- `next_funding_time`
- `timestamp`
- `data_age_ms`

Quality and contract fields:

- `comparability_pass`
- `freshness_pass`
- `required_missing_fields`
- `parser_warnings`
- `normalized_status`: one of `OK`, `NEED_DATA`, or `REJECT`.

Planning gap fields may be included only when enough data exists:

- `long_gap_pct`, if mark/ask are comparable.
- `short_gap_pct`, if bid/mark are comparable.
- `estimated_net_gap_pct`, only after fee/slippage/buffer assumptions are available; otherwise keep it `null` or leave it to readiness.

## Parser responsibilities

The parser should:

- parse fields from raw public mark/ticker responses;
- parse fields from raw public orderbook/top-of-book responses;
- parse fields from raw public instrument metadata responses;
- verify same instrument / same category / same `instId` across mark, orderbook, and metadata inputs;
- normalize decimal numeric fields safely without lossy float assumptions in parser-level contracts;
- identify missing fields and populate `required_missing_fields`;
- identify unknown size unit or unknown notional formula and keep the output in `NEED_DATA` when those are required;
- compute planning gaps only if mark, bid/ask, and comparability checks are sufficient;
- return a `NEED_DATA` contract object instead of raising for expected missing-data cases.

The parser should not:

- call live network;
- read API keys, secrets, tokens, or auth headers;
- access private endpoints;
- decide execution;
- trigger Council;
- trigger alerts or notifications;
- write generated artifacts;
- place orders or cancellations;
- check account or balance state;
- create withdrawals, deposits, transfers, or fiat/bank flows.

## Readiness responsibilities

Readiness should consume parser output and interpret it into strategy decision states. Readiness should:

- map insufficient parser data to `NEED_DATA`;
- apply persistence rules;
- apply fee/slippage/buffer assumptions;
- apply liquidity thresholds;
- apply freshness and latency thresholds;
- decide `REJECT` when data is sufficient but the post-assumption opportunity is not positive;
- decide `WATCH` when the observation is positive enough to monitor but still not automation;
- decide `COUNCIL_REVIEW_CANDIDATE` only after repeated `WATCH` evidence and sufficient data quality;
- keep `WATCH` analysis-only;
- keep `COUNCIL_REVIEW_CANDIDATE` analysis-only;
- never treat parser output as an order instruction.

## Error handling contract

Expected future behavior:

- Malformed JSON fixture or malformed raw payload: parser error in future parser tests.
- Missing mark/ticker response: normalized output with `normalized_status=NEED_DATA`.
- Missing orderbook/top-of-book response or missing bid/ask: `NEED_DATA`.
- Missing instrument metadata: `NEED_DATA`.
- Instrument mismatch across mark/orderbook/metadata: `NEED_DATA`.
- Bybit category/type mismatch: `NEED_DATA`.
- OKX `instId` mismatch: `NEED_DATA`.
- Unknown size unit or missing notional-critical metadata: `NEED_DATA`.
- Stale timestamp / excessive latency: `NEED_DATA` or `REJECT`; final rule remains TBD until readiness thresholds are set.
- Non-positive net gap after fee/slippage/buffer: likely `REJECT` in readiness, not parser.
- Positive mark-orderbook gap with complete metadata: parser may return `OK`; readiness may classify as `WATCH` only, not execution.
- Unexpected code bug: exception.

## Test mapping

Current mocked fixture tests should map to the future parser contract as follows:

- Binance valid BTCUSDT fixture -> parser `OK` same-instrument case.
- Bybit valid BTCUSDT linear fixture -> parser `OK` same-category and same-symbol case.
- OKX valid BTC-USDT-SWAP fixture -> parser `OK` same-`instId` case.
- Missing mark/orderbook/metadata cases -> `NEED_DATA` contract tests.
- Instrument/category/`instId` mismatch cases -> `NEED_DATA` contract tests.
- Unknown size unit / missing `ctVal` or lot size -> `NEED_DATA` contract test.
- Stale timestamp / excessive latency -> `NEED_DATA` or `REJECT` depending on future threshold rule; current fixture baseline pins `NEED_DATA`.
- Non-positive gap after fee/slippage/buffer -> readiness `REJECT` contract test.
- Positive gap with complete metadata -> readiness `WATCH` contract test, not execution.
- No fixture should ever imply `execution_allowed=true`.
- No fixture should require live network or credentials.

## Venue-specific notes

### Binance USDⓈ-M planned parser mode: `binance_usdm`

- Expected public mark input: `GET /fapi/v1/premiumIndex` response.
- Expected public orderbook input: `GET /fapi/v1/depth` response.
- Expected public metadata input: `GET /fapi/v1/exchangeInfo` response.
- Same-instrument check: mark `symbol`, metadata `symbol`, and metadata `pair` should match selected instrument.
- Quantity/notional assumptions remain planning-level until final human review confirms formulas for selected products.

### Bybit linear planned parser mode: `bybit_linear`

- Expected public ticker input: `GET /v5/market/tickers` response.
- Expected public orderbook input: `GET /v5/market/orderbook` response.
- Expected public metadata input: `GET /v5/market/instruments-info` response.
- Same-instrument check: ticker `category`, orderbook category supplied by caller, metadata `category`, and symbol should be compatible.
- Quantity/notional assumptions remain planning-level until final human review confirms formulas for selected products.

### OKX swap planned parser mode: `okx_swap`

- Expected public mark input: `GET /api/v5/public/mark-price` response.
- Expected public books/ticker input: `GET /api/v5/market/books` or `GET /api/v5/market/ticker` response.
- Expected public metadata input: `GET /api/v5/public/instruments` response.
- Same-instrument check: mark, books/ticker, and metadata should use the same `instId`.
- Contract sizing must use `ctVal`, `ctMult`, `ctValCcy`, `settleCcy`, `lotSz`, and `minSz`; final notional formula remains a future parser/readiness decision.

## Future execution/API note

The user intends a future execution/risk engine only after multiple strategies have better-defined decision structures. That future engine must be common/shared, not strategy-specific ad hoc order code.

Future execution work requires a separate task card, credential isolation, dry-run/paper trading, kill switch, risk limits, order-state machine, audit logs, rollback plan, and explicit human review. This PR does not implement any part of that future execution/API layer.

## Next recommended step

After this contract is reviewed, open either:

1. `Mark-Orderbook Gap Hunt Parser Contract Tests v0`, if reviewers want test scaffolding around this interface before production code; or
2. `Mark-Orderbook Gap Hunt Production Parser v0`, if reviewers approve moving from contract to parser implementation.

Runtime adapter, config registration, sampling, alert/notification, Council auto-call, active promotion, and execution/private API work should remain separate future tasks.
