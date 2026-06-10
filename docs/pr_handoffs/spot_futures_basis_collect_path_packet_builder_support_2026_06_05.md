# Spot-Futures Basis Collect Path / OpportunityPacketBuilder Support v0

## 1. 작업 목적

이 문서는 `spot_futures_basis_v0` adapter가 반환하는 packet-compatible dict를 existing collect path의 `OpportunityPacketBuilder().build(snapshot)` 단계에서 validation/pass-through 할 수 있도록 지원한 작은 implementation PR의 handoff이다.

목적:

- `OpportunityPacketBuilder`에 `strategy_family="spot_futures_basis"` branch를 추가한다.
- 이미 adapter / pure packet builder가 만든 `opportunity_packet_v0` compatible dict를 `OpportunityPacket.model_validate(snapshot)`로 검증한다.
- `tools/collect_market_data.py` 변경 없이 mocked/unit tests에서 collect path equivalent snapshot pass-through를 검증한다.
- Live endpoint 호출, user-local collect smoke, `sample_market_data` support, generated JSON 생성 없이 `NO_TRADE_ONLY` posture를 유지한다.

## 2. 변경 파일

| File | Change |
| --- | --- |
| `src/market_data/packet_builder.py` | `strategy_family == "spot_futures_basis"` branch 및 `build_spot_futures_basis(...)` validation/pass-through helper 추가. |
| `tests/test_spot_futures_basis_collect_path.py` | Mocked fixture / mocked adapter packet dict를 `OpportunityPacketBuilder().build(...)`로 검증하는 collect-path unit tests 추가. |
| `docs/pr_handoffs/spot_futures_basis_collect_path_packet_builder_support_2026_06_05.md` | 이 handoff 문서 추가. |

## 3. OpportunityPacketBuilder support summary

- `OpportunityPacketBuilder.build(...)` now recognizes `strategy_family == "spot_futures_basis"`.
- `build_spot_futures_basis(snapshot)` validates the adapter-produced or pure-builder-produced packet-compatible dict through `OpportunityPacket.model_validate(snapshot)`.
- The new branch mirrors the Mark-Orderbook Gap Hunt validation/pass-through style.
- The new branch does not fetch live data.
- The new branch does not read or write files.
- The new branch does not parse source bundles.
- The new branch does not calculate readiness.
- The new branch does not generate candidates.
- The new branch does not add execution, alert, Council auto-call, or auto-trading behavior.

## 4. Collect path implication

- `tools/collect_market_data.py` already calls `OpportunityPacketBuilder().build(snapshot)` after `adapter.fetch_snapshot()`.
- This PR adds `spot_futures_basis` validation/pass-through support so adapter packet-shaped output can pass through builder in mocked/unit tests.
- This PR does not change `tools/collect_market_data.py`.
- This PR does not run user-local collect smoke.
- Live collect smoke must be user-local and evidence-only next.
- Generated collect output, when future user-local smoke is requested, remains a smoke artifact and must not be committed.

## 5. Tests added

Added `tests/test_spot_futures_basis_collect_path.py` with mocked/unit-only coverage:

1. `test_opportunity_packet_builder_accepts_spot_futures_basis_packet`
2. `test_collect_path_equivalent_snapshot_from_adapter_mocked`
3. `test_builder_preserves_no_trade_watch_assumptions`
4. `test_builder_rejects_or_errors_on_unsupported_strategy_still`
5. `test_no_private_or_execution_fields_after_builder`
6. `test_no_generated_json_paths_referenced`

The tests use deterministic fixture payloads and mocked HTTP client behavior only. They do not call real Binance endpoints and do not create generated JSON files.

## 6. Explicitly not implemented

- `tools/collect_market_data.py` 변경 없음.
- `tools/sample_market_data.py` 변경 없음.
- Live collect smoke 없음.
- `sample_market_data` support 없음.
- Registry/config 변경 없음.
- Active strategy 변경 없음.
- Live endpoint 호출 없음.
- Generated JSON 생성 없음.
- Private API 없음.
- Credentials 없음.
- Account/balance/position/order/cancel/withdraw/deposit/transfer 없음.
- Execution 없음.
- Alert 없음.
- Council auto-call 없음.
- Auto-trading 없음.

## 7. No-trade compliance

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

## 8. Generated JSON commit 금지 확인

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- 이번 PR에는 `data/market_samples` 또는 `data/generated_packets` 변경 없음.
- New tests validate packet objects in memory only and do not write output files.

## 9. Rollback plan

Rollback steps:

1. Remove the `strategy_family == "spot_futures_basis"` branch from `OpportunityPacketBuilder.build(...)`.
2. Remove `build_spot_futures_basis(...)` from `src/market_data/packet_builder.py`.
3. Remove `tests/test_spot_futures_basis_collect_path.py`.
4. Remove this handoff document.
5. Rerun the required tests and generated JSON path checks.

No generated-data rollback is required because this PR does not create generated JSON files.

## 10. 다음 PR 후보

Recommended next PR sequence:

1. User-local public-read-only collect smoke request.
2. Docs-only collect evidence handoff.
3. `sample_market_data` support with mocked/unit tests.
4. User-local 3-sample sampling evidence.
5. User-local 30-sample extended evidence.
