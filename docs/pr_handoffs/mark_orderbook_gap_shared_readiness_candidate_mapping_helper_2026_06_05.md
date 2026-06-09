# Mark-Orderbook Gap Shared Readiness Candidate Mapping Helper v0

## 1. 작업 목적

Binance / Bybit / OKX `mark_orderbook_gap_hunt_v0` adapters에서 반복되던 readiness output → `OpportunityCandidate` fields / `candidate.metrics` / warnings / required missing fields mapping을 작은 module-local helper로 정리한다.

이번 PR은 small implementation PR이며 behavior-equivalent refactor다. 이미 계산된 parser/readiness 결과를 기존 위치에 동일하게 복사/매핑하는 것이 목적이며, readiness 판단 기준이나 gap 계산은 변경하지 않는다.

## 2. 변경 파일

- `src/market_data/adapters/mark_orderbook_gap_hunt.py`
  - `_mark_orderbook_gap_candidate_readiness_fields(...)` helper를 추가했다.
  - Binance / Bybit / OKX candidate construction에서 중복 readiness/candidate mapping을 helper output으로 대체했다.
- `tests/test_mark_orderbook_gap_hunt_metadata_wording.py`
  - PR #118 regression safety net을 유지하면서 helper refactor 이후 candidate/readiness mapping fields, warnings, parser normalized status가 동일하게 보존되는지 추가 검증했다.
- `docs/pr_handoffs/mark_orderbook_gap_shared_readiness_candidate_mapping_helper_2026_06_05.md`
  - 이 handoff evidence 문서다.

No parser, readiness, config, registry, generated-data file is changed.

## 3. helper로 공통화한 mapping 항목

`src/market_data/adapters/mark_orderbook_gap_hunt.py` 내부에 새 source file 없이 module-local helper를 추가했다.

공통화한 mapping 항목:

- `readiness_status`
- `readiness_pass`
- `recommended_default_decision`
- `required_missing_fields`
- readiness `warnings`
- `metrics.readiness_status`
- `metrics.recommended_default_decision`
- `metrics.readiness_pass`
- `metrics.comparability_pass`
- `metrics.fee_slippage_buffer_pct`
- `metrics.estimated_net_gap_pct`
- `metrics.max_observed_gap_pct`
- `metrics.parser_normalized_status`
- candidate gap field copies from already-computed readiness metrics:
  - `gross_gap_pct`
  - `estimated_net_gap_pct`
  - `long_gap_pct`
  - `short_gap_pct`
  - `liquidity_pass`
  - `freshness_pass`
  - `gap_pass`

Helper scope:

- The helper reads already-computed `readiness` and `parser_output` dictionaries.
- The helper does not call the readiness helper.
- The helper does not compute new gaps or thresholds.
- The helper does not alter warnings, required missing fields, or decisions.

## 4. behavior equivalence 설명

This refactor is intended to be runtime-behavior equivalent:

- Existing parser output construction is unchanged.
- Existing readiness helper invocation is unchanged.
- Existing readiness thresholds are unchanged.
- Existing readiness warnings generation is unchanged.
- Existing gross/net gap values are copied from the same readiness metrics as before.
- Existing candidate metrics keys and values are preserved.
- Existing `candidate.required_missing_fields` is preserved.
- Existing candidate assumptions are preserved.
- Existing candidate warning extensions are preserved.
- Existing diagnostics helper behavior is unchanged.
- Existing metadata helper behavior is unchanged.
- Existing HTTP request paths, params, and fetch order are unchanged.
- Existing timestamp/data_age behavior is unchanged.
- OKX `index_price=None` remains unchanged.

## 5. venue-specific boundary 유지 내용

The helper intentionally does not hide or change venue-specific semantics:

- Binance keeps `venue_id="binance"`, `parser_mode="binance_usdm"`, `BTCUSDT`, and base-asset size units.
- Bybit keeps `venue_id="bybit"`, `category="linear"`, `parser_mode="bybit_linear"`, `BTCUSDT`, `retCode` / `retMsg` diagnostics, `funding_interval=480` warnings, and negative `data_age_ms` pass-through.
- OKX keeps `venue_id="okx"`, `instType="SWAP"`, `instId="BTC-USDT-SWAP"`, `parser_mode="okx_swap"`, `code` / `msg` diagnostics, `index_price=None`, contract size units, contract value/multiplier/lot/min size fields, and negative `data_age_ms` pass-through.
- `NO_TRADE_ONLY`, experimental, non-active, and analysis-only metadata/assumptions remain unchanged.

## 6. 테스트 결과

Commands run by Codex:

- `python -m unittest tests.test_mark_orderbook_gap_hunt_metadata_wording`
  - Result: passed, `Ran 4 tests`, `OK`.
- `python -m unittest discover -s tests`
  - Result: passed, `Ran 343 tests`, `OK`.

## 7. No-trade compliance

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
- Parser behavior change: no
- Readiness threshold change: no
- Timestamp policy implementation: no
- OKX index endpoint implementation: no
- Diagnostics helper change: no
- Metadata helper change: no
- Generated JSON commit: no
- `NO_TRADE_ONLY` preserved: yes

## 8. generated JSON commit 금지 확인

Generated packet/sampling files remain smoke artifacts only and must not be committed:

- `data/market_samples/*.json`
- `data/generated_packets/*.json`

This PR must include no generated JSON files. Final verification should confirm generated JSON is not staged or committed.

## 9. rollback plan

Rollback path:

1. Revert this PR.
2. Restore inline candidate/readiness mapping in `src/market_data/adapters/mark_orderbook_gap_hunt.py` from the previous main commit.
3. Remove the added mapping assertions from `tests/test_mark_orderbook_gap_hunt_metadata_wording.py`.
4. Remove `docs/pr_handoffs/mark_orderbook_gap_shared_readiness_candidate_mapping_helper_2026_06_05.md`.
5. Re-run `python -m unittest discover -s tests`.

No parser/readiness/config/registry/generated-data/Council/alert/execution rollback is required.

## 10. 다음 PR 후보

- PR 5: user-local smoke evidence update
- 이후 별도 planning: timestamp/clock-skew policy
- 이후 별도 planning: OKX index/reference semantics
- 이후 후보: multi-venue comparative summary
