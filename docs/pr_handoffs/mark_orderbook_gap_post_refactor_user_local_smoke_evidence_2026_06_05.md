# Mark-Orderbook Gap Post-Refactor User-Local Smoke Evidence v0

## 1. 작업 목적

PR #116~#119 refactor 이후 Binance / Bybit / OKX `mark_orderbook_gap_hunt_v0` live public-read-only sampling path가 계속 정상인지 확인하기 위한 post-refactor smoke evidence handoff 문서다.

Correction note for this handoff:

- Initial PR #120 received the literal placeholder `PASTE_USER_LOCAL_RESULT_HERE`, so Codex recorded venue-level metrics as `not_provided` rather than fabricating values.
- This follow-up correction reflects the actual user-local summary lines provided later by the user.
- The generated JSON summary files remain smoke artifacts and are not committed.

This evidence is intended as post-refactor runtime smoke evidence. It is not profitability evidence and does not prove a persistent edge.

## 2. User-local commands

The user-local public-read-only smoke commands recorded for the post-refactor check are:

```bash
python tools/sample_market_data.py --adapter live_binance_mark_orderbook_gap_btcusdt --samples 3 --interval 2 --output data/market_samples/mark_orderbook_gap_binance_post_refactor_smoke_3x_summary.json
```

```bash
python tools/sample_market_data.py --adapter live_bybit_mark_orderbook_gap_btcusdt --samples 3 --interval 2 --output data/market_samples/mark_orderbook_gap_bybit_post_refactor_smoke_3x_summary.json
```

```bash
python tools/sample_market_data.py --adapter live_okx_mark_orderbook_gap_btc_usdt_swap --samples 3 --interval 2 --output data/market_samples/mark_orderbook_gap_okx_post_refactor_smoke_3x_summary.json
```

These commands write generated sampling artifacts under `data/market_samples/`. Those JSON files are smoke artifacts only and must not be committed.

## 3. Evidence summary

### Input received for this correction

The user provided these post-refactor user-local command summaries:

- Binance output path: `data\market_samples\mark_orderbook_gap_binance_post_refactor_smoke_3x_summary.json`
- Binance summary: `status=NO_PERSISTENT_EDGE ok=3 errors=0 council_recommended=False`
- Bybit output path: `data\market_samples\mark_orderbook_gap_bybit_post_refactor_smoke_3x_summary.json`
- Bybit summary: `status=NO_PERSISTENT_EDGE ok=3 errors=0 council_recommended=False`
- OKX output path: `data\market_samples\mark_orderbook_gap_okx_post_refactor_smoke_3x_summary.json`
- OKX summary: `status=NO_PERSISTENT_EDGE ok=3 errors=0 council_recommended=False`

Generated JSON files were not supplied for commit and are not committed by this PR.

### Binance

- `adapter_id`: `live_binance_mark_orderbook_gap_btcusdt`
- `samples_requested`: 3
- `samples_ok`: 3
- `samples_error`: 0
- `summary status / persistence_status`: `NO_PERSISTENT_EDGE`
- `council_recommended`: false
- exact command output path: `data\market_samples\mark_orderbook_gap_binance_post_refactor_smoke_3x_summary.json`
- exact `candidate_seen_count`: not_provided in pasted summary
- exact `readiness_status`: not_provided in pasted summary
- exact `recommended_default_decision`: not_provided in pasted summary
- exact `positive_net_gap_count`: not_provided in pasted summary
- exact `diagnostics_count`: not_provided in pasted summary
- exact `stale_assumption_wording_observed`: not_provided in pasted summary

### Bybit

- `adapter_id`: `live_bybit_mark_orderbook_gap_btcusdt`
- `samples_requested`: 3
- `samples_ok`: 3
- `samples_error`: 0
- `summary status / persistence_status`: `NO_PERSISTENT_EDGE`
- `council_recommended`: false
- exact command output path: `data\market_samples\mark_orderbook_gap_bybit_post_refactor_smoke_3x_summary.json`
- exact `candidate_seen_count`: not_provided in pasted summary
- exact `readiness_status`: not_provided in pasted summary
- exact `recommended_default_decision`: not_provided in pasted summary
- exact `positive_net_gap_count`: not_provided in pasted summary
- exact `diagnostics_count`: not_provided in pasted summary
- exact `stale_assumption_wording_observed`: not_provided in pasted summary
- negative `data_age_ms`: keep as a watch item based on previous 30-sample evidence; this pasted 3-line summary does not include the exact post-refactor count.

### OKX

- `adapter_id`: `live_okx_mark_orderbook_gap_btc_usdt_swap`
- `samples_requested`: 3
- `samples_ok`: 3
- `samples_error`: 0
- `summary status / persistence_status`: `NO_PERSISTENT_EDGE`
- `council_recommended`: false
- exact command output path: `data\market_samples\mark_orderbook_gap_okx_post_refactor_smoke_3x_summary.json`
- exact `candidate_seen_count`: not_provided in pasted summary
- exact `readiness_status`: not_provided in pasted summary
- exact `recommended_default_decision`: not_provided in pasted summary
- exact `positive_net_gap_count`: not_provided in pasted summary
- exact `diagnostics_count`: not_provided in pasted summary
- exact `stale_assumption_wording_observed`: not_provided in pasted summary
- OKX `index_price=None`: keep as a watch item based on previous 30-sample evidence; this pasted 3-line summary does not include the exact post-refactor count.
- OKX negative `data_age_ms`: keep as a watch item based on previous 30-sample evidence; this pasted 3-line summary does not include the exact post-refactor count.

## 4. Watch items

The following observations remain watch items, not failures:

- Bybit negative `data_age_ms` is a timestamp/clock-skew policy watch item based on previous 30-sample evidence.
- OKX negative `data_age_ms` is a timestamp/clock-skew policy watch item based on previous 30-sample evidence.
- OKX `index_price=None` is an OKX index/reference semantics watch item based on previous 30-sample evidence.
- The pasted 3-line post-refactor summaries do not include exact watch counts, so this correction does not infer or estimate those counts.
- Positive gross gap with negative estimated net gap, if present in the generated JSON, can still be a normal no-edge `REJECT` outcome.

These watch items do not justify timestamp policy changes, OKX index endpoint implementation, alerts, Council auto-call, execution, or active strategy promotion in this PR.

## 5. Interpretation

- This user-local smoke result is post-refactor sampling pipeline smoke success evidence.
- `samples_ok=3` and `samples_error=0` for Binance / Bybit / OKX confirm that the 3-sample smoke path completed without sampling errors for all three venues.
- `NO_PERSISTENT_EDGE` and `council_recommended=false` can be normal no-edge outcomes.
- This evidence does not prove profitable edge.
- This evidence does not prove persistent edge.
- Mark price is not an executable price.
- `WATCH` and `REJECT` are analysis-only labels.
- `NO_TRADE_ONLY` remains mandatory.

## 6. No-trade compliance

- Active strategy promotion: no
- `mark_orderbook_gap_hunt_v0` active promotion: no
- Council auto-call: no
- Alert: no
- Execution: no
- Private API: no
- Credentials/API keys/secrets/tokens: no
- Account/balance/position lookup: no
- Order/cancel: no
- Withdrawal/deposit/transfer: no
- Auto-trading: no
- Config/registry change: no
- Source/runtime behavior change: no
- Parser behavior change: no
- Readiness threshold change: no
- Timestamp policy implementation: no
- OKX index endpoint implementation: no
- Generated JSON commit: no
- `NO_TRADE_ONLY` preserved: yes

## 7. Generated JSON commit 금지

Generated packet/sampling files remain smoke artifacts only and must not be committed:

- `data/market_samples/*.json`
- `data/generated_packets/*.json`

This PR intentionally updates only this handoff document and does not add generated JSON.

## 8. Rollback plan

Rollback path:

1. Revert this docs-only correction PR.
2. Restore the previous version of `docs/pr_handoffs/mark_orderbook_gap_post_refactor_user_local_smoke_evidence_2026_06_05.md`.
3. No code/config/registry/runtime/parser/readiness/generated-data rollback is required.

## 9. Next PR candidates

Recommended order after this correction:

1. Timestamp / clock-skew policy planning
2. OKX index/reference semantics planning
3. Mark-Orderbook Gap multi-venue comparative summary
4. 이후 후보: next experimental strategy planning
