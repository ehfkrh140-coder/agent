# Mark-Orderbook Gap Hunt User-Local OKX collect_market_data Smoke Evidence v0

## 1. Purpose

Record user-local normal-network evidence that the registered OKX Mark-Orderbook Gap Hunt adapter id, `live_okx_mark_orderbook_gap_btc_usdt_swap`, can run through the official `tools/collect_market_data.py` path and produce an analysis-only `OpportunityPacket` from live OKX public data.

This is an evidence-only docs PR. The smoke was run by the user locally, not by Codex workspace live networking. This PR does not change runtime code, config, registry, tools, tests, sampling logic, parser/readiness/timestamp/freshness logic, OKX index/reference semantics, adapter metadata wording, alert/notification behavior, Council behavior, or execution/private API behavior.

## 2. Baseline

- `OkxMarkOrderbookGapHuntAdapter` class exists.
- Mocked OKX adapter unit tests passed in the runtime/config-registration PRs.
- User-local direct OKX adapter smoke succeeded before official collect-path evidence.
- OKX config/registry registration is complete for `live_okx_mark_orderbook_gap_btc_usdt_swap`.
- User-local official `collect_market_data` OKX smoke succeeded.
- Generated packet JSON is a smoke artifact and is excluded from this PR.
- `NO_TRADE_ONLY` remains required for this stage.

## 3. User-local collect command

The user ran this command from a normal local network:

```bash
python tools/collect_market_data.py --adapter live_okx_mark_orderbook_gap_btc_usdt_swap --output data/generated_packets/live_okx_mark_orderbook_gap_btc_usdt_swap.json
```

## 4. User-local collect result

Observed result summary:

- `schema_version: opportunity_packet_v0`
- `adapter_id: live_okx_mark_orderbook_gap_btc_usdt_swap`
- `adapter_type: okx_mark_orderbook_gap_hunt`
- `venue_id: okx`
- `venue_name: OKX`
- `instType: SWAP`
- `instId: BTC-USDT-SWAP`
- `strategy_family: mark_orderbook_gap_hunt`
- `strategy_id: mark_orderbook_gap_hunt_v0`
- `asset: BTC`
- `quote: USDT`
- `signal_type: mark_orderbook_gap_hunt`
- `observations: 1`
- `candidates: 1`
- `market_symbol: BTC-USDT-SWAP`
- `instrument_type: linear_swap`
- `mark_price: 63743.0`
- `index_price: null`
- `bid: 63739.7`
- `ask: 63739.8`
- `bid_size: 66.94`
- `ask_size: 99.34`
- `candidate_type: mark_orderbook_gap_observation`
- `gross_gap_pct: 0.0050201590762907295`
- `estimated_net_gap_pct: -0.19497984092370926`
- `readiness_status: REJECT`
- `recommended_default_decision: REJECT`
- `readiness_pass: false`
- `required_missing_fields: []`
- `parser_mode: okx_swap`
- `parser_normalized_status: OK`
- `comparability_pass: true`
- `freshness_pass: true`
- `diagnostics_count: 3`
- mark-price endpoint: `http_status: 200`, OKX `code: "0"`
- books endpoint: `http_status: 200`, OKX `code: "0"`
- instruments endpoint: `http_status: 200`, OKX `code: "0"`
- `data_age_ms: approximately -7577.9 ms`
- `no_trade_only: true`
- `execution_policy: NO_TRADE_ONLY`
- `has_execution_allowed: false`
- `has_council_auto_call: false`
- `has_alert_trigger: false`

## 5. Result interpretation

- User-local `collect_market_data` OKX smoke succeeded.
- The registered adapter id `live_okx_mark_orderbook_gap_btc_usdt_swap` can be executed through the official `tools/collect_market_data.py` path.
- The adapter fetched live OKX public no-key mark-price, books, and instruments data.
- The official collect path generated an `OpportunityPacket` with one observation and one candidate.
- `readiness_status=REJECT` is expected no-edge behavior because gross gap existed but estimated net gap was negative after fee/slippage buffer.
- This is not a data collection failure.
- This is not a trade signal.
- No `execution_allowed`, `council_auto_call`, or `alert_trigger` fields were present.
- `no_trade_only=true` and `execution_policy=NO_TRADE_ONLY` were preserved.

## 6. OKX index_price / reference watch item

- `index_price` was `null` in the official collect output.
- This is not a blocker in this smoke because `required_missing_fields=[]`, `parser_normalized_status=OK`, readiness completed, and packet creation succeeded.
- This PR does not change OKX index/reference semantics.
- Carry this forward as a future OKX index/reference interpretation watch item.
- Future OKX index/reference interpretation should compare Binance, Bybit, and OKX before changing shared packet semantics.

## 7. Timestamp / data_age watch item

- `data_age_ms` was approximately `-7577.9 ms`.
- The observation timestamp was later than packet `created_at` by about 7.6 seconds.
- This likely reflects exchange timestamp versus local collection timestamp alignment / clock skew.
- This is not treated as a blocker in this evidence PR because `parser_normalized_status=OK`, `freshness_pass=true`, `required_missing_fields=[]`, endpoint diagnostics were all OK, and packet creation succeeded.
- This PR does not change timestamp/freshness policy.
- This PR does not clamp or reinterpret negative `data_age_ms`.
- Future timestamp policy should compare Binance, Bybit, and OKX timestamp behavior before changing shared logic.

## 8. Adapter metadata wording watch item

- If packet assumptions still contain older standalone-stage wording such as “no config registration in this PR” or “no registry integration in this PR”, treat it as stale adapter assumption wording from the earlier standalone adapter context.
- This wording does not affect packet generation.
- This wording does not affect `NO_TRADE_ONLY` safety.
- This PR does not clean up adapter metadata wording.
- Future cleanup candidate: `Mark-Orderbook Gap Adapter Metadata Context Cleanup v0`.

## 9. What this proves

- Registered OKX adapter id can run through `tools/collect_market_data.py` in user-local normal network.
- OKX public mark-price/books/instruments fetch path works from user-local environment.
- Parser/readiness integration works through the official collect path.
- Adapter can produce an analysis-only `OpportunityPacket` through the official collect path.
- `REJECT` no-edge classification is represented correctly.
- `NO_TRADE_ONLY` boundary is preserved.

## 10. What this does not prove

- It does not prove profitability.
- It does not prove sampling/persistence behavior.
- It does not justify alert/notification implementation.
- It does not justify Council auto-call.
- It does not justify active strategy promotion.
- It does not justify execution/private API.
- It does not prove multi-venue composite.
- It does not resolve timestamp freshness / clock-skew policy.
- It does not resolve OKX `index_price` / reference semantics.
- It does not clean up adapter metadata wording.

## 11. Generated artifact handling

- Generated output path was `data/generated_packets/live_okx_mark_orderbook_gap_btc_usdt_swap.json`.
- It is a smoke artifact only.
- It must not be committed.
- Generated packet JSON is excluded from this PR.

## 12. Changed files

- `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_okx_collect_market_data_smoke_v0.md`

No `src/`, `configs/`, `tests/`, `tools/`, generated packet, generated sampling, Council, notification, storage, Gemini runtime/prompt, parser/readiness/timestamp/freshness, OKX index/reference semantics, adapter metadata wording, multi-venue composite, or generic/base adapter files are changed.

## 13. Tests run by Codex

Codex checks for this docs-only evidence PR:

- `git status` — checked repository state before changes.
- `git diff --name-only` — checked changed-file scope.
- `python -m unittest discover -s tests` — passed (`Ran 330 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_okx_adapter` — passed (`Ran 13 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_sampling` — passed (`Ran 6 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_adapter` — passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter` — passed (`Ran 9 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_parser` — passed (`Ran 8 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_readiness` — passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_sampling` — passed (`Ran 5 tests`, `OK`).
- `python tools/collect_market_data.py --list-adapters` — passed; adapter listing still works and includes `live_okx_mark_orderbook_gap_btc_usdt_swap`.
- `rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md` — completed as a no-trade/credential scan across existing repository references.
- `rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md` — completed as an active-strategy/no-trade scan across existing repository references.
- `git status --short` — checked final working tree state.
- `git diff --name-only HEAD~1..HEAD` — recorded after commit in the final response.

## 14. Risks

- This is user-local evidence; it should not be described as Codex workspace live network success.
- Future OKX endpoint behavior may differ due to network, exchange status, regional access, or response-shape changes.
- `index_price=null` remains unresolved and should not be silently reinterpreted.
- Negative `data_age_ms` remains unresolved and should not be silently clamped or reinterpreted.
- Stale adapter assumption wording may confuse reviewers until a separate cleanup PR is scoped.

## 15. Rollback plan

- Revert this docs-only evidence PR.
- Remove `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_okx_collect_market_data_smoke_v0.md`.
- No code/config/test/tool/generated-data rollback is required because this PR changes only the evidence document.
- Re-run `python -m unittest discover -s tests` if rollback verification is desired.

## 16. Human review required

Human review should first inspect this handoff file to confirm:

1. The smoke is clearly attributed to user-local normal network, not Codex workspace live success.
2. Generated packet JSON is excluded from this PR.
3. `NO_TRADE_ONLY` and no execution/Council/alert boundaries are preserved.
4. OKX `index_price=null` is carried as a watch item, not silently fixed.
5. Negative `data_age_ms` is carried as a timestamp/data_age watch item without policy change.
6. Stale adapter metadata wording is recorded as a future cleanup candidate only.

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
- config adapter registration changes: no
- registry changes: no
- sampling implementation: no
- parser/readiness/timestamp/freshness logic changes: no
- data_age_ms clamp or reinterpretation: no
- OKX index/reference semantics change: no
- adapter metadata wording cleanup: no
- live network smoke as merge requirement: no
- multi-venue composite implementation: no
- generic/base adapter extraction: no

## 18. Next recommended step

Open a separate planning or cleanup task only if human review wants to address stale adapter metadata wording, OKX index/reference semantics, or shared timestamp/data_age policy. Do not proceed to OKX sampling, alerts, Council auto-call, active promotion, execution/private API, multi-venue composite, or generic/base adapter extraction from this evidence PR.
