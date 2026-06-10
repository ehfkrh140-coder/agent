# Spot-Futures Basis Binance 3-Sample Sampling Evidence v0

## 1. 작업 목적

이 문서는 `spot_futures_basis_v0`의 첫 user-local 3-sample sampling result를 기록하는 docs-only evidence handoff이다.

목적:

- `spot_futures_basis_v0`의 첫 user-local 3-sample sampling result를 기록한다.
- 이번 evidence는 `sample_market_data` path가 `market_sampling_v1` summary 생성까지 성공했음을 의미한다.
- 이 evidence는 profitability 증명이 아니다.
- 이 evidence는 persistent edge 증명이 아니다.
- `NO_TRADE_ONLY`를 유지한다.
- Runtime behavior, source, tests, config, registry, tools, generated JSON은 변경하지 않는다.

## 2. User-local command

User-local command recorded by the user:

```bash
python tools/sample_market_data.py --adapter live_binance_spot_futures_basis_btcusdt --samples 3 --interval 2 --output data/market_samples/spot_futures_basis_binance_sampling_3x_summary.json
```

The generated sampling JSON file is a smoke artifact and must not be committed.

## 3. Evidence summary

| Field | Value |
| --- | --- |
| `adapter_id` | `live_binance_spot_futures_basis_btcusdt` |
| `schema_version` | `market_sampling_v1` |
| `samples_requested` | `3` |
| `interval_seconds` | `2.0` |
| `samples_len` | `3` |
| `samples_ok` | `3` |
| `samples_error` | `0` |
| `candidate_seen_count` | `3` |
| `readiness_status_counts` | `{'REJECT': 3}` |
| `reject_count` | `3` |
| `watch_count` | `0` |
| `need_data_count` | `0` |
| `positive_net_gap_count` | `0` |
| `readiness_pass_count` | `0` |
| `persistence_status` | `NO_PERSISTENT_EDGE` |
| `recommended_default_decision` | `REJECT` |
| `council_recommended` | `false` |
| `council_reason` | `NO_PERSISTENT_EDGE: persistent ready edge handoff packet not available` |
| `generated_json_committed` | `false` |

Cleanup requirement:

- User must delete `data/market_samples/spot_futures_basis_binance_sampling_3x_summary.json` after inspection.
- Generated JSON must not be committed.

## 4. Per-sample evidence table

| sample_index | status | strategy_family | strategy_id | candidate_count | readiness_status | recommended_default_decision | estimated_net_gap_pct | required_missing_fields | parser_normalized_status | diagnostics_count | no_trade_only | execution_policy | best_candidate_type |
| --- | --- | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | --- |
| 1 | `ok` | `spot_futures_basis` | `spot_futures_basis_v0` | 1 | `REJECT` | `REJECT` | `-0.15087684590741288` | `[]` | `OK` | 7 | `true` | `NO_TRADE_ONLY` | `spot_futures_basis_observation` |
| 2 | `ok` | `spot_futures_basis` | `spot_futures_basis_v0` | 1 | `REJECT` | `REJECT` | `-0.15125568045922075` | `[]` | `OK` | 7 | `true` | `NO_TRADE_ONLY` | `spot_futures_basis_observation` |
| 3 | `ok` | `spot_futures_basis` | `spot_futures_basis_v0` | 1 | `REJECT` | `REJECT` | `-0.1490553311722307` | `[]` | `OK` | 7 | `true` | `NO_TRADE_ONLY` | `spot_futures_basis_observation` |

## 5. REJECT / NO_PERSISTENT_EDGE interpretation

- `REJECT`는 sampling failure가 아니다.
- `NO_PERSISTENT_EDGE`는 adapter failure가 아니다.
- `samples_ok=3`, `samples_error=0`이므로 sampling path는 성공했다.
- `REJECT`는 estimated net basis가 음수라 no-edge로 판단한 analysis-only label이다.
- `positive_net_gap_count=0`이다.
- `readiness_pass_count=0`이다.
- 따라서 persistent edge evidence가 없다.
- `council_recommended=false`는 정상 no-edge 결과다.
- 이 evidence는 profitability 증명이 아니다.
- 이 evidence는 persistent edge 증명이 아니다.
- `WATCH` / `NEED_DATA` / `REJECT`는 analysis-only label이다.
- Spot/perp basis는 executable edge로 오해하면 안 된다.
- Mark/index/funding context는 executable basis가 아니다.
- `NO_TRADE_ONLY`는 유지된다.

## 6. No-trade compliance

This docs-only evidence PR records no-trade posture:

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
- `NO_TRADE_ONLY` 유지.

## 7. Generated JSON commit 금지

Generated JSON policy:

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- User-local generated sampling JSON은 evidence 요약 후 삭제해야 한다.
- 이번 PR에는 generated JSON을 추가하지 않는다.
- `data/market_samples/spot_futures_basis_binance_sampling_3x_summary.json`는 user-local smoke artifact이며 commit 금지다.

## 8. Rollback plan

- Docs-only PR이므로 revert하고 이 handoff 문서 1개를 제거하면 된다.
- Code rollback은 필요 없다.
- Config/registry rollback은 필요 없다.
- Runtime rollback은 필요 없다.
- Parser/readiness rollback은 필요 없다.
- Test/fixture rollback은 필요 없다.
- Generated-data rollback은 필요 없다.

## 9. Next PR candidates

1. User-local 30-sample extended sampling evidence.
2. Bybit public source research against common contract.
3. OKX public source research against common contract.
4. Depth/VWAP planning for `spot_futures_basis_v0`.
5. Basis-specific sampling summary alias refinement if reviewer requests explicit `estimated_net_basis_pct` naming.
