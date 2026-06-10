# Spot-Futures Basis Binance + Bybit Comparative Summary v0

## 1. 작업 목적

이 문서는 `spot_futures_basis_v0`의 Binance + Bybit public-read-only baseline을 비교 정리하는 docs-only close-out summary다.

목적:

- Binance + Bybit `spot_futures_basis_v0` baseline을 비교 정리한다.
- 이번 summary는 Binance + Bybit cycle close-out 문서다.
- OKX는 future expansion으로 defer한다.
- Profitability / persistent edge 증명이 아니다.
- `NO_TRADE_ONLY`를 유지한다.

## 2. Strategy scope

| Field | Value |
| --- | --- |
| `strategy_family` | `spot_futures_basis` |
| `strategy_id` | `spot_futures_basis_v0` |
| `status` | proposed / experimental / non-active / `NO_TRADE_ONLY` |
| Active strategy | `cross_exchange_spot_spread_v1` remains active |
| `comparison_type` | `same_exchange_spot_perp_basis` |
| Scope | Binance + Bybit only for this cycle |
| OKX | deferred / future expansion |

## 3. Binance baseline recap

Binance baseline recap:

- `adapter_id: live_binance_spot_futures_basis_btcusdt`.
- Collect smoke success.
- 3-sample sampling evidence complete.
- 30-sample extended sampling evidence complete.

Binance 30-sample evidence:

| Field | Value |
| --- | --- |
| `samples_requested` | `30` |
| `samples_ok` | `30` |
| `samples_error` | `0` |
| `candidate_seen_count` | `30` |
| `readiness_status_counts` | `{'REJECT': 30}` |
| `sample_parser_statuses` | `{'OK': 30}` |
| `samples_with_required_missing_fields` | `0` |
| `diagnostics_count_distribution` | `{7: 30}` |
| `positive_net_gap_count` | `0` |
| `readiness_pass_count` | `0` |
| `persistence_status` | `NO_PERSISTENT_EDGE` |
| `council_recommended` | `false` |
| `min_estimated_net_gap_pct` | `-0.1602191209077834` |
| `max_estimated_net_gap_pct` | `-0.13967667333565484` |
| `avg_estimated_net_gap_pct` | `-0.14763819394759045` |

## 4. Bybit baseline recap

Bybit baseline recap:

- `adapter_id: live_bybit_spot_futures_basis_btcusdt`.
- Collect smoke success after orderbook category live-shape fix.
- 3-sample sampling evidence complete.
- 30-sample extended sampling evidence complete.

Bybit 30-sample evidence:

| Field | Value |
| --- | --- |
| `samples_requested` | `30` |
| `samples_ok` | `30` |
| `samples_error` | `0` |
| `candidate_seen_count` | `30` |
| `readiness_status_counts` | `{'REJECT': 30}` |
| `sample_parser_statuses` | `{'OK': 30}` |
| `samples_with_required_missing_fields` | `0` |
| `diagnostics_count_distribution` | `{6: 30}` |
| `positive_net_gap_count` | `0` |
| `readiness_pass_count` | `0` |
| `persistence_status` | `NO_PERSISTENT_EDGE` |
| `council_recommended` | `false` |
| `min_estimated_net_gap_pct` | `-0.16557374120872367` |
| `max_estimated_net_gap_pct` | `-0.14965088573836977` |
| `avg_estimated_net_gap_pct` | `-0.15713512720458947` |

## 5. Comparative evidence table

| venue | adapter_id | collect_smoke | 3_sample | 30_sample | samples_ok_30 | samples_error_30 | parser_ok_30 | missing_fields_30 | diagnostics_count | readiness_status_counts | positive_net_gap_count | readiness_pass_count | persistence_status | council_recommended | avg_estimated_net_gap_pct | key_watch_items |
| --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| Binance | `live_binance_spot_futures_basis_btcusdt` | success | complete | complete | 30 | 0 | `{'OK': 30}` | 0 | `{7: 30}` | `{'REJECT': 30}` | 0 | 0 | `NO_PERSISTENT_EDGE` | `false` | `-0.14763819394759045` | min-notional live-shape resolved; mark/funding context not executable; depth/VWAP future work |
| Bybit | `live_bybit_spot_futures_basis_btcusdt` | success after orderbook category fix | complete | complete | 30 | 0 | `{'OK': 30}` | 0 | `{6: 30}` | `{'REJECT': 30}` | 0 | 0 | `NO_PERSISTENT_EDGE` | `false` | `-0.15713512720458947` | orderbook category live-shape resolved; `funding_interval=480`; negative data age timestamp watch |

## 6. Common outcome

Common outcome:

- Both Binance and Bybit completed public-read-only collect + sampling baseline.
- Both 30-sample runs had `samples_ok=30` and `samples_error=0`.
- Both had parser `OK` for all 30 samples.
- Both had `required_missing_fields` empty.
- Both had `readiness_status_counts={'REJECT': 30}`.
- Both had `positive_net_gap_count=0` and `readiness_pass_count=0`.
- Both had `persistence_status=NO_PERSISTENT_EDGE`.
- Therefore there is no persistent positive net basis evidence in this baseline.
- This is a successful pipeline baseline, not a profitable edge proof.

## 7. Venue-specific differences

### Binance

- `diagnostics_count=7`.
- Public endpoint set includes spot + USDⓈ-M futures endpoints.
- Prior Spot `exchangeInfo` min_notional live-shape follow-up resolved `NEED_DATA`.
- Watch items currently no critical blocker in 30-sample evidence.
- Estimated net basis average around `-0.14763819394759045`.

### Bybit

- `diagnostics_count=6`.
- Public endpoint set includes Bybit V5 spot + linear endpoints.
- Prior orderbook category live-shape follow-up resolved category mismatch `NEED_DATA`.
- `funding_interval=480` context.
- `negative_data_age_watch` may appear depending timestamp alignment.
- Estimated net basis average around `-0.15713512720458947`.

## 8. Watch items

Watch items:

- `mark_price_not_executable`.
- `funding_rate_not_basis`.
- `depth_vwap_not_implemented`.
- `negative_data_age_watch` / timestamp clock-skew.
- `funding_interval=480` Bybit context.
- `non_positive_estimated_net_basis`.
- Top-of-book liquidity is not fill feasibility.
- Spot/perp symbol equality is not product equivalence.

## 9. Interpretation

Interpretation:

- `REJECT`는 collect/sampling failure가 아니다.
- `NO_PERSISTENT_EDGE`는 adapter failure가 아니다.
- Bybit/Binance pipeline은 성공했다.
- Estimated net basis가 모두 음수라 no-edge `REJECT`가 정상이다.
- Current evidence does not justify active promotion.
- Current evidence does not justify alerting.
- Current evidence does not justify Council auto-call.
- Current evidence does not justify execution.
- `WATCH` / `NEED_DATA` / `REJECT` are analysis-only labels.
- Spot/perp basis is not automatically executable edge.
- Mark/index/funding context is not executable basis.

## 10. OKX deferred scope note

- 이번 `spot_futures_basis_v0` cycle은 Binance + Bybit까지만 진행한다.
- OKX는 future expansion으로 defer한다.
- This is scope control, not permanent rejection.
- 이번 PR에서는 OKX adapter/config/research를 만들지 않는다.

## 11. No-trade compliance

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

## 12. Generated JSON commit 금지

Generated JSON policy 확인:

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- User-local generated sampling JSON은 evidence 요약 후 삭제해야 함.
- 이번 PR에는 generated JSON을 추가하지 않음.

## 13. Conclusion / recommended next phase

Conclusion:

- Binance + Bybit `spot_futures_basis_v0` public-read-only baseline is complete for this cycle.
- `spot_futures_basis_v0` should remain experimental / non-active / `NO_TRADE_ONLY`.
- Do not promote to active.
- Recommended next step is Next Big Project Phase Planning.

Future enhancement candidates:

- Depth/VWAP planning.
- Basis-specific sampling summary alias refinement if desired.
- OKX public source research as future expansion only.
- Strategy Evidence Dashboard / Journal Summary.
- Council review handoff criteria.

## 14. Rollback plan

Rollback plan:

- Docs-only PR이므로 revert하고 이 handoff 문서 1개를 제거하면 된다.
- Code/config/registry/runtime/parser/readiness/test/fixture/generated-data rollback은 필요 없다.
- Re-run repository tests if the revert PR process requires evidence.
- Confirm no generated JSON files are committed.

## 15. Next PR candidates

다음 PR 후보 순서:

1. Next Big Project Phase Planning.
2. Strategy Evidence Dashboard / Journal Summary Planning.
3. Council Review Handoff Criteria Planning.
4. Depth/VWAP Planning for `spot_futures_basis_v0`.
5. OKX public source research as future expansion only.
