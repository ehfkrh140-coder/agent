# Mark-Orderbook Gap Hunt Bybit Sampling Baseline v0

## 1. Purpose

Document the Bybit sampling baseline scope for `live_bybit_mark_orderbook_gap_btcusdt`, including the mocked-first validation target and future user-local sampling evidence path.

This document records the baseline scope and next gate. The accompanying implementation PR validates the existing sampling pipeline with mocked Bybit `mark_orderbook_gap_hunt` packets and exposes timestamp/data_age watch fields without changing parser/readiness/timestamp/freshness policy. It does not modify `tools/sample_market_data.py`, config, registry, parser/readiness logic, alerts, Council behavior, active promotion, execution/private API, generated packet JSON, generated sampling JSON, OKX registration, multi-venue composite behavior, or generic/base adapter extraction.

## 2. Current baseline

- `live_bybit_mark_orderbook_gap_btcusdt` is registered in config/registry as disabled, experimental, non-active, and `NO_TRADE_ONLY`.
- User-local direct Bybit adapter smoke succeeded.
- User-local official `collect_market_data` Bybit smoke succeeded through the registered adapter id.
- The official collect smoke generated an analysis-only `OpportunityPacket` with one Bybit observation and one Mark-Orderbook Gap candidate.
- The collect smoke produced `readiness_status=REJECT`, `parser_normalized_status=OK`, `comparability_pass=true`, `freshness_pass=true`, `required_missing_fields=[]`, diagnostics count `3`, and no execution/Council/alert fields.
- A negative `data_age_ms` around `-6647 ms` was observed and is carried forward as a timestamp/data_age watch item only.

## 3. Sampling baseline scope

Planning target:

- adapter_id: `live_bybit_mark_orderbook_gap_btcusdt`
- strategy_family: `mark_orderbook_gap_hunt`
- strategy_id: `mark_orderbook_gap_hunt_v0`
- venue: `bybit`
- instrument: `BTCUSDT`
- category: `linear`
- status: experimental / disabled / non-active / `NO_TRADE_ONLY`
- sampling purpose: repeated analysis-only observations of mark-vs-orderbook gap candidates
- no alert
- no Council auto-call
- no execution
- no private API
- no credentials
- no generated JSON commit

## 4. Proposed sampling command

Future command to document only; do not run as a merge requirement in Codex:

```bash
python tools/sample_market_data.py --adapter live_bybit_mark_orderbook_gap_btcusdt --samples 3 --interval 1 --output data/market_samples/mark_orderbook_gap_bybit_sampling_summary.json
```

Generated sampling JSON is a smoke artifact only. It must be deleted after inspection and must not be committed.

## 5. Expected sample-level fields

Future Bybit sampling baseline should expose or allow inspection of the following sample-level fields when available:

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
- `gross_gap_pct` or `max_observed_gap_pct`
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
- `venue_id`
- `market_symbol`
- `parser_normalized_status`
- `diagnostics_count`
- `data_age_ms` or timestamp/data_age watch fields, if available

## 6. Expected summary-level fields

Future Bybit sampling baseline should expose or allow inspection of the following summary-level fields when available:

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
- `timestamp_data_age_watch_count` (planning-only if applicable)
- `negative_data_age_observed` (planning-only if applicable)

## 7. Persistence interpretation

- `NO_PERSISTENT_EDGE` should be used when there is no repeated `WATCH` and no repeated positive net gap.
- `REJECT` is normal no-edge behavior and should not be interpreted as an API/data failure by itself.
- `NEED_DATA` means data, metadata, freshness, or comparability requirements are missing.
- `WATCH` remains analysis-only and must not trigger Council, alert, notification, active promotion, or execution in this phase.
- `min_consecutive_ready` should remain planning-only until reviewed.
- `readiness_pass` should remain `false` unless a future explicit policy changes it.

## 8. Timestamp / data_age carry-forward

The Bybit user-local collect smoke observed negative `data_age_ms` around `-6647 ms`.

Carry-forward interpretation:

- This likely reflects exchange timestamp vs local collection timestamp alignment or clock skew.
- It was not a blocker for the collect evidence because `parser_normalized_status=OK`, `freshness_pass=true`, `required_missing_fields=[]`, endpoint diagnostics were all OK, and packet creation succeeded.
- Bybit sampling planning should record whether negative `data_age_ms` repeats across samples.
- Do not change code in this planning PR.
- Do not clamp negative `data_age_ms` in this planning PR.
- Do not reinterpret negative `data_age_ms` in this planning PR.
- Do not change parser/readiness/timestamp/freshness policy in this planning PR.

Future policy candidates remain:

- `Market Data Timestamp Freshness / Clock Skew Policy v0`
- `Mark-Orderbook Gap Hunt Timestamp Alignment Policy v0`

Future policy should compare Binance, Bybit, and OKX timestamp behavior before changing shared logic.

## 9. User-local smoke plan

Codex workspace live endpoint access may fail due to network tunnel or 403 restrictions, so live Bybit sampling should be a separate user-local evidence PR.

Future user-local sampling evidence should verify:

- the proposed sampling command completes from a normal local network;
- generated output is inspected and then deleted;
- generated sampling JSON is not committed;
- `REJECT` is treated as no-edge behavior, not API failure;
- `WATCH` remains analysis-only;
- `council_recommended` remains `false`;
- no `execution_allowed`, `council_auto_call`, or `alert_trigger` fields appear.

If user-local sampling fails, separate the failure class:

- network/public endpoint issue;
- adapter/packet-builder issue;
- sampling summary issue;
- readiness interpretation issue;
- timestamp/data_age policy issue.

## 10. Future implementation gate

Future `Mark-Orderbook Gap Hunt Bybit Sampling Baseline v0` PR should:

- use mocked tests first if `sample_market_data` or sampling code needs changes;
- keep `NO_TRADE_ONLY`;
- not add alert, Council auto-call, active promotion, or execution;
- not commit generated JSON;
- include handoff evidence;
- include user-local live smoke only as evidence, not a Codex workspace merge requirement;
- carry the timestamp/data_age watch item forward without changing policy unless explicitly scoped.

## 11. No-trade constraints

This plan does not add:

- private API;
- API key/secret/token;
- env credential lookup;
- auth/private headers;
- account/balance lookup;
- position lookup;
- order/cancel;
- withdrawal/deposit/transfer;
- fiat/bank transfer;
- auto-trading;
- Council auto-call;
- active strategy promotion;
- alert/notification expansion;
- generated packet JSON commit;
- generated sampling JSON commit;
- sampling implementation;
- parser/readiness/timestamp/freshness changes;
- `data_age_ms` clamp or reinterpretation.

## 12. Next recommended step

After this mocked-first sampling baseline is reviewed, open a separate `Mark-Orderbook Gap Hunt User-Local Bybit Sampling Smoke Evidence v0` PR. Keep generated sampling JSON out of git and carry the timestamp/data_age watch item forward without policy changes unless explicitly scoped.
