# Spot-Futures Basis Binance Public Source / Endpoint Research v0

## 1. 작업 목적

이 문서는 `spot_futures_basis_v0`의 첫 implementation 전에 Binance Spot `BTCUSDT`와 Binance USDⓈ-M Futures `BTCUSDT` perpetual 비교에 필요한 public-read-only source / endpoint 후보를 공식 Binance 문서 기준으로 정리하는 docs-only research handoff다.

Scope:

- Binance spot/perp public source 후보를 정리한다.
- 이 문서는 research / planning 문서다.
- Endpoint 호출을 하지 않는다.
- Implementation을 하지 않는다.
- `NO_TRADE_ONLY`를 유지한다.
- Generated packet/sampling JSON은 smoke artifact이며 commit하지 않는다.

Research note:

- Official Binance docs were used as source references for endpoint names and response-shape candidates.
- No Binance endpoint was called from this workspace.
- This PR does not add adapters, parsers, readiness helpers, registry/config entries, runtime behavior, generated data, alerts, Council auto-call, execution, or active strategy promotion.

## 2. Scope

Initial research target:

- Spot venue: Binance Spot
- Futures venue: Binance USDⓈ-M Futures
- Asset: BTC
- Quote: USDT
- Spot symbol: `BTCUSDT`
- Perp symbol: `BTCUSDT`
- Comparison type: same-exchange spot/perp basis
- Status: proposed / experimental / non-active / `NO_TRADE_ONLY`

## 3. Official source candidates

Official documentation references used for this research:

- Binance Spot market data endpoints: `https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints`
- Binance Spot general endpoints / exchange information: `https://developers.binance.com/docs/binance-spot-api-docs/rest-api/general-endpoints`
- Binance USDⓈ-M Futures order book: `https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Order-Book`
- Binance USDⓈ-M Futures symbol order book ticker: `https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Symbol-Order-Book-Ticker`
- Binance USDⓈ-M Futures mark price / premium index: `https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Mark-Price`
- Binance USDⓈ-M Futures exchange information: `https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Exchange-Information`

### Binance Spot candidates

#### `GET /api/v3/ticker/bookTicker`

- Purpose: spot best bid / ask and quantity.
- Likely fields from official examples: `symbol`, `bidPrice`, `bidQty`, `askPrice`, `askQty`.
- Candidate role: top-of-book executable context.
- Research interpretation: top-of-book context only; actual order placement or account-specific fill feasibility is not verified without private/execution APIs, which remain forbidden.

#### `GET /api/v3/depth`

- Purpose: spot order book depth.
- Likely fields from official examples: `lastUpdateId`, `bids`, `asks`.
- Candidate role: future VWAP / depth context.
- Research interpretation: depth can support future VWAP planning, but this PR does not implement VWAP.

#### `GET /api/v3/ticker/price`

- Purpose: latest spot price.
- Likely fields from official examples: `symbol`, `price`.
- Candidate role: weak context only, not executable.
- Research interpretation: latest price can be context, but last/latest price alone must not be used as decision basis.

#### `GET /api/v3/exchangeInfo`

- Purpose: spot symbol filters / lot / tick / min-notional research.
- Likely fields from official examples: `symbols`, `symbol`, `status`, `baseAsset`, `quoteAsset`, `filters`, permissions / permission sets, and related symbol metadata.
- Candidate role: metadata source.
- Follow-up note: exact filter names and min-notional equivalents should be verified again during mocked fixture planning; mark exact parser-required fields as `needs_follow_up_verification` until fixtures are reviewed.

### Binance USDⓈ-M Futures candidates

#### `GET /fapi/v1/ticker/bookTicker`

- Purpose: futures/perp best bid / ask and quantity.
- Likely fields from official examples: `symbol`, `bidPrice`, `bidQty`, `askPrice`, `askQty`, `time`.
- Candidate role: top-of-book executable context.
- Research interpretation: top-of-book context only; actual order placement, position entry, margin, or fill feasibility is not verified without private/execution APIs, which remain forbidden.

#### `GET /fapi/v1/depth`

- Purpose: futures/perp order book depth.
- Likely fields from official examples: `lastUpdateId`, `E`, `T`, `bids`, `asks`.
- Candidate role: future VWAP / depth context.
- Research interpretation: depth can support future VWAP planning, but this PR does not implement VWAP.

#### `GET /fapi/v1/premiumIndex`

- Purpose: mark price, index price, funding rate, next funding time.
- Likely fields from official examples: `symbol`, `markPrice`, `indexPrice`, `lastFundingRate`, `interestRate`, `nextFundingTime`, `time`.
- Candidate role: non-executable mark/index/funding context.
- Research interpretation: mark/index/funding context can explain basis environment, but it is not executable basis.

#### `GET /fapi/v1/exchangeInfo`

- Purpose: futures trading rules and symbol information.
- Likely fields from official examples: `symbols`, `baseAsset`, `quoteAsset`, `marginAsset`, `filters`, tick/step/min-notional-style rule metadata, contract/product metadata.
- Candidate role: metadata / unit / rule source.
- Follow-up note: exact parser-required fields should be locked in mocked fixtures before implementation.

## 4. Input classification

### Executable-context candidate

- Spot `GET /api/v3/ticker/bookTicker`
- Futures `GET /fapi/v1/ticker/bookTicker`

Notes:

- Spot bookTicker and futures bookTicker are top-of-book context only.
- They do not verify actual order feasibility, account permissions, margin, balances, position availability, or fill probability.
- Private/execution APIs remain forbidden.

### Depth / VWAP-context candidate

- Spot `GET /api/v3/depth`
- Futures `GET /fapi/v1/depth`

Notes:

- Depth is a future VWAP/depth context candidate.
- This PR does not implement VWAP, depth aggregation, size simulation, or sampling JSON generation.

### Weak context only

- Spot `GET /api/v3/ticker/price`

Notes:

- Ticker/price or last/latest price is weak context.
- It must not be used as decision basis.
- It is not executable price.

### Metadata / rules candidate

- Spot `GET /api/v3/exchangeInfo`
- Futures `GET /fapi/v1/exchangeInfo`

Notes:

- These endpoints are candidates for symbol status, unit, filter, tick/step/min-notional-style metadata.
- Exact parser fields should be locked only after mocked fixture planning.

### Funding / mark / index context candidate

- Futures `GET /fapi/v1/premiumIndex`

Notes:

- `premiumIndex` mark price / index price / funding fields are context.
- Mark price and index price are not executable basis.
- Funding rate must remain separate from basis.

## 5. Proposed initial endpoint set

Recommended first mocked implementation candidate endpoint set:

Spot:

- `/api/v3/ticker/bookTicker`
- `/api/v3/depth`

Futures:

- `/fapi/v1/ticker/bookTicker`
- `/fapi/v1/depth`
- `/fapi/v1/premiumIndex`
- `/fapi/v1/exchangeInfo`

Implementation guardrail:

- The next implementation PR must start with mocked fixtures before any live endpoint call.
- Live endpoint calls remain out of scope until an explicit user-local public-read-only smoke step.
- Registry/config planning must remain separate and must not activate `spot_futures_basis_v0`.

## 6. Required fields for future parser

The following fields are planning-only parser candidates. They are not implemented in this PR.

### Spot observation required candidates

- `spot_symbol`
- `spot_bid`
- `spot_bid_qty`
- `spot_ask`
- `spot_ask_qty`
- `spot_book_timestamp_or_update_id`
- `spot_depth_bids`
- `spot_depth_asks`
- `spot_tick_size`
- `spot_step_size`
- `spot_min_notional` or min-notional equivalent, if available

### Perp observation required candidates

- `perp_symbol`
- `perp_bid`
- `perp_bid_qty`
- `perp_ask`
- `perp_ask_qty`
- `perp_book_timestamp`
- `perp_depth_bids`
- `perp_depth_asks`
- `mark_price`
- `index_price`
- `funding_rate`
- `next_funding_time`
- `margin_asset`
- `contract_type`
- `tick_size`
- `step_size`
- `min_notional`

## 7. Comparability questions

A future readiness policy should answer at least these questions:

- Is the spot symbol and perp symbol mapping explicit?
- Are the spot quote asset and perp margin/settlement asset comparable?
- Are `BTCUSDT` spot and `BTCUSDT` perp both active/trading?
- Are units comparable as base asset, or do they require conversion?
- Do spot ask and perp bid exist for long spot / short perp direction?
- Do perp ask and spot bid exist for long perp / short spot direction?
- Does depth exist and is it sufficient for future VWAP context?
- Is mark price not used as executable price?
- Is last price not used as executable price?
- Is funding rate kept separate from basis?
- Are timestamps available and is freshness policy documented?
- Are `required_missing_fields` explicit?
- Are no-trade assumptions preserved?
- Are public-read-only and analysis-only boundaries preserved?

## 8. Formula implications

Formula implications for `spot_futures_basis_v0` planning:

- `mid_basis_pct` may use `spot_mid` and `perp_mid` as context only.
- `long_spot_short_perp_gross_pct` should use spot ask and perp bid.
- `long_perp_short_spot_gross_pct` should use perp ask and spot bid.
- `estimated_net_basis_pct` should subtract fee/slippage/buffer assumptions.
- Mark-price basis should be clearly labeled non-executable context.
- Last-price basis should be weak context only.
- Depth/VWAP context should remain future planning until depth aggregation is implemented and tested.
- No thresholds are set by this research PR.

## 9. Risk assessment

Key risks:

- Spot/futures symbol mapping errors.
- Contract/perp metadata interpretation errors.
- Misreading mark price as executable price.
- Misreading last price as executable price.
- Top-of-book liquidity illusion.
- Over-interpreting basis before depth/VWAP is implemented.
- Confusing funding rate with basis.
- Timestamp / `data_age_ms` mismatch.
- Inability to verify actual position/order feasibility without private APIs.
- Endpoint response shape changes.
- Fee/slippage/buffer assumptions may be too optimistic if not backed by evidence.
- Same-symbol `BTCUSDT` naming can still hide different product semantics between Spot and USDⓈ-M Futures.

## 10. No-trade compliance

This research PR preserves no-trade posture:

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
- Endpoint call: no
- Adapter implementation: no
- Parser implementation: no
- Readiness implementation: no
- Generated JSON commit: no
- `NO_TRADE_ONLY` preserved: yes

## 11. Generated JSON commit 금지

Generated packet/sampling files remain smoke artifacts only and must not be committed:

- `data/market_samples/*.json`
- `data/generated_packets/*.json`

This PR intentionally adds only this research handoff document and does not add generated JSON.

## 12. Rollback plan

Rollback path:

1. Revert this docs-only research PR.
2. Remove `docs/pr_handoffs/spot_futures_basis_binance_public_source_research_2026_06_05.md`.
3. No code/config/registry/runtime/parser/readiness/generated-data rollback is required.

## 13. Next PR candidates

Recommended order after this research PR:

1. Mocked parser fixture planning
2. Readiness policy planning
3. First mocked parser/readiness implementation, `NO_TRADE_ONLY`
4. Registry/config planning, no activation
5. User-local public-read-only collect smoke
6. 3-sample sampling evidence
