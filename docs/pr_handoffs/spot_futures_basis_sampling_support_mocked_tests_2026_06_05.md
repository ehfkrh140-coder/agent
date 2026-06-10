# Spot-Futures Basis sample_market_data Support with Mocked Unit Tests v0

## 1. 작업 목적

이 문서는 `spot_futures_basis_v0` packet-shaped adapter output이 `run_market_sampling(...)` path에서 `market_sampling_v1` summary로 안전하게 요약되는지 mocked/unit tests로 검증한 결과를 기록한다.

목적:

- User-local live sampling 전에 mocked/unit tests로 Spot-Futures Basis sampling support를 검증한다.
- Binance public-read-only adapter output이 `run_market_sampling(...)`에서 3-sample summary로 집계되는지 확인한다.
- `sample_market_data.py` live command는 실행하지 않는다.
- Live endpoint 호출은 하지 않는다.
- Generated sampling JSON은 생성하거나 commit하지 않는다.
- `spot_futures_basis_v0`는 proposed / experimental / non-active / `NO_TRADE_ONLY` 상태를 유지한다.

## 2. 변경 파일

| 파일 | 변경 요약 |
| --- | --- |
| `src/market_data/sampling.py` | Sampling record의 embedded `opportunity_packet` dump에서 `exclude_none=True`를 사용해 schema-level `None` fields가 generated sampling summary에 불필요하게 남지 않도록 했다. This preserves mocked summary behavior while avoiding private/execution-looking null keys in sampling output. |
| `tests/test_spot_futures_basis_sampling.py` | Mocked Binance HTTP client와 fixture payloads로 `run_market_sampling(...)`의 Spot-Futures Basis 3-sample summary, readiness counts, metrics preservation, no-trade guardrails, generated JSON non-write behavior, WATCH no-trade behavior를 검증했다. |
| `docs/pr_handoffs/spot_futures_basis_sampling_support_mocked_tests_2026_06_05.md` | 이번 mocked sampling support 검증의 목적, 변경 파일, coverage, no-trade compliance, generated JSON policy, rollback, next PR candidates를 기록했다. |

## 3. Sampling support summary

- `run_market_sampling(...)`은 mocked `BinanceSpotFuturesBasisAdapter`를 통해 packet-shaped snapshot을 받아 `OpportunityPacketBuilder().build(snapshot)` path로 검증한다.
- `market_sampling_v1` output은 `adapter_id`, `samples_requested`, sample records, summary, Council handoff metadata를 포함한다.
- Existing generic sampling summary가 `strategy_family=spot_futures_basis`, `candidate_seen_count`, `positive_net_gap_count`, `readiness_pass_count`, `direction_counts`, `max_estimated_net_gap_pct`, `avg_estimated_net_gap_pct`, `max_gross_gap_pct`, latency fields, persistence status, and readiness status counts를 집계한다.
- Sampling record의 embedded `opportunity_packet`은 `exclude_none=True`로 직렬화되어 null schema fields such as unused execution/private-looking placeholders are omitted from the sampled output.
- `also_save_packets=False`, `output_path=None`, `interval_seconds=0`, no-op `sleep_fn`으로 테스트하며 generated JSON을 쓰지 않는다.

## 4. Mocked/unit test coverage

- `test_run_market_sampling_spot_futures_basis_three_samples_ok`
  - mocked adapter로 3 samples를 실행한다.
  - `schema_version=market_sampling_v1`, adapter id, `samples_requested=3`, `samples_ok=3`, `samples_error=0`, per-sample `status=ok`, `strategy_family=spot_futures_basis`, `strategy_id=spot_futures_basis_v0`, `candidate_count=1`, `no_trade_only=True`, `execution_policy=NO_TRADE_ONLY`를 검증한다.
- `test_sampling_summary_contains_readiness_counts`
  - `summary.readiness_status_counts`, `reject_count`, `watch_count`, `need_data_count`가 존재하고, readiness counts total이 `samples_ok`와 일치하는지 검증한다.
- `test_sampling_record_preserves_spot_futures_metrics`
  - `best_candidate.candidate_type=spot_futures_basis_observation`, readiness status/decision, estimated net gap/basis-compatible field, empty required missing fields, parser `OK`, diagnostics count 7을 검증한다.
- `test_sampling_no_trade_and_no_private_fields`
  - sampling result 전체에서 private/account/execution key substrings가 없는지 재귀적으로 검증하고 no-trade metadata를 확인한다.
- `test_sampling_does_not_write_generated_json_paths`
  - `data/market_samples/*.json` 및 `data/generated_packets/*.json`에 파일을 쓰지 않았는지 확인한다.
  - `sampling_output_file`이 `None`이고 result repr에 generated JSON paths가 들어가지 않는지 확인한다.
- `test_sampling_with_watch_still_no_trade_only`
  - mocked prices를 WATCH로 조정한 뒤 sampling path에서 WATCH가 유지되지만 `NO_TRADE_ONLY`, no execution, no alert, no Council auto-call assumptions가 유지되는지 검증한다.

## 5. Summary fields verified

Verified `market_sampling_v1` top-level fields:

- `schema_version`
- `adapter_id`
- `samples_requested`
- `interval_seconds`
- `samples`
- `summary`
- `council_recommended`
- `council_reason`
- `sampling_output_file`

Verified summary fields:

- `samples_ok`
- `samples_error`
- `candidate_seen_count`
- `readiness_status_counts`
- `reject_count`
- `watch_count`
- `need_data_count`
- `positive_net_gap_count`
- `readiness_pass_count`
- `direction_counts`
- `max_estimated_net_gap_pct`
- `avg_estimated_net_gap_pct`
- `max_gross_gap_pct`
- `persistence_status`
- `recommended_default_decision`

Verified per-sample fields:

- `strategy_family=spot_futures_basis`
- `strategy_id=spot_futures_basis_v0`
- `candidate_count=1`
- `best_candidate.candidate_type=spot_futures_basis_observation`
- `readiness_status`
- `recommended_default_decision`
- `estimated_net_gap_pct`
- `required_missing_fields=[]`
- `parser_normalized_status=OK`
- `diagnostics_count=7`
- `no_trade_only=True`
- `execution_policy=NO_TRADE_ONLY`

## 6. No-trade / WATCH interpretation

- WATCH is not ENTER.
- WATCH is an analysis-only label.
- WATCH in sampling does not trigger execution.
- WATCH in sampling does not trigger alert.
- WATCH in sampling does not trigger Council auto-call.
- `council_recommended` remains false unless the existing persistence handoff conditions are met with a handoff packet, and this PR does not create one.
- REJECT remains a normal no-edge analysis label.
- NEED_DATA remains an analysis-only insufficient-data label.
- Spot/perp basis must not be interpreted as executable edge.
- `NO_TRADE_ONLY` is preserved in sample records and embedded packet extensions.

## 7. Explicitly not implemented

- User-local live sampling 실행 없음.
- `tools/sample_market_data.py` 변경 없음.
- `tools/collect_market_data.py` 변경 없음.
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
- Readiness threshold 변경 없음.
- Persistence policy 변경 없음.
- Council handoff metadata policy 변경 없음.
- Collect/sample command behavior 변경 없음.

## 8. No-trade compliance

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

## 9. Generated JSON commit 금지 확인

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지다.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지다.
- 이번 PR 테스트는 generated sampling JSON을 쓰지 않는다.
- 이번 PR에는 `data/market_samples` 또는 `data/generated_packets` 변경이 없다.
- User-local 3-sample sampling output은 다음 단계에서 요약만 evidence docs에 기록하고 원본은 commit하지 않아야 한다.

## 10. Rollback plan

- 문제가 있으면 this PR commit을 revert한다.
- Revert 시 제거되는 항목:
  - `src/market_data/sampling.py`의 embedded packet `exclude_none=True` dump adjustment.
  - `tests/test_spot_futures_basis_sampling.py` mocked/unit tests.
  - 이 handoff 문서.
- Tools/config/registry/adapter/parser/readiness/packet-builder rollback은 필요 없다.
- Generated data rollback은 필요 없다.

## 11. 다음 PR 후보

1. User-local 3-sample sampling evidence.
2. User-local 30-sample extended evidence.
3. Bybit public source research against common contract.
4. OKX public source research against common contract.
5. Depth/VWAP planning for `spot_futures_basis_v0`.
6. Sampling summary refinements for basis-specific aliases if reviewer requests more explicit `estimated_net_basis_pct` naming.
