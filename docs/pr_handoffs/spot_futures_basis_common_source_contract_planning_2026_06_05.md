# Spot-Futures Basis Common Source Contract / Venue Expansion Planning v0

## 1. 작업 목적

이 문서는 `spot_futures_basis_v0`가 Binance 전용 implementation으로 굳어지는 것을 방지하고, Binance / Bybit / OKX 등 다른 venue로 확장 가능한 거래소 독립 common source contract와 venue-specific boundary를 정의하는 docs-only architecture planning handoff다.

Scope:

- Binance 전용 implementation으로 굳어지는 것을 방지한다.
- `spot_futures_basis_v0`의 공통 normalized source contract를 정의한다.
- 거래소별 endpoint / response 차이는 venue-specific source adapter boundary에 가둔다.
- Formula / readiness / candidate mapping은 strategy-common layer로 유지한다.
- 이 문서는 implementation이 아니라 planning이다.
- `NO_TRADE_ONLY`를 유지한다.
- Generated packet/sampling JSON은 smoke artifact이며 commit하지 않는다.

This PR does not implement adapters, parsers, readiness helpers, registry/config entries, endpoint calls, runtime behavior, generated data, alerts, Council auto-call, execution, or active strategy promotion.

## 2. Architecture principle

### Layer A: Venue-specific source layer

The venue-specific source layer owns exchange-specific access and raw interpretation boundaries:

- Endpoint path.
- Query params.
- Response status code semantics.
- Raw response shape.
- Symbol / `instId` / `category` / `instType` naming.
- Timestamp semantics.
- Rate limit / diagnostics fields.
- Venue-specific error fields, such as Bybit `retCode` / `retMsg` or OKX `code` / `msg`.

This layer should not make strategy decisions and should not decide whether basis is actionable.

### Layer B: Normalized market observation contract

The normalized observation layer converts venue-specific public market data into venue-neutral observations:

- Venue-neutral spot observation.
- Venue-neutral futures/perp observation.
- Explicit units.
- Explicit timestamps.
- Explicit metadata fields.
- `required_missing_fields`.
- Parser warnings and normalization status.

This layer preserves evidence and missing fields without hiding venue differences.

### Layer C: Strategy-common basis logic

The strategy-common layer owns basis interpretation and candidate construction:

- Basis formulas.
- Gross / estimated net basis.
- Fee/slippage buffer.
- Direction labels.
- Readiness questions.
- OpportunityPacket candidate mapping.

This layer should be shared across venues and should not duplicate formula or readiness logic per venue.

### Layer D: Evidence and sampling layer

The evidence layer owns reviewability and smoke/sampling artifacts:

- Collect smoke.
- 3-sample evidence.
- 30-sample evidence.
- Generated JSON commit ban.
- `docs/pr_handoffs/` as source-of-truth for review handoffs.

Generated JSON remains a local smoke artifact unless explicitly approved for commit.

## 3. Proposed normalized source contract

The following contracts are planning-only candidates and are not implemented by this PR.

### `SpotObservationNormalized` candidate fields

- `venue_id`
- `venue_name`
- `market_type="spot"`
- `symbol`
- `base_asset`
- `quote_asset`
- `best_bid`
- `best_bid_qty`
- `best_ask`
- `best_ask_qty`
- `bid_qty_unit`
- `ask_qty_unit`
- `book_timestamp`
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

### `PerpObservationNormalized` candidate fields

- `venue_id`
- `venue_name`
- `market_type="perp"` or `market_type="futures"`
- `symbol`
- `base_asset`
- `quote_asset`
- `settlement_asset`
- `contract_type`
- `margin_asset`
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
- `contract_value`
- `contract_multiplier`
- `contract_value_currency`
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

Contract guardrails:

- Units must be explicit and must not be inferred silently.
- Raw endpoint provenance should remain visible through `raw_endpoint_ids`.
- Negative `data_age_ms` must not be clamped or normalized without a separate approved timestamp policy.
- `index_price=None` must not be synthetically filled.
- Missing optional context should be distinct from missing required basis fields.

## 4. Common candidate contract

A future basis candidate should use a common strategy-level candidate contract. The following fields are planning-only candidates and are not implemented by this PR:

- `candidate_type: spot_futures_basis_observation`
- `direction`:
  - `analysis_only_long_spot_short_perp_basis`
  - `analysis_only_long_perp_short_spot_basis`
- `spot_observation_id`
- `perp_observation_id`
- `gross_basis_pct`
- `estimated_net_basis_pct`
- `fee_slippage_buffer_pct`
- `spot_bid`
- `spot_ask`
- `perp_bid`
- `perp_ask`
- `spot_mid`
- `perp_mid`
- `mark_basis_context_pct`
- `funding_rate_context`
- `readiness_status`
- `recommended_default_decision`
- `readiness_pass`
- `required_missing_fields`
- `warnings`
- `assumptions`

Common candidate guardrails:

- Direction labels must remain analysis-only.
- Gross basis must be separated from estimated net basis.
- Fee/slippage buffer must be explicit.
- Mark basis is context and not executable basis.
- Funding context must remain distinct from basis decision context.
- `WATCH`, `REJECT`, and `NEED_DATA` are analysis-only labels.

## 5. Venue-specific boundaries

### Binance

Keep these Binance details in the venue-specific source layer:

- Spot `/api/v3/...` versus USDⓈ-M `/fapi/v1/...` endpoint families.
- `BTCUSDT` symbol appears identical across spot and USDⓈ-M, but product semantics differ.
- Spot `exchangeInfo` filters versus Futures `exchangeInfo` filters.
- Futures `premiumIndex` mark/index/funding context.
- Spot and futures timestamp fields and update IDs.
- Any Binance-specific rate limit or diagnostics metadata.

### Bybit

Keep these Bybit details in the venue-specific source layer:

- Spot / V5 market endpoint differences.
- `category=spot` versus `category=linear`.
- `retCode` / `retMsg` diagnostics.
- `BTCUSDT` symbol reuse with product category differences.
- Funding interval warning possibility.
- Timestamp / `data_age_ms` semantics.
- Bybit-specific lot, tick, contract, and funding field semantics.

### OKX

Keep these OKX details in the venue-specific source layer:

- `instId` format: `BTC-USDT` versus `BTC-USDT-SWAP`.
- `instType=SPOT` versus `instType=SWAP`.
- `code` / `msg` diagnostics.
- Contracts size unit.
- `contract_value` / `lot_size` semantics.
- Index/reference semantics.
- Timestamp / `data_age_ms` watch possibility.
- OKX-specific instrument metadata and contract value currency semantics.

## 6. Reuse boundaries from `mark_orderbook_gap_hunt_v0`

### Reusable

The following `mark_orderbook_gap_hunt_v0` patterns can be reused conceptually:

- `NO_TRADE_ONLY` metadata pattern.
- Assumptions wording.
- Diagnostics envelope idea.
- Readiness/candidate mapping pattern.
- Sampling/evidence workflow.
- Watch item policy style.
- Generated JSON commit ban.
- Handoff-first review style under `docs/pr_handoffs/`.

### Not directly reusable

The following must not be copied directly into `spot_futures_basis_v0`:

- `mark_orderbook_gap_hunt` formula.
- Mark price versus bid/ask one-venue comparison.
- Single-venue candidate shape.
- OKX mark/index semantics as-is.
- Threshold values without new evidence.
- Venue-specific timestamp interpretations without a new policy review.
- Assumptions that imply mark price or last price is executable.

## 7. Expansion strategy

Recommended venue expansion approach:

1. First implementation: Binance only, but it must satisfy the common normalized source contract.
2. Second venue: add Bybit source mapping against the same contract.
3. Third venue: add OKX source mapping against the same contract.
4. Each venue addition must be a thin source/normalizer adapter plus fixture plus user-local smoke evidence.
5. Strategy-common basis formulas and readiness questions should not be duplicated per venue.
6. Venue-specific parser code should normalize inputs and preserve warnings, not make strategy decisions.
7. Each venue should get separate public source research before implementation.

Expansion guardrails:

- A Binance-first implementation is acceptable only as the first reference venue, not as a Binance-only strategy design.
- Bybit and OKX should map into the same normalized contracts rather than receiving copied strategy logic.
- New venue evidence must include generated JSON commit checks.

## 8. Anti-patterns

The following anti-patterns are explicitly forbidden for this strategy track:

- Creating venue-specific strategy classes such as `BinanceSpotFuturesBasisStrategy`.
- Copying strategy logic into `BybitSpotFuturesBasisStrategy` / `OKXSpotFuturesBasisStrategy`.
- Letting a venue-specific parser make strategy decisions directly.
- Using mark price or last price as executable basis.
- Assuming product equivalence just because symbol strings match.
- Hiding or auto-flattening contract units.
- Silently converting contracts to base asset without explicit metadata and tests.
- Committing generated live JSON as fixtures.
- Treating gross basis as net edge.
- Letting optional funding or mark/index context become implicit required fields without policy approval.

## 9. Next PR sequence update

Recommended updated PR sequence:

1. PR 1: Common source contract planning v0.
2. PR 2: Binance mocked fixture planning against common contract.
3. PR 3: Binance parser/readiness mocked implementation, `NO_TRADE_ONLY`.
4. PR 4: Binance registry/config planning, no activation.
5. PR 5: Binance user-local public-read-only collect smoke.
6. PR 6: Binance 3-sample sampling evidence.
7. PR 7: Bybit public source research against same contract.
8. PR 8: OKX public source research against same contract.

Sequence guardrails:

- PR 2 should remain docs/test-design planning before implementation.
- PR 3 must be mocked/unit-test-first and preserve `NO_TRADE_ONLY`.
- PR 4 must not activate the strategy.
- PR 5 and PR 6 must keep generated JSON artifacts out of git unless explicitly approved.
- PR 7 and PR 8 must not duplicate strategy-common basis logic.

## 10. No-trade compliance

This architecture planning PR preserves no-trade posture:

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

This PR intentionally adds only this architecture planning handoff document and does not add generated JSON.

## 12. Rollback plan

Rollback path:

1. Revert this docs-only architecture planning PR.
2. Remove `docs/pr_handoffs/spot_futures_basis_common_source_contract_planning_2026_06_05.md`.
3. No code/config/registry/runtime/parser/readiness/generated-data rollback is required.

## 13. Next PR candidates

Recommended order after this planning PR:

1. Binance mocked parser fixture planning against common contract
2. Readiness policy planning
3. First mocked parser/readiness implementation, `NO_TRADE_ONLY`
4. Registry/config planning, no activation
5. User-local public-read-only collect smoke
6. 3-sample sampling evidence
