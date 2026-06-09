# Spot-Futures Basis Binance User-Local Collect Smoke Evidence v0

## 1. 작업 목적

이 문서는 `spot_futures_basis_v0`의 첫 user-local public-read-only collect smoke 결과를 기록하는 docs-only evidence handoff이다.

목적:

- `spot_futures_basis_v0`의 첫 user-local public-read-only collect smoke 결과를 기록한다.
- 이 evidence는 live public endpoint collect path가 `OpportunityPacket` 저장까지 성공했음을 의미한다.
- 이 evidence는 profitability 증명이 아니다.
- 이 evidence는 persistent edge 증명이 아니다.
- `NO_TRADE_ONLY`를 유지한다.
- Runtime behavior, source, tests, config, registry, tools, generated JSON은 변경하지 않는다.

## 2. User-local command

User-local command recorded by the user:

```bash
python tools/collect_market_data.py --adapter live_binance_spot_futures_basis_btcusdt --output data/generated_packets/spot_futures_basis_binance_collect_smoke_packet.json
```

Reported output:

```text
OpportunityPacket saved to: data\generated_packets\spot_futures_basis_binance_collect_smoke_packet.json
```

The generated JSON file is a smoke artifact and must not be committed.

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
| `readiness_status` | `NEED_DATA` |
| `recommended_default_decision` | `NEED_DATA` |
| `readiness_pass` | `false` |
| `estimated_net_basis_pct` | `None` |
| `selected_direction` | `analysis_only_no_positive_executable_basis` |
| `output_path` | `data/generated_packets/spot_futures_basis_binance_collect_smoke_packet.json` |
| `generated_json_committed` | `false` |

Additional inspected fields:

- `candidate_required_missing_fields`: `['spot_spot_min_notional_missing', 'spot_parser_normalized_status']`
- `candidate_warnings`: `['mark_price_not_executable', 'funding_rate_not_basis', 'depth_vwap_not_implemented', 'parser_required_missing_fields_present', 'parser_status_not_ok', 'negative_data_age_watch', 'required_fields_missing']`
- `candidate_direction`: `analysis_only_no_positive_executable_basis`
- `spot_required_missing_fields`: `['spot_min_notional_missing']`
- `perp_required_missing_fields`: `[]`
- `spot_parser_status`: `NEED_DATA`
- `perp_parser_status`: `OK`

## 4. NEED_DATA interpretation

- `NEED_DATA` is not a collect smoke failure.
- The collect smoke success criteria are `OpportunityPacket` save, schema, signal, observations, candidates, diagnostics, and no-trade metadata.
- `NEED_DATA` is an analysis-only label indicating readiness found insufficient information for executable-basis judgment.
- `NEED_DATA` does not trigger execution.
- `NEED_DATA` does not trigger alerts.
- `NEED_DATA` does not trigger Council auto-call.
- This `NEED_DATA` is grounded in spot parser status `NEED_DATA` and `spot_min_notional_missing`.
- Perp parser status is `OK` and perp `required_missing_fields` is empty.
- `candidate_required_missing_fields` includes `spot_spot_min_notional_missing` and `spot_parser_normalized_status`.
- `spot_spot_min_notional_missing` naming is a future parser/readiness field naming follow-up candidate.

## 5. Warnings / watch items

Recorded watch items:

- `mark_price_not_executable`
- `funding_rate_not_basis`
- `depth_vwap_not_implemented`
- `parser_required_missing_fields_present`
- `parser_status_not_ok`
- `negative_data_age_watch`
- `required_fields_missing`
- `spot_min_notional_missing`
- `spot_spot_min_notional_missing` naming follow-up

## 6. Prior failure and fix

- The first collect smoke failed during `OpportunityPacket` validation because `observations.1.data_quality.max_data_age_ms` received a fractional float value.
- The DataQuality integer coercion fix allowed the collect smoke to proceed through packet validation and save successfully.
- Negative/fractional `data_age_ms` is not hidden.
- Negative/fractional `data_age_ms` is converted to schema-compatible int values for schema fields.
- Raw values are preserved in observation extensions.
- This evidence PR records the post-fix user-local result; it is not the fix implementation PR.

## 7. Interpretation

- This result is public-read-only collect path success evidence.
- This result is not profitable edge evidence.
- This result is not persistent edge evidence.
- `readiness_status=NEED_DATA` is a no-trade analysis label.
- `WATCH` / `NEED_DATA` / `REJECT` are analysis-only labels.
- Spot/perp basis must not be interpreted as executable edge.
- Mark price, index price, and funding context are not executable basis.
- `NO_TRADE_ONLY` is preserved.

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
- `data/generated_packets/spot_futures_basis_binance_collect_smoke_packet.json` must remain uncommitted.

Cleanup reminder:

```powershell
Remove-Item data\generated_packets\spot_futures_basis_binance_collect_smoke_packet.json
```

## 10. Rollback plan

Rollback path:

1. Revert this docs-only evidence PR.
2. Remove `docs/pr_handoffs/spot_futures_basis_binance_collect_smoke_evidence_2026_06_05.md`.
3. No code/config/registry/runtime/parser/readiness/test/fixture/generated-data rollback is required.

## 11. Next PR candidates

Recommended next PR sequence:

1. Spot `exchangeInfo` `min_notional` live-shape parser follow-up / naming cleanup.
2. `sample_market_data` support with mocked/unit tests.
3. User-local 3-sample sampling evidence.
4. User-local 30-sample extended evidence.
5. Bybit public source research against common contract.
6. OKX public source research against common contract.
