# Mark-Orderbook Gap Shared Diagnostics Builder Helper v0

## 1. 작업 목적

Binance / Bybit / OKX `mark_orderbook_gap_hunt_v0` adapters에서 반복되던 public HTTP diagnostics envelope construction을 작은 module-local helper로 정리한다.

이번 PR은 small implementation PR이며 mocked/unit-test first로 진행했다. 목적은 diagnostics dict construction 중복 제거이며, HTTP request 실행, endpoint/params/parser stage, safe response preview 정책, parser/readiness/sampling/runtime 의미 변경은 하지 않는다.

## 2. 변경 파일

- `src/market_data/adapters/mark_orderbook_gap_hunt.py`
  - module-local diagnostics helper를 추가해 common public GET diagnostics envelope를 공통화했다.
  - Binance / Bybit / OKX `_public_get`의 HTTP request 순서, endpoints, params, parser stages는 변경하지 않았다.
  - Bybit `retCode` / `retMsg`, OKX `code` / `msg`는 venue-specific inline handling으로 유지했다.
- `tests/test_mark_orderbook_gap_hunt_metadata_wording.py`
  - mocked unit tests를 보강해 diagnostics count, common fields, venue-specific endpoint/params/parser_stage, Bybit/OKX status fields, safe response preview, no-trade metadata, OKX `index_price=None`, negative `data_age_ms`, readiness mapping equivalence를 검증했다.
- `docs/pr_handoffs/mark_orderbook_gap_shared_diagnostics_builder_helper_2026_06_05.md`
  - 이 handoff evidence 문서다.

## 3. helper로 공통화한 diagnostics 항목

`src/market_data/adapters/mark_orderbook_gap_hunt.py` 내부에 새 source file 없이 module-local helper를 추가했다.

공통화한 request diagnostics envelope:

- `endpoint`
- `params`
- `parser_stage`

공통화한 response diagnostics fields:

- `http_status`
- `safe_response_preview`
- `elapsed_ms`
- `url`

Helper scope:

- `_mark_orderbook_gap_public_get_diagnostic(...)` builds only the initial public GET diagnostic envelope.
- `_mark_orderbook_gap_add_response_diagnostic_fields(...)` attaches only common response diagnostic fields from an already-fetched response.
- The helper does not execute HTTP requests.
- The helper does not change endpoints, params, parser stages, response preview policy, or venue-specific status fields.

## 4. venue-specific으로 남긴 항목

The helper intentionally does not hide venue-specific response semantics.

Venue-specific fields still remain at each adapter `_public_get` call site:

- Binance-specific response/status behavior remains unchanged.
- Bybit `retCode` / `retMsg` extraction remains inline in the Bybit adapter.
- OKX `code` / `msg` extraction remains inline in the OKX adapter.
- Binance endpoints and `BTCUSDT` params remain venue-specific.
- Bybit V5 `category=linear` endpoints and params remain venue-specific.
- OKX `instType=SWAP`, `instId=BTC-USDT-SWAP`, and `sz` params remain venue-specific.
- OKX `index_price=None` semantics remain unchanged.
- Bybit/OKX negative `data_age_ms` timestamp/clock-skew watch semantics remain unchanged.
- Size units, contract value, lot size, min notional, funding fields, and venue-specific warnings remain outside this helper.

## 5. behavior equivalence 설명

This refactor is intended to be runtime-behavior equivalent:

- Existing HTTP request execution remains inside each adapter `_public_get` method.
- Existing fetch order is unchanged.
- Existing endpoint paths are unchanged.
- Existing request params are unchanged.
- Existing parser stage names are unchanged.
- Existing `safe_response_preview` behavior is preserved: use `response.safe_response_preview` when present, otherwise fall back to the same `_safe_preview(data)` helper.
- Existing `elapsed_ms`, `http_status`, and `url` values are preserved.
- Existing Bybit `retCode` / `retMsg` and OKX `code` / `msg` diagnostics are preserved.
- Parser output construction is unchanged.
- Readiness helper invocation and thresholds are unchanged.
- Candidate metrics mapping is unchanged.
- Metadata wording helper from PR #116 remains unchanged.
- No timestamp policy was implemented.
- No OKX index endpoint was implemented.
- No common base adapter was implemented.
- No candidate/readiness mapping helper was implemented.
- No config/registry/active strategy behavior changed.

The tests verify that:

- Binance / Bybit / OKX `diagnostics` length remains `3` for the mocked success path.
- Each diagnostics entry keeps `endpoint`, `params`, `parser_stage`, `http_status`, `safe_response_preview`, `elapsed_ms`, and `url`.
- Venue-specific endpoint and params are not changed by the helper.
- Bybit diagnostics keep `retCode` / `retMsg`.
- OKX diagnostics keep `code` / `msg`.
- `no_trade_only` and `execution_policy` metadata remain preserved.
- OKX `index_price=None` is not filled or changed by the helper.
- Negative `data_age_ms` can still pass through without clamp/normalization.
- Candidate `readiness_status` and `recommended_default_decision` still mirror readiness output.

## 6. 테스트 결과

Commands run by Codex:

- `python -m unittest tests.test_mark_orderbook_gap_hunt_metadata_wording`
  - Result: passed, `Ran 3 tests`, `OK`.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_metadata_wording tests.test_mark_orderbook_gap_hunt_binance_adapter tests.test_mark_orderbook_gap_hunt_bybit_adapter tests.test_mark_orderbook_gap_hunt_okx_adapter`
  - Result: passed, `Ran 37 tests`, `OK`.
- `python -m unittest discover -s tests`
  - Result: passed, `Ran 342 tests`, `OK`.

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
- Candidate/readiness mapping helper: no
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
2. Restore inline diagnostics envelope / response field construction in `src/market_data/adapters/mark_orderbook_gap_hunt.py` from the previous main commit.
3. Remove the added diagnostics assertions from `tests/test_mark_orderbook_gap_hunt_metadata_wording.py`.
4. Remove `docs/pr_handoffs/mark_orderbook_gap_shared_diagnostics_builder_helper_2026_06_05.md`.
5. Re-run `python -m unittest discover -s tests`.

No config/registry/generated-data/runtime/Council/alert/execution rollback is required.

## 10. 다음 PR 후보

- PR 3: shared readiness/candidate mapping helper
- PR 4: venue-specific adapter regression tests
- PR 5: user-local smoke evidence update
- 이후 별도 planning: timestamp/clock-skew policy
- 이후 별도 planning: OKX index/reference semantics
