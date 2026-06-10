# Strategy Market Data Requirements Matrix v0

## 1. 작업 목적

이 문서는 active / experimental / proposed strategy 후보들이 어떤 public market data primitive를 필요로 하는지 먼저 정리하고, 이후 strategy 개발을 data-first architecture로 확장하기 위한 docs-only architecture planning handoff다.

Purpose:

- 전략을 하나씩 도장깨기식으로만 개발하지 않기 위해 공통 data-first architecture를 정리한다.
- Strategy별 필요한 market data primitive를 정리한다.
- 거래소별 endpoint / response shape / status code / timestamp 차이는 venue-specific source layer에 가둔다.
- Strategy formula / readiness / candidate mapping은 common strategy layer에 둔다.
- 이번 문서는 implementation이 아니라 architecture planning이다.
- `NO_TRADE_ONLY`를 유지한다.

This PR does not implement adapters, parsers, readiness helpers, registry/config changes, fixture files, endpoint calls, generated JSON, alerts, Council auto-call, execution, private API, account/balance/position lookup, orders, transfers, withdrawals, deposits, or active strategy promotion.

## 2. Architecture principle

Recommended architecture principles:

1. Define data primitives first.
   - Start with reusable primitives such as spot top-of-book, depth, instrument metadata, perp top-of-book, funding context, reference price, trade flow, and timestamp quality.
   - Do not start by building one-off strategy-specific endpoint callers.

2. Define normalized contracts before strategy logic.
   - Venue-specific endpoint differences should normalize into common contracts.
   - Strategy logic should depend on normalized observations rather than raw exchange response fields.

3. Build strategy-specific parser/readiness after contracts are clear.
   - Parser/readiness should state required fields, optional context, warning taxonomy, and no-trade assumptions.
   - Strategy formulas should not be duplicated per venue.

4. Keep Codex work docs/research/mocked/unit-test centered.
   - Codex should focus on docs-only research, official/public endpoint candidates, mocked fixture planning, unit tests, small parser/readiness implementation, and handoff evidence.
   - Codex should not collect large live datasets.

5. Separate live public smoke from source PRs.
   - Live public-read-only smoke evidence should be user-local and summarized in handoff docs.
   - Generated JSON should remain smoke artifact and must not be committed.

6. Preserve no-trade boundaries.
   - No private API, no credentials, no account/balance/position lookup, no orders, no transfers, no execution, no alerts, no Council auto-call, and no active promotion.

## 3. Strategy catalog recap

| Strategy / artifact | Current status | Primary purpose | NO_TRADE_ONLY posture | Notes |
|---|---:|---|---|---|
| `cross_exchange_spot_spread_v1` | active | Domestic cross-exchange spot spread baseline | Yes | Active baseline, still analysis/no-trade by policy. |
| `tether_cross_market_premium` / `usdt_krw_global_reference_v0` | experimental / non-active | Domestic USDT/KRW premium and global reference health | Yes | Needs domestic KRW/USDT plus global reference data. |
| `orderbook_imbalance_v0` | experimental / non-active | Orderbook imbalance context | Yes | Needs depth and timestamp quality; not execution. |
| `mark_orderbook_gap_hunt_v0` | experimental complete/hardened / non-active | Mark price vs orderbook bid/ask watch item analysis | Yes | 3-venue hardening, smoke, sampling, policy docs complete. |
| `spot_futures_basis_v0` | proposed / experimental / non-active | Spot vs futures/perp basis analysis | Yes | Planning, Binance source research, common contract, fixture planning, readiness policy complete. |
| `funding_rate_context_v0` | future / proposed | Funding rate and next funding context | Yes | Funding is context, not automatic edge. |
| `derivatives_flow_context_v0` | future / proposed | Open interest / liquidation / derivatives flow context | Yes | Endpoint availability and semantics need research. |
| `trade_flow_momentum_v0` | future / proposed | Recent trades and taker-flow momentum context | Yes | High false-positive/noise risk. |
| `strategy_evidence_dashboard` | non-strategy infrastructure candidate | Summarize strategy evidence and readiness status | Yes | Helps review and project governance. |
| `council_review_handoff_criteria` | non-strategy governance candidate | Define evidence needed for Council discussion | Yes | Council remains analysis-only. |

## 4. Market data primitive catalog

| Primitive | Description | Used by strategies | Public-read-only feasibility | Normalized contract candidate |
|---|---|---|---|---|
| Spot best bid / ask | Top-of-book executable-context bid/ask and quantities. | `cross_exchange_spot_spread_v1`, `tether_cross_market_premium`, `spot_futures_basis_v0` | Usually yes via public book/ticker endpoints. | `SpotObservationNormalized` |
| Spot orderbook depth | Multi-level bids/asks for depth or future VWAP context. | `cross_exchange_spot_spread_v1`, `orderbook_imbalance_v0`, `spot_futures_basis_v0` | Usually yes via public depth/orderbook endpoints. | `OrderbookDepthNormalized` |
| Spot last price | Latest trade/ticker price; weak context only. | `tether_cross_market_premium`, `trade_flow_momentum_v0`, context for others | Usually yes. | `ReferencePriceNormalized` |
| Spot instrument metadata | Symbol status, base/quote, filters, tick/step/min notional. | `cross_exchange_spot_spread_v1`, `spot_futures_basis_v0`, `orderbook_imbalance_v0` | Usually yes. | `InstrumentMetadataNormalized` |
| Domestic spot KRW/USDT data | Domestic KRW-quoted USDT market bid/ask/depth/last. | `tether_cross_market_premium`, `cross_exchange_spot_spread_v1` | Usually yes for public domestic sources. | `SpotObservationNormalized`, `ReferencePriceNormalized` |
| Global USDT reference data | Global USDT reference price/health for premium context. | `tether_cross_market_premium` | Usually yes, source-dependent. | `ReferencePriceNormalized`, `DiagnosticsEnvelope` |
| Perp/futures best bid / ask | Derivatives top-of-book bid/ask and quantities. | `mark_orderbook_gap_hunt_v0`, `spot_futures_basis_v0`, `funding_rate_context_v0` | Usually yes. | `PerpObservationNormalized` |
| Perp/futures orderbook depth | Derivatives depth for future VWAP/liquidity context. | `mark_orderbook_gap_hunt_v0`, `spot_futures_basis_v0`, `orderbook_imbalance_v0` | Usually yes. | `OrderbookDepthNormalized`, `PerpObservationNormalized` |
| Mark price | Derivatives mark/reference price; not executable. | `mark_orderbook_gap_hunt_v0`, `spot_futures_basis_v0`, `funding_rate_context_v0` | Usually yes. | `ReferencePriceNormalized`, `PerpObservationNormalized` |
| Index price | Derivatives index/reference price; context only unless policy says otherwise. | `mark_orderbook_gap_hunt_v0`, `spot_futures_basis_v0`, `funding_rate_context_v0` | Usually yes, endpoint-dependent. | `ReferencePriceNormalized`, `PerpObservationNormalized` |
| Funding rate | Current or predicted funding rate. | `funding_rate_context_v0`, `spot_futures_basis_v0` context | Usually yes for perps. | `FundingContextNormalized` |
| Next funding time | Timestamp for next funding event. | `funding_rate_context_v0`, `spot_futures_basis_v0` context | Usually yes for perps. | `FundingContextNormalized`, `TimestampQualityEnvelope` |
| Open interest | Outstanding derivatives contracts/positions count context. | `derivatives_flow_context_v0`, `funding_rate_context_v0` context | Often public, venue-dependent. | `LiquidationContextNormalized` or future `DerivativesFlowNormalized` |
| Liquidation data | Liquidation events or liquidation heat/cluster context. | `derivatives_flow_context_v0` | Public availability varies widely. | `LiquidationContextNormalized` |
| Recent trades | Recent public trade prints. | `trade_flow_momentum_v0`, context for spot/perp strategies | Usually yes. | `TradeFlowNormalized` |
| Taker buy/sell volume | Directional taker flow or aggressor-side volume. | `trade_flow_momentum_v0`, `derivatives_flow_context_v0` context | Venue-dependent public availability. | `TradeFlowNormalized` |
| Instrument metadata | Generic symbol/product rules, status, base/quote/settlement, filters. | Most strategies | Usually yes. | `InstrumentMetadataNormalized` |
| Contract value / lot size / tick size / step size / min notional | Unit, sizing, and notional interpretation fields. | `mark_orderbook_gap_hunt_v0`, `spot_futures_basis_v0`, derivatives strategies | Usually yes through public metadata endpoints. | `InstrumentMetadataNormalized`, `PerpObservationNormalized` |
| Timestamp / latency / `data_age_ms` | Data freshness and clock-skew context. | All market-data strategies | Derived from public responses and local collection metadata. | `TimestampQualityEnvelope` |
| Fee/slippage/buffer assumptions | Explicit no-private-data buffer assumptions for net estimates. | `cross_exchange_spot_spread_v1`, `mark_orderbook_gap_hunt_v0`, `spot_futures_basis_v0` | Yes as configuration/planning assumptions, not private account data. | Strategy candidate metrics / assumptions contract |

## 5. Strategy x Data matrix

Legend: `Required` = needed for core readiness; `Optional` = useful if available; `Context` = non-executable context or reviewer context; `Not used` = not part of current planning.

| Strategy | Spot bid/ask | Spot depth | Domestic KRW/USDT | Global USDT ref | Perp bid/ask | Perp depth | Mark/index | Funding | OI/liquidations | Trades/taker flow | Metadata/units | Timestamp quality | Buffer assumptions |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `cross_exchange_spot_spread_v1` | Required | Required | Optional | Not used | Not used | Not used | Not used | Not used | Not used | Context | Required | Required | Required |
| `tether_cross_market_premium` / `usdt_krw_global_reference_v0` | Required | Optional | Required | Required | Not used | Not used | Context | Not used | Not used | Context | Required | Required | Optional |
| `orderbook_imbalance_v0` | Required | Required | Not used | Not used | Optional | Optional | Not used | Not used | Not used | Context | Required | Required | Optional |
| `mark_orderbook_gap_hunt_v0` | Not used | Not used | Not used | Not used | Required | Required | Required | Context | Not used | Not used | Required | Required | Required |
| `spot_futures_basis_v0` | Required | Required | Not used | Not used | Required | Required | Context | Context | Not used | Context | Required | Required | Required |
| `funding_rate_context_v0` | Optional | Optional | Not used | Not used | Optional | Optional | Required | Required | Optional | Context | Required | Required | Context |
| `derivatives_flow_context_v0` | Context | Optional | Not used | Not used | Context | Optional | Context | Context | Required | Optional | Required | Required | Optional |
| `trade_flow_momentum_v0` | Context | Optional | Not used | Not used | Context | Optional | Not used | Not used | Optional | Required | Optional | Required | Optional |

Matrix interpretation:

- `Required` does not mean executable trading is allowed.
- `Context` fields must not be promoted into decision fields without a separate policy and tests.
- Last price, mark price, index price, funding, OI, liquidation, and taker-flow context can be useful but are not automatically executable edge.

## 6. Reusable normalized contracts

| Normalized contract candidate | Purpose | Reusable by strategies |
|---|---|---|
| `SpotObservationNormalized` | Venue-neutral spot quote/depth/metadata observation with explicit units and timestamps. | `cross_exchange_spot_spread_v1`, `tether_cross_market_premium`, `orderbook_imbalance_v0`, `spot_futures_basis_v0`, `trade_flow_momentum_v0` context |
| `PerpObservationNormalized` | Venue-neutral perp/futures top-of-book, mark/index/funding, contract metadata, and timestamp observation. | `mark_orderbook_gap_hunt_v0`, `spot_futures_basis_v0`, `funding_rate_context_v0`, `derivatives_flow_context_v0` |
| `OrderbookDepthNormalized` | Bids/asks levels, quantity units, update IDs, timestamps, and future VWAP context. | `cross_exchange_spot_spread_v1`, `orderbook_imbalance_v0`, `spot_futures_basis_v0`, `mark_orderbook_gap_hunt_v0` |
| `InstrumentMetadataNormalized` | Symbol/product status, base/quote/settlement, filters, tick/step/min notional, contract units. | Most strategies, especially `spot_futures_basis_v0` and derivatives strategies |
| `FundingContextNormalized` | Funding rate, interest rate, next funding time, mark/index context. | `funding_rate_context_v0`, `spot_futures_basis_v0`, `derivatives_flow_context_v0` context |
| `ReferencePriceNormalized` | Last/mark/index/global reference prices with source, timestamp, and executable-context label. | `tether_cross_market_premium`, `mark_orderbook_gap_hunt_v0`, `spot_futures_basis_v0`, `funding_rate_context_v0` |
| `TradeFlowNormalized` | Recent trades, taker-side volume, aggressor imbalance, time bucket metadata. | `trade_flow_momentum_v0`, `derivatives_flow_context_v0`, context for spot/perp strategies |
| `LiquidationContextNormalized` | Liquidation event counts/notionals, clusters, venue support, and timestamp quality. | `derivatives_flow_context_v0` |
| `TimestampQualityEnvelope` | Raw timestamps, local created_at, latency, `data_age_ms`, negative-age watch, stale policy flags. | All market-data strategies |
| `DiagnosticsEnvelope` | Public GET diagnostics, endpoint ID, params, HTTP/status fields, response status fields, latency, warnings. | All adapters/source layers |

Contract guardrails:

- A normalized contract should preserve raw/source identity enough for diagnostics.
- A normalized contract should not hide venue-specific unit differences.
- A normalized contract should not make strategy decisions by itself.
- Strategy-specific readiness should consume normalized contracts and emit explicit `required_missing_fields`, warnings, and assumptions.

## 7. Venue expansion principle

Venue expansion principles:

- Binance / Bybit / OKX source research is not intended to create venue-specific strategies.
- Each venue should add only a source/normalizer adapter that satisfies common normalized contracts.
- Strategy formula / readiness / candidate mapping should not be copied per venue.
- Venue-specific parser/source logic should not directly decide strategy readiness or trading labels.
- New venue addition should be a thin source mapping + mocked fixture + user-local public-read-only smoke evidence.
- Venue-specific response semantics must remain visible: endpoint paths, query params, raw status fields, symbol formats, category/instType, timestamp behavior, units, and diagnostics fields.
- Strategy-common code should be venue-neutral and should compare normalized observations, not raw endpoint payloads.

## 8. What Codex should and should not do

Codex should do:

- Docs-only research and architecture planning.
- Official/public endpoint candidate summaries.
- Mocked fixture planning.
- Hand-written or sanitized fixture design.
- Unit tests.
- Small parser/readiness implementation when explicitly allowed.
- Handoff evidence documenting purpose, files, tests, risks, rollback, no-trade compliance.

Codex should not do:

- Large live data collection.
- Live endpoint calls unless explicitly requested.
- Private API usage.
- Credentials/API keys/secrets/tokens usage.
- Generated live JSON fixture commit.
- Strategy active promotion.
- Registry/config activation without explicit task scope.
- Execution, alert, Council auto-call, or auto-trading.
- Account/balance/position/order/cancel/withdrawal/deposit/transfer work.

## 9. Recommended next development model

Recommended workflow for future strategy work:

1. Strategy/data requirement planning.
2. Source contract / endpoint research.
3. Mocked fixture planning.
4. Mocked parser/readiness implementation.
5. Registry/config planning, no activation.
6. User-local public-read-only collect smoke.
7. 3-sample evidence.
8. 30-sample evidence.
9. Comparative summary.
10. Only then consider next implementation or policy change.

Workflow guardrails:

- Do not jump from endpoint research directly to live strategy behavior.
- Do not let Codex commit generated sampling JSON.
- Do not let a planning WATCH become a trading signal.
- Do not promote a strategy from experimental/non-active to active without explicit human approval and a separate high-risk review path.

## 10. Immediate next PR recommendation

Recommended order after this matrix:

1. First mocked fixture files and parser unit test planning for `spot_futures_basis_v0`.
   - This is the most direct continuation of the completed `spot_futures_basis_v0` planning chain.
   - It should remain docs/test-design first and should not create generated live JSON fixtures.

2. First mocked parser/readiness implementation, `NO_TRADE_ONLY`.
   - Only after fixture/test expectations are clear.
   - Should use hand-written or sanitized mocked fixtures, not live generated artifacts.

3. Strategy Evidence Dashboard / Journal Summary Planning.
   - Useful once multiple strategy evidence tracks need a single reviewer-facing status surface.

4. Registry/config planning, no activation.
   - Should remain planning/no activation until mocked implementation and evidence are ready.

5. User-local public-read-only collect smoke and 3-sample sampling evidence.
   - Should be user-local evidence and should not commit generated JSON artifacts.

## 11. No-trade compliance

This docs-only architecture planning PR preserves no-trade posture:

- Active strategy promotion: no
- New strategy active promotion: no
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
- Live endpoint call: no
- Fixture JSON creation: no
- Parser/readiness/adapter implementation: no
- Generated JSON commit: no
- `NO_TRADE_ONLY` preserved: yes

## 12. Generated JSON commit 금지

Generated packet/sampling files remain smoke artifacts only and must not be committed:

- `data/market_samples/*.json`
- `data/generated_packets/*.json`

Additional guardrails:

- Live generated JSON must not be committed as fixture.
- User-local smoke outputs should be summarized in handoff docs only.
- This PR intentionally adds only this strategy market data requirements matrix document and does not add generated JSON.

## 13. Rollback plan

Rollback path:

1. Revert this docs-only architecture planning PR.
2. Remove `docs/pr_handoffs/strategy_market_data_requirements_matrix_2026_06_05.md`.
3. No code/config/registry/runtime/parser/readiness/test/fixture/generated-data rollback is required.

## 14. Next PR candidates

Recommended order:

1. First mocked fixture files and parser unit test planning for `spot_futures_basis_v0`
2. First mocked parser/readiness implementation, `NO_TRADE_ONLY`
3. Strategy Evidence Dashboard / Journal Summary Planning
4. Registry/config planning, no activation
5. User-local public-read-only collect smoke
6. 3-sample sampling evidence
