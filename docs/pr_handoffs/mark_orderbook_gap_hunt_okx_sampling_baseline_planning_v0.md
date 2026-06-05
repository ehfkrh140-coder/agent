# Mark-Orderbook Gap Hunt OKX Sampling Baseline Planning v0

## 1. Purpose

Document the OKX Mark-Orderbook Gap Hunt sampling baseline scope and expected summary fields before connecting `live_okx_mark_orderbook_gap_btc_usdt_swap` to `tools/sample_market_data.py` / the sampling pipeline.

This is a planning-only PR. It does not implement sampling, modify `tools/sample_market_data.py`, change config/registry, change adapter/parser/readiness/timestamp/freshness logic, change OKX index/reference semantics, clamp/reinterpret `data_age_ms`, add adapter metadata wording cleanup, add alert/Council/execution/private API behavior, create a multi-venue composite, or extract a generic/base adapter.

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
- Timestamp/freshness/index/reference policy must not change in this PR.

## 3. Sampling baseline scope

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

## 4. Proposed sampling command

Document only; do not require Codex workspace live network success:

```bash
python tools/sample_market_data.py --adapter live_okx_mark_orderbook_gap_btc_usdt_swap --samples 3 --interval 1 --output data/market_samples/mark_orderbook_gap_okx_sampling_summary.json
```

Generated sampling JSON is a smoke artifact only and must not be committed.

## 5. Expected sample-level fields

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
- `timestamp_data_age_watch_count`, planning-only if applicable
- `negative_data_age_observed`, planning-only if applicable
- `index_price_null_observed`, planning-only if applicable
- `stale_assumption_wording_observed`, planning-only if applicable

## 7. Persistence interpretation

- `NO_PERSISTENT_EDGE` if no repeated `WATCH` and no positive net gap.
- `REJECT` is normal no-edge behavior, not API failure.
- `NEED_DATA` means data, metadata, freshness, or comparability requirement is missing.
- `WATCH` is analysis-only and should not trigger Council, alert, or execution in this phase.
- `min_consecutive_ready` should remain planning-only until reviewed.
- `readiness_pass` should remain false unless future policy explicitly changes.

## 8. OKX index_price / reference carry-forward

- OKX collect smoke observed `index_price=None`.
- This was not a blocker because `required_missing_fields=[]`, `parser_normalized_status=OK`, readiness completed, and packet creation succeeded.
- Sampling planning should record whether `index_price` remains `None` across samples.
- Do not change OKX index/reference semantics in this PR.
- Future policy candidate: `Mark-Orderbook Gap OKX Index/Reference Semantics v0`.

## 9. Timestamp / data_age carry-forward

- OKX collect smoke observed negative `data_age_ms` around `-7577.9 ms`.
- This likely reflects exchange timestamp vs local collection timestamp alignment / clock skew.
- It was not a blocker for collect evidence because `parser_normalized_status=OK`, `freshness_pass=true`, `required_missing_fields=[]`, endpoint diagnostics all OK, and packet creation succeeded.
- Sampling planning should record whether negative `data_age_ms` repeats across samples.
- Do not change code or policy in this PR.
- Future policy candidates: `Market Data Timestamp Freshness / Clock Skew Policy v0` or `Mark-Orderbook Gap Hunt Timestamp Alignment Policy v0`.

## 10. Metadata wording cleanup carry-forward

- Metadata context cleanup removed stale PR-stage assumptions for future generated packets.
- Historical generated JSON may still contain stale wording and should not be treated as cleanup failure.
- Future OKX sampling smoke should verify newly generated packet assumptions do not include:
  - `no config registration in this PR`
  - `no registry integration in this PR`
  - `no sampling integration in this PR`
- Do not modify wording again in this planning PR.

## 11. User-local smoke plan

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

## 12. Future implementation gate

Future `Mark-Orderbook Gap Hunt OKX Sampling Baseline v0` PR should:

- use mocked tests first if `sample_market_data.py` needs code changes;
- keep `NO_TRADE_ONLY`;
- not add alert/Council/execution;
- not commit generated JSON;
- include handoff evidence;
- include user-local smoke only as evidence, not Codex workspace requirement;
- carry OKX index/reference and timestamp/data_age watch items forward without changing policy unless explicitly scoped;
- verify metadata wording cleanup effect in mocked or generated packet assumptions if practical.

## 13. Tests run

- `git status` completed before and after edits to confirm only the two allowed planning docs changed.
- `git diff --name-only` completed before commit; only the two allowed planning docs were present as untracked/new files before staging.
- `python -m unittest discover -s tests` passed (`Ran 330 tests`, `OK`).
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
- `git status --short` confirmed only the two allowed planning docs were changed before staging/commit.

## 14. What this proves

- OKX sampling baseline scope is documented.
- Expected sample-level fields are documented.
- Expected summary-level fields are documented.
- Persistence interpretation is documented.
- OKX `index_price=None` carry-forward is documented without changing semantics.
- Negative `data_age_ms` carry-forward is documented without changing timestamp/freshness policy.
- Metadata wording cleanup carry-forward is documented without further wording changes.
- User-local sampling smoke is planned as separate evidence, not Codex workspace merge requirement.

## 15. What this does not prove

- It does not implement OKX sampling.
- It does not prove user-local OKX sampling success.
- It does not prove profitability or persistent edge.
- It does not justify alert/notification implementation.
- It does not justify Council auto-call.
- It does not justify active strategy promotion.
- It does not justify execution/private API.
- It does not implement multi-venue composite.
- It does not implement generic/base adapter extraction.
- It does not resolve timestamp freshness / clock-skew policy.
- It does not resolve OKX index/reference semantics.
- It does not change adapter metadata wording.

## 16. Changed files

- `docs/sampling_plans/mark_orderbook_gap_hunt_okx_sampling_baseline_v0.md`
- `docs/pr_handoffs/mark_orderbook_gap_hunt_okx_sampling_baseline_planning_v0.md`

No `src/`, `configs/`, `tests/`, `tools/`, generated data, Council, notification, storage, Gemini runtime/prompt, parser/readiness/timestamp/freshness, OKX index/reference semantics, adapter metadata wording, sampling implementation, multi-venue composite, or generic/base adapter files are changed.

## 17. Risks

- Future OKX sampling may expose repeated `index_price=None`, negative `data_age_ms`, or endpoint/network issues.
- Future implementation could accidentally widen into sampling logic, alert/Council/execution, timestamp policy, or OKX index/reference semantics if not constrained.
- Historical generated JSON may still contain stale assumption wording and should not be mistaken for a metadata cleanup regression.
- Human review is required before any sampling implementation.

## 18. Rollback plan

- Revert this docs-only planning PR.
- Remove `docs/sampling_plans/mark_orderbook_gap_hunt_okx_sampling_baseline_v0.md`.
- Remove `docs/pr_handoffs/mark_orderbook_gap_hunt_okx_sampling_baseline_planning_v0.md`.
- No code/config/test/tool/generated-data rollback is required.
- Re-run `python -m unittest discover -s tests` if rollback verification is desired.

## 19. Human review required

Human review should first inspect:

1. `docs/sampling_plans/mark_orderbook_gap_hunt_okx_sampling_baseline_v0.md` to confirm the OKX sampling baseline scope and expected fields.
2. This handoff file to confirm no-trade compliance, future implementation gate, index/reference carry-forward, timestamp/data_age carry-forward, metadata wording cleanup carry-forward, and generated artifact handling.

## 20. No-trade compliance

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
- multi-venue composite implementation: no
- generic/base adapter extraction: no
- parser/readiness/timestamp/freshness logic changes: no
- data_age_ms clamp or reinterpretation: no
- OKX index/reference semantics change: no
- adapter metadata wording cleanup: no

## 21. Next recommended step

Open a separate `Mark-Orderbook Gap Hunt OKX Sampling Baseline v0` implementation PR after human review. Keep it mocked-first, `NO_TRADE_ONLY`, generated-artifact-free, and separate from alert/Council/execution/private API, multi-venue composite, generic/base adapter extraction, timestamp policy, OKX index/reference semantics, and further metadata wording cleanup.
