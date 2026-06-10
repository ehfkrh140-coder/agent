# Spot-Futures Basis Bybit 30-Sample Extended Sampling Evidence v0

## 1. 작업 목적

이 문서는 `spot_futures_basis_v0`의 Bybit user-local 30-sample extended sampling result를 기록한다.

목적:

- `spot_futures_basis_v0`의 Bybit user-local 30-sample extended sampling result를 기록한다.
- 이번 evidence는 `sample_market_data` path가 Bybit public-read-only 30 consecutive samples에서 `market_sampling_v1` summary 생성까지 성공했음을 의미한다.
- Profitability / persistent edge 증명이 아니다.
- `NO_TRADE_ONLY`를 유지한다.
- 이 문서는 3-sample evidence가 아니라 30-sample extended evidence다.

## 2. User-local command

사용자 로컬 실행 명령:

```bash
python tools/sample_market_data.py --adapter live_bybit_spot_futures_basis_btcusdt --samples 30 --interval 2 --output data/market_samples/spot_futures_basis_bybit_sampling_30x_summary.json
```

이 명령은 사용자가 로컬에서 실행한 public-read-only 30-sample extended sampling이며, 이번 PR에서는 live endpoint 호출을 실행하지 않았다.

## 3. Evidence summary

Bybit 30-sample extended sampling evidence summary:

| Field | Value |
| --- | --- |
| `adapter_id` | `live_bybit_spot_futures_basis_btcusdt` |
| `schema_version` | `market_sampling_v1` |
| `samples_requested` | `30` |
| `interval_seconds` | `2.0` |
| `samples_ok` | `30` |
| `samples_error` | `0` |
| `candidate_seen_count` | `30` |
| `readiness_status_counts` | `{'REJECT': 30}` |
| `reject_count` | `30` |
| `watch_count` | `0` |
| `need_data_count` | `0` |
| `positive_net_gap_count` | `0` |
| `readiness_pass_count` | `0` |
| `persistence_status` | `NO_PERSISTENT_EDGE` |
| `recommended_default_decision` | `REJECT` |
| `council_recommended` | `false` |
| `council_reason` | `NO_PERSISTENT_EDGE: persistent ready edge handoff packet not available` |
| `sample_readiness_statuses` | `{'REJECT': 30}` |
| `sample_parser_statuses` | `{'OK': 30}` |
| `samples_with_required_missing_fields` | `0` |
| `diagnostics_count_distribution` | `{6: 30}` |
| `min_estimated_net_gap_pct` | `-0.16557374120872367` |
| `max_estimated_net_gap_pct` | `-0.14965088573836977` |
| `avg_estimated_net_gap_pct` | `-0.15713512720458947` |
| `generated_json_committed` | `false` |

## 4. First / last sample evidence

| sample_label | status | strategy_family | strategy_id | candidate_count | readiness_status | recommended_default_decision | estimated_net_gap_pct | required_missing_fields | parser_normalized_status | diagnostics_count | no_trade_only | execution_policy | best_candidate_type |
| --- | --- | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | --- |
| First sample | `ok` | `spot_futures_basis` | `spot_futures_basis_v0` | 1 | `REJECT` | `REJECT` | `-0.15388195404109142` | `[]` | `OK` | 6 | `true` | `NO_TRADE_ONLY` | `spot_futures_basis_observation` |
| Last sample | `ok` | `spot_futures_basis` | `spot_futures_basis_v0` | 1 | `REJECT` | `REJECT` | `-0.15502998542126617` | `[]` | `OK` | 6 | `true` | `NO_TRADE_ONLY` | `spot_futures_basis_observation` |

## 5. REJECT / NO_PERSISTENT_EDGE interpretation

Interpretation:

- `REJECT`는 sampling failure가 아니다.
- `NO_PERSISTENT_EDGE`는 adapter failure가 아니다.
- `samples_ok=30`, `samples_error=0`이므로 Bybit extended sampling path는 성공했다.
- `parser_normalized_status`는 30 samples 모두 `OK`다.
- `required_missing_fields`는 30 samples 모두 비어 있다.
- `REJECT`는 estimated net basis가 음수라 no-edge로 판단한 analysis-only label이다.
- Min/max/avg estimated net basis가 모두 음수이므로 positive net basis evidence가 없다.
- `positive_net_gap_count=0`, `readiness_pass_count=0`이므로 persistent edge evidence가 없다.
- `council_recommended=false`는 정상 no-edge 결과다.
- Profitability / persistent edge 증명이 아니다.
- `WATCH` / `NEED_DATA` / `REJECT`는 analysis-only label이다.

## 6. Warnings / watch items

Recorded warnings / watch items:

- `negative_data_age_watch` may appear depending sample-level timestamp alignment.
- `funding_interval=480` Bybit context.
- `mark_price_not_executable`.
- `funding_rate_not_basis`.
- `depth_vwap_not_implemented`.
- `non_positive_estimated_net_basis`.

Interpretation:

- Mark price와 funding rate는 context이며 executable basis가 아니다.
- `depth_vwap_not_implemented`는 future depth/VWAP implementation 후보이다.
- Negative data age는 timestamp/clock-skew watch item이며 blocker가 아니다.
- `funding_interval=480`은 Bybit metadata/context warning이며 trading signal이 아니다.
- `non_positive_estimated_net_basis`는 정상 `REJECT` 이유이다.

## 7. No-trade compliance

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
- Source/runtime behavior 변경 없음.

## 8. Generated JSON commit 금지

Generated JSON policy 확인:

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- User-local generated sampling JSON은 evidence 요약 후 삭제해야 함.
- 이번 PR에는 generated JSON을 추가하지 않음.
- `data/market_samples/spot_futures_basis_bybit_sampling_30x_summary.json`는 commit 대상이 아니다.

## 9. OKX deferred scope note

- 이번 `spot_futures_basis_v0` cycle은 Binance + Bybit까지만 진행한다.
- OKX는 future expansion으로 defer한다.
- This is scope control, not permanent rejection.
- 이번 PR에서는 OKX adapter/config/research를 만들지 않는다.

## 10. Rollback plan

Rollback plan:

- Docs-only PR이므로 revert하고 이 handoff 문서 1개를 제거하면 된다.
- Code/config/registry/runtime/parser/readiness/test/fixture/generated-data rollback은 필요 없다.
- Re-run repository tests if the revert PR process requires evidence.
- Confirm no generated JSON files are committed.

## 11. Next PR candidates

다음 PR 후보 순서:

1. Binance + Bybit Spot-Futures Basis comparative summary.
2. Next big project phase planning.
3. OKX public source research as future expansion only.
4. Depth/VWAP planning for `spot_futures_basis_v0` as future enhancement.
