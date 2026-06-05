# Mark-Orderbook Gap Hunt User-Local OKX Direct Adapter Smoke Evidence v0

## 1. Purpose

Record evidence that a human user ran `OkxMarkOrderbookGapHuntAdapter` directly from a normal local network and successfully created an analysis-only `OpportunityPacket` from live public OKX BTC-USDT-SWAP data.

This is a docs-only evidence PR. The smoke was run by the user, not by Codex in the workspace. This PR does not modify runtime code, config, registry, tools, tests, sampling logic, parser/readiness/timestamp/freshness logic, alert/notification behavior, Council behavior, active strategy state, execution/private API surfaces, or generated artifacts.

## 2. Baseline

- `OkxMarkOrderbookGapHuntAdapter` exists as a standalone public-read-only runtime adapter class.
- The OKX adapter uses public OKX mark-price, books, and instruments endpoints for `BTC-USDT-SWAP`.
- The adapter reuses `parse_mark_orderbook_gap_snapshot` with `parser_mode="okx_swap"`.
- The adapter reuses `evaluate_mark_orderbook_gap_readiness`.
- The adapter is not registered in config or registry yet.
- OKX `collect_market_data` execution is not proven yet.
- OKX sampling integration is not proven yet.
- Binance and Bybit already have broader collect/sampling evidence; OKX is still at direct adapter smoke evidence stage.
- The active strategy remains `cross_exchange_spot_spread_v1`; `mark_orderbook_gap_hunt_v0` remains experimental/non-active/analysis-only.

## 3. User-local smoke method

The user ran a direct Python snippet that imported and executed:

- class: `OkxMarkOrderbookGapHuntAdapter`
- output artifact: `data/generated_packets/debug_mark_orderbook_gap_okx_direct.json`

The generated output is a smoke artifact only and must not be committed.

## 4. User-local smoke result

User-local result summary:

- `saved: data\generated_packets\debug_mark_orderbook_gap_okx_direct.json`
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
- `candidate_type: mark_orderbook_gap_observation`
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

## 5. Result interpretation

- User-local direct OKX adapter smoke succeeded.
- The adapter fetched live OKX public mark-price, books, and instruments data.
- The adapter created one observation and one candidate.
- `diagnostics_count=3` is expected: mark-price, books, and instruments fetch.
- `readiness_status=REJECT` is expected because gross gap existed but estimated net gap was negative after fee/slippage buffer.
- This is not a data collection failure.
- This is not a trade signal.
- No `execution_allowed`, `council_auto_call`, or `alert_trigger` fields were present.
- `no_trade_only` and `NO_TRADE_ONLY` were preserved.
- `adapter_type=okx_mark_orderbook_gap_hunt` was preserved.
- `index_price=None` was observed. It is not a blocker in this smoke because `required_missing_fields=[]` and packet creation succeeded.

## 6. OKX index_price / reference watch item

Observed OKX index/reference field:

- `index_price: None`

Interpretation:

- This is not treated as a blocker for this direct smoke because `required_missing_fields=[]`, readiness completed, and packet creation succeeded.
- The OKX runtime adapter/parser path currently proves mark-vs-orderbook observation generation, not full OKX index/reference semantics.
- Record `index_price=None` as a future OKX index/reference interpretation watch item.
- Do not change code in this PR.
- Do not change parser/readiness/timestamp/freshness logic in this PR.
- Do not add OKX ticker/index endpoint interpretation in this PR.
- Future follow-up may evaluate whether OKX index/reference fields should be added or normalized consistently across Binance, Bybit, and OKX.

## 7. What this proves

- `OkxMarkOrderbookGapHuntAdapter` can fetch live public no-key OKX BTC-USDT-SWAP data from a user-local normal network.
- The adapter can build an analysis-only `OpportunityPacket`.
- Parser/readiness integration works in live user-local direct class invocation.
- Diagnostics are produced for public fetch stages.
- `NO_TRADE_ONLY` boundary is preserved.

## 8. What this does not prove

- It does not prove config registration.
- It does not prove registry integration.
- It does not prove `collect_market_data` execution.
- It does not prove sampling integration.
- It does not prove profitability.
- It does not prove persistent edge.
- It does not justify alert/Council auto-call/active promotion/execution/private API.
- It does not prove multi-venue composite.
- It does not resolve timestamp freshness / clock-skew policy.
- It does not resolve OKX index_price/reference semantics.

## 9. Generated artifact handling

- Generated output path was `data/generated_packets/debug_mark_orderbook_gap_okx_direct.json`.
- It is a smoke artifact only.
- It must not be committed.
- Generated packet JSON is excluded from this PR.
- No generated packet JSON or generated sampling JSON is committed by this docs-only evidence PR.

## 10. Changed files

- `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_okx_direct_adapter_smoke_v0.md`

No `src/`, `configs/`, `tests/`, `tools/`, generated data, Council, notification, storage, Gemini runtime/prompt, registry, sampling, parser/readiness/timestamp/freshness, multi-venue composite, or generic/base adapter files are changed.

## 11. Tests run by Codex

Codex checks for this docs-only evidence PR:

- `git status` — checked repository status before changes.
- `git diff --name-only` — checked changed-file scope.
- `python -m unittest discover -s tests` — passed (`Ran 328 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_okx_adapter` — passed (`Ran 11 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_sampling` — passed (`Ran 6 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_adapter` — passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter` — passed (`Ran 9 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_parser` — passed (`Ran 8 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_readiness` — passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_sampling` — passed (`Ran 5 tests`, `OK`).
- `python tools/collect_market_data.py --list-adapters` — passed; this PR did not register OKX Mark-Orderbook Gap adapter.
- `rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md` — completed as a no-trade/credential scan across existing repository references.
- `rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md` — completed as an active-strategy/no-trade scan across existing repository references.
- `git status --short` — checked final working tree state.
- `git diff --name-only HEAD~1..HEAD` — recorded after commit in the final response.

## 12. Risks

- This evidence is user-local and live-market-time-specific; future public OKX endpoint behavior may differ.
- OKX config/registry, official collect path, and sampling path remain unproven.
- `index_price=None` remains an OKX index/reference interpretation watch item.
- This docs-only PR does not prove profitability, persistent edge, or execution readiness.
- Human review is still required before any future config/registry registration, timestamp/index/reference policy, sampling, alert, Council, active promotion, multi-venue composite, or execution work.

## 13. Rollback plan

- Revert this docs-only PR.
- Remove `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_okx_direct_adapter_smoke_v0.md`.
- No code/config/test/tool/generated-data rollback is required because this PR changes only one handoff document.
- Re-run `python -m unittest discover -s tests` if rollback verification is desired.

## 14. Human review required

Human review should first inspect this handoff file to verify:

1. the smoke is clearly attributed to a user-local normal-network run, not Codex workspace live success;
2. generated packet JSON is excluded from the PR;
3. `index_price=None` is recorded as a future OKX index/reference watch item, not treated as a blocker or silently fixed;
4. `REJECT` is interpreted as no-edge behavior rather than API failure;
5. no-trade compliance remains explicit.

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
- OKX config adapter registration: no
- OKX registry integration: no
- sampling implementation changes: no
- parser/readiness/timestamp/freshness logic changes: no
- data_age_ms clamp or reinterpretation: no
- live network smoke as merge requirement: no
- multi-venue composite implementation: no
- generic/base adapter extraction: no

## 16. Next recommended step

Open a separate `Mark-Orderbook Gap Hunt OKX Config/Registry Planning v0` PR before registering the OKX adapter. Carry the `index_price=None` watch item forward as future OKX index/reference interpretation input, and keep generated packet JSON out of git.
