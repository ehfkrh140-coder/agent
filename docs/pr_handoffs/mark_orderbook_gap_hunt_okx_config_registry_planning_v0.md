# Mark-Orderbook Gap Hunt OKX Config/Registry Planning v0

## 1. Purpose

Document the planned OKX config/registry registration scope before connecting `OkxMarkOrderbookGapHuntAdapter` to the official `tools/collect_market_data.py` path.

This is a planning-only PR. It does not implement config/registry changes, collect-market-data wiring, sampling, alert/notification expansion, Council auto-call, active promotion, execution/private API, parser/readiness/timestamp/freshness changes, OKX index/reference semantics changes, multi-venue composite behavior, or generic/base adapter extraction.

## 2. Baseline

- `OkxMarkOrderbookGapHuntAdapter` class exists.
- Mocked OKX unit tests passed in the runtime adapter PR.
- User-local direct OKX smoke succeeded.
- Direct smoke result included:
  - `strategy_family: mark_orderbook_gap_hunt`
  - `strategy_id: mark_orderbook_gap_hunt_v0`
  - `asset: BTC`
  - `quote: USDT`
  - `observation_count: 1`
  - `candidate_count: 1`
  - `venue_id: okx`
  - `venue_name: OKX`
  - `market_symbol: BTC-USDT-SWAP`
  - `instrument_type: linear_swap`
  - `mark_price: 63622.5`
  - `index_price: None`
  - `bid: 63629.3`
  - `ask: 63629.4`
  - `gross_gap_pct: 0.01068804275217101`
  - `estimated_net_gap_pct: -0.18931195724782898`
  - `readiness_status: REJECT`
  - `recommended_default_decision: REJECT`
  - `readiness_pass: False`
  - `required_missing_fields: []`
  - `diagnostics_count: 3`
  - `no_trade_only: True`
  - `execution_policy: NO_TRADE_ONLY`
  - `adapter_type: okx_mark_orderbook_gap_hunt`
  - `has_execution_allowed: False`
  - `has_council_auto_call: False`
  - `has_alert_trigger: False`
- OKX adapter is not registered in `configs/market_data.yaml` or `src/market_data/registry.py` yet.
- OKX `collect_market_data` and sampling paths are not proven yet.
- `index_price=None` was observed and is carried as a future OKX index/reference interpretation watch item.

## 3. Proposed config entry

Document only; do not implement in this planning PR.

Proposed adapter id: `live_okx_mark_orderbook_gap_btc_usdt_swap`

Proposed config fields:

```yaml
live_okx_mark_orderbook_gap_btc_usdt_swap:
  type: okx_mark_orderbook_gap_hunt
  enabled: false
  experimental: true
  strategy_family: mark_orderbook_gap_hunt
  strategy_id: mark_orderbook_gap_hunt_v0
  base_url: https://www.okx.com
  inst_type: SWAP
  inst_id: BTC-USDT-SWAP
  asset: BTC
  quote: USDT
  orderbook_size: 5
  timeout_seconds: 10
  max_retries: 2
  user_agent: agent-council-market-data-v1
  fee_slippage_buffer_pct: "0.20"
  min_net_gap_pct: "0"
  max_data_age_ms: 10000
  require_freshness: true
  liquidity_pass: true
  size_or_notional_resolved: true
  execution_policy: NO_TRADE_ONLY
  experimental_strategy: true
  non_active_strategy: true
  no_trade_only: true
  note: "Public read-only OKX BTC-USDT-SWAP Mark-Orderbook Gap Hunt adapter. Experimental/non-active/NO_TRADE_ONLY."
```

The future config entry must remain disabled, experimental, non-active, and `NO_TRADE_ONLY`.

## 4. Registry mapping plan

Document only; do not implement in this planning PR.

- Adapter type `okx_mark_orderbook_gap_hunt` should map to `OkxMarkOrderbookGapHuntAdapter`.
- Registration must not change active strategy.
- Registration must not make sampling, alert, Council, or execution automatic.
- Registration must not create multi-venue composite behavior.
- Registration must not trigger generic/base adapter extraction.

## 5. Future collect_market_data behavior

Expected future command after config/registry registration:

```bash
python tools/collect_market_data.py --adapter live_okx_mark_orderbook_gap_btc_usdt_swap --output data/generated_packets/live_okx_mark_orderbook_gap_btc_usdt_swap.json
```

Expected successful packet:

- `strategy_family: mark_orderbook_gap_hunt`
- `strategy_id: mark_orderbook_gap_hunt_v0`
- `asset: BTC`
- `quote: USDT`
- `observations: 1`
- `candidates: 1`
- `venue_id: okx`
- `market_symbol: BTC-USDT-SWAP`
- `execution_policy: NO_TRADE_ONLY`
- `no_trade_only: true`
- no `execution_allowed`
- no `council_auto_call`
- no `alert_trigger`

Generated packet JSON is a smoke artifact only and must not be committed.

## 6. User-local smoke plan

After a future registration PR, user-local normal-network smoke is required because Codex workspace live network may fail due to tunnel or 403 restrictions.

Future user-local smoke should verify:

- command completes through `tools/collect_market_data.py`;
- generated packet JSON is inspected and then deleted;
- generated packet JSON is not committed;
- `readiness_status` may be `NEED_DATA`, `REJECT`, or `WATCH`;
- `REJECT` is not failure;
- `WATCH` remains analysis-only;
- no `execution_allowed`, `council_auto_call`, or `alert_trigger` fields appear;
- `index_price` may be `None` unless future OKX index/reference policy changes.

If `index_price=None` repeats, document it as a watch item, not a blocker unless `required_missing_fields` or readiness policy changes.

## 7. OKX index_price / reference watch item

The user-local direct OKX smoke observed `index_price=None`.

Carry-forward interpretation:

- It was not a blocker because `required_missing_fields=[]` and packet creation succeeded.
- It does not prove full OKX index/reference semantics.
- This planning PR does not change OKX index/reference interpretation.
- This planning PR does not change parser/readiness logic.
- This planning PR does not change timestamp/freshness policy.
- Future OKX index/reference interpretation should compare Binance, Bybit, and OKX before changing shared packet semantics.

## 8. Future registration merge gate

A future `Mark-Orderbook Gap Hunt OKX Config/Registry v0` PR should include:

- unit tests;
- `list-adapters` check;
- `build_adapter` instantiation check mapping to `OkxMarkOrderbookGapHuntAdapter`;
- mocked/no-network `collect_market_data` path check if possible;
- no-trade safety check;
- active strategy check confirming `cross_exchange_spot_spread_v1` remains active;
- generated artifact cleanup confirmation;
- handoff evidence;
- human review.

## 9. Future deferrals

- OKX registration implementation is next separate PR.
- OKX user-local collect smoke is separate evidence.
- OKX sampling is later.
- Multi-venue composite is later.
- Generic/base adapter extraction is later after Binance/Bybit/OKX comparison.
- Timestamp/data_age policy is later after venue comparison.
- OKX index/reference interpretation is later.
- Alert/notification is later.
- Council auto-call is later.
- Active promotion is later.
- Execution/private API is much later via common execution/risk engine.

## 10. Tests run

Codex checks for this planning-only PR:

- `git status` — checked repository state before changes.
- `git diff --name-only` — checked changed-file scope before staging.
- `python -m unittest discover -s tests` — passed (`Ran 328 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_okx_adapter` — passed (`Ran 11 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_sampling` — passed (`Ran 6 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_adapter` — passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter` — passed (`Ran 9 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_parser` — passed (`Ran 8 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_readiness` — passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_sampling` — passed (`Ran 5 tests`, `OK`).
- `python tools/collect_market_data.py --list-adapters` — passed; adapter listing still works and this planning PR did not register `live_okx_mark_orderbook_gap_btc_usdt_swap`.
- `rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md` — completed as a no-trade/credential scan across existing repository references.
- `rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md` — completed as an active-strategy/no-trade scan across existing repository references.
- `git status --short` — checked final working tree state.
- `git diff --name-only HEAD~1..HEAD` — recorded after commit in the final response.

## 11. What this proves

- OKX config/registry registration scope is documented.
- Proposed OKX config fields preserve disabled/experimental/non-active/`NO_TRADE_ONLY` boundaries.
- Proposed registry mapping is limited to `okx_mark_orderbook_gap_hunt` -> `OkxMarkOrderbookGapHuntAdapter`.
- Future collect-market-data expectations are documented.
- Future user-local smoke and generated artifact handling are documented.
- OKX `index_price=None` watch item is carried forward without policy changes.

## 12. What this does not prove

- It does not implement OKX config registration.
- It does not implement OKX registry integration.
- It does not prove `collect_market_data` execution.
- It does not prove sampling integration.
- It does not prove live OKX endpoint reliability through the official CLI path.
- It does not prove profitability or persistent edge.
- It does not justify alert/Council auto-call/active promotion/execution/private API.
- It does not implement multi-venue composite.
- It does not implement generic/base adapter extraction.
- It does not resolve timestamp freshness / clock-skew policy.
- It does not resolve OKX index/reference semantics.

## 13. Changed files

- `docs/adapter_plans/mark_orderbook_gap_hunt_okx_config_registry_v0.md`
- `docs/pr_handoffs/mark_orderbook_gap_hunt_okx_config_registry_planning_v0.md`

No `src/`, `configs/`, `tests/`, `tools/`, generated data, Council, notification, storage, Gemini runtime/prompt, registry, sampling, parser/readiness/timestamp/freshness, multi-venue composite, or generic/base adapter files are changed.

## 14. Risks

- Future registration may accidentally widen scope if not constrained by this plan.
- OKX `index_price=None` remains unresolved and should not be silently fixed in config/registry work.
- Live OKX `collect_market_data` behavior remains unproven until after registration.
- Human review is still required before any config/registry implementation.

## 15. Rollback plan

- Revert this docs-only planning PR.
- Remove `docs/adapter_plans/mark_orderbook_gap_hunt_okx_config_registry_v0.md`.
- Remove `docs/pr_handoffs/mark_orderbook_gap_hunt_okx_config_registry_planning_v0.md`.
- No code/config/test/tool/generated-data rollback is required because this PR changes only docs.
- Re-run `python -m unittest discover -s tests` if rollback verification is desired.

## 16. Human review required

Human review should first inspect:

1. `docs/adapter_plans/mark_orderbook_gap_hunt_okx_config_registry_v0.md` to confirm the proposed config/registry scope is safe and narrow.
2. This handoff file to confirm no-trade compliance, merge gate, future deferrals, generated artifact handling, and OKX `index_price=None` watch carry-forward.

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
- OKX config adapter registration implementation: no
- OKX registry integration implementation: no
- sampling implementation: no
- live network smoke as merge requirement: no
- multi-venue composite implementation: no
- generic/base adapter extraction: no
- parser/readiness/timestamp/freshness logic changes: no
- data_age_ms clamp or reinterpretation: no
- OKX index/reference semantics change: no

## 18. Next recommended step

Open a separate `Mark-Orderbook Gap Hunt OKX Config/Registry v0` implementation PR limited to the disabled/experimental/`NO_TRADE_ONLY` config entry, registry mapping, and mocked/list-adapter/build-adapter checks. After registration, record user-local OKX `collect_market_data` evidence in a separate docs-only PR and keep generated packet JSON out of git.
