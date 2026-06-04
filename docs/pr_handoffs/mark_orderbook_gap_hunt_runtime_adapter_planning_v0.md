# Mark-Orderbook Gap Hunt Runtime Adapter Planning v0 Handoff

## 1. Purpose

Document the runtime adapter scope and packet mapping for `Mark-Orderbook Gap Hunt v0` before implementing any market-data adapter.

This PR is planning-only. It does not implement a runtime adapter, config registration, `collect_market_data` integration, `sample_market_data` integration, sampling, alert/notification, Council auto-call, active strategy promotion, execution/private API, generated packet JSON, or generated sampling JSON.

## 2. Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains experimental / non-active / `NO_TRADE_ONLY`.
- The pure parser already supports Binance USDⓈ-M, Bybit linear, and OKX swap response dictionaries.
- The pure readiness helper already maps parser output to `NEED_DATA`, `REJECT`, or analysis-only `WATCH`.
- Parser/readiness helpers have no network, credential, order, Council, alert, or execution side effects.

## 3. Adapter v0 scope

Proposed first adapter:

- Adapter ID: `live_binance_mark_orderbook_gap_btcusdt`
- Venue: Binance USDⓈ-M Futures
- Instrument: `BTCUSDT`
- Strategy family: `mark_orderbook_gap_hunt`
- Strategy ID: `mark_orderbook_gap_hunt_v0`
- Status: experimental / non-active / `NO_TRADE_ONLY`

The first adapter should be Binance-only and BTCUSDT-only to keep scope small. Bybit and OKX parser support exists, but runtime adapters for those venues should be separate follow-ups.

## 4. Public endpoints

All proposed endpoints are public no-key endpoints:

- Mark price: `https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT`
- Orderbook: `https://fapi.binance.com/fapi/v1/depth?symbol=BTCUSDT&limit=5`
- Metadata: `https://fapi.binance.com/fapi/v1/exchangeInfo`, filtered to `BTCUSDT`

Forbidden endpoint classes:

- private/auth endpoints;
- account/balance endpoints;
- order/cancel endpoints;
- withdrawal/deposit/transfer endpoints;
- fiat/bank endpoints.

## 5. Parser input bundle

Adapter should build:

- `venue_id`: `binance`
- `parser_mode`: `binance_usdm`
- `mark_response`: raw premiumIndex JSON dict
- `orderbook_response`: raw depth JSON dict
- `metadata_response`: raw or filtered exchangeInfo-compatible JSON dict
- `ticker_response`: `None`
- `collected_at_utc`: adapter collection timestamp
- `latency_ms`: measured public request/bundle latency
- `max_data_age_ms`: planning freshness threshold

The bundle must not include credentials, auth headers, account state, balances, orders, withdrawals, deposits, transfers, fiat/bank data, or private payloads.

## 6. Parser/readiness flow

Planned flow:

1. Fetch public mark price.
2. Fetch public orderbook depth.
3. Fetch or cache public exchangeInfo metadata and filter `BTCUSDT`.
4. Call `parse_mark_orderbook_gap_snapshot` with `parser_mode=binance_usdm`.
5. Call `evaluate_mark_orderbook_gap_readiness` with explicit planning thresholds.
6. Build an `OpportunityPacket` for analysis/review.

Boundary rules:

- Parser `OK` does not mean `WATCH`.
- `WATCH` remains analysis-only.
- No `execution_allowed=true`.
- No `council_auto_call=true`.
- No `alert_trigger=true`.
- No private API, account/balance lookup, order/cancel, withdrawal/deposit/transfer, fiat/bank flow, auto-trading, or execution.

## 7. OpportunityPacket mapping

Packet identity fields:

- `strategy_family`: `mark_orderbook_gap_hunt`
- `strategy_id`: `mark_orderbook_gap_hunt_v0`
- `signal_type`: `mark_orderbook_gap_hunt`
- `adapter_id`: `live_binance_mark_orderbook_gap_btcusdt`
- `execution_policy`: `NO_TRADE_ONLY`

Observation fields, where schema supports them:

- `venue_id`
- `market_symbol` / `instrument_id`
- `instrument_type`
- `mark_price`
- `index_price`
- `bid`
- `ask`
- `bid_size`
- `ask_size`
- `tick_size`
- `quantity_step`
- `min_order_size`
- `min_notional`
- `margin_asset`
- `funding_rate`
- `next_funding_time`
- `timestamp`
- `data_age_ms`
- derivatives metadata in `extensions` if needed

Candidate fields:

- `candidate_type`: `mark_orderbook_gap_observation`
- `long_gap_pct`
- `short_gap_pct`
- `max_observed_gap_pct`
- `fee_slippage_buffer_pct`
- `estimated_net_gap_pct`
- `readiness_status`
- `readiness_pass`: `false` in this phase
- `recommended_default_decision`
- `liquidity_pass`
- `freshness_pass`
- `comparability_pass`
- `required_missing_fields`
- `warnings`
- assumptions: mark price is not executable; `WATCH` is analysis-only; no private API or trading behavior

## 8. Readiness threshold planning

Thresholds remain planning/config inputs:

- `fee_slippage_buffer_pct`: placeholder; document/configure in implementation PR
- `min_net_gap_pct`: placeholder; document/configure in implementation PR
- `max_data_age_ms`: public data freshness threshold
- `liquidity_pass`: conservative initial behavior; unresolved size/notional should produce `NEED_DATA`
- `size_or_notional_resolved`: false unless adapter proves quantity unit and notional formula
- metadata cache/refresh policy: must not hide stale market data or stale metadata

Thresholds must not be hard-coded as execution rules. Any future threshold change requires review and remains analysis-only unless a separate execution/risk-engine task is approved.

## 9. Live testing plan

Codex workspace live network may fail due to network tunnel `403`; this should be treated as an environment limitation, not a code failure.

Future adapter unit tests should use mocked public responses first.

User-local live smoke should be a follow-up after adapter implementation:

```text
python tools/collect_market_data.py --adapter live_binance_mark_orderbook_gap_btcusdt --output data/generated_packets/debug_mark_orderbook_gap_binance.json
```

Generated packet JSON must be deleted after smoke and must not be committed.

## 10. Future expansion

- Bybit linear adapter: separate follow-up.
- OKX swap adapter: separate follow-up.
- Multi-venue composite: later.
- Sampling integration: later.
- Alert/notification: much later, after multiple strategies share decision criteria.
- Council auto-call: much later and analysis-only unless explicitly reviewed.
- Execution/private API: much later via common execution/risk engine, credential isolation, dry-run/paper trading, kill switch, risk limits, order-state machine, audit logs, rollback plan, and explicit human review.

## 11. Tests run

### Git status

```text
git status
```

Result: passed before staging; branch `mark-orderbook-gap-runtime-adapter-planning-v0` had only the allowed new adapter-plan directory and handoff file untracked.

### Git diff name check

```text
git diff --name-only
```

Result: passed before staging; no tracked-file diff was present because the allowed files were new/untracked before staging.

### Commit diff name check

```text
git diff --name-only HEAD~1..HEAD
```

Result: passed after commit; output contained only `docs/adapter_plans/mark_orderbook_gap_hunt_runtime_adapter_v0.md` and `docs/pr_handoffs/mark_orderbook_gap_hunt_runtime_adapter_planning_v0.md`.

### Full unit test

```text
python -m unittest discover -s tests
```

Result: passed (`Ran 285 tests in 12.398s`, `OK`).

### Production parser test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_parser
```

Result: passed (`Ran 8 tests in 0.005s`, `OK`).

### Readiness helper test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_readiness
```

Result: passed (`Ran 12 tests in 0.008s`, `OK`).

### No-trade safety check

```text
rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md
```

Result: completed (`exit=0`, `1938` matching lines from existing policy/docs/test references plus this PR's explicit no-trade deferrals); no credential/private/account/order/transfer/execution/adapter/config/sampling/alert/Council implementation surface was added.

### Active strategy check

```text
rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md
```

Result: completed (`exit=0`, `1334` matching lines from existing strategy/no-trade references plus this PR's `mark_orderbook_gap_hunt` planning references); active strategy remains `cross_exchange_spot_spread_v1` and this strategy remains experimental/non-active/`NO_TRADE_ONLY`.

### Final status check

```text
git status --short
```

Result: passed after commit; working tree was clean on `mark-orderbook-gap-runtime-adapter-planning-v0` and no generated artifacts were present.

## 12. What this proves

- The runtime adapter implementation scope is documented before code is added.
- The first adapter is constrained to Binance USDⓈ-M `BTCUSDT` public no-key data.
- Parser input, readiness input, and OpportunityPacket mapping have a reviewable plan.
- Live smoke is not a merge requirement and generated packet JSON must not be committed.

## 13. What this does not prove

- It does not implement runtime adapter code.
- It does not prove live endpoint behavior in this workspace.
- It does not register an adapter in config or registry.
- It does not implement sampling, alert/notification, Council auto-call, active promotion, or execution.
- It does not finalize live trading thresholds or venue notional/liquidity rules.

## 14. Changed files

- Added: `docs/adapter_plans/mark_orderbook_gap_hunt_runtime_adapter_v0.md`.
- Added: `docs/pr_handoffs/mark_orderbook_gap_hunt_runtime_adapter_planning_v0.md`.
- No `src/**` changes.
- No `configs/**` changes.
- No `tests/**` changes.
- No `tools/**` changes.
- No `data/generated_packets/**`, `data/market_samples/**`, or `data/council_sessions/**` changes.
- No Council runtime, notification/alert runtime, storage runtime, Gemini runtime, or prompt changes.

## 15. Risks

- Future adapter PR could exceed scope if it tries to add Bybit/OKX, sampling, config registration, or live smoke as a merge gate.
- Metadata caching and freshness thresholds need careful review before implementation.
- Mark price is not executable and must not be treated as an order price.
- `WATCH` could be misread as actionable unless the analysis-only boundary is preserved.

## 16. Rollback plan

- Revert `docs/adapter_plans/mark_orderbook_gap_hunt_runtime_adapter_v0.md` and `docs/pr_handoffs/mark_orderbook_gap_hunt_runtime_adapter_planning_v0.md`.
- Re-run `python -m unittest discover -s tests` if a rollback PR is opened.
- Confirm active strategy remains `cross_exchange_spot_spread_v1`.
- Confirm no generated packet/sampling/Council-session JSON is committed.

## 17. Human review required

Reviewers should inspect:

1. `docs/adapter_plans/mark_orderbook_gap_hunt_runtime_adapter_v0.md`
2. `docs/pr_handoffs/mark_orderbook_gap_hunt_runtime_adapter_planning_v0.md`

## 18. No-trade compliance

- private API: no
- API key/secret/token: no
- env credential lookup: no
- auth/private headers: no
- account/balance lookup: no
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
- runtime adapter implementation: no
- config adapter registration: no
- sampling implementation: no
- live network smoke as merge requirement: no

## 19. Next recommended step

Open `Mark-Orderbook Gap Hunt Binance Runtime Adapter v0` only after this planning PR is reviewed. Keep that follow-up public-read-only, `NO_TRADE_ONLY`, Binance/BTCUSDT scoped, and separate from config registration, sampling, alert/notification, Council auto-call, active promotion, and execution/private API work.
