# Mark-Orderbook Gap Post-Refactor User-Local Smoke Evidence v0

## 1. 작업 목적

PR #116~#119 refactor 이후 Binance / Bybit / OKX `mark_orderbook_gap_hunt_v0` live public-read-only sampling path가 계속 정상인지 확인하기 위한 post-refactor smoke evidence handoff 문서다.

Important limitation for this handoff:

- The user-local result block provided to Codex was the literal placeholder `PASTE_USER_LOCAL_RESULT_HERE`.
- Therefore this document records the required user-local commands, interpretation rules, no-trade boundaries, and the exact evidence fields that must be checked, but it does not fabricate venue-level result metrics.
- Reviewers should replace the placeholder with actual user-local output in a follow-up evidence update if exact Binance / Bybit / OKX result values are required for merge evidence.

This evidence is intended as post-refactor runtime smoke evidence. It is not profitability evidence and does not prove a persistent edge.

## 2. User-local commands

The user-local public-read-only smoke commands to record for the post-refactor check are:

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

### Input received by Codex

- User-local result payload: `PASTE_USER_LOCAL_RESULT_HERE`
- Exact venue-level metrics supplied: no
- Generated JSON supplied for commit: no
- Generated JSON committed by this PR: no

Because exact user-local JSON output was not provided in the prompt, the venue-level fields below are intentionally left as `not_provided` rather than inferred.

### Binance

- `adapter_id`: `live_binance_mark_orderbook_gap_btcusdt`
- `samples_requested`: not_provided
- `samples_ok`: not_provided
- `samples_error`: not_provided
- `candidate_seen_count`: not_provided
- `readiness_status`: not_provided
- `recommended_default_decision`: not_provided
- `persistence_status` or summary status: not_provided
- `council_recommended`: not_provided
- `positive_net_gap_count`: not_provided
- `no_trade_only`: not_provided
- `execution_policy`: not_provided
- `diagnostics_count`: not_provided
- `stale_assumption_wording_observed`: not_provided

### Bybit

- `adapter_id`: `live_bybit_mark_orderbook_gap_btcusdt`
- `samples_requested`: not_provided
- `samples_ok`: not_provided
- `samples_error`: not_provided
- `candidate_seen_count`: not_provided
- `readiness_status`: not_provided
- `recommended_default_decision`: not_provided
- `persistence_status` or summary status: not_provided
- `council_recommended`: not_provided
- `positive_net_gap_count`: not_provided
- `no_trade_only`: not_provided
- `execution_policy`: not_provided
- `diagnostics_count`: not_provided
- `stale_assumption_wording_observed`: not_provided

### OKX

- `adapter_id`: `live_okx_mark_orderbook_gap_btc_usdt_swap`
- `samples_requested`: not_provided
- `samples_ok`: not_provided
- `samples_error`: not_provided
- `candidate_seen_count`: not_provided
- `readiness_status`: not_provided
- `recommended_default_decision`: not_provided
- `persistence_status` or summary status: not_provided
- `council_recommended`: not_provided
- `positive_net_gap_count`: not_provided
- `no_trade_only`: not_provided
- `execution_policy`: not_provided
- `diagnostics_count`: not_provided
- `stale_assumption_wording_observed`: not_provided

## 4. Watch items

The following observations should be separated as watch items, not automatic failures:

- Bybit negative `data_age_ms` observation: not_provided in the placeholder result; if observed, keep it as a timestamp/clock-skew policy watch item.
- OKX negative `data_age_ms` observation: not_provided in the placeholder result; if observed, keep it as a timestamp/clock-skew policy watch item.
- OKX `index_price=None` observation: not_provided in the placeholder result; if observed, keep it as an OKX index/reference semantics watch item.
- Positive gross gap with negative estimated net gap: if observed, this can still be a normal no-edge `REJECT` outcome.

These watch items do not justify timestamp policy changes, OKX index endpoint implementation, alerts, Council auto-call, execution, or active strategy promotion in this PR.

## 5. Interpretation

- The intended user-local runs are post-refactor sampling pipeline smoke checks.
- The placeholder result supplied to Codex does not provide enough venue-level metrics to claim actual Binance / Bybit / OKX smoke success in this handoff.
- This document does not prove profitable edge.
- This document does not prove persistent edge.
- `REJECT`, `NO_PERSISTENT_EDGE`, and `council_recommended=false`, when present in actual user-local output, can be normal no-edge outcomes.
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

This PR intentionally adds only this handoff document and does not add generated JSON.

## 8. Rollback plan

Rollback path:

1. Revert this docs-only PR.
2. Remove `docs/pr_handoffs/mark_orderbook_gap_post_refactor_user_local_smoke_evidence_2026_06_05.md`.
3. No code/config/registry/runtime/parser/readiness/generated-data rollback is required.

## 9. Next PR candidates

- Timestamp / clock-skew policy planning
- OKX index/reference semantics planning
- Mark-Orderbook Gap multi-venue comparative summary
- 이후 후보: next experimental strategy planning
