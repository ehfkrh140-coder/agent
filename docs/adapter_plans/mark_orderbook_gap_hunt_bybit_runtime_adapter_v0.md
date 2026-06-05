# Mark-Orderbook Gap Hunt Bybit Runtime Adapter Planning v0

## 1. Purpose

Plan the future `live_bybit_mark_orderbook_gap_btcusdt` runtime adapter before any Bybit implementation, config registration, registry integration, sampling change, alert, Council, or execution/private API work.

This is a planning-only document. It extends the Binance single-venue Mark-Orderbook Gap Hunt baseline toward Bybit linear BTCUSDT while preserving the existing shared strategy logic, parser/readiness contract, OpportunityPacket mapping, sampling interpretation, and `NO_TRADE_ONLY` boundary.

## 2. Current baseline summary

- Binance single-venue baseline exists for `live_binance_mark_orderbook_gap_btcusdt` and has collect, 3-sample sampling, and 30-sample extended sampling user-local evidence.
- The 30-sample Binance evidence reported `samples_ok=30`, `samples_error=0`, `candidate_seen_count=30`, `positive_gross_gap_count=26`, `positive_net_gap_count=0`, `REJECT=30`, `NO_PERSISTENT_EDGE`, and `council_recommended=False`.
- Binance evidence is stability evidence, not profitability or persistent-edge evidence.
- Existing parser/readiness code already has a `bybit_linear` parser mode and should be reused by a future Bybit adapter.
- This plan does not alter the active strategy; `cross_exchange_spot_spread_v1` remains active and Mark-Orderbook Gap Hunt remains experimental/non-active.

## 3. Bybit adapter v0 scope

Proposed adapter identity:

- Proposed adapter id: `live_bybit_mark_orderbook_gap_btcusdt`
- Venue: Bybit Derivatives V5
- Category: `linear`
- Instrument: `BTCUSDT`
- Strategy family: `mark_orderbook_gap_hunt`
- Strategy id: `mark_orderbook_gap_hunt_v0`
- Signal type: `mark_orderbook_gap_hunt`
- Status: experimental / non-active / `NO_TRADE_ONLY`
- Purpose: collect public Bybit linear ticker, orderbook, and instruments-info data, pass it through the existing parser/readiness helper, and build an analysis-only OpportunityPacket.

Out of scope for this planning PR:

- Bybit runtime adapter implementation.
- Bybit config adapter registration.
- Bybit registry integration.
- Sampling implementation changes.
- Generated packet or sampling JSON commits.
- Alert/notification, Council auto-call, active promotion, execution, private API, credentials, account/balance/position lookup, orders, cancellations, withdrawals, deposits, or transfers.

## 4. Public endpoints

Future adapter should use only public no-key Bybit V5 market endpoints:

| Purpose | Method | URL | Notes |
| --- | --- | --- | --- |
| Ticker / mark / top-of-book | `GET` | `https://api.bybit.com/v5/market/tickers?category=linear&symbol=BTCUSDT` | Expected source for `markPrice`, `indexPrice`, `bid1Price`, `ask1Price`, `bid1Size`, `ask1Size`, `fundingRate`, and `nextFundingTime` when available. |
| Orderbook | `GET` | `https://api.bybit.com/v5/market/orderbook?category=linear&symbol=BTCUSDT&limit=5` | Expected source for top bid/ask levels under `result.b` and `result.a`, plus sequence/timestamp diagnostics. |
| Metadata | `GET` | `https://api.bybit.com/v5/market/instruments-info?category=linear&symbol=BTCUSDT` | Expected source for symbol/category validation, `priceFilter`, `lotSizeFilter`, and derivative metadata. |

All listed endpoints are public market-data endpoints and should not require API keys, auth headers, private endpoint access, account context, balance lookup, position lookup, or order privileges.

The adapter should reject or safely diagnose non-OK Bybit responses using public response fields such as `retCode`, `retMsg`, `retExtInfo`, and `time`, without logging credentials or private headers.

## 5. Parser input bundle

Future Bybit adapter should build a parser-compatible bundle using the existing `bybit_linear` parser mode:

- `venue_id`: `bybit`
- `parser_mode`: `bybit_linear`
- `ticker_response`: raw public `/v5/market/tickers` JSON
- `orderbook_response`: raw public `/v5/market/orderbook` JSON
- `metadata_response`: raw public `/v5/market/instruments-info` JSON filtered or passed in parser-compatible shape for `BTCUSDT`
- `mark_response`: `ticker_response` or `None`, according to the existing parser contract and final adapter implementation choice
- `collected_at_utc`: adapter collection timestamp
- `latency_ms`: total or per-stage public-fetch latency metric
- `max_data_age_ms`: future config-driven freshness threshold

The future adapter should not mutate parser output before readiness evaluation except for explicitly documented packet-building normalization.

## 6. Parser/readiness flow

Future flow:

1. Fetch public Bybit ticker, orderbook, and instruments-info responses.
2. Record safe public-fetch diagnostics for each stage.
3. Call `parse_mark_orderbook_gap_snapshot` with `parser_mode="bybit_linear"`.
4. Call `evaluate_mark_orderbook_gap_readiness` with explicit conservative, config-driven analysis parameters.
5. Convert normalized parser/readiness output into an analysis-only OpportunityPacket.

Important readiness semantics:

- Parser `OK` does not mean `WATCH`.
- `NEED_DATA` remains valid when metadata, freshness, comparability, liquidity, or size/notional assumptions are unresolved.
- `REJECT` can be normal no-edge behavior, not an API failure.
- `WATCH`, if ever produced, remains analysis-only.
- Do not include `execution_allowed=true`.
- Do not include `council_auto_call=true`.
- Do not include `alert_trigger=true`.
- `readiness_pass` should remain false unless a future explicitly reviewed policy changes it.

## 7. OpportunityPacket mapping

Future packet identity fields:

- `strategy_family`: `mark_orderbook_gap_hunt`
- `strategy_id`: `mark_orderbook_gap_hunt_v0`
- `signal_type`: `mark_orderbook_gap_hunt`
- `asset`: `BTC`
- `quote`: `USDT`
- `execution_policy`: `NO_TRADE_ONLY`
- `experimental_strategy`: `true`
- `non_active_strategy`: `true`
- `no_trade_only`: `true`

Observation mapping target:

- `venue_id`: `bybit`
- `market_symbol` / `instrument_id`: `BTCUSDT`
- `instrument_type`: `linear_perpetual`
- `mark_price`
- `index_price`
- `bid`
- `ask`
- `bid_size`
- `ask_size`
- `timestamp`
- `data_quality`
- `health`
- derivatives metadata in `extensions` when the current schema has no dedicated field

Candidate mapping target:

- `candidate_type`: `mark_orderbook_gap_observation`
- `long_gap_pct`
- `short_gap_pct`
- `max_observed_gap_pct`
- `estimated_net_gap_pct`
- `readiness_status`
- `recommended_default_decision`
- `liquidity_pass`
- `freshness_pass`
- `comparability_pass`
- `required_missing_fields`
- `warnings`
- `assumptions`:
  - mark price is not executable
  - WATCH is analysis-only
  - no private API
  - no trading behavior

## 8. Binance vs Bybit commonization analysis

Reusable/common pieces that should remain strategy-level rather than venue-specific where possible:

- Safe public-fetch diagnostics shape: endpoint, params, stage, status, safe response preview, and sanitized error details.
- Parser/readiness invocation: call parser by venue mode, then call the shared readiness helper.
- OpportunityPacket identity: strategy family/id, signal type, BTC/USDT asset/quote, candidate type, and `NO_TRADE_ONLY` metadata.
- Candidate mapping: gap metrics, readiness status, default decision, gate booleans, missing fields, warnings, and assumptions.
- No-trade assertions: no execution fields, no Council auto-call fields, no alert trigger fields, no private credentials.
- Sampling interpretation: `REJECT` can mean no-edge behavior; `WATCH` is analysis-only; `NO_PERSISTENT_EDGE` should not promote the strategy.
- Generated artifact handling: generated packet/sampling JSON is smoke output only and must not be committed.

Bybit-specific pieces that should stay localized to the future Bybit adapter:

- `base_url`: `https://api.bybit.com`
- Endpoint paths and query parameters.
- `category=linear` handling.
- Bybit V5 response shape under `retCode`, `retMsg`, `result`, and `time`.
- Ticker field mapping such as `markPrice`, `indexPrice`, `bid1Price`, `ask1Price`, `bid1Size`, `ask1Size`, `fundingRate`, and `nextFundingTime`.
- Orderbook field mapping such as `result.b`, `result.a`, `ts`, `cts`, `u`, and `seq`.
- Symbol and category matching for `BTCUSDT` / `linear`.
- Metadata mapping for `priceFilter.tickSize`, `lotSizeFilter.qtyStep`, `lotSizeFilter.minOrderQty`, `lotSizeFilter.minNotionalValue`, and related fields.
- Bybit-specific diagnostics for public API return codes and safe response previews.

## 9. Future base adapter extraction candidates

Do not extract a generic/base Mark-Orderbook Gap Hunt venue adapter in this PR.

After Binance and Bybit implementations both exist, compare duplication before extracting shared helpers. A possible later task is:

`Mark-Orderbook Gap Hunt Venue Adapter Base Planning v0`

Candidate shared responsibilities for a future base/helper layer:

- Safe public fetch with diagnostics.
- Parser/readiness dispatch.
- OpportunityPacket construction.
- Adapter metadata generation.
- No-trade assertions.
- Diagnostics sanitization.
- Shared assumptions/warnings construction.
- Shared generated-artifact and user-local-smoke wording.

Do not extract too early if Bybit response/error/metadata behavior still differs materially from Binance.

## 10. User-local smoke plan

Future collect smoke command after Bybit implementation and registration:

```bash
python tools/collect_market_data.py --adapter live_bybit_mark_orderbook_gap_btcusdt --output data/generated_packets/live_bybit_mark_orderbook_gap_btcusdt.json
```

Future sampling smoke command after collect smoke and sampling readiness review:

```bash
python tools/sample_market_data.py --adapter live_bybit_mark_orderbook_gap_btcusdt --samples 3 --interval 1 --output data/market_samples/mark_orderbook_gap_bybit_sampling_summary.json
```

Smoke interpretation rules:

- Codex workspace live network may fail with tunnel or public endpoint restrictions and should not be a merge requirement.
- User-local normal-network smoke should be recorded in a separate evidence PR.
- Generated packet JSON and generated sampling JSON must be deleted after inspection and must not be committed.
- `NEED_DATA`, `REJECT`, or `WATCH` can all be valid readiness statuses depending on the live public data and configured analysis assumptions.
- `REJECT` is not necessarily a data failure.
- `WATCH` is analysis-only and must not trigger alert, Council, or execution behavior.

## 11. Future deferrals

Separate follow-up PRs should handle:

- `Mark-Orderbook Gap Hunt Bybit Runtime Adapter v0` implementation.
- Bybit config/registry registration after adapter tests pass.
- Bybit user-local collect smoke evidence after registration.
- Bybit sampling baseline and user-local sampling evidence.
- OKX runtime adapter planning/implementation.
- Multi-venue composite planning after individual venues are stable.
- Alert/notification common layer only after multiple strategies have stable criteria.
- Council auto-call only after explicit future policy review.
- Execution/private API only much later via a common execution/risk engine.
