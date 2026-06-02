# Active Strategy

## Active strategy
- `strategy_family`: `cross_exchange_spot_spread`
- `strategy_id`: `cross_exchange_spot_spread_v1`

## Purpose
Detect a potentially executable spot spread between public spot exchanges using source ask and target bid, not last-price gaps.

## Required data
- Best bid and best ask.
- Orderbook depth.
- Target-notional VWAP for source buy and target sell sides.
- Fee configuration.
- Timestamp, latency, and data-age metadata.
- Liquidity and freshness checks.

## Not required for the active strategy
The active spot strategy does not use:
- `mark_price`
- `index_price`
- `leverage`
- `funding_rate`
- `open_interest`

Those fields may exist for experimental or future strategies, but they are not required for `cross_exchange_spot_spread_v1`.

## Current venues and market
- Current venues: Upbit and Bithumb.
- Quote currency: KRW.
- Instrument type: spot.

## Current state
The project is in read-only sampling and alert stage. It can collect public data, compute VWAP/readiness, sample persistence, write journals/alerts, and produce Council handoff packets only when a persistent ready edge exists. It does not execute trades.
