# Mark-Orderbook Gap Hunt User-Local Binance Direct Adapter Smoke Evidence v0

## 1. Purpose

Record user-local evidence that `BinanceMarkOrderbookGapHuntAdapter` can be imported directly and can build an analysis-only `OpportunityPacket` from live Binance USDⓈ-M `BTCUSDT` public market data on the user's normal network.

This PR is evidence-only. It does not modify runtime code, config, registry, tools, tests, sampling, alert/notification, Council runtime, active strategy state, execution/private API, generated packet JSON, generated sampling JSON, or generated Council-session JSON.

This evidence is from the user's local normal-network run. It must not be described as Codex workspace live-network success.

## 2. Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains experimental / non-active / `NO_TRADE_ONLY`.
- `BinanceMarkOrderbookGapHuntAdapter` exists as a standalone Binance USDⓈ-M `BTCUSDT` adapter class.
- The adapter is not registered in `configs/market_data.yaml`.
- The adapter is not integrated into `src/market_data/registry.py`.
- The adapter is not wired into `tools/collect_market_data.py` or sampling.
- The adapter uses existing parser/readiness helpers and preserves analysis-only boundaries.

## 3. User-local smoke method

The user directly imported and instantiated the class in a local Python snippet:

- class: `BinanceMarkOrderbookGapHuntAdapter`
- network context: user-local normal network, not Codex workspace
- data source: Binance USDⓈ-M public no-key market-data endpoints
- output artifact path: `data/generated_packets/debug_mark_orderbook_gap_binance_direct.json`

The generated output artifact is a local smoke-test artifact only. It is intentionally not committed.

## 4. User-local smoke result

User-reported result:

```text
saved: data\generated_packets\debug_mark_orderbook_gap_binance_direct.json
strategy_family: mark_orderbook_gap_hunt
strategy_id: mark_orderbook_gap_hunt_v0
asset: BTC
quote: USDT
observation_count: 1
candidate_count: 1
venue_id: binance
market_symbol: BTCUSDT
mark_price: 63546.9
index_price: 63575.48956522
bid: 63539.6
ask: 63539.7
candidate_type: mark_orderbook_gap_observation
gross_gap_pct: 0.01133021437709786
estimated_net_gap_pct: -0.18866978562290215
readiness_status: REJECT
recommended_default_decision: REJECT
readiness_pass: False
required_missing_fields: []
diagnostics_count: 3
no_trade_only: True
execution_policy: NO_TRADE_ONLY
has_execution_allowed: False
has_council_auto_call: False
has_alert_trigger: False
```

## 5. Result interpretation

- User-local direct adapter smoke succeeded.
- The adapter fetched live Binance public mark price, orderbook, and metadata data.
- The adapter created one observation and one candidate.
- `diagnostics_count: 3` is expected because the adapter fetches mark price, orderbook, and metadata.
- `readiness_status: REJECT` is expected because a gross gap existed, but estimated net gap was negative after the configured fee/slippage buffer.
- `REJECT` is a normal no-edge classification, not a data collection failure.
- This is not a trade signal.
- No `execution_allowed`, `council_auto_call`, or `alert_trigger` fields were present.
- `no_trade_only: True` and `execution_policy: NO_TRADE_ONLY` were preserved.

## 6. What this proves

- `BinanceMarkOrderbookGapHuntAdapter` can fetch live public no-key Binance USDⓈ-M `BTCUSDT` data from the user's local normal network.
- The adapter can build an analysis-only `OpportunityPacket` through direct class invocation.
- Parser/readiness integration works in a live user-local direct class invocation.
- Diagnostics are produced for public fetch stages.
- The `NO_TRADE_ONLY` boundary is preserved in the observed packet metadata.
- The observed packet did not include `execution_allowed`, `council_auto_call`, or `alert_trigger` fields.

## 7. What this does not prove

- It does not prove config registration.
- It does not prove registry integration.
- It does not prove `collect_market_data` execution.
- It does not prove sampling integration.
- It does not prove Codex workspace live-network success.
- It does not prove profitability.
- It does not justify alert expansion.
- It does not justify Council auto-call.
- It does not justify active strategy promotion.
- It does not justify execution/private API.

## 8. Generated artifact handling

- User-local generated artifact: `data/generated_packets/debug_mark_orderbook_gap_binance_direct.json`.
- The artifact was produced by a smoke run and is not source code.
- The artifact must not be committed.
- This PR commits only this evidence handoff file.
- No generated packet JSON, generated sampling JSON, or generated Council-session JSON is included.

## 9. Changed files

- Added: `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_binance_direct_adapter_smoke_v0.md`.
- No `src/**` changes.
- No `configs/**` changes.
- No `tests/**` changes.
- No `tools/**` changes.
- No `data/generated_packets/**`, `data/market_samples/**`, or `data/council_sessions/**` changes.
- No Council runtime, notification/alert runtime, storage runtime, Gemini runtime, or prompt changes.

## 10. Tests run by Codex

### Git status

```text
git status
```

Result: passed before staging; branch `mark-orderbook-gap-user-local-binance-direct-smoke-v0` had only the allowed new handoff file untracked.

### Git diff name check

```text
git diff --name-only
```

Result: passed before staging; no tracked-file diff was present because the allowed handoff file was new/untracked before staging.

### Commit diff name check

```text
git diff --name-only HEAD~1..HEAD
```

Result: passed after commit; output contained only `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_binance_direct_adapter_smoke_v0.md`.

### Full unit test

```text
python -m unittest discover -s tests
```

Result: passed (`Ran 293 tests in 14.158s`, `OK`).

### Binance adapter test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter
```

Result: passed (`Ran 8 tests in 0.012s`, `OK`).

### Production parser test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_parser
```

Result: passed (`Ran 8 tests in 0.006s`, `OK`).

### Readiness helper test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_readiness
```

Result: passed (`Ran 12 tests in 0.009s`, `OK`).

### No-trade safety check

```text
rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md
```

Result: completed (`exit=0`, `2093` matching lines from existing policy/docs/test references plus this evidence file's explicit no-trade deferrals); no code/config/registry/test/tool/generated-data/private/execution surface was added.

### Active strategy check

```text
rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md
```

Result: completed (`exit=0`, `1440` matching lines from existing strategy/no-trade references plus this evidence file's `mark_orderbook_gap_hunt` references); active strategy remains `cross_exchange_spot_spread_v1` and this evidence keeps `mark_orderbook_gap_hunt_v0` experimental/non-active/`NO_TRADE_ONLY`.

### Final status check

```text
git status --short
```

Result: passed after commit; working tree was clean on `mark-orderbook-gap-user-local-binance-direct-smoke-v0` and no generated artifacts were present.

## 11. Risks

- User-local live smoke evidence could be misread as proof of profitability; it is not.
- `readiness_status: REJECT` could be misread as a failure; here it is a normal no-edge decision after buffer adjustment.
- The generated packet artifact path is documented, but the artifact itself must remain uncommitted.
- Future PRs still need separate review before config/registry/CLI/sampling integration.

## 12. Rollback plan

- Revert `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_binance_direct_adapter_smoke_v0.md`.
- Re-run `python -m unittest discover -s tests` if a rollback PR is opened.
- Confirm no generated packet/sampling/Council-session JSON is committed.
- Confirm adapter remains absent from config/registry unless a separate reviewed PR changes that.

## 13. Human review required

Reviewers should inspect:

1. `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_binance_direct_adapter_smoke_v0.md`

Review focus:

- user-local vs Codex-workspace evidence wording;
- generated artifact non-commit handling;
- `REJECT` interpretation as normal no-edge classification;
- no-trade boundary preservation;
- no config/registry/sampling/alert/Council/execution claims.

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
- config adapter registration: no
- registry integration: no
- sampling implementation: no
- live network smoke as merge requirement: no

## 15. Next recommended step

After human review, consider a separate `Mark-Orderbook Gap Hunt Binance Adapter Config/Registry Planning v0` or additional user-local repeat smoke evidence before any config/registry registration. Keep follow-up work public-read-only, `NO_TRADE_ONLY`, and separate from sampling, alert/notification, Council auto-call, active promotion, and execution/private API.
