# Mark-Orderbook Gap Hunt Bybit Sampling Baseline v0

## 1. Purpose

Validate, mocked-first, that the existing sampling pipeline can consume `live_bybit_mark_orderbook_gap_btcusdt` adapter output shaped as a Bybit `mark_orderbook_gap_hunt` OpportunityPacket, while keeping the strategy experimental, non-active, analysis-only, and `NO_TRADE_ONLY`.

This PR also exposes minimal sampling summary/sample fields needed to inspect Bybit Mark-Orderbook Gap Hunt sampling output, including timestamp/data_age watch fields when a negative `data_age_ms` is present. It does not change parser/readiness/timestamp/freshness policy and does not clamp or reinterpret `data_age_ms`.

## 2. Baseline

- `live_bybit_mark_orderbook_gap_btcusdt` is already registered in config/registry.
- User-local direct Bybit adapter smoke succeeded.
- User-local official `collect_market_data` Bybit smoke succeeded.
- The official collect path generated an analysis-only `OpportunityPacket` with:
  - `strategy_family: mark_orderbook_gap_hunt`
  - `strategy_id: mark_orderbook_gap_hunt_v0`
  - `asset: BTC`
  - `quote: USDT`
  - `observations: 1`
  - `candidates: 1`
  - `venue_id: bybit`
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
- Negative `data_age_ms` around `-6647 ms` was observed in collect evidence and is carried forward as a timestamp/data_age watch item.
- The negative `data_age_ms` was not treated as a blocker in collect evidence because `parser_normalized_status=OK`, `freshness_pass=true`, `required_missing_fields=[]`, endpoint diagnostics were all OK, and packet creation succeeded.

## 3. Implementation summary

- Added minimal Mark-Orderbook Gap sampling sample fields in `src/market_data/sampling.py`:
  - `venue_id`
  - `market_symbol`
  - `parser_normalized_status`
  - `diagnostics_count`
  - `data_age_ms`
  - `timestamp_data_age_watch`
  - `negative_data_age_observed`
- Added summary-level timestamp/data_age watch fields in `src/market_data/sampling.py`:
  - `timestamp_data_age_watch_count`
  - `negative_data_age_observed`
- Added mocked Bybit sampling tests in `tests/test_mark_orderbook_gap_hunt_bybit_sampling.py` using a static mocked adapter and static Bybit `mark_orderbook_gap_hunt` OpportunityPacket.
- Updated the Bybit sampling baseline plan next gate wording in `docs/sampling_plans/mark_orderbook_gap_hunt_bybit_sampling_baseline_v0.md`.
- Did not modify `tools/sample_market_data.py` because the existing sampling pipeline can consume mocked Bybit adapter output through `run_market_sampling`.
- Did not modify config, registry, adapter, parser, readiness, timestamp/freshness logic, alert/Council/execution code, or generated data.

## 4. Sampling summary fields

The mocked Bybit sampling tests verify sample-level fields including:

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
- `data_age_ms`
- `timestamp_data_age_watch`
- `negative_data_age_observed`

The mocked Bybit sampling tests verify summary-level fields including:

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
- `timestamp_data_age_watch_count`
- `negative_data_age_observed`

## 5. Persistence interpretation

- `REJECT` remains normal no-edge behavior and is not treated as an API failure.
- `NEED_DATA` means data, metadata, freshness, or comparability requirements are missing.
- `WATCH` remains analysis-only and does not trigger alert, Council auto-call, active promotion, or execution.
- `NO_PERSISTENT_EDGE` remains expected when no repeated `WATCH` or positive net gap appears.
- `readiness_pass` remains `false` in the mocked Mark-Orderbook Gap fixtures unless a future explicit policy changes it.
- `council_recommended` remains `false` for this baseline.

## 6. Timestamp / data_age carry-forward

- Bybit collect smoke observed negative `data_age_ms` around `-6647 ms`.
- This likely reflects exchange timestamp vs local collection timestamp alignment or clock skew.
- It was not a blocker for collect evidence because `parser_normalized_status=OK`, `freshness_pass=true`, `required_missing_fields=[]`, endpoint diagnostics were all OK, and packet creation succeeded.
- This PR surfaces negative `data_age_ms` as `timestamp_data_age_watch` and counts it as `timestamp_data_age_watch_count` without changing policy.
- This PR preserves the raw negative `data_age_ms`; it does not clamp it.
- This PR does not reinterpret negative `data_age_ms` into failure, `NEED_DATA`, or `REJECT`.
- This PR does not change parser/readiness/timestamp/freshness logic.
- Future policy candidate remains `Market Data Timestamp Freshness / Clock Skew Policy v0` or `Mark-Orderbook Gap Hunt Timestamp Alignment Policy v0`.
- Future policy should compare Binance, Bybit, and OKX timestamp behavior before changing shared logic.

## 7. Tests run

Codex checks completed for this PR before commit:

- `git status` — showed only scoped changes before staging.
- `git diff --name-only` — showed tracked scoped changes before staging; new untracked test/handoff files were also visible in `git status`.
- `python -m unittest discover -s tests` — passed (`Ran 317 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_adapter` — passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter` — passed (`Ran 9 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_parser` — passed (`Ran 8 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_readiness` — passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_sampling` — passed (`Ran 5 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_sampling` — passed (`Ran 6 tests`, `OK`).
- `python tools/collect_market_data.py --list-adapters` — passed and listed `live_bybit_mark_orderbook_gap_btcusdt`.
- `rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md` — completed as a no-trade/credential scan across existing repository references.
- `rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md` — completed as an active-strategy/no-trade scan across existing repository references.
- `git status --short` — showed only scoped changes before staging.
- `git diff --name-only HEAD~1..HEAD` — to be recorded after commit in the final response.

## 8. Expected user-local sampling smoke

Future user-local smoke command, not required in Codex workspace:

```bash
python tools/sample_market_data.py --adapter live_bybit_mark_orderbook_gap_btcusdt --samples 3 --interval 1 --output data/market_samples/mark_orderbook_gap_bybit_sampling_summary.json
```

Expected interpretation:

- `samples_ok` can be `3` if public endpoint collection succeeds.
- `readiness_status` may be `NEED_DATA`, `REJECT`, or `WATCH`.
- `REJECT` is not failure.
- `WATCH` is analysis-only.
- `council_recommended` must remain `false`.
- Generated sampling JSON must be deleted after inspection and not committed.
- If negative `data_age_ms` appears, record it as a timestamp/data_age watch item unless a future policy task explicitly changes behavior.

## 9. What this proves

- The existing sampling pipeline can consume mocked Bybit `mark_orderbook_gap_hunt` packet output.
- Bybit sample-level Mark-Orderbook Gap fields can be surfaced in sampling output.
- Bybit summary-level readiness/gap/persistence fields can be summarized.
- Negative `data_age_ms` can be surfaced and counted as a watch item without policy changes.
- `REJECT` no-edge behavior remains distinct from API failure.
- `WATCH` remains analysis-only and does not create alert/Council/execution fields.
- `NO_TRADE_ONLY` boundary is preserved.

## 10. What this does not prove

- It does not prove user-local Bybit live sampling success.
- It does not prove profitability.
- It does not prove persistent edge.
- It does not justify alert or notification implementation.
- It does not justify Council auto-call.
- It does not justify active strategy promotion.
- It does not justify execution/private API.
- It does not prove OKX adapter or multi-venue composite behavior.
- It does not resolve timestamp freshness or clock-skew policy.
- It does not prove negative `data_age_ms` is always safe.

## 11. Changed files

- `src/market_data/sampling.py`
- `tests/test_mark_orderbook_gap_hunt_bybit_sampling.py`
- `docs/pr_handoffs/mark_orderbook_gap_hunt_bybit_sampling_baseline_v0.md`
- `docs/sampling_plans/mark_orderbook_gap_hunt_bybit_sampling_baseline_v0.md`

No config, registry, adapter, parser, readiness, tool, generated data, Council, notification, storage, OKX, composite, or generic/base adapter files are changed.

## 12. Risks

- Timestamp/data_age watch fields are visibility-only; a future policy task is still needed to decide how to handle exchange/local clock skew.
- User-local live sampling may fail due to public endpoint or network issues independent of the mocked sampling baseline.
- If future sampling implementation changes field names, tests and documentation should be updated together.

## 13. Rollback plan

- Revert this PR.
- Remove the Bybit sampling baseline test file and handoff changes.
- Revert the minimal sampling summary field additions.
- Re-run `python -m unittest discover -s tests` and targeted sampling tests.
- No generated data rollback is required because no generated JSON is committed.

## 14. Human review required

Human review should first inspect:

1. `src/market_data/sampling.py` to confirm only safe sampling summary exposure was added and no policy/clamp behavior changed.
2. `tests/test_mark_orderbook_gap_hunt_bybit_sampling.py` to confirm mocked Bybit packet coverage, no live network, and no execution/Council/alert fields.
3. This handoff file for scope, risks, rollback, timestamp/data_age carry-forward, and no-trade compliance.
4. `docs/sampling_plans/mark_orderbook_gap_hunt_bybit_sampling_baseline_v0.md` for next user-local evidence gate wording.

## 15. No-trade compliance

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
- OKX adapter registration: no
- multi-venue composite implementation: no
- generic/base adapter extraction: no
- parser/readiness/timestamp/freshness logic changes: no
- data_age_ms clamp or reinterpretation: no

## 16. Next recommended step

Open a separate `Mark-Orderbook Gap Hunt User-Local Bybit Sampling Smoke Evidence v0` docs-only PR after a human runs the future user-local sampling command from a normal network and deletes the generated sampling JSON after inspection.
