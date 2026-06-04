# Mark-Orderbook Gap Hunt Bybit Sampling Baseline Planning v0

## 1. Purpose

Document the planned Bybit sampling baseline scope for `live_bybit_mark_orderbook_gap_btcusdt` before connecting or validating it through `tools/sample_market_data.py` and the sampling summary pipeline.

This PR is planning-only. It does not implement sampling, does not modify `tools/sample_market_data.py`, does not modify config/registry, does not modify parser/readiness/timestamp/freshness logic, does not clamp or reinterpret `data_age_ms`, and does not add alert, Council auto-call, active promotion, execution/private API, generated packet JSON, generated sampling JSON, OKX registration, multi-venue composite behavior, or generic/base adapter extraction.

## 2. Baseline

- `live_bybit_mark_orderbook_gap_btcusdt` is registered in config/registry.
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
- Negative `data_age_ms` around `-6647 ms` was observed and is carried forward as a timestamp/data_age watch item.
- The negative `data_age_ms` was not treated as a blocker in collect evidence because `parser_normalized_status=OK`, `freshness_pass=true`, `required_missing_fields=[]`, endpoint diagnostics were all OK, and packet creation succeeded.

## 3. Sampling baseline scope

Planning target:

- adapter_id: `live_bybit_mark_orderbook_gap_btcusdt`
- strategy_family: `mark_orderbook_gap_hunt`
- strategy_id: `mark_orderbook_gap_hunt_v0`
- venue: `bybit`
- instrument: `BTCUSDT`
- category: `linear`
- status: experimental / disabled / non-active / `NO_TRADE_ONLY`
- sampling is analysis-only
- no alert
- no Council auto-call
- no execution

## 4. Proposed sampling command

Documented future user-local sampling command:

```bash
python tools/sample_market_data.py --adapter live_bybit_mark_orderbook_gap_btcusdt --samples 3 --interval 1 --output data/market_samples/mark_orderbook_gap_bybit_sampling_summary.json
```

Generated sampling JSON is a smoke artifact only. It must be removed after inspection and must not be committed.

## 5. Expected sample-level fields

Future sampling summary should eventually expose or allow inspection of:

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

## 6. Expected summary-level fields

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
- `timestamp_data_age_watch_count` (planning-only if applicable)
- `negative_data_age_observed` (planning-only if applicable)

## 7. Persistence interpretation

- `NO_PERSISTENT_EDGE` applies if no repeated `WATCH` and no repeated positive net gap are observed.
- `REJECT` is normal no-edge behavior, not API failure.
- `NEED_DATA` means data, metadata, freshness, or comparability requirements are missing.
- `WATCH` is analysis-only and should not trigger Council, alert, notification, active promotion, or execution in this phase.
- `min_consecutive_ready` should remain planning-only until reviewed.
- `readiness_pass` should remain `false` unless future policy explicitly changes.

## 8. Timestamp / data_age carry-forward

- Bybit collect smoke observed negative `data_age_ms` around `-6647 ms`.
- This likely reflects exchange timestamp vs local collection timestamp alignment or clock skew.
- It was not a blocker for collect evidence because `parser_normalized_status=OK`, `freshness_pass=true`, `required_missing_fields=[]`, endpoint diagnostics were all OK, and packet creation succeeded.
- Sampling planning should record whether negative `data_age_ms` repeats across samples.
- Do not change code or policy in this PR.
- Do not clamp negative `data_age_ms` in this PR.
- Do not reinterpret negative `data_age_ms` in this PR.
- Do not change parser/readiness/timestamp/freshness logic in this PR.
- Future policy candidate remains `Market Data Timestamp Freshness / Clock Skew Policy v0` or `Mark-Orderbook Gap Hunt Timestamp Alignment Policy v0`.
- Future policy should compare Binance, Bybit, and OKX timestamp behavior before changing shared logic.

## 9. User-local smoke plan

Codex workspace live network may fail due to tunnel or 403 restrictions. User-local normal-network sampling evidence should be recorded separately.

Future user-local sampling evidence should:

- run the proposed sampling command from a normal local network;
- inspect and then remove generated output;
- keep generated sampling JSON out of git;
- confirm `NO_TRADE_ONLY` remains preserved;
- confirm `council_recommended` remains `false`;
- confirm no `execution_allowed`, `council_auto_call`, or `alert_trigger` fields are present.

If user-local sampling fails, separate the failure class into:

- network/public endpoint issue;
- adapter/packet-builder issue;
- sampling summary issue;
- readiness interpretation issue;
- timestamp/data_age policy issue.

## 10. Future implementation gate

Future `Mark-Orderbook Gap Hunt Bybit Sampling Baseline v0` PR should:

- use mocked tests first if `sample_market_data` needs code changes;
- keep `NO_TRADE_ONLY`;
- not add alert, Council auto-call, active promotion, or execution;
- not commit generated JSON;
- include handoff evidence;
- include user-local smoke only as evidence, not a Codex workspace requirement;
- carry timestamp/data_age watch item forward without changing policy unless explicitly scoped.

## 11. Tests run

Codex checks completed for this planning-only PR before commit:

- `git status` — clean before the docs-only change, then showed only the two new planning docs.
- `git diff --name-only` — showed no tracked file diff before staging because the only changes were new untracked docs.
- `python -m unittest discover -s tests` — passed (`Ran 311 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_adapter` — passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter` — passed (`Ran 9 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_parser` — passed (`Ran 8 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_readiness` — passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_sampling` — passed (`Ran 5 tests`, `OK`).
- `python tools/collect_market_data.py --list-adapters` — passed and listed `live_bybit_mark_orderbook_gap_btcusdt`.
- `rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md` — completed as a no-trade/credential scan across existing repository references.
- `rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md` — completed as an active-strategy/no-trade scan across existing repository references.
- `git status --short` — to be checked again after staging/commit; before staging it showed only the two new planning docs.
- `git diff --name-only HEAD~1..HEAD` — to be recorded after commit in the final response.

## 12. What this proves

- Bybit sampling baseline scope has been defined before implementation.
- Expected sample-level and summary-level fields are documented for review.
- Persistence interpretation is documented before user-local sampling evidence.
- The negative `data_age_ms` watch item is carried forward without code/policy changes.
- The next PR can be scoped as `Mark-Orderbook Gap Hunt Bybit Sampling Baseline v0`.

## 13. What this does not prove

- It does not prove Bybit sampling implementation.
- It does not prove `tools/sample_market_data.py` live success for Bybit.
- It does not prove sampling persistence behavior.
- It does not prove profitability.
- It does not justify alert or notification implementation.
- It does not justify Council auto-call.
- It does not justify active strategy promotion.
- It does not justify execution/private API.
- It does not prove OKX adapter or multi-venue composite behavior.
- It does not resolve timestamp freshness or clock-skew policy.
- It does not prove negative `data_age_ms` is always safe.

## 14. Changed files

- `docs/sampling_plans/mark_orderbook_gap_hunt_bybit_sampling_baseline_v0.md`
- `docs/pr_handoffs/mark_orderbook_gap_hunt_bybit_sampling_baseline_planning_v0.md`

No `src/**`, `configs/**`, `tests/**`, `tools/**`, or generated `data/**` files are changed.

## 15. Risks

- Sampling implementation details may reveal missing fields or summary gaps later; this PR only plans the target fields.
- Negative `data_age_ms` remains a watch item and is not resolved here.
- User-local sampling may fail for network/public endpoint reasons independent of adapter code.
- Without mocked implementation tests in the future PR, sampling summary changes could accidentally blur `REJECT`, `NEED_DATA`, and `WATCH` interpretation.

## 16. Rollback plan

- Revert this planning-only PR.
- Confirm both planning docs are removed.
- No code/config/test/tool rollback is required because none are changed.
- Re-run docs or unit checks as needed.

## 17. Human review required

Human review should first inspect:

1. `docs/sampling_plans/mark_orderbook_gap_hunt_bybit_sampling_baseline_v0.md` for field and scope expectations.
2. This handoff file for baseline, timestamp/data_age carry-forward, risks, rollback, and no-trade compliance.
3. The future implementation gate before opening `Mark-Orderbook Gap Hunt Bybit Sampling Baseline v0`.

## 18. No-trade compliance

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
- sampling implementation: no
- live network smoke as merge requirement: no
- OKX adapter registration: no
- multi-venue composite implementation: no
- generic/base adapter extraction: no
- parser/readiness/timestamp/freshness logic changes: no
- data_age_ms clamp or reinterpretation: no

## 19. Next recommended step

Open `Mark-Orderbook Gap Hunt Bybit Sampling Baseline v0` as a separate mocked-first implementation PR. Keep user-local sampling smoke as a later evidence PR, and carry the timestamp/data_age watch item forward without changing policy unless explicitly scoped.
