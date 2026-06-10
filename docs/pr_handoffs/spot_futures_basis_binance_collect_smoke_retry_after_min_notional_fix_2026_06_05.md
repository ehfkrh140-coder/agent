# Spot-Futures Basis Binance Collect Smoke Retry Evidence after min_notional Follow-up v0

## 1. 작업 목적

이 문서는 `spot_futures_basis_v0`의 Spot `exchangeInfo` min_notional live-shape parser follow-up 이후 user-local public-read-only collect smoke retry 결과를 기록하는 docs-only evidence handoff이다.

목적:

- Spot `exchangeInfo` min_notional live-shape parser follow-up 이후 user-local collect smoke retry 결과를 기록한다.
- 이번 evidence는 prior `NEED_DATA` 원인이 해소되었음을 보여준다.
- collect path가 `OpportunityPacket` 저장까지 성공했고 Spot/Perp parser statuses가 모두 `OK`임을 기록한다.
- 이 evidence는 profitability 증명이 아니다.
- 이 evidence는 persistent edge 증명이 아니다.
- `NO_TRADE_ONLY`를 유지한다.
- Runtime behavior, source, tests, config, registry, tools, generated JSON은 변경하지 않는다.

## 2. User-local command

User-local command recorded by the user:

```bash
python tools/collect_market_data.py --adapter live_binance_spot_futures_basis_btcusdt --output data/generated_packets/spot_futures_basis_binance_collect_smoke_packet.json
```

The generated packet JSON is a smoke artifact and must not be committed.

## 3. Evidence summary

| Field | Value |
| --- | --- |
| `adapter_id` | `live_binance_spot_futures_basis_btcusdt` |
| `schema_version` | `opportunity_packet_v0` |
| `signal_type` | `spot_futures_basis` |
| `strategy_family` | `spot_futures_basis` |
| `strategy_id` | `spot_futures_basis_v0` |
| `observations_count` | `2` |
| `candidates_count` | `1` |
| `diagnostics_count` | `7` |
| `no_trade_only` | `true` |
| `execution_policy` | `NO_TRADE_ONLY` |
| `readiness_status` | `REJECT` |
| `recommended_default_decision` | `REJECT` |
| `readiness_pass` | `false` |
| `estimated_net_basis_pct` | `-0.1421874877764524` |
| `selected_direction` | `analysis_only_long_perp_short_spot_basis` |
| `spot_parser_status` | `OK` |
| `perp_parser_status` | `OK` |
| `spot_required_missing_fields` | `[]` |
| `perp_required_missing_fields` | `[]` |
| `candidate_required_missing_fields` | `[]` |
| `spot_min_notional` | `5.0` |
| `perp_min_notional` | `50.0` |
| `output_path` | `data/generated_packets/spot_futures_basis_binance_collect_smoke_packet.json` |
| `generated_json_committed` | `false` |

Additional retry fields:

- `candidate_warnings`: `['mark_price_not_executable', 'funding_rate_not_basis', 'depth_vwap_not_implemented', 'negative_data_age_watch', 'non_positive_estimated_net_basis']`
- `candidate_direction`: `analysis_only_long_perp_short_spot_basis`

Cleanup requirement:

- User must delete `data/generated_packets/spot_futures_basis_binance_collect_smoke_packet.json` after inspection.
- Generated JSON must not be committed.

## 4. Prior NEED_DATA resolved

- 이전 collect smoke evidence에서는 `readiness_status=NEED_DATA`였다.
- 이전 원인은 `spot_parser_status=NEED_DATA`, `spot_min_notional_missing`, `spot_spot_min_notional_missing` naming issue였다.
- 이번 retry에서는 `spot_parser_status=OK`이다.
- 이번 retry에서는 `perp_parser_status=OK`이다.
- 이번 retry에서는 Spot/Perp/Candidate `required_missing_fields`가 모두 비어 있다.
- 따라서 min_notional live-shape parser follow-up과 missing-field naming cleanup이 user-local collect path에서 효과를 확인했다.
- 이번 PR은 retry evidence를 기록하는 docs-only PR이며, parser/readiness fix 구현 PR이 아니다.

## 5. REJECT interpretation

- `REJECT`는 collect smoke failure가 아니다.
- Collect smoke 성공 기준은 `OpportunityPacket` save, schema, signal, observations, candidates, diagnostics, no-trade metadata, parser `OK`다.
- `REJECT`는 `estimated_net_basis_pct`가 음수라 no-edge로 판단한 analysis-only label이다.
- 이번 `estimated_net_basis_pct=-0.1421874877764524`는 fee/slippage/buffer 이후 positive net basis가 없음을 의미한다.
- `REJECT`는 execution을 트리거하지 않는다.
- `REJECT`는 alert를 트리거하지 않는다.
- `REJECT`는 Council auto-call을 트리거하지 않는다.
- 이 결과는 profitability 증명이 아니다.
- 이 결과는 persistent edge 증명이 아니다.

## 6. Warnings / watch items

Recorded watch items:

- `mark_price_not_executable`
- `funding_rate_not_basis`
- `depth_vwap_not_implemented`
- `negative_data_age_watch`
- `non_positive_estimated_net_basis`

Interpretation:

- Mark price와 funding rate는 context이며 executable basis가 아니다.
- `depth_vwap_not_implemented`는 future depth/VWAP implementation 후보이다.
- `negative_data_age_watch`는 timestamp/clock-skew watch item이며 blocker가 아니다.
- `non_positive_estimated_net_basis`는 정상 `REJECT` 이유이다.

## 7. Interpretation

- 이번 결과는 public-read-only collect path success evidence다.
- 이번 결과는 profitable edge 증명이 아니다.
- 이번 결과는 persistent edge 증명이 아니다.
- `readiness_status=REJECT`는 no-trade analysis label이다.
- `WATCH` / `NEED_DATA` / `REJECT`는 analysis-only label이다.
- Spot/perp basis는 executable edge로 오해하면 안 된다.
- Mark/index/funding context는 executable basis가 아니다.
- `NO_TRADE_ONLY`는 유지된다.

## 8. No-trade compliance

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

## 9. Generated JSON commit 금지

Generated JSON policy:

- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- User-local generated packet JSON은 evidence 요약 후 삭제해야 한다.
- 이번 PR에는 generated JSON을 추가하지 않는다.
- `data/generated_packets/spot_futures_basis_binance_collect_smoke_packet.json`는 user-local smoke artifact이며 commit 금지다.

## 10. Rollback plan

- Docs-only PR이므로 revert하고 이 handoff 문서 1개를 제거하면 된다.
- Code rollback은 필요 없다.
- Config/registry rollback은 필요 없다.
- Runtime rollback은 필요 없다.
- Parser/readiness rollback은 필요 없다.
- Test/fixture rollback은 필요 없다.
- Generated-data rollback은 필요 없다.

## 11. Next PR candidates

1. `sample_market_data` support with mocked/unit tests.
2. User-local 3-sample sampling evidence.
3. User-local 30-sample extended evidence.
4. Bybit public source research against common contract.
5. OKX public source research against common contract.
6. Depth/VWAP planning for `spot_futures_basis_v0`.
