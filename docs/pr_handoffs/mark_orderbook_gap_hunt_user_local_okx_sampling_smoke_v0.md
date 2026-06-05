# Mark-Orderbook Gap Hunt User-Local OKX Sampling Smoke Evidence v0

## 1. Purpose

Record user-local evidence that `tools/sample_market_data.py --adapter live_okx_mark_orderbook_gap_btc_usdt_swap` successfully ran three OKX Mark-Orderbook Gap Hunt samples from live public OKX data and summarized the analysis-only results.

This evidence is user-local normal-network evidence. It is not Codex workspace live-network evidence. This PR is evidence-only and does not modify runtime code, config, registry, tools, tests, sampling logic, adapter/parser/readiness/timestamp/freshness logic, metadata wording, alert, Council, execution, or private API behavior.

## 2. Baseline

- `live_okx_mark_orderbook_gap_btc_usdt_swap` is registered in config/registry.
- OKX direct adapter smoke succeeded.
- OKX official `collect_market_data` smoke succeeded.
- OKX sampling baseline mocked tests passed in the previous implementation PR.
- The previous summary top-level fields triage clarified that `market_sampling_v1` aggregate fields live under `payload["summary"]`, not at the top-level envelope.
- Generated sampling JSON is a smoke artifact and must not be committed.

## 3. User-local sampling command

User-local command executed by the user:

```bash
python tools/sample_market_data.py --adapter live_okx_mark_orderbook_gap_btc_usdt_swap --samples 3 --interval 1 --output data/market_samples/mark_orderbook_gap_okx_sampling_summary.json
```

## 4. Market sampling schema note

`market_sampling_v1` output is an envelope with top-level fields such as:

- `schema_version`
- `adapter_id`
- `samples_requested`
- `samples`
- `summary`

Aggregate sampling fields must be read from `payload["summary"]` / `summary.<field>`. Top-level lookups such as `payload.get("samples_ok")` may return `None` and should not be recorded as failure.

## 5. User-local sampling result

Values below are from `payload["summary"]` and sample records.

Envelope:

- `schema_version`: `market_sampling_v1`
- `adapter_id`: `live_okx_mark_orderbook_gap_btc_usdt_swap`
- `samples_requested`: `3`

Summary:

- `summary.samples_ok`: `3`
- `summary.samples_error`: `0`
- `summary.candidate_seen_count`: `3`
- `summary.positive_gross_gap_count`: `3`
- `summary.positive_net_gap_count`: `0`
- `summary.readiness_status_counts`: `{'REJECT': 3}`
- `summary.watch_count`: `0`
- `summary.reject_count`: `3`
- `summary.need_data_count`: `0`
- `summary.max_estimated_net_gap_pct`: `-0.1859044065359208`
- `summary.avg_estimated_net_gap_pct`: `-0.19039189338596102`
- `summary.max_gross_gap_pct`: `0.014095593464079202`
- `summary.avg_latency_ms`: `248.0`
- `summary.max_latency_ms`: `294.0`
- `summary.persistence_status`: `NO_PERSISTENT_EDGE`
- `summary.recommended_default_decision`: `REJECT`
- `summary.timestamp_data_age_watch_count`: `0`
- `summary.negative_data_age_observed`: `False`
- `summary.index_price_null_count`: `3`
- `summary.index_price_null_observed`: `True`
- `summary.stale_assumption_wording_count`: `0`
- `summary.stale_assumption_wording_observed`: `False`
- `council_recommended`: `False`

Sample-level:

- `statuses`: `['ok', 'ok', 'ok']`
- `readiness`: `['REJECT', 'REJECT', 'REJECT']`
- `decisions`: `['REJECT', 'REJECT', 'REJECT']`
- `venue_id`: `['okx', 'okx', 'okx']`
- `market_symbol`: `['BTC-USDT-SWAP', 'BTC-USDT-SWAP', 'BTC-USDT-SWAP']`
- `parser_status`: `['OK', 'OK', 'OK']`
- `data_age_ms`: `[82.0, 56.0, 50.0]`
- `index_price`: `[None, None, None]`
- `index_price_null`: `[True, True, True]`
- `timestamp_watch`: `[False, False, False]`
- `stale_wording`: `[False, False, False]`
- `no_trade_only`: `[True, True, True]`
- `execution_policy`: `['NO_TRADE_ONLY', 'NO_TRADE_ONLY', 'NO_TRADE_ONLY']`
- `has_execution_allowed`: `False`
- `has_council_auto_call`: `False`
- `has_alert_trigger`: `False`

## 6. Result interpretation

- User-local OKX sampling smoke succeeded.
- `samples_ok=3` and `samples_error=0` means all requested live public samples succeeded.
- `candidate_seen_count=3` means each sample produced one OKX Mark-Orderbook Gap candidate.
- `readiness_status_counts={'REJECT': 3}` is normal no-edge behavior, not data/API failure.
- `positive_net_gap_count=0` means fee/slippage/buffer-adjusted net gap was not positive.
- `persistence_status=NO_PERSISTENT_EDGE` is expected because there were no `WATCH` samples and no positive net gap samples.
- `council_recommended=False` is expected.
- `no_trade_only` and `NO_TRADE_ONLY` were preserved.
- No `execution_allowed`, `council_auto_call`, or `alert_trigger` fields were present.

## 7. OKX index_price / reference watch item

- `index_price=None` appeared in all three samples.
- This is carried as an OKX index/reference watch item.
- It is not a blocker for this smoke because samples succeeded, candidates were produced, readiness completed as `REJECT`, and summary fields populated under `payload["summary"]`.
- This PR does not change OKX index/reference semantics.
- Future policy candidate remains `Mark-Orderbook Gap OKX Index/Reference Semantics v0`.

## 8. Timestamp / data_age watch item

- `data_age_ms` values were positive in this run: `[82.0, 56.0, 50.0]`.
- `summary.timestamp_data_age_watch_count=0` and `summary.negative_data_age_observed=False`.
- `timestamp_watch` was false for all samples.
- This PR does not clamp, reinterpret, or otherwise change timestamp/freshness policy.
- Future policy candidates remain `Market Data Timestamp Freshness / Clock Skew Policy v0` or `Mark-Orderbook Gap Hunt Timestamp Alignment Policy v0` if later negative values reappear.

## 9. Metadata wording cleanup verification

- `summary.stale_assumption_wording_count=0`.
- `summary.stale_assumption_wording_observed=False`.
- Sample-level `stale_wording` was `[False, False, False]`.
- This is positive evidence that metadata wording cleanup is reflected in future-generated packets.
- This PR does not change adapter metadata wording.

## 10. What this proves

- User-local normal-network OKX sampling path can run three live public OKX samples through `tools/sample_market_data.py`.
- The registered OKX adapter can produce three analysis-only Mark-Orderbook Gap samples through the sampling path.
- Sampling summary fields populate under `payload["summary"]` when inspected through the correct schema path.
- Each sample produced one OKX Mark-Orderbook Gap candidate.
- `REJECT` no-edge classification is represented correctly.
- `NO_PERSISTENT_EDGE` is represented correctly for no `WATCH` / no positive net gap samples.
- `index_price=None` is surfaced and counted as an OKX index/reference watch item.
- Positive `data_age_ms` values did not trigger timestamp/data_age watches.
- Metadata stale wording guard remained false for generated packets.
- `NO_TRADE_ONLY` boundary was preserved.

## 11. What this does not prove

- It does not prove profitability.
- It does not prove persistent edge.
- It does not justify alert/notification implementation.
- It does not justify Council auto-call.
- It does not justify active strategy promotion.
- It does not justify execution/private API.
- It does not prove multi-venue composite behavior.
- It does not resolve timestamp freshness / clock-skew policy.
- It does not resolve OKX index_price/reference semantics.
- It does not implement generic/base adapter extraction.

## 12. Generated artifact handling

- Generated output path was `data/market_samples/mark_orderbook_gap_okx_sampling_summary.json`.
- It is a smoke artifact only.
- It must not be committed.
- This PR excludes generated sampling JSON.

## 13. Changed files

- `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_okx_sampling_smoke_v0.md`

No `src/`, `configs/`, `tests/`, `tools/`, generated packet/sampling data, Council, notification, storage, Gemini runtime/prompt, adapter/parser/readiness/timestamp/freshness, OKX index/reference semantics, sampling implementation, multi-venue composite, or generic/base adapter files are changed.

## 14. Tests run by Codex

- `git status` completed before edits to confirm branch/worktree state.
- `git diff --name-only` completed before commit to confirm only the allowed evidence file changed.
- `python -m unittest discover -s tests` passed (`Ran 339 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_okx_sampling` passed (`Ran 9 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_okx_adapter` passed (`Ran 13 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_sampling` passed (`Ran 6 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_adapter` passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter` passed (`Ran 9 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_parser` passed (`Ran 8 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_readiness` passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_sampling` passed (`Ran 5 tests`, `OK`).
- `python tools/collect_market_data.py --list-adapters` passed and listed `live_okx_mark_orderbook_gap_btc_usdt_swap`.
- `rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md` completed as an audit scan; matches are existing policy/test/doc references and no generated artifacts were introduced.
- `rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md` completed as a strategy/no-trade audit scan.
- `git status --short` confirmed only the allowed evidence file was changed before staging/commit.

## 15. Risks

- This evidence depends on a user-local normal-network run and does not guarantee Codex workspace live-network reachability.
- OKX `index_price=None` remains a watch item for future policy review.
- Future runs may again show negative `data_age_ms`; that should remain a timestamp/data_age watch item unless a separate policy task changes behavior.
- This evidence should not be interpreted as profitability, persistent edge, or permission to add alert/Council/execution behavior.

## 16. Rollback plan

- Revert this docs-only PR.
- Remove `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_okx_sampling_smoke_v0.md`.
- No code/config/test/tool/generated-data rollback is required.

## 17. Human review required

Human review should first inspect this handoff file to confirm:

1. Values are recorded from `payload["summary"]` and sample records, not top-level aggregate lookups.
2. Generated sampling JSON is excluded from the PR.
3. `index_price=None` and timestamp/data_age observations are documented as watch items only.
4. No-trade compliance and no execution/Council/alert behavior remain intact.

## 18. No-trade compliance

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
- config/registry changes: no
- sampling implementation changes: no
- adapter/parser/readiness logic changes: no
- parser/readiness/timestamp/freshness logic changes: no
- data_age_ms clamp or reinterpretation: no
- OKX index/reference semantics change: no
- multi-venue composite implementation: no
- generic/base adapter extraction: no

## 19. Next recommended step

Review this evidence, then decide whether to keep collecting OKX Mark-Orderbook Gap Hunt sampling evidence across more user-local windows before opening any separate policy task for OKX index/reference semantics or timestamp/data_age interpretation. Do not add alert/Council/execution/private API behavior from this evidence alone.
