# Mark-Orderbook Gap Hunt User-Local Bybit Direct Adapter Smoke Evidence v0

## 1. Purpose

Record evidence that the user directly imported and ran `BybitMarkOrderbookGapHuntAdapter` from a normal user-local network and confirmed it can fetch live public Bybit V5 linear `BTCUSDT` data and build an analysis-only OpportunityPacket.

This is an evidence-only PR. It does not modify runtime code, config, registry, tools, tests, sampling logic, alerting, Council behavior, execution/private API surfaces, or generated packet artifacts.

## 2. Baseline

- `BybitMarkOrderbookGapHuntAdapter` exists as a standalone runtime adapter class.
- The Bybit adapter is not registered in config/registry in the current implementation phase.
- The adapter uses public Bybit V5 ticker, orderbook, and instruments-info market-data endpoints.
- The adapter reuses the shared `bybit_linear` parser and shared Mark-Orderbook Gap Hunt readiness helper.
- Binance single-venue baseline already has collect, short sampling, and extended sampling evidence.
- Mark-Orderbook Gap Hunt remains experimental / non-active / `NO_TRADE_ONLY`.
- This smoke is user-local evidence and must not be presented as Codex workspace live success.

## 3. User-local smoke method

The user ran a local Python snippet that directly imported and executed:

- Class: `BybitMarkOrderbookGapHuntAdapter`
- Invocation style: direct adapter class invocation, not `collect_market_data` and not registry/config lookup
- Output artifact path: `data/generated_packets/debug_mark_orderbook_gap_bybit_direct.json`

The generated packet JSON is a local smoke artifact only and is excluded from this PR.

## 4. User-local smoke result

User-local verification summary:

```text
saved: data\generated_packets\debug_mark_orderbook_gap_bybit_direct.json
strategy_family: mark_orderbook_gap_hunt
strategy_id: mark_orderbook_gap_hunt_v0
asset: BTC
quote: USDT
observation_count: 1
candidate_count: 1
venue_id: bybit
market_symbol: BTCUSDT
mark_price: 63884.8
index_price: 63916.51
bid: 63896.2
ask: 63896.3
candidate_type: mark_orderbook_gap_observation
gross_gap_pct: 0.017844620316569824
estimated_net_gap_pct: -0.18215537968343018
readiness_status: REJECT
recommended_default_decision: REJECT
readiness_pass: False
required_missing_fields: []
diagnostics_count: 3
no_trade_only: True
execution_policy: NO_TRADE_ONLY
adapter_type: bybit_mark_orderbook_gap_hunt
has_execution_allowed: False
has_council_auto_call: False
has_alert_trigger: False
```

## 5. Result interpretation

- User-local direct Bybit adapter smoke succeeded.
- The adapter fetched live Bybit public V5 ticker, orderbook, and instruments-info data.
- The adapter created one observation and one candidate.
- `diagnostics_count=3` is expected because the adapter performs ticker, orderbook, and metadata fetch stages.
- `readiness_status=REJECT` is expected because a positive gross gap existed but estimated net gap was negative after the fee/slippage buffer.
- This is not a data collection failure.
- This is not a trade signal.
- No `execution_allowed`, `council_auto_call`, or `alert_trigger` fields were present.
- `no_trade_only=True` and `execution_policy=NO_TRADE_ONLY` were preserved.
- `adapter_type=bybit_mark_orderbook_gap_hunt` was preserved.

## 6. What this proves

- `BybitMarkOrderbookGapHuntAdapter` can fetch live public no-key Bybit V5 linear `BTCUSDT` data from a user-local normal network.
- The adapter can build an analysis-only OpportunityPacket.
- Parser/readiness integration works in live user-local direct class invocation.
- Diagnostics are produced for public fetch stages.
- The `NO_TRADE_ONLY` boundary is preserved.

## 7. What this does not prove

- It does not prove config registration.
- It does not prove registry integration.
- It does not prove `collect_market_data` execution.
- It does not prove sampling integration.
- It does not prove profitability.
- It does not prove persistent edge.
- It does not justify alert implementation.
- It does not justify Council auto-call.
- It does not justify active strategy promotion.
- It does not justify execution/private API.
- It does not prove OKX adapter behavior.
- It does not prove multi-venue composite behavior.
- It does not prove a generic/base adapter should be extracted now.

## 8. Generated artifact handling

- Generated output path was `data/generated_packets/debug_mark_orderbook_gap_bybit_direct.json`.
- It is a smoke artifact only.
- It must not be committed.
- Generated packet JSON is excluded from this PR.

## 9. Changed files

- `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_bybit_direct_adapter_smoke_v0.md`

No `src/**`, `configs/**`, `tests/**`, `tools/**`, generated data, Council, notifications, storage, or Gemini runtime/prompt files are changed.

## 10. Tests run by Codex

- `git status` — completed before/after changes.
- `git diff --name-only` — completed before commit and showed only the allowed docs-only file.
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

## 11. Risks

- This evidence reflects one user-local direct adapter run and does not cover all live Bybit edge cases.
- Bybit public endpoint responses can change or fail independently of this evidence.
- Since the adapter is not registered in config/registry, official collect/sampling paths remain unproven for Bybit.
- `REJECT` with negative estimated net gap should not be misread as a data failure or as a trade signal.

## 12. Rollback plan

Revert this docs-only PR or delete `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_bybit_direct_adapter_smoke_v0.md`. No runtime/config/test/tool/generated-data rollback is required because those files are not changed.

## 13. Human review required

Human review should first inspect:

- `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_bybit_direct_adapter_smoke_v0.md`

Review focus:

- Confirm the user-local smoke result is recorded accurately.
- Confirm the smoke is clearly described as user-local direct adapter evidence, not Codex workspace live success.
- Confirm generated packet JSON is excluded from the PR.
- Confirm the result is not framed as profitability, persistent edge, alert/Council justification, active promotion, or execution/private API justification.

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
- Bybit config adapter registration: no
- Bybit registry integration: no
- sampling implementation changes: no
- live network smoke as merge requirement: no
- OKX adapter implementation: no
- multi-venue composite implementation: no
- generic/base adapter extraction: no

## 15. Next recommended step

Open a separate `Mark-Orderbook Gap Hunt Bybit Adapter Config/Registry Planning v0` PR to plan the minimum safe config/registry scope before making the Bybit adapter executable through official `collect_market_data` paths.
