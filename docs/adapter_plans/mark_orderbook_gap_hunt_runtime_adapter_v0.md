# Mark-Orderbook Gap Hunt Runtime Adapter Planning v0

## Purpose

Plan the first runtime market-data adapter for `Mark-Orderbook Gap Hunt v0` before any adapter, config registration, sampling, alert, Council auto-call, active promotion, or execution work is implemented.

This document is planning-only. It does not modify `src/**`, `configs/**`, `tests/**`, `tools/**`, generated data, Council runtime, notification runtime, storage runtime, or Gemini runtime/prompt files.

## Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains experimental / non-active / `NO_TRADE_ONLY`.
- A pure parser already exists for Binance USDⓈ-M, Bybit linear, and OKX swap public response dictionaries.
- A pure readiness helper already maps normalized parser output to `NEED_DATA`, `REJECT`, or analysis-only `WATCH`.
- Neither parser nor readiness helper calls live network, reads credentials, places orders, triggers Council, emits alerts, or writes generated artifacts.

## Adapter v0 scope

Proposed first adapter:

- Adapter ID: `live_binance_mark_orderbook_gap_btcusdt`
- Venue: Binance USDⓈ-M Futures
- Instrument: `BTCUSDT`
- Strategy family: `mark_orderbook_gap_hunt`
- Strategy ID: `mark_orderbook_gap_hunt_v0`
- Status: experimental / non-active / `NO_TRADE_ONLY`

Purpose:

Collect public mark price, orderbook, and exchangeInfo metadata for Binance USDⓈ-M `BTCUSDT`, then feed those public responses into the existing parser and readiness helper to produce a normalized snapshot plus analysis-only candidate fields.

Initial v0 should be single-venue and single-instrument. Bybit and OKX parsers exist, but runtime adapters for those venues should remain follow-up PRs after the Binance adapter plan is reviewed.

## Public endpoints

All endpoints must be public no-key endpoints. No private/auth/account/order/transfer endpoint is allowed.

### Mark price

```text
https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT
```

Expected use:

- raw `mark_response` for parser mode `binance_usdm`
- fields of interest: `symbol`, `markPrice`, `indexPrice`, `lastFundingRate`, `nextFundingTime`, `time`

### Orderbook

```text
https://fapi.binance.com/fapi/v1/depth?symbol=BTCUSDT&limit=5
```

The `limit` should be configurable later, but v0 can start with a small public depth request for top-of-book planning.

Expected use:

- raw `orderbook_response` for parser mode `binance_usdm`
- fields of interest: `bids`, `asks`, `E`, `T`, `lastUpdateId`

### Metadata

```text
https://fapi.binance.com/fapi/v1/exchangeInfo
```

Expected use:

- raw `metadata_response` for parser mode `binance_usdm`
- adapter should filter the `symbols` array to selected `BTCUSDT` or pass a response shape compatible with the parser fixture
- fields of interest: `symbol`, `pair`, `contractType`, `status`, `baseAsset`, `quoteAsset`, `marginAsset`, `PRICE_FILTER.tickSize`, `LOT_SIZE.stepSize`, `LOT_SIZE.minQty`, `MIN_NOTIONAL.notional`

## Parser input bundle

The adapter should build this parser input bundle:

- `venue_id`: `binance`
- `parser_mode`: `binance_usdm`
- `mark_response`: raw JSON dict from `premiumIndex`
- `orderbook_response`: raw JSON dict from `depth`
- `metadata_response`: raw JSON dict or filtered exchangeInfo-compatible dict
- `ticker_response`: `None`
- `collected_at_utc`: adapter collection timestamp
- `latency_ms`: measured public request / bundle latency
- `max_data_age_ms`: configured planning threshold

The adapter must not include credentials, auth headers, account identifiers, balances, positions, orders, withdrawals, deposits, transfers, or private endpoint payloads in this bundle.

## Parser/readiness flow

Planned flow:

1. Adapter fetches public mark price.
2. Adapter fetches public orderbook depth.
3. Adapter fetches or caches public exchangeInfo metadata and filters to `BTCUSDT`.
4. Adapter calls `parse_mark_orderbook_gap_snapshot` with `parser_mode=binance_usdm`.
5. Adapter calls `evaluate_mark_orderbook_gap_readiness` with explicit planning thresholds.
6. Adapter builds an `OpportunityPacket` with observation/candidate metadata for review.

Boundary rules:

- Parser `OK` does not mean `WATCH`.
- Readiness `WATCH` remains analysis-only.
- No `execution_allowed=true`.
- No `council_auto_call=true`.
- No `alert_trigger=true`.
- No order placement, account lookup, balance lookup, transfer, withdrawal, deposit, fiat/bank flow, or private API.

## OpportunityPacket mapping

Planned packet fields:

- `strategy_family`: `mark_orderbook_gap_hunt`
- `strategy_id`: `mark_orderbook_gap_hunt_v0`
- `signal_type`: `mark_orderbook_gap_hunt`
- `adapter_id`: `live_binance_mark_orderbook_gap_btcusdt`
- `execution_policy`: `NO_TRADE_ONLY`

### Observation mapping

Observation should include, where schema supports it:

- `venue_id`: `binance`
- `market_symbol` / `instrument_id`: `BTCUSDT`
- `instrument_type`: `linear_perpetual`
- `mark_price`
- `index_price`
- `bid`
- `ask`
- `bid_size`
- `ask_size`
- `tick_size`
- `quantity_step`
- `min_order_size`
- `min_notional`
- `margin_asset`
- `funding_rate`
- `next_funding_time`
- `timestamp`
- `data_age_ms`
- derivatives metadata in `extensions` if the core schema does not have dedicated fields

### Candidate mapping

Candidate should include:

- `candidate_type`: `mark_orderbook_gap_observation`
- `long_gap_pct`
- `short_gap_pct`
- `max_observed_gap_pct`
- `fee_slippage_buffer_pct`
- `estimated_net_gap_pct`
- `readiness_status`
- `readiness_pass`: `false` in this phase
- `recommended_default_decision`
- `liquidity_pass`
- `freshness_pass`
- `comparability_pass`
- `required_missing_fields`
- `warnings`

Candidate assumptions should explicitly include:

- mark price is not executable;
- bid/ask are the executable reference inputs;
- `WATCH` is analysis-only;
- no private API / no trading behavior;
- no Council auto-call;
- no alert/notification trigger.

## Readiness threshold planning

Thresholds are planning/config inputs, not execution rules.

Initial adapter planning should require explicit values for:

- `fee_slippage_buffer_pct`: placeholder; must be documented or config-driven in the implementation PR
- `min_net_gap_pct`: placeholder; must be documented or config-driven in the implementation PR
- `max_data_age_ms`: public data freshness threshold
- `liquidity_pass`: initial behavior should be conservative; if size/notional is unresolved, return `NEED_DATA`
- `size_or_notional_resolved`: should remain false unless the adapter can prove quantity unit and notional formula are known
- metadata caching / refresh policy: must not hide stale metadata or stale market data

Do not hard-code trading thresholds as execution rules. Any future threshold change needs human review and must remain analysis-only unless a separate execution/risk-engine task is approved.

## Live testing plan

Codex workspace live network may fail due to network tunnel `403`; that should be treated as an environment limitation, not a code failure.

Unit tests for the future adapter should use mocked public responses first.

User-local live smoke should be a follow-up after adapter implementation, for example:

```text
python tools/collect_market_data.py --adapter live_binance_mark_orderbook_gap_btcusdt --output data/generated_packets/debug_mark_orderbook_gap_binance.json
```

Generated packet JSON must be deleted after smoke and must not be committed.

## Future expansion

- Bybit linear runtime adapter should be a separate follow-up.
- OKX swap runtime adapter should be a separate follow-up.
- Multi-venue composite / comparison should be later.
- Sampling integration should be later.
- Alert/notification should be much later, after multiple strategies share decision criteria.
- Council auto-call should be much later and still analysis-only unless explicitly reviewed.
- Execution/private API work should be much later and must use a common execution/risk engine, credential isolation, dry-run/paper trading, kill switch, risk limits, order-state machine, audit logs, rollback plan, and explicit human review.

## Next recommended step

Open `Mark-Orderbook Gap Hunt Binance Runtime Adapter v0` only after this planning PR is reviewed. That follow-up should still be public-read-only, `NO_TRADE_ONLY`, and should not add config registration until explicitly scoped.
