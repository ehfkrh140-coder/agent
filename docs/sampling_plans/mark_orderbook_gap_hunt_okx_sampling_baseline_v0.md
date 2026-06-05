# Mark-Orderbook Gap Hunt OKX Sampling Baseline Planning v0

## 1. Purpose

Plan the OKX Mark-Orderbook Gap Hunt sampling baseline before connecting `live_okx_mark_orderbook_gap_btc_usdt_swap` to `tools/sample_market_data.py` / the sampling pipeline.

This is planning-only. It does not implement sampling, change `tools/sample_market_data.py`, change config/registry, change adapter/parser/readiness/timestamp/freshness logic, change OKX index/reference semantics, clamp/reinterpret `data_age_ms`, add metadata wording cleanup, add alert/Council/execution behavior, or create generated artifacts.

## 2. Sampling baseline scope

- adapter_id: `live_okx_mark_orderbook_gap_btc_usdt_swap`
- strategy_family: `mark_orderbook_gap_hunt`
- strategy_id: `mark_orderbook_gap_hunt_v0`
- venue: `okx`
- instrument: `BTC-USDT-SWAP`
- inst_type: `SWAP`
- status: experimental / disabled / non-active / `NO_TRADE_ONLY`
- sampling is analysis-only
- no alert
- no Council auto-call
- no execution

## 3. Proposed sampling command

Document only; do not require Codex workspace live network success:

```bash
python tools/sample_market_data.py --adapter live_okx_mark_orderbook_gap_btc_usdt_swap --samples 3 --interval 1 --output data/market_samples/mark_orderbook_gap_okx_sampling_summary.json
```

Generated sampling JSON is a smoke artifact only and must not be committed.

## 4. Expected sample-level fields

Sampling summary should eventually expose or allow inspection of:

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
- `venue_id`
- `market_symbol`
- `parser_normalized_status`
- `diagnostics_count`
- `data_age_ms` or timestamp/data_age watch fields, if available
- `index_price_null_observed` or OKX index/reference watch field, planning-only if applicable
- `stale_assumption_wording_observed`, expected to be `false` for future generated packets after metadata context cleanup

## 5. Expected summary-level fields

Planning target:

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
- `timestamp_data_age_watch_count`, planning-only if applicable
- `negative_data_age_observed`, planning-only if applicable
- `index_price_null_observed`, planning-only if applicable
- `stale_assumption_wording_observed`, planning-only if applicable

## 6. Persistence interpretation

- `NO_PERSISTENT_EDGE` if no repeated `WATCH` and no repeated positive net gap.
- `REJECT` is normal no-edge behavior, not API failure.
- `NEED_DATA` means a data, metadata, freshness, or comparability requirement is missing.
- `WATCH` is analysis-only and must not trigger Council, alert, or execution in this phase.
- `min_consecutive_ready` should remain planning-only until reviewed.
- `readiness_pass` should remain false unless future policy explicitly changes.

## 7. OKX index_price / reference carry-forward

- OKX collect smoke observed `index_price=None`.
- This was not a blocker because `required_missing_fields=[]`, `parser_normalized_status=OK`, readiness completed, and packet creation succeeded.
- Sampling planning should record whether `index_price` remains `None` across samples.
- Do not change OKX index/reference semantics in this PR.
- Future policy candidate: `Mark-Orderbook Gap OKX Index/Reference Semantics v0`.

## 8. Timestamp / data_age carry-forward

- OKX collect smoke observed negative `data_age_ms` around `-7577.9 ms`.
- This likely reflects exchange timestamp vs local collection timestamp alignment / clock skew.
- It was not a blocker for collect evidence because `parser_normalized_status=OK`, `freshness_pass=true`, `required_missing_fields=[]`, endpoint diagnostics all OK, and packet creation succeeded.
- Sampling planning should record whether negative `data_age_ms` repeats across samples.
- Do not change code or policy in this PR.
- Future policy candidates: `Market Data Timestamp Freshness / Clock Skew Policy v0` or `Mark-Orderbook Gap Hunt Timestamp Alignment Policy v0`.

## 9. Metadata wording cleanup carry-forward

- Metadata context cleanup removed stale PR-stage assumptions for future generated packets.
- Historical generated JSON may still contain stale wording and should not be treated as cleanup failure.
- Future OKX sampling smoke should verify newly generated packet assumptions do not include:
  - `no config registration in this PR`
  - `no registry integration in this PR`
  - `no sampling integration in this PR`
- Do not modify wording again in this planning PR.

## 10. User-local smoke plan

- Codex workspace may fail due to network tunnel / 403 restrictions.
- User-local normal-network sampling evidence should be separate.
- Generated output must be removed after inspection.
- If user-local sampling fails, separate:
  - network/public endpoint issue
  - adapter/packet-builder issue
  - sampling summary issue
  - readiness interpretation issue
  - timestamp/data_age policy issue
  - OKX index/reference issue
  - stale assumption wording issue

## 11. Future implementation gate

Future `Mark-Orderbook Gap Hunt OKX Sampling Baseline v0` PR should:

- use mocked tests first if `sample_market_data.py` needs code changes;
- keep `NO_TRADE_ONLY`;
- not add alert/Council/execution;
- not commit generated JSON;
- include handoff evidence;
- include user-local smoke only as evidence, not Codex workspace requirement;
- carry OKX index/reference and timestamp/data_age watch items forward without changing policy unless explicitly scoped;
- verify metadata wording cleanup effect in mocked or generated packet assumptions if practical.

## 12. Next recommended step

Open a separate `Mark-Orderbook Gap Hunt OKX Sampling Baseline v0` implementation PR after human review. Keep it mocked-first, `NO_TRADE_ONLY`, generated-artifact-free, and separate from alert/Council/execution/private API, multi-venue composite, generic/base adapter extraction, timestamp policy, and OKX index/reference semantics changes.
