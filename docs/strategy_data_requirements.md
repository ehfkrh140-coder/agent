# Strategy Data Requirement Matrix

## cross_exchange_spot_spread (active P0)

| Area | Required data |
| --- | --- |
| Observations | venue_id, market_symbol, instrument_type=spot, bid, ask, bid_size, ask_size, timestamp_utc |
| Fees | source/taker or trading fee, target/taker or trading fee |
| Liquidity | orderbook_depth_available, depth_levels, estimated_executable_notional |
| Data quality | timestamps_available, max_data_age_ms, latency_ms |
| Candidate | candidate_type=spot_executable_spread_candidate, direction=buy_source_ask_sell_target_bid_candidate, source_observation_id, target_observation_id, estimated_net_gap_pct |
| Default if missing | NEED_DATA |
| Reject if | estimated_net_gap_pct <= 0, stale data, liquidity_pass=false |

## mark_orderbook_gap (experimental)

| Area | Required data |
| --- | --- |
| Observations | mark_price, bid, ask, bid_size, ask_size, leverage or max_leverage, unit, timestamp_utc |
| Candidate | long_gap_pct or short_gap_pct, target_gap_pct, notional, guard flags |
| Default if active v1 | Treat as experimental and do not elevate beyond WATCH/NEED_DATA without explicit future rule |

## future strategy families

Future strategies remain documented in `configs/strategy_registry.yaml` but are not active trading-rule inputs in v1.
