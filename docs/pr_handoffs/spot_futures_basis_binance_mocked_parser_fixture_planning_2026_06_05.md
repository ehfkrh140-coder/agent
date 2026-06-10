# Spot-Futures Basis Binance Mocked Parser Fixture Planning v0

## 1. 작업 목적

이 문서는 Binance-first `spot_futures_basis_v0` implementation이 common source contract를 만족하도록 mocked parser fixture 설계를 먼저 정의하는 docs-only fixture/test-design planning handoff다.

Scope:

- Binance-first implementation이 common source contract를 만족하도록 mocked fixture 설계를 먼저 정의한다.
- Fixture planning은 implementation 전에 parser/readiness behavior를 안전하게 고정하기 위한 단계다.
- 이 문서는 implementation이 아니라 planning이다.
- Fixture 파일도 생성하지 않는다.
- `NO_TRADE_ONLY`를 유지한다.
- Generated packet/sampling JSON은 smoke artifact이며 commit하지 않는다.

This PR does not add fixture JSON, tests, adapters, parsers, readiness helpers, registry/config entries, endpoint calls, runtime behavior, generated data, alerts, Council auto-call, execution, or active strategy promotion.

## 2. Scope

Initial fixture planning target:

- `strategy_family`: `spot_futures_basis`
- `strategy_id`: `spot_futures_basis_v0`
- `status`: proposed / experimental / non-active / `NO_TRADE_ONLY`
- Spot venue: Binance Spot
- Perp venue: Binance USDⓈ-M Futures
- Asset: BTC
- Quote: USDT
- Spot symbol: `BTCUSDT`
- Perp symbol: `BTCUSDT`
- Comparison type: same-exchange spot/perp basis
- Source contract: `SpotObservationNormalized` + `PerpObservationNormalized` from common source contract planning

Boundary:

- Binance is the first reference venue only.
- This planning must not create a Binance-only strategy shape.
- The future fixture expectations should map into the common contract so that Bybit / OKX can later add venue-specific source mappings without duplicating strategy logic.

## 3. Proposed fixture files

The following are candidate fixture paths for a future implementation/test PR. This PR does not create these files:

- `tests/fixtures/market_data/spot_futures_basis/binance_spot_book_ticker_btcusdt.json`
- `tests/fixtures/market_data/spot_futures_basis/binance_spot_depth_btcusdt.json`
- `tests/fixtures/market_data/spot_futures_basis/binance_spot_exchange_info_btcusdt.json`
- `tests/fixtures/market_data/spot_futures_basis/binance_futures_book_ticker_btcusdt.json`
- `tests/fixtures/market_data/spot_futures_basis/binance_futures_depth_btcusdt.json`
- `tests/fixtures/market_data/spot_futures_basis/binance_futures_premium_index_btcusdt.json`
- `tests/fixtures/market_data/spot_futures_basis/binance_futures_exchange_info_btcusdt.json`

Fixture guardrails:

- These are candidate paths only.
- This PR does not create them.
- Live/generated JSON must not be committed as fixtures.
- Future fixtures should be hand-written or sanitized mocked samples.
- Private/account/order/balance/position/cancel/withdrawal/deposit/transfer fields must not appear in fixtures.
- Fixtures should be minimal but representative enough to test normalization, missing fields, and guardrails.

## 4. Fixture source-response design

### Spot bookTicker fixture

Representative response shape:

- `symbol`
- `bidPrice`
- `bidQty`
- `askPrice`
- `askQty`
- Role: spot top-of-book context

Interpretation:

- Top-of-book context can support directional gross basis formulas.
- It does not prove order feasibility, fill probability, balance availability, or execution.

### Spot depth fixture

Representative response shape:

- `lastUpdateId`
- `bids`
- `asks`
- Role: spot depth / future VWAP context

Interpretation:

- Depth can later support VWAP/depth checks.
- This planning does not implement VWAP or size simulation.

### Spot exchangeInfo fixture

Representative response shape:

- Symbol status
- `baseAsset`
- `quoteAsset`
- `filters`
- `tickSize` / `stepSize` / min-notional-style metadata candidates
- Role: spot metadata/rules context

Interpretation:

- Future parser tests should lock symbol status, tick size, step size, and min-notional-style extraction.
- Exact filter names should be verified in the future fixture PR.

### Futures bookTicker fixture

Representative response shape:

- `symbol`
- `bidPrice`
- `bidQty`
- `askPrice`
- `askQty`
- `time` if available
- Role: perp top-of-book context

Interpretation:

- Top-of-book context can support directional gross basis formulas.
- Future planning must verify whether Binance USDⓈ-M `bookTicker` quantity semantics should normalize to base-asset units or contracts.

### Futures depth fixture

Representative response shape:

- `lastUpdateId`
- `E` / `T` or equivalent timestamp fields if available
- `bids`
- `asks`
- Role: perp depth / future VWAP context

Interpretation:

- Depth can later support VWAP/depth checks.
- Timestamp fields must preserve raw values and should not be clamped without timestamp policy approval.

### Futures premiumIndex fixture

Representative response shape:

- `symbol`
- `markPrice`
- `indexPrice`
- `lastFundingRate`
- `interestRate`
- `nextFundingTime`
- `time`
- Role: mark/index/funding context, not executable

Interpretation:

- Mark/index/funding fields are context only.
- Mark price must not be used as executable basis.
- Funding rate must remain distinct from basis.

### Futures exchangeInfo fixture

Representative response shape:

- Symbol status
- `baseAsset`
- `quoteAsset`
- `marginAsset`
- `contractType`
- `filters`
- `tickSize` / `stepSize` / min-notional-style metadata candidates
- Role: perp metadata/rules context

Interpretation:

- Future parser tests should lock margin asset, contract type, tick/step/min-notional-style extraction, and symbol status.
- Product semantics must remain distinct from Binance Spot even when both symbols are `BTCUSDT`.

## 5. Expected normalized SpotObservation

Future parser tests should expect a `SpotObservationNormalized` compatible observation. The following expected fields are planning-only and tied to the common source contract:

- `venue_id="binance"`
- `venue_name="Binance Spot"`
- `market_type="spot"`
- `symbol="BTCUSDT"`
- `base_asset="BTC"`
- `quote_asset="USDT"`
- `best_bid`
- `best_bid_qty`
- `best_ask`
- `best_ask_qty`
- `bid_qty_unit="base_asset"`
- `ask_qty_unit="base_asset"`
- `book_update_id`
- `depth_bids`
- `depth_asks`
- `tick_size`
- `step_size`
- `min_order_size`
- `min_notional`
- `raw_endpoint_ids`
- `data_age_ms`
- `latency_ms`
- `parser_normalized_status`
- `required_missing_fields`
- `parser_warnings`

Expectation guardrails:

- `raw_endpoint_ids` should show which mocked source responses contributed to the normalized observation.
- `required_missing_fields` must distinguish required executable-basis fields from optional context.
- Parser warnings should preserve unit, timestamp, and metadata concerns without making strategy decisions.

## 6. Expected normalized PerpObservation

Future parser tests should expect a `PerpObservationNormalized` compatible observation. The following expected fields are planning-only:

- `venue_id="binance"`
- `venue_name="Binance USDⓈ-M Futures"`
- `market_type="perp"`
- `symbol="BTCUSDT"`
- `base_asset="BTC"`
- `quote_asset="USDT"`
- `settlement_asset="USDT"`
- `margin_asset="USDT"`
- `contract_type`
- `best_bid`
- `best_bid_qty`
- `best_ask`
- `best_ask_qty`
- `bid_qty_unit`
- `ask_qty_unit`
- `book_timestamp`
- `depth_bids`
- `depth_asks`
- `mark_price`
- `index_price`
- `funding_rate`
- `next_funding_time`
- `tick_size`
- `step_size`
- `min_order_size`
- `min_notional`
- `raw_endpoint_ids`
- `data_age_ms`
- `latency_ms`
- `parser_normalized_status`
- `required_missing_fields`
- `parser_warnings`

Perp-specific guardrails:

- The future fixture plan must explicitly verify whether perp quantity unit is base asset or contracts.
- Binance USDⓈ-M `bookTicker` quantity semantics must be rechecked before parser implementation.
- The same `BTCUSDT` symbol string does not mean Spot and USDⓈ-M Futures product semantics are equivalent.
- Mark/index/funding fields are context and must not satisfy executable bid/ask requirements.

## 7. Expected common candidate fields

Future parser/readiness tests should verify a common basis candidate shape. The following fields are planning-only expectations:

- `candidate_type="spot_futures_basis_observation"`
- Direction candidates:
  - `analysis_only_long_spot_short_perp_basis`
  - `analysis_only_long_perp_short_spot_basis`
- `spot_observation_id`
- `perp_observation_id`
- `spot_bid`
- `spot_ask`
- `perp_bid`
- `perp_ask`
- `spot_mid`
- `perp_mid`
- `gross_basis_pct`
- `estimated_net_basis_pct`
- `fee_slippage_buffer_pct`
- `mark_basis_context_pct`
- `funding_rate_context`
- `readiness_status`
- `recommended_default_decision`
- `readiness_pass`
- `required_missing_fields`
- `warnings`
- `assumptions`

Candidate guardrails:

- Direction labels are analysis-only.
- Gross basis and estimated net basis must remain separate.
- Fee/slippage buffer must be explicit.
- Mark price and funding context must not become executable basis.
- `WATCH`, `REJECT`, and `NEED_DATA` must remain analysis-only labels.

## 8. Formula test cases

Future fixture/test PRs should include formula cases like the following. This PR does not create tests.

### Case A: no gross executable basis

- `perp_bid <= spot_ask`
- `spot_bid <= perp_ask`
- Expected readiness: `REJECT` or `NEED_DATA` depending on future policy.
- Expected warning: `no_positive_gross_basis` or equivalent.

### Case B: positive gross but negative net

- `gross_basis_pct > 0`
- `estimated_net_basis_pct <= 0` after fee/slippage buffer.
- Expected readiness: `REJECT`.
- Expected warning: `non_positive_estimated_net_basis`.

### Case C: positive net basis, still NO_TRADE_ONLY

- `estimated_net_basis_pct > 0`
- Expected label may be `WATCH`, but still analysis-only.
- Council auto-call / alert / execution remain forbidden.

### Case D: missing metadata

- Missing tick/step/min-notional or contract metadata.
- Expected `required_missing_fields` populated.
- Expected `NEED_DATA` or `REJECT` depending on future policy.

### Case E: stale timestamp

- `data_age_ms` too high.
- Expected freshness warning or `NEED_DATA` depending on future policy.

### Case F: mark-only context

- Mark/index present but bid/ask missing.
- Expected not executable.
- Expected `required_missing_fields` for executable basis fields.

## 9. Negative and guardrail fixture cases

Future fixtures should cover these guardrails:

- Spot last price only: weak context, not decision basis.
- Perp mark price only: context, not executable.
- Funding rate present but no executable basis: no trade signal.
- Same symbol string but mismatched product metadata: `required_missing_fields` or warning.
- Missing or invalid bid/ask: `NEED_DATA` or `REJECT`.
- Zero or negative prices/qty: parser warning / invalid field.
- Inconsistent quote/settlement asset: comparability warning.
- Stale timestamp / negative `data_age_ms`: preserve raw value, do not clamp without policy.
- Generated live JSON must not be committed as fixture.
- Private/account/order/balance/position/cancel/withdrawal/deposit/transfer fields must never appear in fixtures.

## 10. Test design recommendations

Future implementation/test PRs should consider tests such as:

- `test_parse_binance_spot_observation_from_mocked_fixtures`
- `test_parse_binance_perp_observation_from_mocked_fixtures`
- `test_spot_futures_basis_candidate_no_gross_basis_reject`
- `test_spot_futures_basis_positive_gross_negative_net_reject`
- `test_spot_futures_basis_positive_net_watch_no_trade_only`
- `test_spot_futures_basis_missing_metadata_need_data`
- `test_spot_futures_basis_mark_or_last_price_not_executable`
- `test_spot_futures_basis_generated_json_not_used_as_fixture`
- `test_spot_futures_basis_same_symbol_different_product_metadata_warning`
- `test_spot_futures_basis_perp_qty_unit_explicit`

Test design guardrails:

- Tests should be mocked/unit tests only until an explicit user-local public-read-only smoke step.
- Fixture JSON should be hand-written or sanitized mocked samples.
- Live generated JSON must not be used as fixture input.
- Tests must assert `NO_TRADE_ONLY`, no private API assumptions, and no trading behavior assumptions.

## 11. Reuse and non-reuse from previous strategy

### Reusable from `mark_orderbook_gap_hunt_v0`

- `NO_TRADE_ONLY` metadata pattern.
- Assumptions wording.
- Diagnostics envelope idea.
- `parser_normalized_status` / `required_missing_fields` style.
- Readiness/candidate mapping style.
- Sampling/evidence workflow.
- Watch item policy style.

### Not directly reusable

- Mark price vs bid/ask formula.
- One-venue candidate shape.
- `mark_orderbook_gap_hunt` thresholds.
- OKX index semantics.
- Timestamp assumptions without new policy.
- Generated live JSON as fixture.
- Any implication that mark price or last price is executable.

## 12. Explicitly not doing now

This PR explicitly does not do any of the following:

- Fixture JSON creation.
- Parser implementation.
- Readiness implementation.
- Adapter implementation.
- Config/registry change.
- Active strategy change.
- `spot_futures_basis_v0` active promotion.
- Live endpoint call.
- Generated JSON creation or commit.
- Private API use.
- Credentials/API keys/secrets/tokens use.
- Account/balance/position lookup.
- Order/cancel.
- Withdrawal/deposit/transfer.
- Execution.
- Alerting.
- Council auto-call.
- Auto-trading.

## 13. No-trade compliance

This fixture planning PR preserves no-trade posture:

- Active strategy promotion: no
- `spot_futures_basis_v0` active promotion: no
- Private API: no
- Credentials/API keys/secrets/tokens: no
- Account/balance/position lookup: no
- Order/cancel: no
- Withdrawal/deposit/transfer: no
- Auto-trading: no
- Council auto-call: no
- Alert: no
- Execution: no
- Config/registry change: no
- Source/runtime behavior change: no
- Fixture JSON creation: no
- Test file creation: no
- Live endpoint call: no
- Generated JSON commit: no
- `NO_TRADE_ONLY` preserved: yes

## 14. Generated JSON commit 금지

Generated packet/sampling files remain smoke artifacts only and must not be committed:

- `data/market_samples/*.json`
- `data/generated_packets/*.json`

Additional fixture guardrail:

- Live generated JSON must not be committed as fixture.
- This PR intentionally adds only this fixture/test-design planning handoff document and does not add generated JSON.

## 15. Rollback plan

Rollback path:

1. Revert this docs-only fixture planning PR.
2. Remove `docs/pr_handoffs/spot_futures_basis_binance_mocked_parser_fixture_planning_2026_06_05.md`.
3. No code/config/registry/runtime/parser/readiness/test/fixture/generated-data rollback is required.

## 16. Next PR candidates

Recommended order after this fixture planning PR:

1. Readiness policy planning
2. First mocked fixture files and parser unit test planning
3. First mocked parser/readiness implementation, `NO_TRADE_ONLY`
4. Registry/config planning, no activation
5. User-local public-read-only collect smoke
6. 3-sample sampling evidence
