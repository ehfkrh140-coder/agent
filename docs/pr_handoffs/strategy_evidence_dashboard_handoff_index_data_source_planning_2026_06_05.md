# Handoff Index / Data Source Planning for Strategy Evidence Dashboard v0

## 1. 작업 목적

이 문서는 Strategy Evidence Dashboard / Journal Summary가 사용할 data source와 handoff index policy를 planning-only로 설계한다.

목적:

- Strategy Evidence Dashboard / Journal Summary의 data source와 handoff index policy를 설계한다.
- 이번 문서는 implementation이 아니라 planning이다.
- Dashboard는 generated JSON 원본이 아니라 `docs/pr_handoffs` evidence summary를 기반으로 해야 한다.
- `NO_TRADE_ONLY`를 유지한다.
- Active strategy는 `cross_exchange_spot_spread_v1`로 유지한다.

## 2. Problem statement

Problem statement:

- `docs/pr_handoffs` 문서가 많아져 dashboard row를 만들 때 어떤 문서를 우선해야 하는지 명확히 해야 한다.
- PR title/body는 generic/cumulative처럼 보일 수 있어 step-specific handoff가 source-of-truth다.
- Generated `data/market_samples/*.json` 및 `data/generated_packets/*.json`는 smoke artifact이며 commit 금지라 dashboard source로 삼으면 안 된다.
- Dashboard row에는 source handoff path가 반드시 있어야 한다.
- Latest evidence와 comparative summary의 우선순위가 필요하다.

## 3. Source-of-truth hierarchy

Dashboard source-of-truth hierarchy:

1. Strategy-specific comparative summary handoff.
   - 예: `docs/pr_handoffs/mark_orderbook_gap_multi_venue_comparative_summary_2026_06_05.md`.
   - 예: `docs/pr_handoffs/spot_futures_basis_binance_bybit_comparative_summary_2026_06_05.md`.
2. Latest 30-sample extended sampling evidence.
   - 예: `docs/pr_handoffs/spot_futures_basis_binance_sampling_30x_evidence_2026_06_05.md`.
   - 예: `docs/pr_handoffs/spot_futures_basis_bybit_sampling_30x_evidence_2026_06_05.md`.
   - 예: mark-orderbook-gap venue 30x evidence docs.
3. 3-sample sampling evidence.
4. Collect smoke evidence.
5. Planning/research/commonization docs.
6. Generated JSON is not source-of-truth and must not be committed.

Policy details:

- Dashboard는 source handoff path를 기록해야 한다.
- Conflicting metadata가 있으면 newer step-specific handoff와 comparative summary를 우선한다.
- Generated JSON path는 source-of-truth로 사용하지 않는다.
- PR body/title보다 task-specific handoff evidence를 우선한다.

## 4. Initial handoff index candidate

### `cross_exchange_spot_spread_v1`

- Source candidates:
  - active baseline / existing governance docs.
  - future active-strategy inventory handoff if created later.
- No new execution behavior implied.
- Source handoff may need future inventory.
- Dashboard status: active baseline.

### `tether_cross_market_premium` / `usdt_krw_global_reference_v0`

- Source candidates:
  - `docs/pr_handoffs/strategy_market_data_requirements_matrix_2026_06_05.md`.
  - Relevant tether/global reference handoff docs if present.
- Status: experimental / non-active / `NO_TRADE_ONLY`.
- Dashboard row should keep domestic/global context visible without implying active promotion.

### `orderbook_imbalance_v0`

- Source candidates:
  - `docs/pr_handoffs/strategy_market_data_requirements_matrix_2026_06_05.md`.
- Future evidence row only.
- Status: experimental / non-active / `NO_TRADE_ONLY`.

### `mark_orderbook_gap_hunt_v0`

- Primary source:
  - `docs/pr_handoffs/mark_orderbook_gap_multi_venue_comparative_summary_2026_06_05.md`.
- Secondary sources:
  - Timestamp/clock-skew planning.
  - OKX index/reference semantics planning.
  - Binance/Bybit/OKX evidence docs.
- Status: experimental / non-active / `NO_TRADE_ONLY`.
- Dashboard row should emphasize no active promotion and no persistent positive net edge evidence.

### `spot_futures_basis_v0`

- Primary source:
  - `docs/pr_handoffs/spot_futures_basis_binance_bybit_comparative_summary_2026_06_05.md`.
- Secondary sources:
  - `docs/pr_handoffs/spot_futures_basis_binance_sampling_30x_evidence_2026_06_05.md`.
  - `docs/pr_handoffs/spot_futures_basis_bybit_sampling_30x_evidence_2026_06_05.md`.
  - `docs/pr_handoffs/strategy_evidence_dashboard_journal_summary_planning_2026_06_05.md` as dashboard planning source.
- Status: proposed / experimental / non-active / `NO_TRADE_ONLY`.
- OKX deferred.

### Future strategies

- Future rows:
  - `funding_rate_context_v0`.
  - `derivatives_flow_context_v0`.
  - `trade_flow_momentum_v0`.
- Source candidates:
  - `docs/pr_handoffs/next_big_project_phase_planning_2026_06_05.md`.
  - `docs/pr_handoffs/strategy_market_data_requirements_matrix_2026_06_05.md`.
- Status: proposed / future only until separate planning and evidence exist.

## 5. Dashboard row extraction fields

For each strategy row, extraction candidates:

- `strategy_family`
- `strategy_id`
- `status`
- `active_flag`
- `no_trade_only`
- `execution_policy`
- `venue_coverage`
- `latest_collect_smoke_status`
- `latest_3_sample_status`
- `latest_30_sample_status`
- `latest_comparative_summary_status`
- `samples_ok`
- `samples_error`
- `readiness_status_counts`
- `parser_status_counts`
- `required_missing_fields_count`
- `positive_net_gap_count`
- `readiness_pass_count`
- `persistence_status`
- `council_recommended`
- `watch_items`
- `current_recommendation`
- `next_action`
- `source_handoff_paths`
- `rollback_reference`

Extraction policy:

- 없는 field는 `unknown` / `not_provided` / `not_applicable`로 두고 임의로 추정하지 않는다.
- Dashboard value는 evidence를 요약하는 것이지 trading permission이 아니다.
- Extracted fields must preserve no-trade posture and source handoff path.

## 6. Evidence status taxonomy

Evidence status candidates:

| Status | Meaning | Execution implication |
| --- | --- | --- |
| `NOT_STARTED` | Evidence work has not started. | None. |
| `PLANNING_ONLY` | Planning docs exist, but no implementation/evidence baseline is claimed. | None. |
| `MOCKED_ONLY` | Mocked/unit evidence exists. | None. |
| `COLLECT_SMOKE_COMPLETE` | User-local or mocked collect smoke evidence summary exists. | None. |
| `SAMPLING_3X_COMPLETE` | 3-sample sampling evidence summary exists. | None. |
| `SAMPLING_30X_COMPLETE` | 30-sample extended sampling evidence summary exists. | None. |
| `COMPARATIVE_SUMMARY_COMPLETE` | Comparative summary handoff exists. | None. |
| `NEEDS_TRIAGE` | Evidence indicates a data/metadata issue requiring follow-up. | None. |
| `DEFERRED` | Scope is deferred to future expansion. | None. |
| `FUTURE` | Candidate exists only as a future idea. | None. |

Each status is evidence tracking only. It is not execution permission and does not mean active promotion.

## 7. Watch item taxonomy

Initial watch item taxonomy:

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

Watch item policy:

- Watch item presence is not a trading signal.
- Watch item presence should link back to source handoff paths.
- Watch item wording should avoid implying order feasibility or fill feasibility.

## 8. Manual dashboard source map option

Option A: manual source map markdown.

Candidate columns:

- Strategy row.
- Primary handoff path.
- Secondary handoff paths.
- Latest evidence status.
- Update trigger.
- Owner / reviewer.

장점:

- 안전함.
- Generated JSON 없음.
- 초보자가 읽기 쉬움.
- Reviewers can audit source handoff paths directly.

단점:

- 사람이 갱신해야 함.
- Drift can happen if reviewers forget to update rows after evidence PRs.

Recommendation:

- Start with Option A before any generator implementation.

## 9. Future generated dashboard source map option

Option B: future generator planning.

Future possibility:

- A generated dashboard script could read handoff markdown.
- Schema governance is required before implementation.
- Parser drift risk exists.
- The script must not read generated market JSON as source-of-truth.
- Policy is needed to decide whether output dashboard markdown is a generated artifact or committed doc.

Recommendation:

- 지금은 Option A manual source map planning을 유지한다.
- 구현 전 Council criteria planning과 manual dashboard markdown v0를 먼저 진행한다.
- Future generator planning must include tests and no-trade/private-field guardrails before implementation.

## 10. Validation / review policy

Validation and review policy:

- Dashboard row는 source handoff path 없이 추가하면 안 된다.
- Generated JSON path를 source로 쓰면 안 된다.
- Active promotion / execution wording이 들어가면 안 된다.
- `WATCH` is not `ENTER`.
- `REJECT` is not failure.
- `NO_PERSISTENT_EDGE` is not adapter failure.
- `council_recommended=false` can be normal no-edge.
- Any future automated dashboard must have tests that forbid private/account/order/execution fields.
- Any future dashboard row should preserve `NO_TRADE_ONLY` posture unless a separate approved active-strategy change exists.

## 11. Relationship to next manual dashboard PR

Relationship:

- 이 PR은 data source planning이다.
- 다음 구현 후보는 Manual Dashboard Markdown v0 또는 Council Review Handoff Criteria Planning v0다.
- Manual dashboard는 처음에는 docs-only markdown으로 작성하고, 각 row에 handoff path를 명시해야 한다.
- 아직 generated dashboard script는 하지 않는다.
- Manual dashboard should use this source hierarchy and extraction field list as its review checklist.

## 12. Explicitly not doing now

이번 PR에서 명시적으로 하지 않는 것:

- Manual dashboard markdown 생성 없음.
- Dashboard implementation 없음.
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

## 13. OKX deferred scope note

- `spot_futures_basis_v0` OKX는 future expansion으로 defer한다.
- 이는 scope control이지 permanent rejection이 아니다.
- 이번 PR에서는 OKX research/adapter/config를 만들지 않는다.

## 14. No-trade compliance

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

## 15. Generated JSON commit 금지

Generated JSON policy 확인:

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- Dashboard source map은 generated JSON 원본이 아니라 handoff evidence summary를 기반으로 해야 한다.
- 이번 PR에는 generated JSON을 추가하지 않음.

## 16. Rollback plan

Rollback plan:

- Docs-only PR이므로 revert하고 이 handoff 문서 1개를 제거하면 된다.
- Code/config/registry/runtime/parser/readiness/test/fixture/generated-data rollback은 필요 없다.
- Confirm GitHub Files changed contains only this handoff file after rollback.
- Re-run required validation commands if rollback evidence is requested.

## 17. Next PR candidates

다음 PR 후보 순서:

1. Manual Dashboard Markdown v0.
2. Council Review Handoff Criteria Planning v0.
3. Timestamp / Clock-Skew Policy Planning v0.
4. Depth/VWAP Planning v0.
5. Next Experimental Strategy Selection v0.
