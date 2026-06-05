# Mark-Orderbook Gap Hunt Binance Sampling Baseline Planning v0

## 1. Purpose

Plan the sampling baseline scope for `live_binance_mark_orderbook_gap_btcusdt` before connecting Mark-Orderbook Gap Hunt Binance output to sampling/persistence. This is planning-only: it does not implement sampling, does not modify `tools/sample_market_data.py`, and does not change runtime code, config, registry, tests, generated artifacts, alerts, Council behavior, execution, or private API surfaces.

## 2. Baseline

- `live_binance_mark_orderbook_gap_btcusdt` is registered in config/registry as experimental, non-active, public-read-only, and `NO_TRADE_ONLY`.
- User-local official `collect_market_data` smoke succeeded through `tools/collect_market_data.py`.
- The user-local collect smoke produced `strategy_family=mark_orderbook_gap_hunt`, `strategy_id=mark_orderbook_gap_hunt_v0`, `asset=BTC`, `quote=USDT`, one observation, one candidate, `readiness_status=REJECT`, `no_trade_only=True`, and `execution_policy=NO_TRADE_ONLY`.
- No `execution_allowed`, `council_auto_call`, or `alert_trigger` fields were present in the user-local collect smoke.
- The generated collect packet JSON was a smoke artifact and was not committed.

## 3. Sampling baseline scope

Future sampling baseline scope should be limited to:

- `adapter_id`: `live_binance_mark_orderbook_gap_btcusdt`
- `strategy_family`: `mark_orderbook_gap_hunt`
- `strategy_id`: `mark_orderbook_gap_hunt_v0`
- `venue`: `binance`
- `instrument`: `BTCUSDT`
- `status`: experimental / non-active / `NO_TRADE_ONLY`
- `sampling_role`: analysis-only baseline

Sampling baseline work must not add alerts, Council auto-call, active promotion, execution, private API, Bybit/OKX registration, or a multi-venue composite.

## 4. Proposed sampling command

Conservative first user-local sampling command to document for a future evidence run:

```bash
python tools/sample_market_data.py --adapter live_binance_mark_orderbook_gap_btcusdt --samples 3 --interval 1 --output data/market_samples/mark_orderbook_gap_binance_sampling_summary.json
```

Optional extended command after the conservative run is reviewed:

```bash
python tools/sample_market_data.py --adapter live_binance_mark_orderbook_gap_btcusdt --samples 5 --interval 1 --output data/market_samples/mark_orderbook_gap_binance_sampling_summary.json
```

Generated sampling JSON is a smoke artifact only and must not be committed.

## 5. Expected sample-level fields

Future sample records should expose or allow inspection of:

- `sample_index`
- `status`
- `error`
- `packet_id`
- `strategy_family`
- `strategy_id`
- `candidate_count`
- `readiness_status`
- `readiness_pass`
- `recommended_default_decision`
- `best_candidate`
- `long_gap_pct`
- `short_gap_pct`
- `gross_gap_pct` / `max_observed_gap_pct`
- `estimated_net_gap_pct`
- `liquidity_pass`
- `freshness_pass`
- `comparability_pass`
- `required_missing_fields`
- `mark_price`
- `index_price`
- `bid`
- `ask`
- `no_trade_only`
- `execution_policy`

## 6. Expected summary-level fields

Future summary output should include:

- `samples_requested`
- `samples_ok`
- `samples_error`
- `candidate_seen_count`
- `positive_gross_gap_count`
- `positive_net_gap_count`
- `readiness_status_counts`
- `watch_count`
- `reject_count`
- `need_data_count`
- `max_estimated_net_gap_pct`
- `avg_estimated_net_gap_pct`
- `max_gross_gap_pct`
- `avg_latency_ms`
- `max_latency_ms`
- `persistence_status`
- `recommended_default_decision`
- `council_recommended: false`

## 7. Persistence interpretation

- `NO_PERSISTENT_EDGE`: no repeated analysis-only `WATCH` and no repeated positive net gap.
- `REJECT`: normal no-edge behavior, not a data collection or API failure.
- `NEED_DATA`: missing data, metadata, freshness, or comparability requirement.
- `WATCH`: analysis-only observation; it must not trigger Council, alert, active promotion, or execution in this phase.
- `min_consecutive_ready`: planning-only until explicitly reviewed.
- `readiness_pass`: should remain false unless a future policy change explicitly says otherwise.

## 8. User-local smoke plan

- Codex workspace live network may fail due to tunnel `403 Forbidden`; workspace live success must not be a merge requirement.
- User-local normal-network sampling evidence should be recorded in a separate evidence-only PR after implementation or if existing sampling already supports the adapter.
- Generated output must be removed after inspection and must not be committed.
- If user-local sampling fails, classify the failure separately as one of:
  - network/public endpoint issue;
  - adapter/packet-builder issue;
  - sampling summary issue;
  - readiness interpretation issue.

## 9. Future implementation gate

A future `Mark-Orderbook Gap Hunt Binance Sampling Baseline v0` PR should:

- use mocked tests first if sampling code or `tools/sample_market_data.py` needs changes;
- keep all behavior `NO_TRADE_ONLY`;
- not add alert, Council auto-call, active promotion, execution, or private API work;
- not commit generated JSON;
- include handoff evidence;
- include user-local smoke as evidence only, not as a Codex workspace live merge requirement;
- keep Bybit/OKX registration and multi-venue composite out of scope.

## 10. Tests run

- `git status` — checked before changes.
- `git diff --name-only` — checked before commit to verify docs-only scope.
- `python -m unittest discover -s tests` — passed; 294 tests OK.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter` — passed; 9 tests OK.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_parser` — passed; 8 tests OK.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_readiness` — passed; 12 tests OK.
- `python tools/collect_market_data.py --list-adapters` — passed; output included `live_binance_mark_orderbook_gap_btcusdt`.
- `rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md` — completed; expected policy/test/documentation matches only.
- `rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md` — completed as a strategy/no-trade scan.
- `git status --short` — run after commit.

## 11. What this proves

- The sampling baseline scope and expected fields are documented before implementation.
- Future sampling evidence has a conservative user-local command and artifact-handling rule.
- Persistence interpretation is separated from data collection and readiness status.
- The planning preserves the `NO_TRADE_ONLY` boundary.

## 12. What this does not prove

- It does not implement sampling.
- It does not prove user-local sampling success.
- It does not prove persistence or profitability.
- It does not justify alert/notification implementation.
- It does not justify Council auto-call.
- It does not justify active strategy promotion.
- It does not justify execution/private API work.
- It does not register Bybit/OKX adapters or implement a multi-venue composite.

## 13. Changed files

- `docs/sampling_plans/mark_orderbook_gap_hunt_binance_sampling_baseline_v0.md` — sampling baseline plan.
- `docs/pr_handoffs/mark_orderbook_gap_hunt_binance_sampling_baseline_planning_v0.md` — this handoff evidence file.

No runtime code, config, registry, tool, test, generated data, Council, notification, storage, or Gemini runtime files were changed.

## 14. Risks

- Field names may need adjustment when the future sampling implementation inspects the actual packet shape.
- Live sampling may still fail in Codex workspace because of network tunnel restrictions.
- A future user-local sampling run may produce `NEED_DATA`, `REJECT`, or analysis-only `WATCH`; none of those should be treated as execution permission.

## 15. Rollback plan

Revert this docs-only commit to remove the sampling plan and handoff. No runtime rollback is needed because this PR does not change code, config, registry, tools, tests, generated artifacts, sampling, alerts, Council, or execution behavior.

## 16. Human review required

Reviewers should verify:

- sampling scope remains Binance-only and analysis-only;
- proposed commands write only generated smoke artifacts that must not be committed;
- expected fields are sufficient for future persistence review;
- `WATCH` remains analysis-only;
- no alert, Council auto-call, active promotion, execution, private API, config, registry, or sampling implementation was added.

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
- sampling implementation: no
- live network smoke as merge requirement: no
- Bybit/OKX adapter registration: no
- multi-venue composite implementation: no

## 18. Next recommended step

Proceed, only with user approval, to `Mark-Orderbook Gap Hunt Binance Sampling Baseline v0`. That future PR should first verify whether existing sampling can consume the adapter output; if code changes are needed, they should be covered by mocked tests, preserve `NO_TRADE_ONLY`, avoid generated JSON commits, and record user-local sampling evidence separately.
