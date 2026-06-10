# Spot-Futures Basis Binance Spot exchangeInfo min_notional Live-Shape Parser Follow-up v0

## 1. 작업 목적

- `spot_futures_basis_v0`의 user-local public-read-only collect smoke evidence에서 발견된 Binance Spot `exchangeInfo` min_notional metadata normalization gap을 parser/readiness metadata 레벨에서 보완한다.
- 이번 PR은 `spot_min_notional_missing`으로 인해 Spot parser가 `NEED_DATA`가 된 원인을 mocked/unit-test 경로에서 재현하고, live-like `NOTIONAL` filter shape를 parser가 처리하도록 확장한다.
- readiness `required_missing_fields`에 `spot_spot_min_notional_missing`처럼 중복 prefix가 붙는 naming issue를 정리한다.
- live endpoint 호출, collect smoke 재실행, sampling support, config/registry 변경, active strategy 변경, runtime behavior 변경은 하지 않는다.
- `spot_futures_basis_v0`는 계속 proposed / experimental / non-active / `NO_TRADE_ONLY` 상태로 유지한다.

## 2. 사용자 로컬 collect smoke에서 발견된 NEED_DATA 원인

- 이전 user-local collect smoke는 성공적으로 `OpportunityPacket` 저장까지 도달했다.
- Evidence summary에서 `readiness_status=NEED_DATA`가 기록되었다.
- Spot observation은 `spot_parser_status=NEED_DATA`였다.
- Spot parser missing fields는 `spot_required_missing_fields=['spot_min_notional_missing']`였다.
- Candidate-level missing fields에는 `spot_spot_min_notional_missing`가 포함되어 있었다.
- 추정 root cause는 두 가지다.
  - Binance Spot `exchangeInfo` live filter shape가 mocked fixture의 `MIN_NOTIONAL.minNotional` 형태와 달리 `NOTIONAL.minNotional` 또는 `NOTIONAL.notional` 형태로 들어올 수 있는데, 기존 parser가 Spot min_notional extraction에서 이를 충분히 커버하지 못했다.
  - readiness layer가 parser missing field를 candidate/readiness missing field로 전파하면서 이미 `spot_` prefix가 있는 field에 다시 `spot_` prefix를 붙였다.
- 이번 PR은 위 두 metadata issue만 수정하며, profitability / persistent edge 판단 또는 readiness threshold를 변경하지 않는다.

## 3. 변경 파일

| 파일 | 변경 요약 |
| --- | --- |
| `src/market_data/parsers/spot_futures_basis.py` | Spot `exchangeInfo` min_notional extraction에서 `MIN_NOTIONAL` 및 `NOTIONAL` filter type과 `minNotional` / `notional` aliases를 지원하도록 helper를 추가했다. |
| `src/strategy/spot_futures_basis_readiness.py` | parser missing field 전파 시 이미 `spot_` 또는 `perp_` prefix가 있으면 중복 prefix를 붙이지 않도록 정리했다. |
| `tests/test_spot_futures_basis_mocked_parser.py` | live-like `NOTIONAL` filter와 min_notional alias matrix를 mocked parser unit test로 검증했다. |
| `tests/test_spot_futures_basis_mocked_readiness.py` | `spot_spot_*` 중복 prefix가 더 이상 생성되지 않는지 readiness unit test로 검증했다. |
| `tests/test_spot_futures_basis_collect_path.py` | live-like `NOTIONAL` Spot `exchangeInfo`가 parser → readiness → packet builder → `OpportunityPacketBuilder` validation path에서 `spot_min_notional_missing` 없이 통과하는지 검증했다. |
| `docs/pr_handoffs/spot_futures_basis_spot_exchange_info_min_notional_live_shape_followup_2026_06_05.md` | 이번 metadata follow-up의 목적, 원인, 변경 사항, 테스트, no-trade 및 rollback 근거를 기록했다. |

## 4. Spot exchangeInfo min_notional live-shape support summary

- Spot parser는 이제 Binance Spot symbol filters에서 다음 min_notional shapes를 지원한다.
  - `MIN_NOTIONAL.minNotional`
  - `MIN_NOTIONAL.notional`
  - `NOTIONAL.minNotional`
  - `NOTIONAL.notional`
- `PRICE_FILTER.tickSize` 및 `LOT_SIZE.stepSize` 처리는 기존 behavior를 유지한다.
- min_notional 값이 발견되면 normalized observation의 `min_notional`에 float로 저장된다.
- min_notional 값이 발견되면 `spot_min_notional_missing`은 `required_missing_fields`에 추가되지 않는다.
- required missing fields가 비어 있으면 `parser_normalized_status`는 `OK`를 유지한다.
- Futures parser는 기존 `MIN_NOTIONAL` filter path를 유지하면서 동일 alias extraction helper만 사용하므로 기존 futures mocked fixture behavior를 보존한다.

## 5. Readiness missing-field naming cleanup

- readiness parser missing propagation은 이제 source missing field가 이미 `spot_` 또는 `perp_` prefix로 시작하면 그대로 보존한다.
- `spot_min_notional_missing`은 candidate/readiness `required_missing_fields`에서도 `spot_min_notional_missing`으로 유지된다.
- `spot_spot_min_notional_missing` 및 `spot_spot_ask_missing` 같은 중복 prefix field는 더 이상 생성되지 않아야 한다.
- prefix가 없는 parser missing field는 기존처럼 observation prefix를 붙여 source를 명확히 표시한다.

## 6. Tests added

- `test_parse_binance_spot_observation_accepts_live_like_notional_filter`
  - mocked Spot fixture의 `MIN_NOTIONAL` filter를 inline copy에서 live-like `NOTIONAL.minNotional` filter로 교체한다.
  - `parser_normalized_status == "OK"`, `required_missing_fields == []`, `min_notional` extraction 성공, `spot_min_notional_missing` 부재를 검증한다.
- `test_parse_binance_spot_observation_accepts_min_notional_and_notional_aliases`
  - `MIN_NOTIONAL.minNotional`, `MIN_NOTIONAL.notional`, `NOTIONAL.minNotional`, `NOTIONAL.notional` alias matrix를 subTest로 검증한다.
- `test_readiness_does_not_double_prefix_spot_missing_fields`
  - parser output에 `spot_min_notional_missing`이 있을 때 readiness가 이를 중복 prefix 없이 전파하는지 검증한다.
- 기존 `test_parser_missing_fields_need_data`도 `spot_spot_ask_missing` 대신 `spot_ask_missing` 보존을 검증하도록 업데이트했다.
- `test_collect_path_live_shape_notional_packet_no_need_data_from_min_notional`
  - live-like `NOTIONAL` Spot exchangeInfo를 사용해 parser → readiness → packet builder → `OpportunityPacketBuilder` validation path를 mocked/unit-test로 검증한다.
  - `spot_min_notional_missing` 및 `spot_spot_min_notional_missing`이 없고, readiness가 min_notional missing 때문에 `NEED_DATA`가 되지 않음을 확인한다.

## 7. Explicitly not implemented

- live collect smoke 재실행 없음.
- `tools/collect_market_data.py` 변경 없음.
- `tools/sample_market_data.py` 변경 없음.
- registry/config 변경 없음.
- active strategy 변경 없음.
- timestamp policy 구현 없음.
- readiness threshold 변경 없음.
- adapter behavior 변경 없음.
- packet builder behavior 변경 없음.
- generated JSON 생성 없음.
- private API 없음.
- credentials 없음.
- account/balance/position/order/cancel/withdraw/deposit/transfer 없음.
- execution 없음.
- alert 없음.
- Council auto-call 없음.
- auto-trading 없음.

## 8. No-trade compliance

- active strategy promotion 없음.
- `spot_futures_basis_v0` active 승격 없음.
- `enabled=false` 유지.
- private API 없음.
- credentials 없음.
- account/balance/position lookup 없음.
- order/cancel 없음.
- withdrawal/deposit/transfer 없음.
- auto-trading 없음.
- Council auto-call 없음.
- alert 없음.
- execution 없음.
- generated JSON 파일 생성 없음.
- `NO_TRADE_ONLY` 유지.

## 9. Generated JSON commit 금지 확인

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지다.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지다.
- 이번 PR에는 `data/market_samples` 또는 `data/generated_packets` 변경이 없다.
- user-local generated collect JSON은 다음 smoke 재시도 후 요약만 evidence docs에 기록하고 원본은 commit하지 않아야 한다.

## 10. Rollback plan

- 이 PR은 small parser/readiness metadata bugfix와 mocked/unit tests, handoff 문서만 포함한다.
- 문제가 있으면 PR commit을 revert하여 다음 변경을 되돌린다.
  - Spot parser `MIN_NOTIONAL` / `NOTIONAL` alias support.
  - readiness parser missing field prefix preservation.
  - 관련 unit tests.
  - handoff 문서.
- code/config/registry/runtime activation/generated-data rollback은 필요 없다.
- generated JSON artifact가 없으므로 data cleanup rollback도 필요 없다.

## 11. 다음 PR 후보

1. User-local collect smoke retry after Spot exchangeInfo min_notional live-shape parser follow-up / naming cleanup.
2. `sample_market_data` support with mocked/unit tests.
3. User-local 3-sample sampling evidence.
4. User-local 30-sample extended evidence.
5. Bybit public source research against common contract.
6. OKX public source research against common contract.
