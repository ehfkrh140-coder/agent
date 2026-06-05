# Mark-Orderbook Gap Hunt OKX Sampling Baseline v0

## 1. Purpose

Verify mocked-first that the existing sampling pipeline can consume `live_okx_mark_orderbook_gap_btc_usdt_swap` / `mark_orderbook_gap_hunt` OKX packet output, and add only the minimal sampling-summary watch fields needed for OKX baseline review.

This PR does not require live network smoke, does not change config/registry, does not change adapter/parser/readiness/timestamp/freshness policy, does not change OKX index/reference semantics, does not clamp or reinterpret `data_age_ms`, does not add alert/Council/execution/private API behavior, does not create generated artifacts, does not implement a multi-venue composite, and does not extract a generic/base adapter.

## 2. Baseline

- `live_okx_mark_orderbook_gap_btc_usdt_swap` adapter is registered in config/registry.
- User-local direct OKX adapter smoke succeeded.
- User-local official `collect_market_data` OKX smoke succeeded.
- Official collect path generated an analysis-only `OpportunityPacket` with:
  - `strategy_family: mark_orderbook_gap_hunt`
  - `strategy_id: mark_orderbook_gap_hunt_v0`
  - `asset: BTC`
  - `quote: USDT`
  - `observations: 1`
  - `candidates: 1`
  - `venue_id: okx`
  - `market_symbol: BTC-USDT-SWAP`
  - `readiness_status: REJECT`
  - `parser_normalized_status: OK`
  - `comparability_pass: true`
  - `freshness_pass: true`
  - `diagnostics_count: 3`
  - `no_trade_only: true`
  - `execution_policy: NO_TRADE_ONLY`
  - no `execution_allowed`
  - no `council_auto_call`
  - no `alert_trigger`
- Generated packet JSON was a smoke artifact and was not committed.
- OKX collect smoke observed `index_price=None`.
- OKX collect smoke observed negative `data_age_ms` around `-7577.9 ms`.
- Metadata context cleanup removed stale PR-stage wording from future generated packet assumptions.
- Historical generated JSON may still contain stale wording; this is expected and should not be treated as cleanup failure.

## 3. Implementation summary

- Added `index_price_null_observed` to each successful sampling record when the first observation exists and its `index_price` is `None`.
- Added `stale_assumption_wording_observed` to each successful sampling record by scanning candidate assumptions for stale PR-stage phrases:
  - `no config registration in this PR`
  - `no registry integration in this PR`
  - `no sampling integration in this PR`
- Added summary-level `index_price_null_count`, `index_price_null_observed`, `stale_assumption_wording_count`, and `stale_assumption_wording_observed` fields.
- Preserved existing negative `data_age_ms` behavior: sampling surfaces the value and counts it as `timestamp_data_age_watch_count` without clamping or reinterpretation.
- Added mocked OKX sampling tests that use an in-memory adapter and packet, with no live network or env credential lookup.
- Did not modify `tools/sample_market_data.py`; the existing tool path continues to call `run_market_sampling`.

## 4. Sampling summary fields

The mocked OKX sampling test confirms sample-level exposure of:

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
- `index_price_null_observed`
- `bid`
- `ask`
- `no_trade_only`
- `execution_policy`
- `venue_id`
- `market_symbol`
- `parser_normalized_status`
- `diagnostics_count`
- `data_age_ms`
- `timestamp_data_age_watch`
- `negative_data_age_observed`
- `stale_assumption_wording_observed`

The mocked OKX sampling summary test confirms summary-level exposure of:

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
- `timestamp_data_age_watch_count`
- `negative_data_age_observed`
- `index_price_null_count`
- `index_price_null_observed`
- `stale_assumption_wording_count`
- `stale_assumption_wording_observed`

`council_recommended` remains top-level sampling output metadata and is asserted `false` for the mocked OKX baseline.

## 5. Persistence interpretation

- `NO_PERSISTENT_EDGE` remains the expected no-edge summary when mocked samples have a positive gross gap but no positive net gap and no repeated ready edge.
- `REJECT` remains normal no-edge behavior, not API failure.
- `NEED_DATA` remains the state for missing data, metadata, freshness, or comparability requirements.
- `WATCH` remains analysis-only and must not trigger Council, alert, or execution.
- `readiness_pass` remains false in the mocked `WATCH` test to preserve current analysis-only policy.

## 6. OKX index_price / reference carry-forward

- OKX collect smoke observed `index_price=None`.
- This remains non-blocking because `required_missing_fields=[]`, `parser_normalized_status=OK`, readiness completed, and packet creation succeeded.
- Sampling now surfaces `index_price_null_observed` per sample and `index_price_null_count` / `index_price_null_observed` at summary level.
- This is a watch item only; this PR does not change OKX index/reference semantics.
- Future policy candidate remains `Mark-Orderbook Gap OKX Index/Reference Semantics v0`.

## 7. Timestamp / data_age carry-forward

- OKX collect smoke observed negative `data_age_ms` around `-7577.9 ms`.
- This likely reflects exchange timestamp vs local collection timestamp alignment / clock skew.
- It was not a blocker for collect evidence because `parser_normalized_status=OK`, `freshness_pass=true`, `required_missing_fields=[]`, endpoint diagnostics all OK, and packet creation succeeded.
- Sampling continues to surface negative `data_age_ms` and count it as a timestamp/data_age watch.
- This PR does not clamp, reinterpret, or otherwise change timestamp/freshness policy.
- Future policy candidates remain `Market Data Timestamp Freshness / Clock Skew Policy v0` or `Mark-Orderbook Gap Hunt Timestamp Alignment Policy v0`.

## 8. Metadata wording cleanup carry-forward

- Metadata context cleanup removed stale PR-stage assumptions for future generated packets.
- Historical generated JSON may still contain stale wording and should not be treated as cleanup failure.
- Sampling now exposes `stale_assumption_wording_observed` per sample and summary-level stale wording count/flag.
- Mocked tests verify future-style packet assumptions do not trip the stale wording flag, while an intentionally stale mocked assumption does trip the guard.
- This PR does not modify adapter metadata wording.

## 9. Tests run

- `git status` completed before edits to confirm branch/worktree state.
- `git diff --name-only` completed before commit to confirm only allowed files changed.
- `python -m unittest discover -s tests` passed (`Ran 338 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_okx_sampling` passed (`Ran 8 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_okx_adapter` passed (`Ran 13 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_sampling` passed (`Ran 6 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_adapter` passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter` passed (`Ran 9 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_parser` passed (`Ran 8 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_readiness` passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_sampling` passed (`Ran 5 tests`, `OK`).
- `python tools/collect_market_data.py --list-adapters` passed and listed `live_okx_mark_orderbook_gap_btc_usdt_swap`.
- `rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md` completed as an audit scan; matches are existing policy/test/doc references and no generated artifacts were introduced.
- `rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md` completed as a strategy/no-trade audit scan.
- `git status --short` confirmed only allowed files were changed before staging/commit.

## 10. Expected user-local sampling smoke

Future user-local evidence command, not required for Codex merge:

```bash
python tools/sample_market_data.py --adapter live_okx_mark_orderbook_gap_btc_usdt_swap --samples 3 --interval 1 --output data/market_samples/mark_orderbook_gap_okx_sampling_summary.json
```

Expected interpretation:

- `samples_ok` can be `3` if public endpoint collection succeeds.
- `readiness_status` may be `NEED_DATA`, `REJECT`, or `WATCH`.
- `REJECT` is not failure.
- `WATCH` is analysis-only.
- `council_recommended` must remain `false`.
- Generated sampling JSON must be deleted after inspection and not committed.
- If `index_price=None` appears, record it as OKX index/reference watch item unless a future policy task changes behavior.
- If negative `data_age_ms` appears, record it as timestamp/data_age watch item unless a future policy task changes behavior.
- If stale assumption wording appears in newly generated packets after cleanup, record it as metadata wording regression.

## 11. What this proves

- Existing sampling pipeline can consume mocked OKX `mark_orderbook_gap_hunt` packet output.
- OKX sample-level Mark-Orderbook Gap fields and summary-level readiness/gap/persistence fields can be surfaced.
- `index_price=None` can be surfaced as a watch item without changing OKX index/reference policy.
- Negative `data_age_ms` can be surfaced and counted as a watch item without changing timestamp/freshness policy.
- Stale assumption wording can be checked as a cleanup regression guard.
- `WATCH` remains analysis-only and does not create execution/Council/alert fields.

## 12. What this does not prove

- It does not prove user-local OKX live sampling success.
- It does not prove profitability or persistent edge.
- It does not justify alert/notification implementation.
- It does not justify Council auto-call.
- It does not justify active strategy promotion.
- It does not justify execution/private API.
- It does not justify multi-venue composite behavior.
- It does not resolve timestamp freshness / clock-skew policy.
- It does not resolve OKX index_price/reference semantics.
- It does not implement generic/base adapter extraction.

## 13. Changed files

- `src/market_data/sampling.py`
- `tests/test_mark_orderbook_gap_hunt_okx_sampling.py`
- `docs/pr_handoffs/mark_orderbook_gap_hunt_okx_sampling_baseline_v0.md`

No `configs/`, registry, adapter, parser, readiness, Council, notification, storage, generated packet, generated sampling, Gemini runtime/prompt, multi-venue composite, or generic/base adapter files are changed.

## 14. Risks

- Future live OKX sampling may expose repeated `index_price=None`, negative `data_age_ms`, endpoint/network failures, or summary interpretation gaps.
- The stale wording guard is based on explicit known phrases and should be updated only if future cleanup policies identify additional stale phrases.
- Human review is required before relying on user-local live sampling evidence.

## 15. Rollback plan

- Revert this PR.
- Remove `tests/test_mark_orderbook_gap_hunt_okx_sampling.py`.
- Revert the minimal `src/market_data/sampling.py` watch-field additions.
- Remove `docs/pr_handoffs/mark_orderbook_gap_hunt_okx_sampling_baseline_v0.md`.
- No config/registry/adapter/parser/readiness/tool/generated-artifact rollback is required.
- Re-run `python -m unittest discover -s tests` after rollback if verification is desired.

## 16. Human review required

Human review should first inspect:

1. `src/market_data/sampling.py` to confirm the new fields are summary/watch exposure only.
2. `tests/test_mark_orderbook_gap_hunt_okx_sampling.py` to confirm mocked-first OKX packet sampling, no live network, no env lookup, no execution/Council/alert fields, no policy changes, and stale wording guard coverage.
3. This handoff file to confirm no-trade compliance, rollback, expected user-local smoke, and watch-item carry-forward.

## 17. No-trade compliance

- private API: no
- API key/secret/token: no
- env credential lookup: no
- auth/private headers: no
- account/balance lookup: no
- position lookup: no
- order/cancel: no
- withdrawal/deposit/transfer: no
- fiat/bank transfer: no
- auto-trading: no
- Council auto-call: no
- Council decision to trade conversion: no
- active strategy promotion: no
- alert expansion: no
- notification expansion: no
- generated packet JSON commit: no
- generated sampling JSON commit: no
- live network smoke as merge requirement: no
- config/registry changes: no
- adapter/parser/readiness logic changes: no
- parser/readiness/timestamp/freshness logic changes: no
- data_age_ms clamp or reinterpretation: no
- OKX index/reference semantics change: no
- multi-venue composite implementation: no
- generic/base adapter extraction: no

## 18. Next recommended step

After human review, run a separate user-local OKX sampling smoke evidence PR using normal network access. Keep generated sampling JSON out of git, carry `index_price=None` and negative `data_age_ms` as watch items, and do not add alert/Council/execution/private API behavior.
