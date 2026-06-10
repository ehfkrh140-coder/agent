# Spot-Futures Basis Bybit Collect Smoke Evidence after Orderbook Category Fix v0

## 1. 작업 목적

이 문서는 Bybit orderbook category live-shape parser follow-up 이후 사용자가 로컬에서 재실행한 Bybit public-read-only collect smoke 결과를 기록한다.

목적:

- Bybit orderbook category live-shape parser follow-up 이후 user-local collect smoke retry 결과를 기록한다.
- 이번 evidence는 Bybit live public endpoint collect path가 OpportunityPacket 저장까지 성공했고 parser statuses가 `OK`임을 의미한다.
- Prior category mismatch `NEED_DATA`가 해소되었음을 기록한다.
- Profitability / persistent edge 증명이 아니다.
- `NO_TRADE_ONLY`를 유지한다.

## 2. User-local command

사용자 로컬 실행 명령:

```bash
python tools/collect_market_data.py --adapter live_bybit_spot_futures_basis_btcusdt --output data/generated_packets/spot_futures_basis_bybit_collect_smoke_packet.json
```

이 명령은 사용자가 로컬에서 실행한 public-read-only collect smoke이며, 이번 PR에서는 live endpoint 호출을 실행하지 않았다.

## 3. Evidence summary

Bybit collect smoke retry evidence summary:

| Field | Value |
| --- | --- |
| `adapter_id` | `live_bybit_spot_futures_basis_btcusdt` |
| `adapter_type` | `bybit_spot_futures_basis` |
| `source_venue_id` | `bybit` |
| `schema_version` | `opportunity_packet_v0` |
| `signal_type` | `spot_futures_basis` |
| `strategy_family` | `spot_futures_basis` |
| `strategy_id` | `spot_futures_basis_v0` |
| `observations_count` | `2` |
| `candidates_count` | `1` |
| `diagnostics_count` | `6` |
| `no_trade_only` | `true` |
| `execution_policy` | `NO_TRADE_ONLY` |
| `readiness_status` | `REJECT` |
| `recommended_default_decision` | `REJECT` |
| `readiness_pass` | `false` |
| `estimated_net_basis_pct` | `-0.1527317452944347` |
| `estimated_net_gap_pct` | `-0.1527317452944347` |
| `output_path` | `data/generated_packets/spot_futures_basis_bybit_collect_smoke_packet.json` |
| `generated_json_committed` | `false` |

## 4. Spot / Perp parser evidence

### Spot observation

| Field | Value |
| --- | --- |
| `observation_id` | `bybit_spot_btcusdt_spot_futures_basis` |
| `venue_id` | `bybit` |
| `venue_name` | `Bybit Spot` |
| `market_symbol` | `BTCUSDT` |
| `instrument_type` | `spot` |
| `parser_status` | `OK` |
| `required_missing_fields` | `[]` |
| `min_notional` | `5.0` |

### Perp observation

| Field | Value |
| --- | --- |
| `observation_id` | `bybit_linear_btcusdt_perp_spot_futures_basis` |
| `venue_id` | `bybit` |
| `venue_name` | `Bybit Derivatives V5` |
| `market_symbol` | `BTCUSDT` |
| `instrument_type` | `linear_perpetual` |
| `category` | `linear` |
| `parser_status` | `OK` |
| `required_missing_fields` | `[]` |
| `min_notional` | `5.0` |
| `funding_interval` | `480` |

## 5. Prior NEED_DATA resolved

Prior `NEED_DATA` resolution:

- 이전 Bybit collect smoke는 OpportunityPacket save/validation까지 도달했지만 `readiness_status=NEED_DATA`였다.
- 이전 원인은 `spot_orderbook_category_mismatch` 및 `linear_orderbook_category_mismatch`였다.
- Bybit V5 orderbook response body가 `category`를 echo하지 않는 live shape를 parser가 fatal mismatch로 처리한 것이 원인이었다.
- 이번 retry에서는 `spot_parser_status=OK`, `perp_parser_status=OK`, spot/perp/candidate `required_missing_fields`가 모두 비어 있다.
- 따라서 orderbook category live-shape follow-up이 user-local collect path에서 효과를 확인했다.

## 6. REJECT interpretation

`REJECT` interpretation:

- `REJECT`는 collect smoke failure가 아니다.
- Collect smoke 성공 기준은 OpportunityPacket save / schema / signal / observations / candidates / diagnostics / no-trade metadata / parser OK다.
- `REJECT`는 `estimated_net_basis_pct`가 음수라 no-edge로 판단한 analysis-only label이다.
- 이번 `estimated_net_basis_pct=-0.1527317452944347`은 fee/slippage/buffer 이후 positive net basis가 없음을 의미한다.
- `REJECT`는 execution, alert, Council auto-call을 트리거하지 않는다.
- Profitability / persistent edge 증명이 아니다.

## 7. Warnings / watch items

Recorded warnings / watch items:

- `mark_price_not_executable`
- `funding_rate_not_basis`
- `depth_vwap_not_implemented`
- `negative_data_age_watch`
- `non_positive_estimated_net_basis`
- `funding_interval=480`

Interpretation:

- Mark price와 funding rate는 context이며 executable basis가 아니다.
- `depth_vwap_not_implemented`는 future depth/VWAP implementation 후보이다.
- `negative_data_age_watch`는 timestamp/clock-skew watch item이며 blocker가 아니다.
- `funding_interval=480`은 Bybit metadata/context warning이며 trading signal이 아니다.
- `non_positive_estimated_net_basis`는 정상 `REJECT` 이유이다.

## 8. Interpretation

Interpretation:

- 이번 결과는 public-read-only collect path success evidence다.
- 이번 결과는 profitable edge 증명이 아니다.
- 이번 결과는 persistent edge 증명이 아니다.
- `readiness_status=REJECT`는 no-trade analysis label이다.
- `WATCH` / `NEED_DATA` / `REJECT`는 analysis-only label이다.
- Spot/perp basis는 executable edge로 오해하면 안 된다.
- Mark/index/funding context는 executable basis가 아니다.
- `NO_TRADE_ONLY` 유지.

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
- Source/runtime behavior 변경 없음.

## 10. Generated JSON commit 금지

Generated JSON policy 확인:

- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- User-local generated packet JSON은 evidence 요약 후 삭제해야 함.
- 이번 PR에는 generated JSON을 추가하지 않음.
- `data/generated_packets/spot_futures_basis_bybit_collect_smoke_packet.json`는 commit 대상이 아니다.

## 11. OKX deferred scope note

- 이번 `spot_futures_basis_v0` cycle은 Binance + Bybit까지만 진행한다.
- OKX는 future expansion으로 defer한다.
- This is scope control, not permanent rejection.
- 이번 PR에서는 OKX adapter/config/research를 만들지 않는다.

## 12. Rollback plan

Rollback plan:

- Docs-only PR이므로 revert하고 이 handoff 문서 1개를 제거하면 된다.
- Code/config/registry/runtime/parser/readiness/test/fixture/generated-data rollback은 필요 없다.
- Re-run repository tests if the revert PR process requires evidence.
- Confirm no generated JSON files are committed.

## 13. Next PR candidates

다음 PR 후보 순서:

1. Bybit user-local 3-sample sampling evidence.
2. Bybit user-local 30-sample extended sampling evidence.
3. Binance + Bybit Spot-Futures Basis comparative summary.
4. Next big project phase planning.
5. OKX public source research as future expansion only.
