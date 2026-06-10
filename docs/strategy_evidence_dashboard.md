# Strategy Evidence Dashboard / Journal Summary

## 1. 문서 목적

이 문서는 Strategy Evidence Dashboard / Journal Summary의 첫 manual dashboard다.

- 이 문서는 trading signal이 아니다.
- 이 문서는 Council auto-call이 아니다.
- 이 문서는 alert / execution / active promotion을 트리거하지 않는다.
- Source-of-truth는 `docs/pr_handoffs/*.md`이다.
- Generated JSON은 source-of-truth가 아니며 commit 금지다.
- `NO_TRADE_ONLY` 유지.

## 2. Dashboard metadata

| Field | Value |
| --- | --- |
| dashboard_version | `manual_v0` |
| updated_at | `2026-06-05` |
| active_strategy | `cross_exchange_spot_spread_v1` |
| execution_policy | `NO_TRADE_ONLY` |
| source_policy | `docs/pr_handoffs` evidence summary only |
| generated_json_source | `forbidden` |
| dashboard_status | manual / docs-only |

## 3. Strategy dashboard table

| Strategy | Strategy ID | Status | Active? | NO_TRADE_ONLY? | Venue Coverage | Latest Evidence Status | 30x Evidence | Persistence Status | Council Handoff Status | Council Recommended | Positive Net Count | Readiness Pass Count | Key Watch Items | Current Recommendation | Next Action | Primary Source Handoff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `cross_exchange_spot_spread_v1` | `cross_exchange_spot_spread_v1` | active baseline | yes | yes | Upbit / Bithumb spot spread baseline | active baseline / existing governance | `not_applicable` | `not_applicable` | `ACTIVE_BASELINE` / not part of new experimental Council review; keep active baseline; no new execution behavior implied | `not_applicable` | `not_applicable` | `not_applicable` | generated_json_commit_ban | Keep as active baseline, no new execution behavior. | Future inventory / dashboard source clarification. | Governance / future inventory needed. |
| `tether_cross_market_premium / usdt_krw_global_reference_v0` | `usdt_krw_global_reference_v0` | experimental / non-active / `NO_TRADE_ONLY` | no | yes | Domestic USDT/KRW + global reference context | experimental reference context | `not_applicable` | `unknown` | `NEED_DATA_TRIAGE` / `POLICY_REVIEW`; reference context, domestic/global reference semantics, non-active | `not_applicable` | `unknown` | `unknown` | last_price_weak_context_only; generated_json_commit_ban | Keep non-active, track as reference/context strategy. | Future dashboard row refinement. | `docs/pr_handoffs/strategy_market_data_requirements_matrix_2026_06_05.md` and relevant tether/global reference handoffs if present. |
| `orderbook_imbalance_v0` | `orderbook_imbalance_v0` | experimental / non-active / `NO_TRADE_ONLY` | no | yes | Future / baseline row | `PLANNING_ONLY` | `not_applicable` | `unknown` | `NOT_REVIEW_READY`; experimental/non-active, insufficient reviewed evidence in dashboard | `not_applicable` | `unknown` | `unknown` | top_of_book_liquidity_not_fill_feasibility; generated_json_commit_ban | Keep non-active. | Future evidence inventory. | `docs/pr_handoffs/strategy_market_data_requirements_matrix_2026_06_05.md` |
| `mark_orderbook_gap_hunt_v0` | `mark_orderbook_gap_hunt_v0` | experimental / non-active / `NO_TRADE_ONLY` | no | yes | Binance / Bybit / OKX | `COMPARATIVE_SUMMARY_COMPLETE` | complete | `NO_PERSISTENT_EDGE` | `NO_EDGE_ARCHIVE` + `POLICY_REVIEW`; comparative summary complete, `REJECT` / `NO_PERSISTENT_EDGE`, positive net evidence absent, timestamp/data_age and OKX index/reference watch items | false | 0 in summarized baseline | 0 in summarized baseline | timestamp_data_age_watch; negative_data_age_watch; OKX index_price=None / index reference semantics; mark_price_not_executable; non_positive_estimated_net_basis or net gap equivalent | Keep experimental / non-active / `NO_TRADE_ONLY`. | Timestamp policy / OKX index semantics / depth or common dashboard review. | `docs/pr_handoffs/mark_orderbook_gap_multi_venue_comparative_summary_2026_06_05.md` |
| `spot_futures_basis_v0` | `spot_futures_basis_v0` | proposed / experimental / non-active / `NO_TRADE_ONLY` | no | yes | Binance + Bybit; OKX deferred | `COMPARATIVE_SUMMARY_COMPLETE` | Binance complete, Bybit complete | `NO_PERSISTENT_EDGE` | `NO_EDGE_ARCHIVE` + `POLICY_REVIEW`; comparative summary complete, `REJECT` / `NO_PERSISTENT_EDGE`, positive net basis absent, top-of-book/depth/VWAP/timestamp/mark-index-funding context watch items | false | 0 | 0 | top_of_book_liquidity_not_fill_feasibility; mark_price_not_executable; funding_rate_not_basis; depth_vwap_not_implemented; negative_data_age_watch; non_positive_estimated_net_basis; OKX deferred | Keep experimental / non-active / `NO_TRADE_ONLY`. | Council criteria / timestamp policy / depth-VWAP planning, not active promotion. | `docs/pr_handoffs/spot_futures_basis_binance_bybit_comparative_summary_2026_06_05.md` |
| `funding_rate_context_v0` | `funding_rate_context_v0` | future / proposed | no | yes | Future | `FUTURE` | `not_applicable` | `not_applicable` | `FUTURE`; future/proposed strategy row only | `not_applicable` | `not_applicable` | `not_applicable` | funding_rate_not_basis; generated_json_commit_ban | Planning only later. | Next experimental selection. | `docs/pr_handoffs/next_big_project_phase_planning_2026_06_05.md`; `docs/pr_handoffs/strategy_market_data_requirements_matrix_2026_06_05.md` |
| `derivatives_flow_context_v0` | `derivatives_flow_context_v0` | future / proposed | no | yes | Future | `FUTURE` | `not_applicable` | `not_applicable` | `FUTURE`; future/proposed strategy row only | `not_applicable` | `not_applicable` | `not_applicable` | generated_json_commit_ban | Planning only later. | Next experimental selection. | `docs/pr_handoffs/next_big_project_phase_planning_2026_06_05.md`; `docs/pr_handoffs/strategy_market_data_requirements_matrix_2026_06_05.md` |
| `trade_flow_momentum_v0` | `trade_flow_momentum_v0` | future / proposed | no | yes | Future | `FUTURE` | `not_applicable` | `not_applicable` | `FUTURE`; future/proposed strategy row only | `not_applicable` | `not_applicable` | `not_applicable` | generated_json_commit_ban | Planning only later. | Next experimental selection. | `docs/pr_handoffs/next_big_project_phase_planning_2026_06_05.md`; `docs/pr_handoffs/strategy_market_data_requirements_matrix_2026_06_05.md` |

## 4. Evidence status legend

- `NOT_STARTED`: evidence work has not started.
- `PLANNING_ONLY`: planning docs exist; no evidence baseline is claimed.
- `MOCKED_ONLY`: mocked/unit evidence exists.
- `COLLECT_SMOKE_COMPLETE`: collect smoke evidence summary exists.
- `SAMPLING_3X_COMPLETE`: 3-sample sampling evidence summary exists.
- `SAMPLING_30X_COMPLETE`: 30-sample extended sampling evidence summary exists.
- `COMPARATIVE_SUMMARY_COMPLETE`: comparative summary handoff exists.
- `NEEDS_TRIAGE`: evidence indicates a data/metadata follow-up is needed.
- `DEFERRED`: scope is deferred to future expansion.
- `FUTURE`: candidate exists only as a future idea.

Each status is evidence tracking status and is not execution permission.

## 5. Council handoff status legend

- `ACTIVE_BASELINE`: active baseline strategy; not part of new experimental Council review in this planning.
- `NOT_REVIEW_READY`: planning-only / mocked-only / insufficient evidence.
- `NEED_DATA_TRIAGE`: parser missing fields, diagnostics error, schema validation failure, venue response shape issue, missing source handoff path, conflicting evidence.
- `POLICY_REVIEW`: timestamp/data_age, OKX index/reference, depth/VWAP, symbol/product semantics, mark/funding/last-price context policy item.
- `NO_EDGE_ARCHIVE`: samples OK, parser OK, `required_missing_fields` empty, all/repeated `REJECT`, `positive_net_gap_count=0`, `readiness_pass_count=0`, `NO_PERSISTENT_EDGE`.
- `MANUAL_REVIEW_CANDIDATE`: repeated `WATCH` or positive net evidence with parser OK, missing fields empty, no-trade metadata preserved.
- `DEFERRED`: explicitly scoped future expansion.
- `FUTURE`: proposed/future strategy, not yet evidence-ready.

Council handoff status is not execution permission. `MANUAL_REVIEW_CANDIDATE` is not `ENTER`. Council review is not Council auto-call, alert, or execution.

## 6. Watch item legend

- `timestamp_data_age_watch`
- `negative_data_age_watch`
- `OKX index_price=None / index reference semantics`
- `mark_price_not_executable`
- `last_price_weak_context_only`
- `funding_rate_not_basis`
- `depth_vwap_not_implemented`
- `top_of_book_liquidity_not_fill_feasibility`
- `symbol_product_semantics_mismatch`
- `non_positive_estimated_net_basis`
- `no_persistent_edge`
- `generated_json_commit_ban`

## 7. Source handoff index

### `mark_orderbook_gap_hunt_v0`

- Primary: `docs/pr_handoffs/mark_orderbook_gap_multi_venue_comparative_summary_2026_06_05.md`.
- Secondary:
  - Timestamp policy planning.
  - OKX index/reference planning.
  - Venue evidence docs.

### `spot_futures_basis_v0`

- Primary: `docs/pr_handoffs/spot_futures_basis_binance_bybit_comparative_summary_2026_06_05.md`.
- Secondary:
  - `docs/pr_handoffs/spot_futures_basis_binance_sampling_30x_evidence_2026_06_05.md`.
  - `docs/pr_handoffs/spot_futures_basis_bybit_sampling_30x_evidence_2026_06_05.md`.
  - `docs/pr_handoffs/strategy_evidence_dashboard_journal_summary_planning_2026_06_05.md`.
  - `docs/pr_handoffs/strategy_evidence_dashboard_handoff_index_data_source_planning_2026_06_05.md`.

### Future strategies

- `docs/pr_handoffs/next_big_project_phase_planning_2026_06_05.md`.
- `docs/pr_handoffs/strategy_market_data_requirements_matrix_2026_06_05.md`.

## 8. Relationship to Council criteria

- Dashboard is evidence inventory.
- Council criteria interprets dashboard rows.
- This dashboard update only records manual `council_handoff_status`.
- It does not create Council runtime, Council packet, alert, or execution behavior.
- Future Council review packets, if any, require separate planning/approval.

## 9. What this dashboard must not imply

- Dashboard는 trading signal이 아니다.
- Council Handoff Status는 trading signal이 아니다.
- `WATCH`는 `ENTER`가 아니다.
- `REJECT`는 failure가 아니다.
- `NO_PERSISTENT_EDGE`는 adapter failure가 아니다.
- `NO_EDGE_ARCHIVE`는 실패가 아니다.
- `POLICY_REVIEW`는 trading edge가 아니다.
- `MANUAL_REVIEW_CANDIDATE`도 `ENTER`가 아니다.
- `council_recommended=false`는 정상 no-edge일 수 있다.
- Dashboard는 alert, Council auto-call, execution, active promotion을 trigger하지 않는다.
- Dashboard row가 Council auto-call을 trigger하지 않는다.
- Dashboard는 private API / account / order feasibility를 암시하지 않는다.

## 10. Update policy

- 새 collect evidence, 3x evidence, 30x evidence, comparative summary가 merge되면 dashboard를 수동 갱신한다.
- 새 evidence나 Council criteria 변경이 merge되면 `council_handoff_status`도 수동 갱신한다.
- Generated JSON을 직접 참조하지 않는다.
- Dashboard row에는 source handoff path를 유지한다.
- Missing field는 `unknown` / `not_provided` / `not_applicable`로 두고 임의 추정하지 않는다.

## 11. No-trade compliance

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

## 12. Generated JSON commit 금지

Generated JSON policy 확인:

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- Dashboard는 generated JSON 원본이 아니라 handoff evidence summary를 기반으로 한다.
- 이번 PR에는 generated JSON을 추가하지 않는다.

## 13. Next update candidates

- Timestamp / Clock-Skew Policy Planning v0.
- Depth/VWAP Planning v0.
- Next Experimental Strategy Selection v0.
- Optional dashboard schema tests / generated dashboard planning later.
