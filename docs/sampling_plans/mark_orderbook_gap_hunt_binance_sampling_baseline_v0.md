# Mark-Orderbook Gap Hunt Binance Sampling Baseline Planning v0

## Purpose

Plan the future sampling baseline for the experimental Binance-only `mark_orderbook_gap_hunt_v0` adapter before implementing sampling/persistence changes. This document is planning-only and does not modify `tools/sample_market_data.py`, runtime code, config, registry, tests, generated artifacts, alerts, Council behavior, or execution/private API surfaces.

## Current baseline

- Adapter id: `live_binance_mark_orderbook_gap_btcusdt`.
- Strategy family: `mark_orderbook_gap_hunt`.
- Strategy id: `mark_orderbook_gap_hunt_v0`.
- Venue/instrument: Binance USDⓈ-M Futures `BTCUSDT`.
- Status: experimental / disabled / non-active / `NO_TRADE_ONLY`.
- User-local official `collect_market_data` smoke succeeded and generated an analysis-only `OpportunityPacket` with one observation and one candidate.
- The observed user-local readiness result was `REJECT`, which is normal no-edge behavior when estimated net gap is negative after buffer.
- Generated collect smoke JSON was not committed and future sampling JSON must also not be committed.

## Sampling baseline scope

Future sampling should be scoped to:

- `adapter_id`: `live_binance_mark_orderbook_gap_btcusdt`
- `strategy_family`: `mark_orderbook_gap_hunt`
- `strategy_id`: `mark_orderbook_gap_hunt_v0`
- `venue`: `binance`
- `instrument`: `BTCUSDT`
- `status`: experimental / non-active / `NO_TRADE_ONLY`
- `sampling_role`: analysis-only baseline

Out of scope for the future baseline:

- alert/notification behavior;
- Council auto-call;
- active strategy promotion;
- execution/private API;
- Bybit/OKX adapter registration;
- multi-venue composite implementation;
- generated sampling JSON commit.

## Proposed sampling command

Recommended conservative user-local command for the first sampling evidence run:

```bash
python tools/sample_market_data.py --adapter live_binance_mark_orderbook_gap_btcusdt --samples 3 --interval 1 --output data/market_samples/mark_orderbook_gap_binance_sampling_summary.json
```

Optional extended command after the conservative run is reviewed:

```bash
python tools/sample_market_data.py --adapter live_binance_mark_orderbook_gap_btcusdt --samples 5 --interval 1 --output data/market_samples/mark_orderbook_gap_binance_sampling_summary.json
```

Generated sampling JSON is a smoke artifact only. It must be inspected locally, summarized in a handoff, and removed before commit.

## Expected sample-level fields

Future sampling summaries should expose or allow inspection of these sample-level fields:

- `sample_index`
- `status`
- `error`
- `packet_id`
- `strategy_family`
- `strategy_id`
- `candidate_count`
- `readiness_status`
- `readiness_pass`
- `recommended_default_decision`
- `best_candidate`
- `long_gap_pct`
- `short_gap_pct`
- `gross_gap_pct` / `max_observed_gap_pct`
- `estimated_net_gap_pct`
- `liquidity_pass`
- `freshness_pass`
- `comparability_pass`
- `required_missing_fields`
- `mark_price`
- `index_price`
- `bid`
- `ask`
- `no_trade_only`
- `execution_policy`

## Expected summary-level fields

Future summary-level output should include:

- `samples_requested`
- `samples_ok`
- `samples_error`
- `candidate_seen_count`
- `positive_gross_gap_count`
- `positive_net_gap_count`
- `readiness_status_counts`
- `watch_count`
- `reject_count`
- `need_data_count`
- `max_estimated_net_gap_pct`
- `avg_estimated_net_gap_pct`
- `max_gross_gap_pct`
- `avg_latency_ms`
- `max_latency_ms`
- `persistence_status`
- `recommended_default_decision`
- `council_recommended: false`

## Persistence interpretation

- `NO_PERSISTENT_EDGE`: no repeated analysis-only `WATCH` and no repeated positive net gap.
- `REJECT`: normal no-edge behavior, not an API failure.
- `NEED_DATA`: data, metadata, freshness, or comparability requirement is missing.
- `WATCH`: analysis-only observation; must not trigger Council, alert, active promotion, or execution in this phase.
- `min_consecutive_ready`: planning-only until reviewed.
- `readiness_pass`: should remain false unless future policy explicitly changes.

## User-local smoke plan

- Codex workspace live network may fail with tunnel `403 Forbidden`; workspace live success must not be a merge requirement.
- User-local normal-network sampling evidence should be captured in a separate evidence-only PR after implementation or if existing sampling already supports the adapter.
- Generated output must be removed after inspection and must not be committed.
- If user-local sampling fails, triage separately:
  - network/public endpoint issue;
  - adapter/packet-builder issue;
  - sampling summary issue;
  - readiness interpretation issue.

## Future implementation gate

A future `Mark-Orderbook Gap Hunt Binance Sampling Baseline v0` implementation PR should:

- use mocked tests first if `tools/sample_market_data.py` or sampling summary code needs changes;
- preserve `NO_TRADE_ONLY`;
- avoid alert/Council/execution additions;
- avoid generated JSON commits;
- include a handoff evidence file;
- include user-local smoke only as evidence, not as a Codex workspace merge requirement;
- keep Bybit/OKX and multi-venue composite work out of scope.


## Implementation note from Sampling Baseline v0

The follow-up Sampling Baseline v0 implementation should preserve this planning scope. The first implementation target is minimal summary-field extraction in `src/market_data/sampling.py` plus mocked tests for `mark_orderbook_gap_hunt` packet consumption. Any user-local sampling JSON remains a smoke artifact and must not be committed. Future work after implementation should record user-local sampling evidence separately and must not add alert, Council auto-call, active promotion, execution, private API, Bybit/OKX registration, or multi-venue composite behavior.
