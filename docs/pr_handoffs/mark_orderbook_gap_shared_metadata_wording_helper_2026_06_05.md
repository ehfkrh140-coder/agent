# Mark-Orderbook Gap Shared Metadata Wording Helper v0

## 1. 작업 목적

Binance / Bybit / OKX `mark_orderbook_gap_hunt_v0` adapters에서 반복되던 `NO_TRADE_ONLY`, experimental, non-active, analysis-only metadata와 assumptions wording을 작은 module-local helper/constants로 정리한다.

이번 PR은 small implementation PR이며 mocked/unit-test first로 진행했다. 목적은 문구와 metadata construction 중복 제거이며, parser/readiness/sampling/runtime 의미 변경은 하지 않는다.

## 2. 변경 파일

- `src/market_data/adapters/mark_orderbook_gap_hunt.py`
  - module-local constants/helper로 common no-trade metadata와 assumptions wording을 공통화했다.
  - Binance / Bybit / OKX venue-specific fields는 각 adapter call site에 남겼다.
- `tests/test_mark_orderbook_gap_hunt_metadata_wording.py`
  - mocked unit tests를 추가해 common metadata/assumptions 유지, stale PR-stage wording 부재, venue-specific boundary 보존, OKX `index_price=None`, negative `data_age_ms`, readiness mapping equivalence를 검증했다.
- `docs/pr_handoffs/mark_orderbook_gap_shared_metadata_wording_helper_2026_06_05.md`
  - 이 handoff evidence 문서다.

## 3. helper/constants로 공통화한 항목

`src/market_data/adapters/mark_orderbook_gap_hunt.py` 내부에 새 source file 없이 module-local constants/helper를 추가했다.

공통화한 metadata 의미:

- `experimental_strategy=true`
- `non_active_strategy=true`
- `no_trade_only=true`
- `execution_policy="NO_TRADE_ONLY"`

공통화한 packet-level assumptions wording:

- `public no-key endpoints only`
- `analysis-only packet`
- `adapter may be registered but remains disabled/experimental/non-active unless explicitly enabled in config`
- `sampling integration is separate from packet generation`
- `timestamp/data_age policy unchanged`
- `no private API`
- `no trading behavior`

공통화한 candidate-level assumptions wording:

- `mark price is not executable`
- `WATCH is analysis-only`
- `no private API`
- `no trading behavior`

Helper scope:

- `_mark_orderbook_gap_adapter_metadata(...)` builds only common adapter metadata plus caller-provided venue fields.
- `_mark_orderbook_gap_extension_assumptions()` returns a fresh list of packet-level assumptions.
- `_mark_orderbook_gap_candidate_assumptions()` returns a fresh list of candidate-level assumptions.

## 4. venue-specific으로 남긴 항목

The helper intentionally does not hide venue-specific market-data, parser, or instrument semantics.

Venue-specific fields still remain at the adapter call sites or existing parser/readiness paths:

- Binance adapter id, venue id, endpoints, `BTCUSDT` symbol, `binance_usdm` parser mode.
- Bybit adapter id, venue id, `category=linear`, endpoints, `BTCUSDT` symbol, `bybit_linear` parser mode.
- OKX adapter id, venue id, `instType=SWAP`, `instId=BTC-USDT-SWAP`, endpoints, `okx_swap` parser mode.
- OKX `index_price=None` semantics.
- Bybit/OKX negative `data_age_ms` timestamp/clock-skew watch semantics.
- Size units such as `base_asset` vs `contracts`.
- Contract value, lot size, min notional, funding fields, and venue-specific warnings.

## 5. behavior equivalence 설명

This refactor is intended to be runtime-behavior equivalent:

- Existing adapter metadata values are preserved for all three venues.
- Existing assumptions text is preserved and returned as lists.
- Parser output construction is unchanged.
- Readiness helper invocation and thresholds are unchanged.
- Candidate metrics mapping is unchanged.
- Diagnostics builder behavior is unchanged.
- No timestamp policy was implemented.
- No OKX index endpoint was implemented.
- No common base adapter was implemented.
- No config/registry/active strategy behavior changed.

The new tests verify that:

- Binance / Bybit / OKX `adapter_metadata.no_trade_only` remains `true`.
- `execution_policy` remains `NO_TRADE_ONLY`.
- `experimental_strategy` and `non_active_strategy` remain `true`.
- Required assumptions remain present.
- Stale PR-stage wording does not reappear.
- OKX `index_price=None` is not filled or changed by the helper.
- Negative `data_age_ms` can still pass through without clamp/normalization.
- Candidate `readiness_status` and `recommended_default_decision` still mirror readiness output.

## 6. 테스트 결과

Commands run by Codex:

- `python -m unittest tests.test_mark_orderbook_gap_hunt_metadata_wording`
  - Result: passed, `Ran 2 tests`, `OK`.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_metadata_wording tests.test_mark_orderbook_gap_hunt_binance_adapter tests.test_mark_orderbook_gap_hunt_bybit_adapter tests.test_mark_orderbook_gap_hunt_okx_adapter`
  - Result: passed, `Ran 36 tests`, `OK`.
- `python -m unittest discover -s tests`
  - Result: passed, `Ran 341 tests`, `OK`.

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
2. Restore inline metadata/assumptions construction in `src/market_data/adapters/mark_orderbook_gap_hunt.py` from the previous main commit.
3. Remove `tests/test_mark_orderbook_gap_hunt_metadata_wording.py`.
4. Remove `docs/pr_handoffs/mark_orderbook_gap_shared_metadata_wording_helper_2026_06_05.md`.
5. Re-run `python -m unittest discover -s tests`.

No config/registry/generated-data/runtime/Council/alert/execution rollback is required.

## 10. 다음 PR 후보

- PR 2: shared diagnostics builder helper
- PR 3: shared readiness/candidate mapping helper
- PR 4: venue-specific adapter regression tests
- PR 5: user-local smoke evidence update
