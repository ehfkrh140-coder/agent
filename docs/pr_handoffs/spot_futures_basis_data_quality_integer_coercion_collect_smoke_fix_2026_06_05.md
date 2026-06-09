# Spot-Futures Basis DataQuality Integer Coercion Collect Smoke Fix v0

## 1. 작업 목적

이 문서는 user-local `collect_market_data` smoke에서 발견된 `OpportunityPacket` validation type issue를 수정한 small bugfix PR의 handoff이다.

목적:

- `src/market_data/spot_futures_basis_packet_builder.py`가 `data_quality.max_data_age_ms`, `data_quality.data_age_ms`, `data_quality.latency_ms` schema-level fields에 int 또는 None을 넣도록 변환한다.
- Fractional `data_age_ms` / `latency_ms` raw evidence는 observation `extensions.raw_data_age_ms` / `extensions.raw_latency_ms`에 보존한다.
- Negative `data_age_ms`는 timestamp / clock-skew watch item으로 유지하되 0으로 clamp하지 않는다.
- Live endpoint 호출, collect smoke 재실행, registry/config 변경, active strategy 변경, generated JSON 생성 없이 `NO_TRADE_ONLY` posture를 유지한다.

## 2. 사용자 로컬 collect smoke 실패 원인

User-local command:

```bash
python tools/collect_market_data.py --adapter live_binance_spot_futures_basis_btcusdt --output data/generated_packets/spot_futures_basis_binance_collect_smoke_packet.json
```

Observed failure:

- `collect_market_data` path reached `OpportunityPacketBuilder` validation.
- `observations.1.data_quality.max_data_age_ms` expected `int` but received fractional float `-558.491943359375`.
- Root cause was the spot-futures pure packet builder passing fractional `data_age_ms` directly into schema-level `max_data_age_ms`.

Policy for this fix:

- Do not clamp negative `data_age_ms` to 0.
- Do not flip the sign.
- Do not hide raw float evidence.
- Put schema-compatible int values in `data_quality` fields.
- Preserve raw numeric evidence in observation extensions.

## 3. 변경 파일

| File | Change |
| --- | --- |
| `src/market_data/spot_futures_basis_packet_builder.py` | Added integer coercion/raw number helpers and applied them to spot/perp `data_quality` fields and extensions. |
| `tests/test_spot_futures_basis_packet_builder.py` | Added unit coverage for fractional negative data age, fractional latency, and no-clamp negative data age behavior. |
| `tests/test_spot_futures_basis_collect_path.py` | Added collect-path builder pass-through coverage for live-like fractional negative data age packet dicts. |
| `docs/pr_handoffs/spot_futures_basis_data_quality_integer_coercion_collect_smoke_fix_2026_06_05.md` | This handoff document. |

## 4. DataQuality coercion summary

New helper behavior:

- `_coerce_optional_int_ms(value)` returns `None` for `None`, bools, and unparseable values.
- Existing `int` values remain unchanged.
- `float` values are converted with `int(value)`, removing only the fractional part.
- Numeric strings are parsed through `float(...)` and then converted to `int`.
- Negative values remain negative.
- No `max(0, value)` clamp is used.

Applied schema-level fields:

- Spot `data_quality.latency_ms`
- Spot `data_quality.data_age_ms`
- Spot `data_quality.max_data_age_ms`
- Perp `data_quality.latency_ms`
- Perp `data_quality.data_age_ms`
- Perp `data_quality.max_data_age_ms`

## 5. Raw data_age_ms preservation

Raw numeric evidence is preserved under observation extensions:

- Spot `extensions.raw_data_age_ms`
- Spot `extensions.raw_latency_ms`
- Perp `extensions.raw_data_age_ms`
- Perp `extensions.raw_latency_ms`

For example, live-like `perp_observation.data_age_ms = -558.491943359375` becomes:

- `perp.data_quality.max_data_age_ms = -558`
- `perp.extensions.raw_data_age_ms = -558.491943359375`

## 6. Negative data_age_ms policy

- Negative `data_age_ms` is preserved as a negative int in schema-level data-quality fields.
- Raw negative float evidence is preserved in extensions.
- Negative `data_age_ms` is not treated as freshness policy in this PR.
- Timestamp / clock-skew policy is not implemented in this PR.
- Freshness behavior is unchanged.
- Readiness behavior is unchanged.
- Diagnostics behavior is unchanged.
- `OpportunityPacketBuilder` pass-through behavior is unchanged.

## 7. Tests added

Added/updated mocked/unit-only tests:

1. `tests.test_spot_futures_basis_packet_builder.test_fractional_negative_data_age_ms_validates_as_int_and_preserves_raw`
2. `tests.test_spot_futures_basis_packet_builder.test_fractional_latency_ms_validates_as_int_and_preserves_raw`
3. `tests.test_spot_futures_basis_packet_builder.test_data_age_not_clamped_to_zero`
4. `tests.test_spot_futures_basis_collect_path.test_collect_path_builder_accepts_live_like_fractional_data_age_packet`

These tests validate `OpportunityPacketBuilder().build(...)` success without live endpoints and without generated JSON files.

## 8. Explicitly not implemented

- Live collect smoke 재실행 없음.
- `tools/collect_market_data.py` 변경 없음.
- `tools/sample_market_data.py` 변경 없음.
- Registry/config 변경 없음.
- Active strategy 변경 없음.
- Timestamp policy 구현 없음.
- Negative `data_age_ms` clamp 없음.
- Readiness behavior 변경 없음.
- Adapter behavior 변경 없음.
- Generated JSON 생성 없음.
- Private API 없음.
- Credentials 없음.
- Account/balance/position/order/cancel/withdraw/deposit/transfer 없음.
- Execution 없음.
- Alert 없음.
- Council auto-call 없음.
- Auto-trading 없음.

## 9. No-trade compliance

- Active strategy promotion 없음.
- `spot_futures_basis_v0` active 승격 없음.
- `enabled=false` 유지.
- Private API 없음.
- Credentials 없음.
- Account/balance/position lookup 없음.
- Order/cancel 없음.
- Withdrawal/deposit/transfer 없음.
- Auto-trading 없음.
- Council auto-call 없음.
- Alert 없음.
- Execution 없음.
- Generated JSON 파일 생성 없음.
- `NO_TRADE_ONLY` 유지.

## 10. Generated JSON commit 금지 확인

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- 이번 PR에는 `data/market_samples` 또는 `data/generated_packets` 변경 없음.
- User-local generated collect JSON은 다음 smoke 재시도 후 요약만 evidence docs에 기록하고 원본은 commit하지 않아야 한다.

## 11. Rollback plan

Rollback steps:

1. Remove `_coerce_optional_int_ms(...)` and `_raw_optional_number(...)` helper usage from `src/market_data/spot_futures_basis_packet_builder.py`.
2. Restore spot/perp `data_quality` fields to their previous direct mapping if rollback is required.
3. Remove the added tests from `tests/test_spot_futures_basis_packet_builder.py` and `tests/test_spot_futures_basis_collect_path.py`.
4. Remove this handoff document.
5. Rerun required unit tests and generated JSON path checks.

No generated-data rollback is required because this PR does not create generated JSON files.

## 12. 다음 PR 후보

Recommended next PR sequence:

1. User-local public-read-only collect smoke retry.
2. Docs-only collect smoke evidence handoff.
3. `sample_market_data` support with mocked/unit tests.
4. User-local 3-sample sampling evidence.
5. User-local 30-sample extended evidence.
