# Manual Strategy Evidence Dashboard Markdown v0 Handoff

## 1. 작업 목적

- Manual Strategy Evidence Dashboard Markdown v0를 추가한 docs-only PR임을 기록한다.
- Dashboard는 generated JSON이 아니라 handoff evidence summary 기반임을 기록한다.
- `NO_TRADE_ONLY`를 유지한다.
- Active strategy는 `cross_exchange_spot_spread_v1`로 유지한다.

## 2. 변경 파일

- `docs/strategy_evidence_dashboard.md`
- `docs/pr_handoffs/strategy_evidence_manual_dashboard_v0_2026_06_05.md`

## 3. Dashboard contents summary

Dashboard contents:

- Strategy rows included:
  - `cross_exchange_spot_spread_v1`
  - `tether_cross_market_premium / usdt_krw_global_reference_v0`
  - `orderbook_imbalance_v0`
  - `mark_orderbook_gap_hunt_v0`
  - `spot_futures_basis_v0`
  - `funding_rate_context_v0`
  - `derivatives_flow_context_v0`
  - `trade_flow_momentum_v0`
- Evidence status legend included.
- Watch item legend included.
- Source handoff index included.
- Update policy included.

## 4. Source-of-truth policy

- `docs/pr_handoffs/*.md`가 source-of-truth다.
- Generated JSON source 금지.
- Conflicting metadata는 comparative summary / newest step-specific handoff를 우선한다.
- Dashboard row는 source handoff path를 유지해야 한다.
- Missing field는 `unknown` / `not_provided` / `not_applicable`로 두고 임의 추정하지 않는다.

## 5. Explicitly not doing now

이번 PR에서 명시적으로 하지 않는 것:

- Generated dashboard script 없음.
- JSON/YAML dashboard file 없음.
- Source/runtime behavior 변경 없음.
- Config/registry 변경 없음.
- Active strategy 변경 없음.
- Live endpoint 호출 없음.
- `sample_market_data` 실행 없음.
- `collect_market_data` 실행 없음.
- Generated market JSON 생성/commit 없음.
- Alert 없음.
- Council auto-call 없음.
- Execution 없음.
- Private API 없음.
- Credentials 없음.
- Account/balance/position/order/cancel/withdraw/deposit/transfer 없음.
- Auto-trading 없음.
- OKX `spot_futures_basis` implementation 없음.

## 6. No-trade compliance

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

## 7. Generated JSON commit 금지

Generated JSON policy 확인:

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- Dashboard는 generated JSON 원본이 아니라 handoff evidence summary를 기반으로 한다.
- 이번 PR에는 generated JSON을 추가하지 않음.

## 8. Rollback plan

Rollback plan:

- Docs-only PR이므로 dashboard markdown과 handoff 문서 2개를 제거하면 된다.
- Code/config/registry/runtime/parser/readiness/test/fixture/generated-data rollback은 필요 없다.
- Confirm GitHub Files changed contains only the two dashboard docs after rollback.
- Re-run required validation commands if rollback evidence is requested.

## 9. Next PR candidates

다음 PR 후보:

1. Council Review Handoff Criteria Planning v0.
2. Timestamp / Clock-Skew Policy Planning v0.
3. Depth/VWAP Planning v0.
4. Next Experimental Strategy Selection v0.
5. Optional dashboard schema tests / generated dashboard planning later.
