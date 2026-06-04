# Mark-Orderbook Gap Hunt Binance Sampling Baseline v0

## 1. Purpose

Verify that the existing sampling pipeline can consume `mark_orderbook_gap_hunt` adapter-produced packet dictionaries and expose the minimum Binance Mark-Orderbook Gap Hunt sample/summary fields needed for future user-local sampling evidence.

This PR is not a live smoke PR. It uses mocked packet/adapter tests and does not make live network success a merge requirement.

## 2. Baseline

- `live_binance_mark_orderbook_gap_btcusdt` is registered and user-local `collect_market_data` smoke already succeeded.
- The adapter output is an analysis-only `OpportunityPacket` dictionary with `strategy_family=mark_orderbook_gap_hunt`.
- The packet-builder supports adapter-produced `mark_orderbook_gap_hunt` packets.
- Sampling planning identified sample-level and summary-level fields needed before persistence evidence.
- Generated packet/sampling JSON remains a smoke artifact and must not be committed.

## 3. Implementation summary

- Added Mark-Orderbook Gap Hunt field extraction in `src/market_data/sampling.py` sample records.
- Sampling now prefers packet/adapter readiness extension values for `mark_orderbook_gap_hunt` packets, so `REJECT` / `WATCH` / `NEED_DATA` comes from the parser-readiness contract rather than the generic unsupported-strategy fallback.
- Added sample-level fields for strategy id, gap metrics, readiness fields, liquidity/freshness/comparability, required missing fields, mark/index/bid/ask, no-trade metadata, and execution policy.
- Enriched summary output with positive gross gap count, readiness status counts, and explicit watch/reject/need-data counts.
- Added mocked unit tests in `tests/test_mark_orderbook_gap_hunt_sampling.py` using a static packet adapter; no live network or credential lookup is required.
- Did not modify `tools/sample_market_data.py`, config, registry, adapter, parser, readiness helper, generated data, alerts, Council, or execution/private API code.

## 4. Sampling summary fields

Sample-level fields now verified for Mark-Orderbook Gap Hunt include:

- `strategy_family`
- `strategy_id`
- `candidate_count`
- `readiness_status`
- `readiness_pass`
- `recommended_default_decision`
- `long_gap_pct`
- `short_gap_pct`
- `gross_gap_pct`
- `max_observed_gap_pct`
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

Summary-level fields now verified include:

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
- top-level `council_recommended: false` in mocked Mark-Orderbook Gap Hunt tests

## 5. Persistence interpretation

- `REJECT` remains normal no-edge behavior when estimated net gap is not positive after buffer; it is not an API failure by itself.
- `NEED_DATA` should indicate missing data, metadata, freshness, or comparability requirements.
- `WATCH` remains analysis-only and must not trigger alert, Council auto-call, active promotion, or execution.
- `readiness_pass` remains false in the current Mark-Orderbook Gap Hunt policy phase.
- `NO_PERSISTENT_EDGE` remains the expected persistence status when no repeated ready edge exists.

## 6. Tests run

- `git status` — checked before changes.
- `git diff --name-only` — checked before commit.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_sampling` — passed; 5 tests OK.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter` — passed; 9 tests OK.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_parser` — passed; 8 tests OK.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_readiness` — passed; 12 tests OK.
- `python -m unittest discover -s tests` — passed; 299 tests OK.
- `python tools/collect_market_data.py --list-adapters` — passed; output included `live_binance_mark_orderbook_gap_btcusdt`.
- `rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md` — completed; expected policy/test/documentation matches only.
- `rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md` — completed as a strategy/no-trade scan.
- `git status --short` — run after commit.

## 7. Expected user-local sampling smoke

Future user-local smoke command to run outside Codex workspace:

```bash
python tools/sample_market_data.py --adapter live_binance_mark_orderbook_gap_btcusdt --samples 3 --interval 1 --output data/market_samples/mark_orderbook_gap_binance_sampling_summary.json
```

Expected interpretation:

- `samples_ok` can be 3 if public endpoint collection succeeds.
- `readiness_status` may be `NEED_DATA`, `REJECT`, or `WATCH`.
- `REJECT` is not a sampling/API failure by itself.
- `WATCH` is analysis-only.
- `council_recommended` must remain false for this phase.
- Generated sampling JSON must be deleted after inspection and must not be committed.

## 8. What this proves

- The sampling pipeline can consume a mocked `mark_orderbook_gap_hunt` adapter-produced packet dictionary.
- Mark-Orderbook Gap Hunt sample-level fields can be surfaced without live network access.
- Mark-Orderbook Gap Hunt summary-level readiness/gap counts can be surfaced without adding alerts, Council auto-call, execution, or private APIs.
- Mocked `WATCH` remains analysis-only and does not introduce `execution_allowed`, `council_auto_call`, or `alert_trigger` fields.

## 9. What this does not prove

- It does not prove user-local sampling success.
- It does not prove profitability.
- It does not prove persistence across live market regimes.
- It does not add alert/notification behavior.
- It does not add Council auto-call.
- It does not add active strategy promotion.
- It does not add execution/private API behavior.
- It does not register Bybit/OKX adapters or implement a multi-venue composite.

## 10. Changed files

- `src/market_data/sampling.py` — minimal Mark-Orderbook Gap Hunt sample/summary field extraction.
- `tests/test_mark_orderbook_gap_hunt_sampling.py` — mocked sampling tests for Mark-Orderbook Gap Hunt packet consumption and no-trade boundaries.
- `docs/pr_handoffs/mark_orderbook_gap_hunt_binance_sampling_baseline_v0.md` — this handoff evidence file.
- `docs/sampling_plans/mark_orderbook_gap_hunt_binance_sampling_baseline_v0.md` — next-gate implementation note.

## 11. Risks

- Field names may need follow-up adjustment after user-local sampling evidence if live packet shapes expose additional useful metadata.
- Existing persistence summary status names are shared across strategy families; reviewers should interpret them through the Mark-Orderbook Gap Hunt handoff context.
- User-local live sampling may still fail because of public endpoint/network issues unrelated to this mocked sampling baseline.

## 12. Rollback plan

Revert this commit to remove the sampling field extraction, mocked tests, and handoff/plan update. No config/registry/adapter/parser/readiness rollback is required because those files are not changed in this PR.

## 13. Human review required

Reviewers should verify:

- sampling fields are read-only summaries of packet contents;
- `WATCH` remains analysis-only;
- `council_recommended` remains false in mocked Mark-Orderbook Gap Hunt sampling tests;
- no generated JSON is committed;
- no alert, Council auto-call, active promotion, execution, private API, config, registry, adapter, parser, or readiness helper change is included.

## 14. No-trade compliance

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
- Bybit/OKX adapter registration: no
- multi-venue composite implementation: no

## 15. Next recommended step

Run the documented user-local sampling command and record the result in a separate evidence-only PR. If it fails, classify the failure as network/public endpoint, adapter/packet-builder, sampling summary, or readiness interpretation before expanding scope.
