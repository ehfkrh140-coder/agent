# Mark-Orderbook Gap Hunt User-Local Bybit Sampling Smoke Evidence v0

## 1. Purpose

Record evidence that a human user ran the registered `live_bybit_mark_orderbook_gap_btcusdt` adapter through `tools/sample_market_data.py` from a normal local network and completed three live public Bybit sampling iterations successfully.

This is a docs-only evidence PR. The smoke was run by the user, not by Codex in the workspace. This PR does not modify runtime code, config, registry, tools, tests, sampling logic, parser/readiness/timestamp/freshness logic, alert/notification behavior, Council behavior, active strategy state, execution/private API surfaces, or generated artifacts.

## 2. Baseline

- `live_bybit_mark_orderbook_gap_btcusdt` is already registered as disabled, experimental, non-active, and `NO_TRADE_ONLY`.
- `BybitMarkOrderbookGapHuntAdapter` already exists and uses public Bybit V5 linear BTCUSDT endpoints.
- The mocked-first Bybit sampling baseline already proved the sampling pipeline can consume mocked Bybit `mark_orderbook_gap_hunt` packet output.
- Previous user-local direct Bybit adapter smoke succeeded.
- Previous user-local official `collect_market_data` Bybit smoke succeeded.
- A negative `data_age_ms` watch item was previously observed around `-6647 ms` and is carried forward without policy changes.
- The active strategy remains `cross_exchange_spot_spread_v1`; `mark_orderbook_gap_hunt_v0` remains experimental/non-active/analysis-only.

## 3. User-local sampling command

The user ran the following command from a normal local network:

```bash
python tools/sample_market_data.py --adapter live_bybit_mark_orderbook_gap_btcusdt --samples 3 --interval 1 --output data/market_samples/mark_orderbook_gap_bybit_sampling_summary.json
```

This command writes a generated sampling artifact. The generated output is smoke evidence only and must not be committed.

## 4. User-local sampling result

User-local result summary:

- `schema_version: market_sampling_v1`
- `adapter_id: live_bybit_mark_orderbook_gap_btcusdt`
- `samples_requested: 3`
- `samples_ok: 3`
- `samples_error: 0`
- `candidate_seen_count: 3`
- `positive_gross_gap_count: 3`
- `positive_net_gap_count: 0`
- `readiness_status_counts: {'REJECT': 3}`
- `watch_count: 0`
- `reject_count: 3`
- `need_data_count: 0`
- `max_estimated_net_gap_pct: -0.19121302606122323`
- `avg_estimated_net_gap_pct: -0.19356717058248743`
- `max_gross_gap_pct: 0.00878697393877676`
- `avg_latency_ms: 285.3333333333333`
- `max_latency_ms: 313.0`
- `persistence_status: NO_PERSISTENT_EDGE`
- `recommended_default_decision: REJECT`
- `council_recommended: False`
- `statuses: ['ok', 'ok', 'ok']`
- `readiness: ['REJECT', 'REJECT', 'REJECT']`
- `decisions: ['REJECT', 'REJECT', 'REJECT']`
- `no_trade_only: [True, True, True]`
- `execution_policy: ['NO_TRADE_ONLY', 'NO_TRADE_ONLY', 'NO_TRADE_ONLY']`
- `has_execution_allowed: False`
- `has_council_auto_call: False`
- `has_alert_trigger: False`
- `timestamp_data_age_watch_count: 3`
- `negative_data_age_observed: True`
- sample `data_age_ms` values were approximately `[-6766, -6877, -6786]`.

## 5. Result interpretation

- User-local Bybit sampling smoke succeeded.
- `samples_ok=3` and `samples_error=0` means live public data collection and the sampling pipeline succeeded for all requested samples.
- `candidate_seen_count=3` means each sample produced one Mark-Orderbook Gap candidate.
- `positive_gross_gap_count=3` means mark-vs-orderbook gross gap was observed in all samples.
- `positive_net_gap_count=0` means fee/slippage/buffer-adjusted net gap was not positive.
- `readiness_status_counts={'REJECT': 3}` is normal no-edge behavior, not a data/API failure.
- `persistence_status=NO_PERSISTENT_EDGE` is expected because there were no `WATCH` samples and no positive net gap samples.
- `council_recommended=False` is expected.
- `no_trade_only` and `NO_TRADE_ONLY` were preserved in all samples.
- No `execution_allowed`, `council_auto_call`, or `alert_trigger` fields were present.
- Negative `data_age_ms` appeared in all three samples and was surfaced as a timestamp/data_age watch item.
- This evidence does not change timestamp/freshness policy.

## 6. Timestamp / data_age watch item

Observed timestamp/data_age fields:

- `timestamp_data_age_watch_count=3`
- `negative_data_age_observed=True`
- sample `data_age_ms` values were approximately `-6766 ms`, `-6877 ms`, and `-6786 ms`.

Interpretation:

- This likely reflects exchange timestamp vs local collection timestamp alignment or clock skew.
- It is not treated as a blocker in this evidence PR because all samples had `status=ok`, `parser_normalized_status=OK`, `freshness_pass=true`, `required_missing_fields=[]`, `diagnostics_count=3`, and packet creation succeeded.
- Do not change code in this PR.
- Do not clamp negative `data_age_ms` in this PR.
- Do not reinterpret negative `data_age_ms` in this PR.
- Do not change parser/readiness/timestamp/freshness logic in this PR.

Future policy candidates remain:

- `Market Data Timestamp Freshness / Clock Skew Policy v0`
- `Mark-Orderbook Gap Hunt Timestamp Alignment Policy v0`

Future timestamp policy work should compare Binance, Bybit, and OKX timestamp behavior before changing shared parser/readiness/sampling interpretation.

## 7. What this proves

- Registered Bybit adapter id can run through `tools/sample_market_data.py` in a user-local normal network.
- Bybit public ticker/orderbook/instruments-info fetch path works repeatedly from the user-local environment.
- Sampling pipeline can summarize `mark_orderbook_gap_hunt` sample-level and summary-level fields for Bybit.
- `REJECT` no-edge classification is represented correctly.
- `NO_PERSISTENT_EDGE` is represented correctly when no positive net gap or `WATCH` appears.
- Negative `data_age_ms` is surfaced as a watch item without policy change.
- `NO_TRADE_ONLY` boundary is preserved.

## 8. What this does not prove

- It does not prove profitability.
- It does not prove persistent edge.
- It does not justify alert/notification implementation.
- It does not justify Council auto-call.
- It does not justify active strategy promotion.
- It does not justify execution/private API.
- It does not prove OKX adapter or multi-venue composite.
- It does not resolve timestamp freshness / clock-skew policy.
- It does not prove negative `data_age_ms` is always safe.

## 9. Generated artifact handling

- Generated output path was `data/market_samples/mark_orderbook_gap_bybit_sampling_summary.json`.
- It is a smoke artifact only.
- It must not be committed.
- Generated sampling JSON is excluded from this PR.
- No generated packet JSON or generated sampling JSON is committed by this docs-only evidence PR.

## 10. Changed files

- `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_bybit_sampling_smoke_v0.md`

No `src/`, `configs/`, `tests/`, `tools/`, generated data, Council, notification, storage, Gemini runtime/prompt, OKX, composite, parser/readiness/timestamp/freshness, or registry files are changed.

## 11. Tests run by Codex

Codex checks for this docs-only evidence PR:

- `git status` — checked repository status before changes.
- `git diff --name-only` — checked changed-file scope.
- `python -m unittest discover -s tests` — run to ensure docs-only evidence did not break the suite.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_sampling` — run to confirm the mocked Bybit sampling baseline still passes.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_adapter` — run to confirm Bybit adapter tests still pass.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter` — run to confirm Binance adapter behavior remains unchanged.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_parser` — run to confirm parser behavior remains unchanged.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_readiness` — run to confirm readiness behavior remains unchanged.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_sampling` — run to confirm generic Mark-Orderbook Gap sampling behavior remains unchanged.
- `python tools/collect_market_data.py --list-adapters` — run to confirm adapter listing still works.
- `rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md` — run as a no-trade/credential scan across existing repository references.
- `rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md` — run as an active-strategy/no-trade scan across existing repository references.
- `git status --short` — checked final working tree state.
- `git diff --name-only HEAD~1..HEAD` — recorded after commit in the final response.

## 12. Risks

- Negative `data_age_ms` repeated across all three user-local samples and remains an unresolved timestamp/clock-skew policy watch item.
- This evidence is user-local and live-market-time-specific; future public endpoint behavior may differ.
- This docs-only PR does not prove profitability, persistent edge, or execution readiness.
- Human review is still required before any future timestamp policy, alert, Council, active promotion, OKX, composite, or execution work.

## 13. Rollback plan

- Revert this docs-only PR.
- Remove `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_bybit_sampling_smoke_v0.md`.
- No code/config/test/tool/generated-data rollback is required because this PR changes only one handoff document.
- Re-run `python -m unittest discover -s tests` if rollback verification is desired.

## 14. Human review required

Human review should first inspect this handoff file to verify:

1. the smoke is clearly attributed to a user-local normal-network run, not Codex workspace live success;
2. generated sampling JSON is excluded from the PR;
3. negative `data_age_ms` is carried forward as a watch item without code or policy changes;
4. `REJECT` and `NO_PERSISTENT_EDGE` are interpreted as no-edge behavior rather than API failure;
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
- config adapter registration changes: no
- registry changes: no
- sampling implementation changes: no
- parser/readiness/timestamp/freshness logic changes: no
- data_age_ms clamp or reinterpretation: no
- live network smoke as merge requirement: no
- OKX adapter registration: no
- multi-venue composite implementation: no
- generic/base adapter extraction: no

## 16. Next recommended step

Open a separate timestamp policy planning task, such as `Market Data Timestamp Freshness / Clock Skew Policy v0` or `Mark-Orderbook Gap Hunt Timestamp Alignment Policy v0`, only after reviewing Binance/Bybit/OKX timestamp behavior together. Do not change timestamp/freshness behavior from this evidence PR.
