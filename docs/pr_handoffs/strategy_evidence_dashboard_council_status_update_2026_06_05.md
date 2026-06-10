# Strategy Evidence Dashboard Council Status Update v0

## 1. 작업 목적

- Manual Strategy Evidence Dashboard에 Council Handoff Status column을 추가한 docs-only PR임을 기록한다.
- Council Review Handoff Criteria Planning v0를 반영한다.
- Council auto-call / alert / execution / active promotion이 아니다.
- `NO_TRADE_ONLY` 유지.

## 2. 변경 파일

- `docs/strategy_evidence_dashboard.md`
- `docs/pr_handoffs/strategy_evidence_dashboard_council_status_update_2026_06_05.md`

## 3. Council status update summary

- `council_handoff_status` column 추가.
- Council handoff status legend 추가.
- `mark_orderbook_gap_hunt_v0` = `NO_EDGE_ARCHIVE` + `POLICY_REVIEW`.
- `spot_futures_basis_v0` = `NO_EDGE_ARCHIVE` + `POLICY_REVIEW`.
- Future strategies = `FUTURE`.
- `orderbook_imbalance_v0` = `NOT_REVIEW_READY`.
- Tether/global reference = `NEED_DATA_TRIAGE` / `POLICY_REVIEW`.
- `cross_exchange_spot_spread_v1` = `ACTIVE_BASELINE` / not part of new experimental review.

## 4. Interpretation

- Council Handoff Status는 manual review classification이다.
- Execution permission이 아니다.
- Council auto-call이 아니다.
- Alert가 아니다.
- Active promotion이 아니다.
- `WATCH` / `REJECT` / `NEED_DATA`는 analysis-only label이다.
- `NO_EDGE_ARCHIVE`는 no-edge archival state이며 failure가 아니다.

## 5. Source-of-truth policy

- `docs/pr_handoffs/*.md`가 source-of-truth다.
- Generated JSON source 금지.
- Council criteria planning handoff를 기준으로 status taxonomy를 적용한다.
- Dashboard row는 source handoff path를 유지한다.

## 6. Explicitly not doing now

이번 PR에서 명시적으로 하지 않는 것:

- Council auto-call 구현 없음.
- Council runtime 구현 없음.
- Council packet builder 구현 없음.
- Alert 구현 없음.
- Execution 구현 없음.
- Active promotion 없음.
- Dashboard generator 없음.
- JSON/YAML dashboard 없음.
- Source/runtime behavior 변경 없음.
- Config/registry 변경 없음.
- Live endpoint 호출 없음.
- `sample_market_data` 실행 없음.
- `collect_market_data` 실행 없음.
- Generated market JSON 생성/commit 없음.
- Private API 없음.
- Credentials 없음.
- Account/balance/position/order/cancel/withdraw/deposit/transfer 없음.
- Auto-trading 없음.
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

- Docs-only PR이므로 dashboard markdown 변경과 handoff 문서 1개를 revert/remove하면 된다.
- Code/config/registry/runtime/parser/readiness/test/fixture/generated-data rollback은 필요 없다.
- Confirm GitHub Files changed contains only the dashboard markdown and this handoff file after rollback.
- Re-run required validation commands if rollback evidence is requested.

## 10. Next PR candidates

다음 PR 후보:

1. Timestamp / Clock-Skew Policy Planning v0.
2. Depth/VWAP Planning v0.
3. Next Experimental Strategy Selection v0.
4. Optional dashboard schema tests / generated dashboard planning later.
