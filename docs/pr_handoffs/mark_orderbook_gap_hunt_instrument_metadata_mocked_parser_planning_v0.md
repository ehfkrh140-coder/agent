# Mark-Orderbook Gap Hunt Instrument Metadata and Mocked Parser Planning v0 Handoff

## 1. Purpose

Document instrument metadata source candidates and mocked parser planning for `Mark-Orderbook Gap Hunt v0` after user-local public endpoint probes confirmed mark/orderbook/top-of-book field availability.

This is a documentation/planning PR only. It does not implement runtime adapters, parser code, config registration, sampling, alerts, notification, Council auto-call, active promotion, execution, private APIs, generated packet JSON, or generated sampling JSON.

## 2. Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains proposed / experimental-planning / inactive.
- Execution policy remains `NO_TRADE_ONLY`.
- Prior public source docs identified Binance USDⓈ-M Futures, Bybit Derivatives V5, and OKX derivatives mark/orderbook candidates.
- Prior user-local endpoint evidence showed all seven mark/orderbook/top-of-book probes returned `STATUS: 200`.
- That evidence confirmed reachability and response-shape availability, but not unit, notional, contract-size, fee, funding, slippage, parser correctness, or profitability.

## 3. Why metadata is needed

Mark price and orderbook/top-of-book fields are insufficient by themselves because derivatives orderbook sizes can represent base units, contracts, lots, or venue-specific units. A future parser must understand instrument metadata before it can compute bid/ask notional or decide whether a mark/orderbook gap is meaningful.

Metadata is required to verify:

- product type and instrument identity;
- base, quote, margin, and settlement assets;
- contract value and multiplier;
- tick size;
- lot size;
- minimum order size;
- quantity step;
- minimum notional;
- bid/ask size unit;
- notional calculation rule;
- whether mark, ticker, and orderbook responses are comparable for the exact same symbol/instrument.

Without this metadata, the correct readiness state is `NEED_DATA`.

## 4. Instrument metadata source matrix

| Venue | Candidate metadata endpoint | Params to plan | Fields to inspect | Remaining question |
| --- | --- | --- | --- | --- |
| Binance USDⓈ-M Futures | `GET /fapi/v1/exchangeInfo` | optional `symbol=BTCUSDT` if supported; otherwise filter response by `symbol` | `symbol`, `pair`, `contractType`, `status`, `baseAsset`, `quoteAsset`, `marginAsset`, `pricePrecision`, `quantityPrecision`, `filters`, `PRICE_FILTER.tickSize`, `LOT_SIZE.minQty`, `LOT_SIZE.maxQty`, `LOT_SIZE.stepSize`, `MARKET_LOT_SIZE`, `MIN_NOTIONAL.notional` | quantity unit and notional formula for selected symbol |
| Bybit Derivatives V5 | `GET /v5/market/instruments-info` | `category=linear` or `inverse`; `symbol=BTCUSDT` | `category`, `symbol`, `contractType`, `status`, `baseCoin`, `quoteCoin`, `settleCoin`, `priceScale`, `priceFilter.tickSize`, `lotSizeFilter.minNotionalValue`, `lotSizeFilter.minOrderQty`, `lotSizeFilter.maxOrderQty`, `lotSizeFilter.qtyStep`, `fundingInterval` | size unit and notional convention by product type |
| OKX derivatives | `GET /api/v5/public/instruments` | `instType=SWAP` or `FUTURES`; `instId=BTC-USDT-SWAP` if supported | `instType`, `instId`, `uly`, `instFamily`, `ctVal`, `ctMult`, `ctValCcy`, `settleCcy`, `tickSz`, `lotSz`, `minSz`, `state` | contract value, multiplier, lot size, size unit, and notional formula |

## 5. Mocked parser planning

A future parser test PR should add mocked response examples before runtime implementation. Required mocked examples:

- Binance mark response example.
- Binance depth response example.
- Binance `exchangeInfo` response excerpt.
- Bybit ticker response example.
- Bybit orderbook response example.
- Bybit `instruments-info` response excerpt.
- OKX mark-price response example.
- OKX books/ticker response example.
- OKX instruments response excerpt.

The mocked parser fixtures should cover:

- valid same-instrument metadata and market-data pairs;
- missing metadata -> `NEED_DATA`;
- mark/orderbook instrument mismatch -> `NEED_DATA`;
- unknown size unit or notional formula -> `NEED_DATA`;
- stale timestamps or excessive latency -> `NEED_DATA` or `REJECT`, depending on the final readiness policy;
- no credential/private/account/order/transfer data.

## 6. Normalized output planning

A future normalized parser output should plan for:

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

These fields are planning targets only. This PR does not add parser code, schema code, runtime adapters, config registration, or tests.

## 7. Decision criteria impact

- If metadata is missing, state is `NEED_DATA`.
- If mark/orderbook instrument IDs do not match, state is `NEED_DATA`.
- If size unit or notional formula is unknown, state is `NEED_DATA`.
- If metadata is known but the gap is not positive after fee/slippage/buffer, state is `REJECT`.
- `WATCH` is only possible after metadata and comparability are confirmed.
- `COUNCIL_REVIEW_CANDIDATE` requires repeated `WATCH`, persistence, and sufficient public data quality. It is not an order instruction.
- `EXECUTION_CANDIDATE` remains forbidden in the current project phase.

## 8. Future execution/API note

The user direction is to defer alert/notification and execution/API work until multiple strategy decision structures are better defined. Future execution/risk work must be common/shared, not strategy-specific ad hoc order code.

Any future execution/API track requires separate task cards, credential isolation, dry-run/paper-trading, a kill switch, risk limits, an order-state machine, audit logs, rollback planning, and explicit human review.

This PR does not implement that future execution track.

## 9. Changed files

- Added: `docs/source_probes/mark_orderbook_gap_hunt_instrument_metadata_v0.md`.
- Added: `docs/pr_handoffs/mark_orderbook_gap_hunt_instrument_metadata_mocked_parser_planning_v0.md`.
- No `src/**` changes.
- No `configs/**` changes.
- No `tests/**` changes.
- No `data/generated_packets/**`, `data/market_samples/**`, or `data/council_sessions/**` changes.
- No Council runtime, notification/alert runtime, Gemini runtime, or prompt changes.

## 10. Tests run

### Git status

```text
git status
```

Result: passed. The branch was `mark-orderbook-gap-instrument-metadata-planning-v0`; only the two allowed documentation files were untracked before staging.

### Git diff name check

```text
git diff --name-only
```

Result: passed. No tracked-file diff was shown before staging because the two new documentation files were still untracked.

### Commit diff name check

```text
git diff --name-only HEAD~1..HEAD
```

Result: passed after commit; output contained only `docs/pr_handoffs/mark_orderbook_gap_hunt_instrument_metadata_mocked_parser_planning_v0.md` and `docs/source_probes/mark_orderbook_gap_hunt_instrument_metadata_v0.md`.

### Full unit test

```text
python -m unittest discover -s tests
```

Result: passed. `Ran 249 tests in 12.274s` and ended with `OK`.

### No-trade safety check

```text
rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md
```

Result: completed. The scan returned existing documentation/test/runtime references plus this PR's explicit no-trade deferrals; this PR added no runtime, config, credential, private API, account/balance, order/cancel, withdrawal/deposit/transfer, or execution surface.

### Active strategy check

```text
rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md
```

Result: completed. Existing references still identify `cross_exchange_spot_spread_v1` as active and keep `mark_orderbook_gap_hunt_v0` proposed/inactive/NO_TRADE_ONLY.

### Final status check

```text
git status --short
```

Result: passed before staging with only the two allowed documentation files untracked and no generated packet, sampling, or Council-session artifacts present.

## 11. Risks

- Metadata documentation can change before implementation.
- Metadata endpoint reachability in user-local or deployment environments still needs separate evidence.
- Incorrect unit, contract, lot, or notional assumptions could create false positives.
- Funding, fee, and slippage handling is still undefined for strategy readiness.
- Mark price is not executable and must not be treated as an order price.
- Future work must not promote this strategy to active automatically.

## 12. Rollback plan

- Revert `docs/source_probes/mark_orderbook_gap_hunt_instrument_metadata_v0.md` and `docs/pr_handoffs/mark_orderbook_gap_hunt_instrument_metadata_mocked_parser_planning_v0.md`.
- Re-run `python -m unittest discover -s tests` if a rollback PR is opened.
- Confirm active strategy remains `cross_exchange_spot_spread_v1`.
- Confirm no generated packet/sampling/Council-session JSON is committed.

## 13. Human review required

Reviewers should inspect:

1. `docs/source_probes/mark_orderbook_gap_hunt_instrument_metadata_v0.md`
2. `docs/pr_handoffs/mark_orderbook_gap_hunt_instrument_metadata_mocked_parser_planning_v0.md`
3. Prior user-local endpoint evidence: `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_public_endpoint_probe_v0.md`
4. Prior source-probe doc: `docs/source_probes/mark_orderbook_gap_hunt_public_sources_v0.md`
5. Strategy card: `docs/strategy_task_cards/mark_orderbook_gap_hunt.md`

## 14. No-trade compliance

- private API: no
- API key/secret/token: no
- auth/private headers: no
- account/balance lookup: no
- order/cancel: no
- withdrawal/deposit/transfer: no
- fiat/bank transfer: no
- auto-trading: no
- Council auto-call: no
- Council decision to trade conversion: no
- active strategy promotion: no
- alert expansion: no
- notification expansion: no
- generated packet JSON commit: no
- generated sampling JSON commit: no
- runtime adapter implementation: no
- config adapter registration: no
- parser implementation: no
- sampling implementation: no
- live network smoke as merge requirement: no

## 15. Next recommended step

Open a separate `Mark-Orderbook Gap Hunt User-Local Instrument Metadata Evidence v0` or `Mark-Orderbook Gap Hunt Mocked Parser Fixture Planning v0` PR. It should remain public-read-only/no-key and should collect safe metadata previews or mocked fixtures before runtime adapter/config/parser work is considered.
