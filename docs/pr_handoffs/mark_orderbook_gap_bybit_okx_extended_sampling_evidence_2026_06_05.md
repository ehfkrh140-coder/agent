# Mark-Orderbook Gap Hunt Bybit/OKX Extended Sampling Evidence v0

## 1. Purpose

Record user-local 30-sample extended sampling evidence for the experimental, non-active, analysis-only `mark_orderbook_gap_hunt_v0` venue adapters:

- Bybit: `live_bybit_mark_orderbook_gap_btcusdt`
- OKX: `live_okx_mark_orderbook_gap_btc_usdt_swap`

This is a docs-only evidence PR. The user-local sampling run produced generated JSON smoke artifacts, but those artifacts are not source files and must not be committed.

## 2. Scope and baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains experimental, non-active, and `NO_TRADE_ONLY`.
- Binance already has 30-sample extended sampling evidence.
- This evidence extends Bybit and OKX from prior 3-sample user-local sampling smoke to 30-sample user-local evidence.
- No source code, config, registry, parser, readiness, timestamp policy, OKX index/reference endpoint, commonization, alert, Council auto-call, execution, or generated-data file is changed.

## 3. Bybit extended sampling evidence

- `adapter_id`: `live_bybit_mark_orderbook_gap_btcusdt`
- `samples_requested`: 30
- `samples_ok`: 30
- `samples_error`: 0
- `candidate_seen_count`: 30
- `positive_net_gap_count`: 0
- `readiness_pass_count`: 0
- `persistence_status`: `NO_PERSISTENT_EDGE`
- `recommended_default_decision`: `REJECT`
- `readiness_status_counts.REJECT`: 30
- `council_recommended`: false
- `max_gross_gap_pct`: 0.023012054161426362
- `max_estimated_net_gap_pct`: -0.17698794583857363
- `avg_estimated_net_gap_pct`: -0.19653008998817884
- `positive_gross_gap_count`: 25
- `timestamp_data_age_watch_count`: 21
- `negative_data_age_observed`: true
- `index_price_null_count`: 0
- `index_price_null_observed`: false
- `stale_assumption_wording_count`: 0
- `stale_assumption_wording_observed`: false

### Bybit interpretation

- The Bybit 30-sample run is evidence that the sampling pipeline completed successfully for all requested user-local live public samples.
- `candidate_seen_count=30` confirms that every successful sample produced a Mark-Orderbook Gap candidate record.
- `positive_gross_gap_count=25` shows gross mark-vs-orderbook gap observations, but gross gap alone is not an executable or profitable edge.
- `positive_net_gap_count=0`, `readiness_pass_count=0`, `NO_PERSISTENT_EDGE`, `REJECT`, and `council_recommended=false` are normal no-edge outcomes.
- `timestamp_data_age_watch_count=21` with `negative_data_age_observed=true` remains a timestamp/clock-skew policy watch item.
- `index_price_null_observed=false` indicates the Bybit samples did not show missing index price values in this evidence set.
- `stale_assumption_wording_observed=false` confirms stale-assumption wording was not observed in the generated sample evidence.

## 4. OKX extended sampling evidence

- `adapter_id`: `live_okx_mark_orderbook_gap_btc_usdt_swap`
- `samples_requested`: 30
- `samples_ok`: 30
- `samples_error`: 0
- `candidate_seen_count`: 30
- `positive_net_gap_count`: 0
- `readiness_pass_count`: 0
- `persistence_status`: `NO_PERSISTENT_EDGE`
- `recommended_default_decision`: `REJECT`
- `readiness_status_counts.REJECT`: 30
- `council_recommended`: false
- `max_gross_gap_pct`: 0.02771747402488164
- `max_estimated_net_gap_pct`: -0.17228252597511837
- `avg_estimated_net_gap_pct`: -0.19391529014802814
- `positive_gross_gap_count`: 28
- `timestamp_data_age_watch_count`: 30
- `negative_data_age_observed`: true
- `index_price_null_count`: 30
- `index_price_null_observed`: true
- `stale_assumption_wording_count`: 0
- `stale_assumption_wording_observed`: false

### OKX interpretation

- The OKX 30-sample run is evidence that the sampling pipeline completed successfully for all requested user-local live public samples.
- `candidate_seen_count=30` confirms that every successful sample produced a Mark-Orderbook Gap candidate record.
- `positive_gross_gap_count=28` shows gross mark-vs-orderbook gap observations, but gross gap alone is not an executable or profitable edge.
- `positive_net_gap_count=0`, `readiness_pass_count=0`, `NO_PERSISTENT_EDGE`, `REJECT`, and `council_recommended=false` are normal no-edge outcomes.
- `timestamp_data_age_watch_count=30` with `negative_data_age_observed=true` adds OKX to the timestamp/clock-skew policy watch list.
- `index_price_null_count=30` and `index_price_null_observed=true` remain an OKX index/reference semantics watch item.
- `stale_assumption_wording_observed=false` confirms stale-assumption wording was not observed in the generated sample evidence.

## 5. Cross-venue interpretation

- This result proves sampling-pipeline success for user-local Bybit and OKX 30-sample runs.
- This result does not prove profitable edge.
- This result does not prove persistent edge.
- `NO_PERSISTENT_EDGE`, `REJECT`, and `council_recommended=false` are expected no-edge classifications, not failures.
- Mark price is not an executable price; it must not be treated as a directly tradable bid/ask.
- `WATCH` and `REJECT` are analysis-only labels.
- This evidence does not justify active strategy promotion, alerting, Council auto-call, execution, private API, order placement, or auto-trading.
- `NO_TRADE_ONLY` remains mandatory.

## 6. Watch items

- Bybit negative `data_age_ms` remains a timestamp/clock-skew policy watch item.
- OKX negative `data_age_ms` is now also observed and should be tracked as a timestamp/clock-skew policy watch item.
- OKX `index_price=None` remains an OKX index/reference semantics watch item.
- Future policy work may compare Binance, Bybit, and OKX timestamp semantics, but this PR does not implement timestamp policy.
- Future OKX index/reference work may clarify or enrich OKX index semantics, but this PR does not implement an OKX index endpoint.
- Future venue adapter commonization may reduce duplication, but this PR does not implement commonization.

## 7. Generated artifact handling

The user-local run may have produced generated sampling JSON under paths such as:

- `data/market_samples/*.json`
- `data/generated_packets/*.json`

These files are smoke artifacts only and must not be committed. This PR intentionally commits only this handoff evidence document.

## 8. Out of scope confirmation

This PR does not change or add:

- `src/` code
- config or strategy registry files
- active strategy state
- private API usage
- credentials, API keys, secrets, tokens, or auth headers
- account, balance, position, order, cancel, withdraw, deposit, or transfer behavior
- Council auto-call
- alerts or notifications
- execution engine or auto-trading behavior
- generated sampling JSON
- generated packet JSON
- venue adapter commonization
- timestamp policy
- OKX index endpoint implementation

## 9. Tests and verification expected for this PR

Codex should verify:

- `git status --short`
- `git diff --name-only origin/main...HEAD` when `origin/main` exists in the workspace
- generated JSON is not staged or committed
- changed files are limited to `docs/pr_handoffs/mark_orderbook_gap_bybit_okx_extended_sampling_evidence_2026_06_05.md`

Because this is a docs-only evidence PR and the user explicitly scoped the work to a single handoff document, no live smoke should be run by Codex. The user-local 30-sample evidence is recorded here, and generated JSON remains uncommitted.

## 10. Rollback plan

- Revert this docs-only PR.
- Remove `docs/pr_handoffs/mark_orderbook_gap_bybit_okx_extended_sampling_evidence_2026_06_05.md`.
- No code, config, registry, generated JSON, runtime, adapter, parser, readiness, timestamp policy, OKX index semantics, Council, alert, or execution rollback is required.

## 11. No-trade compliance

- Public-data evidence only: yes
- Analysis-only labels only: yes
- `NO_TRADE_ONLY` preserved: yes
- Active strategy unchanged: yes
- Private API: no
- Credentials/API keys/secrets/tokens: no
- Account/balance/position lookup: no
- Order/cancel: no
- Withdrawal/deposit/transfer: no
- Council auto-call: no
- Alerts/notifications: no
- Execution engine/auto-trading: no
