# Spot-Futures Basis Bybit Orderbook Category Live-Shape Parser Follow-up v0

## 1. 작업 목적

이 문서는 `spot_futures_basis_v0`의 Bybit V5 orderbook live-shape parser 후속 수정 결과를 기록한다.

목적:

- 사용자 로컬 Bybit collect smoke에서 발견된 orderbook `category` echo 누락 문제를 mocked/unit tests로 재현한다.
- Bybit orderbook response body에 `category`가 없더라도 parser context상 expected category가 명확하면 fatal mismatch로 처리하지 않는다.
- Response body에 명시적으로 잘못된 `category`가 있는 경우 기존 mismatch `NEED_DATA` 정책을 유지한다.
- Adapter, registry/config, packet builder, readiness threshold, collect/sampling tools를 변경하지 않는다.
- `NO_TRADE_ONLY`를 유지한다.

## 2. 사용자 로컬 Bybit collect smoke NEED_DATA 원인

사용자 로컬 Bybit collect smoke 결과 요약:

- Bybit collect smoke reached OpportunityPacket save/validation.
- `adapter_id=live_bybit_spot_futures_basis_btcusdt`.
- `diagnostics_count=6`.
- `source_venue_id=bybit`.
- Spot/perp/candidate ids were Bybit-correct.
- `spot_observation_id=bybit_spot_btcusdt_spot_futures_basis`.
- `perp_observation_id=bybit_linear_btcusdt_perp_spot_futures_basis`.
- `candidate_id=bybit_btcusdt_spot_futures_basis_candidate`.
- `readiness_status=NEED_DATA`.
- `spot_required_missing_fields` included `spot_orderbook_category_mismatch`.
- `perp_required_missing_fields` included `linear_orderbook_category_mismatch`.
- Root cause is live Bybit V5 orderbook response not echoing `category` in response body, while parser expected `category` there.

## 3. 변경 파일

| File | Change |
| --- | --- |
| `src/market_data/parsers/spot_futures_basis.py` | Added an `allow_missing` category validation path and used it only for Bybit spot/linear orderbook payloads. |
| `tests/test_spot_futures_basis_bybit_mocked_parser.py` | Added mocked parser tests for missing orderbook category acceptance and explicit wrong-category rejection. |
| `tests/test_spot_futures_basis_bybit_adapter.py` | Added mocked adapter test for live-like orderbook payloads that omit category while preserving OK parser status and packet validation. |
| `docs/pr_handoffs/spot_futures_basis_bybit_orderbook_category_live_shape_followup_2026_06_05.md` | Added this handoff evidence document. |

## 4. Bybit orderbook category live-shape support summary

Implementation summary:

- Bybit ticker and instruments-info category validation remains strict.
- Bybit orderbook category validation now accepts a missing response-body `category` when the parser function context already defines the expected category.
- `parse_bybit_spot_observation(...)` treats missing orderbook category as accepted for expected `spot`.
- `parse_bybit_perp_observation(...)` treats missing orderbook category as accepted for expected `linear`.
- Missing orderbook category is recorded as an informational parser warning, not as a required missing field.
- Explicit wrong orderbook category still records `spot_orderbook_category_mismatch` or `linear_orderbook_category_mismatch` and returns `NEED_DATA`.

## 5. Parser category policy

Bybit parser category policy after this PR:

- Ticker payloads: category mismatch remains fatal parser data-quality evidence.
- Instruments-info payloads: category mismatch remains fatal parser data-quality evidence.
- Orderbook payloads: missing category echo is accepted because endpoint request params carry `category=spot` or `category=linear` at the adapter/diagnostics boundary.
- Orderbook payloads: explicit wrong category remains fatal and produces category mismatch required missing fields.
- Missing orderbook category does not make `parser_normalized_status` become `NEED_DATA`.
- Timestamp policy, latency policy, and readiness threshold policy are unchanged.

## 6. Tests added

Added mocked/unit coverage for:

- `test_bybit_spot_orderbook_missing_category_is_accepted`.
- `test_bybit_linear_orderbook_missing_category_is_accepted`.
- `test_bybit_orderbook_explicit_wrong_category_still_need_data`.
- `test_bybit_adapter_live_like_orderbook_without_category_builds_parser_ok_packet`.

The adapter test uses copied fixture payloads and removes category from orderbook response bodies only. It does not call live Bybit endpoints.

## 7. Explicitly not implemented

Not implemented in this PR:

- Live collect smoke 재실행 없음.
- `collect_market_data` 실행 없음.
- `sample_market_data` 실행 없음.
- Registry/config 변경 없음.
- Active strategy 변경 없음.
- Adapter behavior 변경 없음.
- Packet builder 변경 없음.
- Readiness threshold 변경 없음.
- Timestamp policy 구현 없음.
- Generated JSON 생성 없음.
- Private API 없음.
- Credentials 없음.
- Account/balance/position/order/cancel/withdraw/deposit/transfer 없음.
- Execution 없음.
- Alert 없음.
- Council auto-call 없음.
- Auto-trading 없음.
- OKX implementation/research 없음.

## 8. OKX deferred scope note

- 이번 `spot_futures_basis_v0` cycle은 Binance + Bybit까지만 진행한다.
- OKX는 future expansion으로 defer한다.
- This is scope control, not permanent rejection.
- 이번 PR에서는 OKX adapter/config/research/parser files를 만들지 않았다.

## 9. No-trade compliance

No-trade compliance 확인:

- Active strategy promotion 없음.
- `spot_futures_basis_v0` active 승격 없음.
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
- Generated JSON 파일 생성 없음.
- `NO_TRADE_ONLY` 유지.

## 10. Generated JSON commit 금지 확인

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- 이번 PR은 mocked/unit tests only이며 generated JSON을 추가하지 않음.
- Future Bybit collect/sampling output은 evidence 요약 후 삭제해야 함.

## 11. Rollback plan

Rollback plan:

1. Revert this PR commit.
2. Re-run targeted Bybit parser/adapter tests.
3. Re-run `python -m unittest discover -s tests`.
4. Confirm no generated JSON files are present in `data/market_samples/` or `data/generated_packets/`.
5. Confirm `spot_futures_basis_v0` remains non-active / `NO_TRADE_ONLY`.

## 12. 다음 PR 후보

다음 PR 후보:

- User-local public-read-only Bybit collect smoke retry after this parser follow-up.
- Bybit smoke evidence handoff summarizing parser status, candidate status, diagnostics, and generated JSON deletion.
- Bybit sampling follow-up only after collect smoke evidence is reviewed.
- OKX remains deferred for future expansion outside the current Binance + Bybit cycle.
