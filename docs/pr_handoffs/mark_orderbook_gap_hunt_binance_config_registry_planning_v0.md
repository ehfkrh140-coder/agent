# Mark-Orderbook Gap Hunt Binance Adapter Config/Registry Planning v0 Handoff

## 1. Purpose

Document the planned config and registry registration scope for `BinanceMarkOrderbookGapHuntAdapter` before making it runnable through `tools/collect_market_data.py`.

This PR is planning-only. It does not implement config registration, registry integration, tool/CLI wiring, sampling, alert/notification, Council auto-call, active strategy promotion, execution/private API, generated packet JSON, generated sampling JSON, or generated Council-session JSON.

## 2. Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains experimental / non-active / `NO_TRADE_ONLY`.
- `BinanceMarkOrderbookGapHuntAdapter` exists as a standalone Binance USDⓈ-M `BTCUSDT` adapter class.
- User-local direct adapter smoke succeeded and produced one observation and one candidate.
- The observed direct-smoke readiness status was `REJECT`, which is a normal no-edge classification after fee/slippage buffer adjustment.
- The direct smoke preserved `no_trade_only: True`, `execution_policy: NO_TRADE_ONLY`, and no `execution_allowed`, `council_auto_call`, or `alert_trigger` fields.
- The adapter is not registered in `configs/market_data.yaml`, is not mapped in `src/market_data/registry.py`, and is not runnable through `tools/collect_market_data.py` yet.

## 3. Proposed config entry

Future registration PR may add this adapter entry. This PR does not modify `configs/market_data.yaml`.

```yaml
adapters:
  live_binance_mark_orderbook_gap_btcusdt:
    type: binance_mark_orderbook_gap_hunt
    enabled: false
    strategy_family: mark_orderbook_gap_hunt
    strategy_id: mark_orderbook_gap_hunt_v0
    base_url: https://fapi.binance.com
    symbol: BTCUSDT
    asset: BTC
    quote: USDT
    orderbook_limit: 5
    timeout_seconds: 10
    max_retries: 2
    fee_slippage_buffer_pct: 0.20
    min_net_gap_pct: 0
    max_data_age_ms: 10000
    require_freshness: true
    liquidity_pass: true
    size_or_notional_resolved: true
    execution_policy: NO_TRADE_ONLY
    experimental_strategy: true
    non_active_strategy: true
    no_trade_only: true
```

Planning constraints:

- Keep `enabled: false` or experimental-only until review.
- Thresholds are analysis/readiness inputs only.
- No credentials, private/auth headers, account state, position state, balances, orders, transfers, fiat/bank data, or private payloads belong in config.

## 4. Registry mapping plan

Future registration PR may map adapter type `binance_mark_orderbook_gap_hunt` to `BinanceMarkOrderbookGapHuntAdapter` in `src/market_data/registry.py`.

Mapping constraints:

- Must not change active strategy.
- Must not automatically run sampling.
- Must not trigger alert/notification behavior.
- Must not trigger Council auto-call.
- Must not add execution/private API behavior.
- Must preserve experimental / non-active / `NO_TRADE_ONLY` metadata.

## 5. Future collect_market_data behavior

After future config/registry registration, expected manual command:

```text
python tools/collect_market_data.py --adapter live_binance_mark_orderbook_gap_btcusdt --output data/generated_packets/live_binance_mark_orderbook_gap_btcusdt.json
```

Expected successful packet:

- `strategy_family`: `mark_orderbook_gap_hunt`
- `strategy_id`: `mark_orderbook_gap_hunt_v0`
- `asset`: `BTC`
- `quote`: `USDT`
- `observations`: `1`
- `candidates`: `1`
- `execution_policy`: `NO_TRADE_ONLY`
- `no_trade_only`: `true`
- no `execution_allowed`
- no `council_auto_call`
- no `alert_trigger`

Generated packet JSON from the command is a smoke artifact and must not be committed.

## 6. User-local smoke plan

- Codex workspace live network may fail due to network tunnel `403`; this should not block a docs/planning PR.
- User-local normal-network smoke is required after future registration.
- Generated packet JSON must be deleted after smoke and must not be committed.
- `readiness_status` may be `NEED_DATA`, `REJECT`, or `WATCH`.
- `REJECT` is not failure; it can be a normal no-edge classification.
- `WATCH` is analysis-only and does not mean execution, Council auto-call, or alert trigger.

## 7. Future registration merge gate

Future registration PR should include:

- unit tests for registry construction;
- `list_adapters` or equivalent adapter listing check;
- collect-market-data mocked/replay/direct smoke as applicable;
- user-local live smoke evidence after registration;
- no-trade safety scan;
- active strategy scan;
- generated artifact cleanup evidence;
- task-specific handoff evidence;
- explicit human review.

## 8. Future deferrals

These are deferred to later separate PRs:

- sampling integration;
- alert/notification;
- Council auto-call;
- Bybit adapter;
- OKX adapter;
- multi-venue composite;
- active strategy promotion;
- execution/private API through a future common execution/risk engine with credential isolation, dry-run/paper trading, kill switch, risk limits, order-state machine, audit logs, rollback plan, and explicit human review.

## 9. Tests run

### Git status

```text
git status
```

Result: passed before staging; branch `mark-orderbook-gap-binance-config-registry-planning-v0` had only the two allowed planning documentation files untracked.

### Git diff name check

```text
git diff --name-only
```

Result: passed before staging; no tracked-file diff was present because the allowed planning files were new/untracked before staging.

### Commit diff name check

```text
git diff --name-only HEAD~1..HEAD
```

Result: passed after commit; output contained only `docs/adapter_plans/mark_orderbook_gap_hunt_binance_config_registry_v0.md` and `docs/pr_handoffs/mark_orderbook_gap_hunt_binance_config_registry_planning_v0.md`.

### Full unit test

```text
python -m unittest discover -s tests
```

Result: passed (`Ran 293 tests in 9.182s`, `OK`).

### Binance adapter test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter
```

Result: passed (`Ran 8 tests in 0.007s`, `OK`).

### Production parser test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_parser
```

Result: passed (`Ran 8 tests in 0.004s`, `OK`).

### Readiness helper test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_readiness
```

Result: passed (`Ran 12 tests in 0.005s`, `OK`).

### No-trade safety check

```text
rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md
```

Result: completed (`exit=0`, `2155` matching lines from existing policy/docs/test references plus this planning file's explicit no-trade deferrals); no code/config/registry/test/tool/generated-data/private/execution surface was added.

### Active strategy check

```text
rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md
```

Result: completed (`exit=0`, `1500` matching lines from existing strategy/no-trade references plus this planning file's `mark_orderbook_gap_hunt` references); active strategy remains `cross_exchange_spot_spread_v1` and this plan keeps `mark_orderbook_gap_hunt_v0` experimental/non-active/`NO_TRADE_ONLY`.

### Final status check

```text
git status --short
```

Result: passed after commit; working tree was clean on `mark-orderbook-gap-binance-config-registry-planning-v0` and no generated artifacts were present.

## 10. What this proves

- The future config entry scope is documented before implementation.
- The future registry mapping scope is documented before implementation.
- Future collect-market-data behavior and generated artifact handling are reviewable before code changes.
- Future user-local smoke and merge gates are explicit.
- No-trade boundaries remain part of the registration plan.

## 11. What this does not prove

- It does not implement config registration.
- It does not implement registry integration.
- It does not make `tools/collect_market_data.py` runnable for this adapter.
- It does not implement sampling.
- It does not run a new live network smoke.
- It does not prove profitability.
- It does not justify alert expansion, Council auto-call, active promotion, or execution/private API.

## 12. Changed files

- Added: `docs/adapter_plans/mark_orderbook_gap_hunt_binance_config_registry_v0.md`.
- Added: `docs/pr_handoffs/mark_orderbook_gap_hunt_binance_config_registry_planning_v0.md`.
- No `src/**` changes.
- No `configs/**` changes.
- No `tests/**` changes.
- No `tools/**` changes.
- No `data/generated_packets/**`, `data/market_samples/**`, or `data/council_sessions/**` changes.
- No Council runtime, notification/alert runtime, storage runtime, Gemini runtime, or prompt changes.

## 13. Risks

- Future registration could accidentally make the experimental adapter appear active if `enabled` and strategy-state wording are not reviewed.
- Generated packet JSON could be accidentally committed after future smoke if cleanup is not enforced.
- `WATCH` could be misread as actionable; it must remain analysis-only.
- `REJECT` could be misread as a failure; it can be normal no-edge behavior.

## 14. Rollback plan

- Revert `docs/adapter_plans/mark_orderbook_gap_hunt_binance_config_registry_v0.md`.
- Revert `docs/pr_handoffs/mark_orderbook_gap_hunt_binance_config_registry_planning_v0.md`.
- Re-run `python -m unittest discover -s tests` if a rollback PR is opened.
- Confirm no config/registry/tool/test/source/generated-data changes are present.

## 15. Human review required

Reviewers should inspect:

1. `docs/adapter_plans/mark_orderbook_gap_hunt_binance_config_registry_v0.md`
2. `docs/pr_handoffs/mark_orderbook_gap_hunt_binance_config_registry_planning_v0.md`

Review focus:

- proposed config fields;
- registry mapping constraints;
- future collect-market-data behavior;
- user-local smoke plan;
- generated artifact cleanup;
- no-trade boundaries;
- future deferrals.

## 16. No-trade compliance

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
- config adapter registration implementation: no
- registry integration implementation: no
- sampling implementation: no
- live network smoke as merge requirement: no

## 17. Next recommended step

Open `Mark-Orderbook Gap Hunt Binance Adapter Config/Registry v0` after human review. Keep that PR limited to config entry, registry mapping, unit/list-adapter checks, generated-artifact cleanup evidence, and `NO_TRADE_ONLY` boundaries.
