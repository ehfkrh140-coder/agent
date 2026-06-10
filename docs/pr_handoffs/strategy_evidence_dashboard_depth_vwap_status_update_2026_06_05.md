# Strategy Evidence Dashboard Depth/VWAP Status Update v0

## 1. 작업 목적

이 문서는 Manual Strategy Evidence Dashboard에 Depth/VWAP status를 반영한 docs-only PR을 기록한다.

Purpose:

- 최근 Depth/VWAP planning, pure helper, mocked fixture contracts, packet/candidate context integration, sampling summary support 흐름을 dashboard에 연결했다.
- `docs/strategy_evidence_dashboard.md`에 `Depth/VWAP Status` column을 추가했다.
- Depth/VWAP status legend와 source handoff index를 추가했다.
- No behavior change.
- `NO_TRADE_ONLY` 유지.

This PR is documentation-only. It does not implement Depth/VWAP logic, sampling logic, readiness changes, dashboard generation, alerting, Council auto-call, execution, or active promotion.

## 2. 변경 파일

Changed files:

- `docs/strategy_evidence_dashboard.md`
- `docs/pr_handoffs/strategy_evidence_dashboard_depth_vwap_status_update_2026_06_05.md`

No source, tests, fixtures, config, registry, tools, generated JSON, or OKX implementation files were changed.

## 3. Depth/VWAP status update summary

Depth/VWAP status update summary:

- Added `Depth/VWAP Status` column to the manual dashboard strategy table.
- Added Depth/VWAP status legend.
- Added Depth/VWAP source handoff index.
- `spot_futures_basis_v0` = `PACKET_CONTEXT_SUPPORTED` + `SAMPLING_SUMMARY_SUPPORTED` + `READINESS_UNCHANGED`.
- `mark_orderbook_gap_hunt_v0` = `WATCH_ITEM_ONLY` / future diagnostics candidate.
- `cross_exchange_spot_spread_v1` = `NOT_APPLICABLE` for this update because the active baseline policy is unchanged.
- `tether_cross_market_premium / usdt_krw_global_reference_v0` = `NOT_APPLICABLE` / reference-context strategy.
- `orderbook_imbalance_v0` and future strategy rows = `FUTURE` or future/not-integrated status.
- No readiness behavior change.
- No trading signal, execution permission, alert, Council auto-call, or active promotion implication.

## 4. Interpretation

Interpretation:

- Depth/VWAP status is evidence/infrastructure status.
- It is not a trading signal.
- It is not execution permission.
- It is not Council auto-call.
- It is not alert.
- It is not active promotion.
- VWAP-adjusted readiness is not implemented.
- `PACKET_CONTEXT_SUPPORTED` means diagnostics-only context can be carried in packet/candidate extensions.
- `SAMPLING_SUMMARY_SUPPORTED` means sampling summary can aggregate diagnostics-only context if present.
- `READINESS_UNCHANGED` means VWAP context does not change readiness, estimated net gap, persistence, or Council recommendation.

## 5. Source-of-truth policy

Source-of-truth policy:

- `docs/pr_handoffs` remains the source-of-truth.
- Generated JSON source is forbidden.
- This dashboard update is based on Depth/VWAP handoff docs, not generated packet/sample JSON.
- Dashboard rows preserve source handoff paths.
- Future Depth/VWAP implementation, dashboard criteria, or readiness policy changes require manual dashboard update after merge.

Depth/VWAP handoff sources:

- `docs/pr_handoffs/strategy_common_depth_vwap_planning_2026_06_05.md`
- `docs/pr_handoffs/depth_vwap_pure_helper_implementation_2026_06_05.md`
- `docs/pr_handoffs/depth_vwap_mocked_fixture_files_2026_06_05.md`
- `docs/pr_handoffs/depth_vwap_packet_context_integration_2026_06_05.md`
- `docs/pr_handoffs/depth_vwap_sampling_summary_context_support_2026_06_05.md`

## 6. Explicitly not doing now

Explicitly not doing now:

- Depth/VWAP implementation 없음.
- Sampling code change 없음.
- Packet builder change 없음.
- Readiness behavior 변경 없음.
- VWAP-adjusted readiness 없음.
- Generated dashboard script 없음.
- JSON/YAML dashboard 없음.
- Source/runtime behavior 변경 없음.
- Config/registry 변경 없음.
- Active strategy 변경 없음.
- Live endpoint 호출 없음.
- `sample_market_data` 실행 없음.
- `collect_market_data` 실행 없음.
- Generated market JSON 생성/commit 없음.
- Private API 없음.
- Credentials 없음.
- Account/balance/position/order/cancel/withdraw/deposit/transfer 없음.
- Auto-trading 없음.
- Council auto-call 없음.
- Alert 없음.
- Execution 없음.
- OKX `spot_futures_basis` implementation 없음.

## 7. No-trade compliance

No-trade compliance 확인:

- Active strategy promotion 없음.
- Experimental strategy active 승격 없음.
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
- Dashboard는 generated JSON 원본이 아니라 handoff evidence summary를 기반으로 한다.
- 이번 PR에는 generated JSON을 추가하지 않는다.

## 9. Rollback plan

Rollback plan:

1. Revert this PR.
2. Revert the dashboard markdown changes in `docs/strategy_evidence_dashboard.md`.
3. Remove `docs/pr_handoffs/strategy_evidence_dashboard_depth_vwap_status_update_2026_06_05.md`.
4. No code/config/registry/runtime/parser/readiness/test/fixture/generated-data rollback is needed.
5. Re-run required validation commands if rollback evidence is requested.

## 10. Next PR candidates

다음 PR 후보:

1. Next Experimental Strategy Selection v0.
2. VWAP-adjusted readiness policy only after separate approval and stronger evidence.
3. Optional generated dashboard planning later.
