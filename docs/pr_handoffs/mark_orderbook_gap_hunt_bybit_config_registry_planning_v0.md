# Mark-Orderbook Gap Hunt Bybit Adapter Config/Registry Planning v0

## 1. Purpose

Document the planned config/registry registration scope for `BybitMarkOrderbookGapHuntAdapter` before making it executable through official `collect_market_data` paths.

This is a planning-only PR. It does not modify config, registry, tools, source code, tests, sampling logic, generated artifacts, alerting, Council behavior, active strategy settings, execution, private API, OKX behavior, multi-venue composite behavior, or generic/base adapter extraction.

## 2. Baseline

- `BybitMarkOrderbookGapHuntAdapter` exists as a standalone adapter class.
- Mocked unit tests for the Bybit adapter pass.
- User-local direct Bybit adapter smoke succeeded.
- Direct smoke produced `strategy_family=mark_orderbook_gap_hunt`, `strategy_id=mark_orderbook_gap_hunt_v0`, one observation, one candidate, `venue_id=bybit`, `market_symbol=BTCUSDT`, `readiness_status=REJECT`, `no_trade_only=True`, `execution_policy=NO_TRADE_ONLY`, and `adapter_type=bybit_mark_orderbook_gap_hunt`.
- Direct smoke had no `execution_allowed`, no `council_auto_call`, and no `alert_trigger` fields.
- Bybit adapter is not yet registered in `configs/market_data.yaml` or `src/market_data/registry.py`.
- Bybit official `collect_market_data` and sampling paths are not proven yet.
- Current active strategy remains `cross_exchange_spot_spread_v1`.

## 3. Proposed config entry

Document only; do not implement in this planning PR.

Proposed adapter id: `live_bybit_mark_orderbook_gap_btcusdt`

Proposed fields:

```yaml
live_bybit_mark_orderbook_gap_btcusdt:
  type: bybit_mark_orderbook_gap_hunt
  enabled: false
  experimental: true
  strategy_family: mark_orderbook_gap_hunt
  strategy_id: mark_orderbook_gap_hunt_v0
  base_url: https://api.bybit.com
  category: linear
  symbol: BTCUSDT
  asset: BTC
  quote: USDT
  orderbook_limit: 5
  timeout_seconds: 10
  max_retries: 2
  user_agent: agent-council-market-data-v1
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
  note: "Public read-only Bybit V5 linear BTCUSDT Mark-Orderbook Gap Hunt adapter. Experimental/non-active/NO_TRADE_ONLY."
```

Config constraints:

- Keep the adapter disabled/experimental for initial registration.
- Keep thresholds analysis-only and reviewable.
- Do not add credentials, private endpoints, account/balance/position fields, order/cancel fields, transfer fields, alert fields, Council fields, or execution fields.
- Do not register OKX or composite behavior in the same change.

## 4. Registry mapping plan

Document only; do not implement in this planning PR.

Future registry mapping:

- Adapter type `bybit_mark_orderbook_gap_hunt` should map to `BybitMarkOrderbookGapHuntAdapter`.
- Registration must not change active strategy.
- Registration must not make sampling automatic.
- Registration must not enable alert/notification behavior.
- Registration must not enable Council auto-call.
- Registration must not enable execution/private API behavior.
- Registration must not register OKX behavior.
- Registration must not create multi-venue composite behavior.
- Registration must not extract a generic/base adapter.

## 5. Future collect_market_data behavior

Document only; do not implement in this planning PR.

Expected future command:

```bash
python tools/collect_market_data.py --adapter live_bybit_mark_orderbook_gap_btcusdt --output data/generated_packets/live_bybit_mark_orderbook_gap_btcusdt.json
```

Expected successful packet:

- `strategy_family: mark_orderbook_gap_hunt`
- `strategy_id: mark_orderbook_gap_hunt_v0`
- `asset: BTC`
- `quote: USDT`
- `observations: 1`
- `candidates: 1`
- `venue_id: bybit`
- `execution_policy: NO_TRADE_ONLY`
- `no_trade_only: true`
- no `execution_allowed`
- no `council_auto_call`
- no `alert_trigger`

Generated packet JSON must remain a local smoke artifact and must not be committed.

## 6. User-local smoke plan

Future registration PR should not require Codex workspace live network success because this workspace may fail with tunnel/public endpoint restrictions such as 403.

After registration, user-local normal-network smoke should be recorded as separate evidence. It should verify:

- The future `collect_market_data` command completes with the registered Bybit adapter id.
- Public Bybit ticker/orderbook/instruments-info fetch stages produce safe diagnostics.
- Packet contains one observation and one candidate when data is complete.
- `readiness_status` may be `NEED_DATA`, `REJECT`, or `WATCH`.
- `REJECT` is not failure.
- `WATCH` is analysis-only.
- `NO_TRADE_ONLY` is preserved.
- Generated packet JSON is deleted after inspection and not committed.

## 7. Future registration merge gate

A future registration implementation PR should include:

- Unit tests for the config entry.
- Unit tests for registry mapping.
- `list-adapters` check showing `live_bybit_mark_orderbook_gap_btcusdt`.
- `build_adapter` instantiation check mapping to `BybitMarkOrderbookGapHuntAdapter`.
- Mocked/no-network `collect_market_data` smoke path check if an existing seam supports it.
- No-trade safety check.
- Active strategy check confirming `cross_exchange_spot_spread_v1` remains active.
- Generated artifact cleanup confirmation.
- Handoff evidence.
- Human review.

## 8. Future deferrals

- Bybit registration implementation is the next separate PR.
- Bybit user-local collect smoke is separate evidence after registration.
- Bybit sampling is later.
- OKX adapter is later.
- Multi-venue composite is later.
- Generic/base adapter extraction is later after Binance/Bybit/OKX comparison.
- Alert/notification is later.
- Council auto-call is later.
- Active promotion is later.
- Execution/private API is much later via common execution/risk engine.

## 9. Tests run

- `git status` — completed before/after changes.
- `git diff --name-only` — completed before commit and showed only the two allowed docs files.
- `python -m unittest discover -s tests` — passed; ran 309 tests.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_adapter` — passed; ran 10 tests.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter` — passed; ran 9 tests.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_parser` — passed; ran 8 tests.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_readiness` — passed; ran 12 tests.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_sampling` — passed; ran 5 tests.
- `python tools/collect_market_data.py --list-adapters` — passed; existing adapter list command completed.
- `rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md` — completed; matches were expected docs/tests/policy references and no private/runtime credential surface was added.
- `rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md` — completed; matches were expected strategy/no-trade references.
- `git status --short` — completed before commit.

## 10. What this proves

- Bybit config/registry registration scope is documented before implementation.
- The proposed config entry preserves disabled/experimental/`NO_TRADE_ONLY` boundaries.
- The planned registry mapping is limited to `bybit_mark_orderbook_gap_hunt` -> `BybitMarkOrderbookGapHuntAdapter`.
- Future `collect_market_data` expected behavior and user-local smoke plan are documented.
- Future registration merge gates and deferrals are explicit.

## 11. What this does not prove

- It does not prove Bybit config registration.
- It does not prove Bybit registry integration.
- It does not prove `collect_market_data` execution.
- It does not prove Bybit sampling integration.
- It does not prove live Bybit public endpoint reachability from Codex workspace.
- It does not prove profitability.
- It does not prove persistent edge.
- It does not justify alert/notification implementation.
- It does not justify Council auto-call.
- It does not justify active strategy promotion.
- It does not justify execution/private API.
- It does not prove OKX adapter behavior.
- It does not prove multi-venue composite behavior.
- It does not prove generic/base adapter extraction should happen now.

## 12. Changed files

- `docs/adapter_plans/mark_orderbook_gap_hunt_bybit_config_registry_v0.md`
- `docs/pr_handoffs/mark_orderbook_gap_hunt_bybit_config_registry_planning_v0.md`

No `src/**`, `configs/**`, `tests/**`, `tools/**`, generated data, Council, notifications, storage, or Gemini runtime/prompt files are changed.

## 13. Risks

- Future config/registry implementation may expose mismatches between planned fields and current registry/config conventions.
- Future `collect_market_data` behavior still requires implementation and user-local evidence.
- Threshold values remain analysis-only placeholders and require review before any future promotion discussion.
- Bybit direct adapter smoke is encouraging but does not replace official collect-path smoke after registration.

## 14. Rollback plan

Revert this docs-only PR or delete the two added planning/handoff documents. No runtime/config/test/tool/generated-data rollback is required because those files are not changed.

## 15. Human review required

Human review should first inspect:

- `docs/adapter_plans/mark_orderbook_gap_hunt_bybit_config_registry_v0.md`
- `docs/pr_handoffs/mark_orderbook_gap_hunt_bybit_config_registry_planning_v0.md`

Review focus:

- Confirm the proposed config entry is disabled/experimental/`NO_TRADE_ONLY`.
- Confirm registry mapping scope does not change active strategy or enable sampling/alert/Council/execution.
- Confirm future collect smoke and generated artifact handling are clear.
- Confirm next PR should be `Mark-Orderbook Gap Hunt Bybit Adapter Config/Registry v0`.

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
- Bybit config adapter registration implementation: no
- Bybit registry integration implementation: no
- sampling implementation: no
- live network smoke as merge requirement: no
- OKX adapter implementation: no
- multi-venue composite implementation: no
- generic/base adapter extraction: no

## 17. Next recommended step

Open a separate `Mark-Orderbook Gap Hunt Bybit Adapter Config/Registry v0` implementation PR that adds only the disabled/experimental Bybit config entry, registry mapping, minimal tests, list-adapters/build-adapter checks, and no-trade evidence.
