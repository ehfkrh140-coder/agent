# Depth / VWAP Pure Helper Implementation v0

## 1. 작업 목적

이 문서는 Depth/VWAP Planning v0 이후 첫 bounded implementation sprint를 기록한다.

Purpose:

- Strategy-common VWAP-style estimate pure helper를 추가했다.
- Helper는 orderbook depth levels와 `target_size` 또는 `target_notional`을 받아 ask/bid side VWAP-style estimate를 계산한다.
- 아직 어떤 strategy에도 연결하지 않는다.
- Adapter, parser, readiness, packet builder, sampling, dashboard, config/registry에는 연결하지 않는다.
- `NO_TRADE_ONLY`를 유지한다.
- Active strategy는 `cross_exchange_spot_spread_v1`로 유지한다.

This implementation is analysis-only and does not imply execution permission, trading signal, account-specific fill feasibility, alerting, or Council auto-call.

## 2. 변경 파일

Changed files:

- `src/market_data/depth_vwap.py`
- `tests/test_depth_vwap.py`
- `docs/pr_handoffs/depth_vwap_pure_helper_implementation_2026_06_05.md`

## 3. 구현 요약

Implemented pure helper functions:

- `calculate_vwap_for_size(levels, target_size, *, side)`
  - Consumes depth levels until target size is filled or public/mock depth is exhausted.
  - Supports partial fill on the final level.
  - Returns insufficient-depth context instead of raising for invalid/unfilled inputs.
- `calculate_vwap_for_notional(levels, target_notional, *, side)`
  - Consumes depth levels until target quote notional is filled or public/mock depth is exhausted.
  - Supports partial notional fill on the final level.
  - Computes filled size as `filled_notional / price` for the consumed notional.
- `summarize_depth_vwap(levels, *, target_size=None, target_notional=None, side)`
  - Dispatches to size or notional helper.
  - Uses size path if both size and notional are supplied, and records a warning that notional was ignored.
  - Returns a warning result if no target is supplied.

Output fields include:

- `side`
- `target_size`
- `target_notional`
- `filled_size`
- `filled_notional`
- `vwap`
- `best_price`
- `slippage_pct`
- `depth_coverage_pct`
- `insufficient_depth`
- `levels_consumed`
- `levels_available`
- `level_sort_assumption`
- `warnings`

Implementation notes:

- Uses `Decimal` for calculations.
- Accepts list/tuple levels such as `[["100", "1"], ["101", "2"]]`.
- Accepts numeric list/tuple levels such as `[[100, 1], [101, 2]]`.
- Accepts dict levels such as `{"price": "100", "quantity": "1"}`.
- Supports `side="ask"` and `side="bid"`.
- Assumes input depth is already best-to-worse and records ordering warnings if ask prices decrease or bid prices increase.
- Does not sort, fetch, persist, or integrate with strategy behavior.

## 4. 쉬운 예시

Example:

| ask price | quantity | consumed cost |
| ---: | ---: | ---: |
| 100 | 1 | 100 |
| 101 | 2 | 202 |
| 102 | 2 | 204 |

For `target_size=5`:

```text
filled_notional = 100 + 202 + 204 = 506
filled_size = 5
vwap = 506 / 5 = 101.2
```

Interpretation:

- Top-of-book ask만 보면 100에 5개를 모두 살 수 있는 것처럼 과대평가할 수 있다.
- Depth를 반영한 VWAP-style estimate는 101.2다.
- 이 값은 public/mock depth context이며 trading signal 또는 execution permission이 아니다.

## 5. Tests added

Added `tests/test_depth_vwap.py` with more than 15 unit tests covering:

- Ask VWAP fully filled at first level.
- Ask VWAP consumes multiple levels.
- Ask VWAP partial fill on last level.
- Bid VWAP consumes multiple levels.
- Bid VWAP partial fill on last level.
- Insufficient ask depth.
- Insufficient bid depth.
- Target-notional ask calculation.
- Target-notional bid calculation.
- Empty levels returns warning and no exception.
- Invalid price/quantity returns warning and no exception.
- Zero/negative price/quantity returns warning and no exception.
- Dict input shape works.
- String decimal input works.
- Unsupported side returns warning and no exception.
- Ask slippage percentage is non-negative.
- Bid slippage percentage is non-negative.
- No file/network/private/credential/execution import or behavior structural guardrail.
- Generated JSON path is not created or referenced.
- Top-of-book example gives `vwap=101.2`.
- `summarize_depth_vwap` size path records ignored-notional warning.
- `summarize_depth_vwap` missing target records warning.

Test guardrails:

- Tests do not call live endpoints.
- Tests do not create `data/generated_packets` or `data/market_samples` files.
- Tests do not require private API.
- Tests verify the pure module has no `requests` / `aiohttp` / `httpx` style imports.
- Tests verify output dict keys do not include execution/order/private credential fields.

## 6. Explicitly not integrated

Explicitly not integrated in this PR:

- Adapter 연결 없음.
- Parser 연결 없음.
- Readiness behavior 변경 없음.
- Packet builder 변경 없음.
- Sampling 변경 없음.
- Dashboard 변경 없음.
- Config/registry 변경 없음.
- Live endpoint 호출 없음.
- Strategy-specific integration 없음.
- Council runtime integration 없음.
- Alert integration 없음.
- Execution integration 없음.

## 7. No-trade compliance

No-trade compliance 확인:

- Active strategy promotion 없음.
- Experimental strategy active 승격 없음.
- Private API 없음.
- Credentials 없음.
- Account/balance/position lookup 없음.
- Order/cancel 없음.
- Withdrawal/deposit/transfer 없음.
- Auto-trading 없음.
- Council auto-call 없음.
- Alert 없음.
- Execution 없음.
- Config/registry 변경 없음.
- Source/runtime behavior 변경 없음.

## 8. Generated JSON commit 금지

Generated JSON policy 확인:

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- Tests do not create generated JSON.
- 이번 PR에는 generated JSON을 추가하지 않음.

## 9. Rollback plan

Rollback plan:

1. Revert this PR.
2. Remove `src/market_data/depth_vwap.py`.
3. Remove `tests/test_depth_vwap.py`.
4. Remove `docs/pr_handoffs/depth_vwap_pure_helper_implementation_2026_06_05.md`.
5. No config/runtime/generated-data rollback is needed.
6. Re-run required validation commands if rollback evidence is requested.

## 10. Next PR candidates

다음 PR 후보:

1. Depth/VWAP mocked fixture planning.
2. Add VWAP diagnostics/context fields to packet/candidate extensions, behavior unchanged.
3. Sampling summary context support, behavior unchanged.
4. Dashboard depth/VWAP policy status update.
5. Next Experimental Strategy Selection v0.
