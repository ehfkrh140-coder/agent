# Mark-Orderbook Gap Hunt User-Local Binance Sampling Smoke Evidence v0

## 1. Purpose

Record evidence that the user ran `tools/sample_market_data.py --adapter live_binance_mark_orderbook_gap_btcusdt` on a normal user-local network and completed three live public-data samples for the experimental Binance Mark-Orderbook Gap Hunt adapter.

This is an evidence-only PR. It does not modify runtime code, config, registry, tools, tests, sampling logic, alerts, Council behavior, execution/private API surfaces, or generated sampling artifacts.

## 2. Baseline

- `live_binance_mark_orderbook_gap_btcusdt` is registered and `NO_TRADE_ONLY`.
- User-local `collect_market_data` smoke already proved the official collect path can produce an analysis-only packet.
- Sampling Baseline v0 added mocked coverage and minimal summary fields for `mark_orderbook_gap_hunt` packets.
- This smoke is user-local evidence and must not be presented as Codex workspace live success.
- Generated sampling JSON is a local smoke artifact and must not be committed.

## 3. User-local sampling command

The user ran:

```bash
python tools/sample_market_data.py --adapter live_binance_mark_orderbook_gap_btcusdt --samples 3 --interval 1 --output data/market_samples/mark_orderbook_gap_binance_sampling_summary.json
```

Generated output path:

```text
data/market_samples/mark_orderbook_gap_binance_sampling_summary.json
```

The generated sampling JSON is not part of this PR.

## 4. User-local sampling result

User-local verification summary:

```text
schema_version: market_sampling_v1
adapter_id: live_binance_mark_orderbook_gap_btcusdt
samples_requested: 3
samples_ok: 3
samples_error: 0
candidate_seen_count: 3
positive_gross_gap_count: 3
positive_net_gap_count: 0
readiness_status_counts: {'REJECT': 3}
watch_count: 0
reject_count: 3
need_data_count: 0
max_estimated_net_gap_pct: -0.18538010897458695
avg_estimated_net_gap_pct: -0.18923190152457398
max_gross_gap_pct: 0.014619891025413055
persistence_status: NO_PERSISTENT_EDGE
recommended_default_decision: REJECT
council_recommended: False
statuses: ['ok', 'ok', 'ok']
readiness: ['REJECT', 'REJECT', 'REJECT']
decisions: ['REJECT', 'REJECT', 'REJECT']
no_trade_only: [True, True, True]
execution_policy: ['NO_TRADE_ONLY', 'NO_TRADE_ONLY', 'NO_TRADE_ONLY']
has_execution_allowed: False
has_council_auto_call: False
has_alert_trigger: False
```

## 5. Result interpretation

- User-local sampling smoke succeeded.
- `samples_ok=3` and `samples_error=0` means live public data collection and the sampling pipeline succeeded for all requested samples.
- `candidate_seen_count=3` means each sample produced one Mark-Orderbook Gap candidate.
- `positive_gross_gap_count=3` means mark-vs-orderbook gross gap was observed in all samples.
- `positive_net_gap_count=0` means fee/slippage/buffer-adjusted net gap was not positive.
- `readiness_status_counts={'REJECT': 3}` is normal no-edge behavior, not a data/API failure.
- `persistence_status=NO_PERSISTENT_EDGE` is expected because there were no repeated `WATCH` or positive net-gap samples.
- `council_recommended=False` is expected.
- `no_trade_only=True` and `execution_policy=NO_TRADE_ONLY` were preserved in all samples.
- No `execution_allowed`, `council_auto_call`, or `alert_trigger` fields were present.

## 6. What this proves

- The registered adapter id can run through `tools/sample_market_data.py` in a user-local normal network.
- The Binance public mark/orderbook/metadata fetch path works repeatedly from the user-local environment.
- The sampling pipeline can summarize `mark_orderbook_gap_hunt` sample-level and summary-level fields.
- `REJECT` no-edge classification is represented correctly.
- The `NO_TRADE_ONLY` boundary is preserved.

## 7. What this does not prove

- It does not prove profitability.
- It does not prove a persistent edge.
- It does not justify alert/notification implementation.
- It does not justify Council auto-call.
- It does not justify active strategy promotion.
- It does not justify execution/private API work.
- It does not prove Bybit/OKX adapters.
- It does not prove a multi-venue composite.

## 8. Generated artifact handling

- Generated output path was `data/market_samples/mark_orderbook_gap_binance_sampling_summary.json`.
- It is a smoke artifact only.
- Generated sampling JSON must not be committed.
- This PR commits only this evidence document and excludes the generated sampling JSON.

## 9. Changed files

- `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_binance_sampling_smoke_v0.md` — user-local Binance sampling smoke evidence.

No runtime code, config, registry, tools, tests, sampling logic, generated data, Council, notification, storage, or Gemini runtime files were changed.

## 10. Tests run by Codex

- `git status` — checked repository state before changes.
- `git diff --name-only` — checked changed files before commit.
- `python -m unittest discover -s tests` — passed; 299 tests OK.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_sampling` — passed; 5 tests OK.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter` — passed; 9 tests OK.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_parser` — passed; 8 tests OK.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_readiness` — passed; 12 tests OK.
- `python tools/collect_market_data.py --list-adapters` — passed; output included `live_binance_mark_orderbook_gap_btcusdt`.
- `rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md` — completed; expected policy/test/documentation matches only.
- `rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md` — completed as a strategy/no-trade scan.
- `git status --short` — run after commit.

Codex did not run live Binance sampling as a merge requirement for this docs-only PR. The live result recorded here is user-local evidence supplied by the user.

## 11. Risks

- Evidence is based on one user-local sampling run; future public endpoint availability and live values may differ.
- Future sampling runs may produce `NEED_DATA`, `REJECT`, or analysis-only `WATCH` depending on live data, metadata, freshness, and thresholds.
- This evidence does not validate alerting, Council review, active promotion, execution, private APIs, Bybit/OKX, or multi-venue behavior.

## 12. Rollback plan

Revert this docs-only commit to remove the user-local sampling smoke evidence file. No runtime rollback is needed because this PR does not change code, config, registry, tools, tests, generated data, sampling logic, alerts, Council, or execution behavior.

## 13. Human review required

Reviewers should verify:

- the evidence is correctly described as user-local, not Codex workspace live success;
- generated sampling JSON is not committed;
- `REJECT` is interpreted as no-edge readiness behavior, not a sampling/API failure and not a trade signal;
- `NO_TRADE_ONLY` is preserved;
- `council_recommended=False` is expected;
- no alert, Council auto-call, active promotion, execution, private API, config, registry, or sampling implementation change is introduced.

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
- config adapter registration changes: no
- registry changes: no
- sampling implementation changes: no
- live network smoke as merge requirement: no
- Bybit/OKX adapter registration: no
- multi-venue composite implementation: no

## 15. Next recommended step

Keep this as the first user-local sampling smoke evidence for the Binance Mark-Orderbook Gap Hunt adapter. If the user wants stronger persistence evidence, run a separate repeated-sampling evidence task with a larger sample count, still preserving `NO_TRADE_ONLY` and excluding generated JSON from commits. Do not add alerts, Council auto-call, active promotion, execution, or private API work at this stage.
