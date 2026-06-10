# Council Review Handoff Criteria Planning v0

## 1. 작업 목적

이 문서는 Strategy Evidence Dashboard 이후 AI Council manual review handoff 기준을 planning-only로 설계한다.

목적:

- Strategy Evidence Dashboard 이후 AI Council manual review handoff 기준을 설계한다.
- 이번 문서는 implementation이 아니라 planning이다.
- Council auto-call이 아니다.
- Alert / execution / active promotion을 트리거하지 않는다.
- `NO_TRADE_ONLY` 유지.
- Active strategy는 `cross_exchange_spot_spread_v1`로 유지한다.

## 2. Problem statement

문제 정의:

- Dashboard는 evidence 상태를 보여주지만, 어떤 상태가 Council manual review 대상인지 아직 기준이 없다.
- `WATCH` / `NEED_DATA` / `REJECT` label을 사람이 오해할 수 있다.
- `REJECT`와 `NO_PERSISTENT_EDGE`는 실패가 아니라 정상 no-edge일 수 있다.
- Council review criteria가 없으면 dashboard row가 trading signal처럼 오해될 수 있다.
- Council auto-call과 manual Council review criteria를 분리해야 한다.

## 3. Council review goal

Council review goal:

- 어떤 strategy evidence가 manual Council review 대상인지 정의한다.
- `WATCH` / `NEED_DATA` / `REJECT` / `NO_PERSISTENT_EDGE` 의미를 명확히 한다.
- Review candidate와 execution permission을 분리한다.
- Policy watch item과 trading edge evidence를 분리한다.
- Source handoff path 기반으로 evidence를 검토한다.
- Generated JSON 원본은 review source가 아니며 commit 금지임을 유지한다.

## 4. Council handoff status taxonomy

Council handoff status 후보:

| Status | Meaning | Execution implication |
| --- | --- | --- |
| `NOT_REVIEW_READY` | Planning-only, mocked-only, collect/sampling evidence 부족. | None. |
| `NEED_DATA_TRIAGE` | Parser missing fields, parser status not OK, diagnostics failure, venue live-shape issue 등으로 data quality 확인 필요. | None. |
| `POLICY_REVIEW` | Timestamp/data_age, OKX index/reference semantics, depth/VWAP, symbol/product semantics 같은 policy watch item 검토 대상. | None. |
| `NO_EDGE_ARCHIVE` | Samples OK, parser OK, required missing empty지만 positive net evidence 없음, `REJECT` / `NO_PERSISTENT_EDGE` 반복. | None. |
| `MANUAL_REVIEW_CANDIDATE` | Repeated `WATCH` 또는 positive net basis/gap evidence가 있고, parser OK, required missing empty, no-trade metadata preserved인 경우. | None. |
| `DEFERRED` | Scope control로 future expansion에 둔 상태. | None. |
| `FUTURE` | Future strategy candidate, 아직 evidence 없음. | None. |

각 status는 execution permission이 아니며 active promotion을 의미하지 않는다.

## 5. Evidence requirements for manual review

Manual Council review candidate 최소 후보 조건:

- Source handoff path exists.
- At least collect smoke complete.
- Preferably 3-sample or 30-sample evidence complete.
- `parser_normalized_status` OK or `parser_status_counts` OK.
- `required_missing_fields` empty.
- `no_trade_only` true.
- `execution_policy` `NO_TRADE_ONLY`.
- Generated JSON not committed.
- No private API / no account / no order fields.
- `positive_net_gap_count > 0` 또는 `readiness_pass_count > 0` 또는 repeated `WATCH` evidence가 있는 경우.

Clarifications:

- 이 조건을 만족해도 execution permission이 아니다.
- 이 조건은 manual review 후보일 뿐이다.
- Active promotion은 별도 process와 훨씬 강한 evidence가 필요하다.

## 6. Current strategy classification using dashboard

### `cross_exchange_spot_spread_v1`

- Evidence: active baseline.
- Council review status: not part of new experimental review in this planning.
- Current action: keep active baseline, no new execution behavior implied.

### `mark_orderbook_gap_hunt_v0`

- Evidence: Binance / Bybit / OKX comparative summary complete.
- Current Council handoff status: `NO_EDGE_ARCHIVE` plus `POLICY_REVIEW` watch items.
- Reason: `REJECT` / `NO_PERSISTENT_EDGE`, positive net evidence absent.
- Policy watch items:
  - timestamp/data_age.
  - OKX index/reference semantics.
  - mark price not executable.

### `spot_futures_basis_v0`

- Evidence: Binance + Bybit comparative summary complete.
- Current Council handoff status: `NO_EDGE_ARCHIVE` plus `POLICY_REVIEW` watch items.
- Reason: `REJECT` / `NO_PERSISTENT_EDGE`, positive net basis absent.
- Policy watch items:
  - top-of-book liquidity.
  - depth/VWAP.
  - timestamp/data_age.
  - mark/index/funding context.
  - OKX deferred.

### `tether_cross_market_premium` / `usdt_krw_global_reference_v0`

- Current Council handoff status: `NEED_DATA_TRIAGE` or `POLICY_REVIEW` depending dashboard evidence.
- Reason: reference context strategy, not active, global/domestic reference semantics need careful treatment.

### `orderbook_imbalance_v0`

- Current Council handoff status: `NOT_REVIEW_READY` or `FUTURE` evidence row.
- Reason: experimental/non-active with insufficient reviewed evidence in dashboard.

### Future strategies

- Strategies:
  - `funding_rate_context_v0`.
  - `derivatives_flow_context_v0`.
  - `trade_flow_momentum_v0`.
- Status: `FUTURE`.

## 7. What should trigger NEED_DATA_TRIAGE

`NEED_DATA_TRIAGE` triggers:

- `parser_normalized_status` not OK.
- `required_missing_fields` non-empty.
- Diagnostics endpoint error.
- Schema validation failure.
- Venue response shape mismatch.
- Generated packet validation failure.
- Missing required metadata / units / notional.
- Source handoff path missing.
- Conflicting handoff evidence not reconciled.

## 8. What should trigger POLICY_REVIEW

`POLICY_REVIEW` triggers:

- `negative_data_age_watch` / timestamp clock-skew.
- OKX `index_price=None` / index reference semantics.
- `depth_vwap_not_implemented`.
- `top_of_book_liquidity_not_fill_feasibility`.
- `mark_price_not_executable`.
- `funding_rate_not_basis`.
- `symbol_product_semantics_mismatch`.
- `last_price_weak_context_only`.
- Basis-specific sampling summary alias refinement.

## 9. What should trigger NO_EDGE_ARCHIVE

`NO_EDGE_ARCHIVE` triggers:

- `samples_ok` complete.
- `samples_error=0` or acceptable.
- Parser OK.
- `required_missing_fields` empty.
- `readiness_status_counts` all `REJECT`.
- `positive_net_gap_count=0`.
- `readiness_pass_count=0`.
- `persistence_status=NO_PERSISTENT_EDGE`.
- `council_recommended=false`.
- No-trade metadata preserved.

## 10. What may trigger MANUAL_REVIEW_CANDIDATE

`MANUAL_REVIEW_CANDIDATE` triggers:

- Repeated `WATCH` evidence.
- `positive_net_gap_count > 0`.
- `readiness_pass_count > 0`.
- Positive estimated net basis/gap after fee/slippage/buffer.
- Parser OK.
- `required_missing_fields` empty.
- Diagnostics OK.
- `no_trade_only` true.
- `execution_policy` `NO_TRADE_ONLY`.
- Comparative summary confirms consistency.
- Source handoff path exists.

Clarifications:

- `MANUAL_REVIEW_CANDIDATE` is not `ENTER`.
- Council review is not execution.
- Council review cannot use private/account/order data at this stage.
- Council review output cannot trigger order placement in current system.

## 11. Council review packet / handoff candidate fields

Planning-only candidate fields; this PR does not implement a packet builder or runtime object:

- `council_handoff_schema_version`
- `created_at_utc`
- `strategy_family`
- `strategy_id`
- `source_dashboard_row`
- `source_handoff_paths`
- `evidence_status`
- `council_handoff_status`
- `readiness_status_counts`
- `persistence_status`
- `council_recommended`
- `positive_net_gap_count`
- `readiness_pass_count`
- `watch_items`
- `why_review`
- `why_not_execution`
- `no_trade_only`
- `execution_policy`
- `reviewer_notes`
- `rollback_reference`

## 12. Relationship to dashboard

Relationship:

- Dashboard는 evidence inventory다.
- Council criteria는 dashboard row를 해석하는 manual review policy다.
- Dashboard row가 자동으로 Council call을 만들면 안 된다.
- Council criteria PR 이후 dashboard에 `council_handoff_status` column을 추가할 수 있다.
- 그 작업도 docs-only/manual dashboard update로 별도 PR이어야 한다.

## 13. Explicitly not doing now

이번 PR에서 명시적으로 하지 않는 것:

- Council auto-call 구현 없음.
- Council runtime 구현 없음.
- Council packet builder 구현 없음.
- Alert 구현 없음.
- Execution 구현 없음.
- Active promotion 없음.
- Dashboard schema implementation 없음.
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
- Council criteria는 generated JSON 원본이 아니라 handoff evidence summary와 dashboard row를 기반으로 해야 한다.
- 이번 PR에는 generated JSON을 추가하지 않음.

## 16. Rollback plan

Rollback plan:

- Docs-only PR이므로 revert하고 이 handoff 문서 1개를 제거하면 된다.
- Code/config/registry/runtime/parser/readiness/test/fixture/generated-data rollback은 필요 없다.
- Confirm GitHub Files changed contains only this handoff file after rollback.
- Re-run required validation commands if rollback evidence is requested.

## 17. Next PR candidates

다음 PR 후보 순서:

1. Manual dashboard update with `council_handoff_status` column v0.
2. Timestamp / Clock-Skew Policy Planning v0.
3. Depth/VWAP Planning v0.
4. Next Experimental Strategy Selection v0.
5. Optional dashboard schema tests / generated dashboard planning later.
