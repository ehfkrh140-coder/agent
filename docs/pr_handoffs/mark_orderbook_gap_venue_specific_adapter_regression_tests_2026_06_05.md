# Mark-Orderbook Gap Venue-Specific Adapter Regression Tests v0

## 1. 작업 목적

Binance / Bybit / OKX `mark_orderbook_gap_hunt_v0` adapters의 venue-specific boundary를 mocked/unit regression tests로 더 강하게 고정한다.

이번 PR은 test-first / regression-test PR이며 runtime behavior를 변경하지 않는다. PR #116 metadata/assumptions helper와 PR #117 diagnostics builder helper 이후, 다음 후보인 readiness/candidate mapping helper를 구현하기 전에 안전망을 강화하는 목적이다.

## 2. 변경 파일

- `tests/test_mark_orderbook_gap_hunt_metadata_wording.py`
  - venue-specific boundary와 candidate/readiness mapping safety net을 강화하는 mocked unit test를 추가했다.
- `docs/pr_handoffs/mark_orderbook_gap_venue_specific_adapter_regression_tests_2026_06_05.md`
  - 이 handoff evidence 문서다.

No `src/`, parser, readiness, config, registry, runtime, generated-data file is changed.

## 3. 강화한 regression test 항목

강화한 test coverage:

- Binance boundary:
  - `venue_id="binance"`
  - `parser_mode="binance_usdm"`
  - `BTCUSDT` symbol
  - endpoint / params / parser_stage diagnostics shape
  - `diagnostics_count=3`
  - `bid_size_unit="base_asset"` / `ask_size_unit="base_asset"`
  - `no_trade_only=true`
  - `execution_policy="NO_TRADE_ONLY"`
  - readiness/candidate mapping fields
- Bybit boundary:
  - `venue_id="bybit"`
  - `category="linear"`
  - `parser_mode="bybit_linear"`
  - `BTCUSDT` symbol
  - endpoint / params / parser_stage diagnostics shape
  - `diagnostics_count=3`
  - `retCode` / `retMsg` diagnostics
  - `funding_interval=480` warning
  - negative `data_age_ms` pass-through without clamp/normalization
  - `no_trade_only=true`
  - `execution_policy="NO_TRADE_ONLY"`
  - readiness/candidate mapping fields
- OKX boundary:
  - `venue_id="okx"`
  - `instType="SWAP"`
  - `instId="BTC-USDT-SWAP"`
  - `parser_mode="okx_swap"`
  - endpoint / params / parser_stage diagnostics shape
  - `diagnostics_count=3`
  - `code` / `msg` diagnostics
  - `index_price=None` remains unset
  - `bid_size_unit="contracts"` / `ask_size_unit="contracts"`
  - `contract_value`, `contract_multiplier`, `lot_size`, `min_order_size`
  - negative `data_age_ms` pass-through without clamp/normalization
  - `no_trade_only=true`
  - `execution_policy="NO_TRADE_ONLY"`
  - readiness/candidate mapping fields
- Common no-trade / wording:
  - assumptions include `public no-key endpoints only`
  - assumptions include `analysis-only packet`
  - assumptions include `no private API`
  - assumptions include `no trading behavior`
  - stale PR-stage wording remains absent

## 4. venue-specific boundary 고정 내용

This PR keeps venue-specific semantics visible and test-protected:

- Binance keeps Binance USDⓈ-M parser mode and `BTCUSDT` symbol handling.
- Binance size units remain base asset quantities.
- Bybit keeps V5 `category=linear` request params and `retCode` / `retMsg` diagnostics.
- Bybit `funding_interval=480` remains visible in parser/readiness warnings.
- Bybit negative `data_age_ms` remains a timestamp/clock-skew watch item and is not normalized by adapter helpers.
- OKX keeps `instType=SWAP`, `instId=BTC-USDT-SWAP`, and OKX response `code` / `msg` diagnostics.
- OKX `index_price=None` remains unset and is not synthesized by helpers.
- OKX swap sizes remain contract units, with contract value/multiplier/lot/min size preserved.
- OKX negative `data_age_ms` remains a timestamp/clock-skew watch item and is not normalized by adapter helpers.

## 5. readiness/candidate mapping helper 전 안전망 설명

This PR does not implement a readiness/candidate mapping helper. It adds regression tests so a future mapping-helper PR must preserve existing semantics for:

- `candidate.metrics.readiness_status`
- `candidate.metrics.recommended_default_decision`
- `candidate.metrics.readiness_pass`
- `candidate.gross_gap_pct`
- `candidate.estimated_net_gap_pct`
- `candidate.required_missing_fields`
- `candidate.assumptions`
- readiness warnings, including venue-specific warnings such as Bybit `funding_interval=480`

This makes the next commonization PR safer by turning current per-venue behavior into explicit unit-test expectations.

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
- Source/runtime behavior change: no
- Parser behavior change: no
- Readiness threshold change: no
- Timestamp policy implementation: no
- OKX index endpoint implementation: no
- Readiness/candidate mapping helper implementation: no
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
2. Remove the added regression assertions from `tests/test_mark_orderbook_gap_hunt_metadata_wording.py`.
3. Remove `docs/pr_handoffs/mark_orderbook_gap_venue_specific_adapter_regression_tests_2026_06_05.md`.
4. Re-run `python -m unittest discover -s tests`.

No source/runtime/config/registry/generated-data/Council/alert/execution rollback is required.

## 10. 다음 PR 후보

- PR 3: shared readiness/candidate mapping helper
- PR 5: user-local smoke evidence update
- 이후 별도 planning: timestamp/clock-skew policy
- 이후 별도 planning: OKX index/reference semantics
