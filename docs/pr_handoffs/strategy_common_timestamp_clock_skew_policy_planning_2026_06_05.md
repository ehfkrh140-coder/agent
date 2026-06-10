# Strategy-Common Timestamp / Clock-Skew Policy Planning v0

## 1. 작업 목적

이 문서는 여러 strategy에서 반복 관찰된 `timestamp_data_age_watch` / `negative_data_age_watch` / clock-skew 문제를 strategy-common policy 관점으로 정리하는 planning-only handoff다.

Scope:

- `timestamp_data_age_watch`, `negative_data_age_watch`, timestamp/clock-skew alignment 문제를 strategy-common policy로 정리한다.
- 이번 문서는 implementation이 아니라 planning이다.
- Readiness behavior를 변경하지 않는다.
- Negative `data_age_ms`를 clamp/normalize하지 않는다.
- `NO_TRADE_ONLY`를 유지한다.
- Active strategy는 `cross_exchange_spot_spread_v1`로 유지한다.

This PR does not implement timestamp policy, readiness behavior changes, freshness behavior changes, clamp/normalize behavior, alerting, Council auto-call, execution, active promotion, or generated JSON artifacts.

## 2. Problem statement

Problem statement:

- Bybit / OKX / 일부 strategy sampling에서 negative `data_age_ms`가 관찰되었다.
- Exchange timestamp가 local collection timestamp보다 미래처럼 보일 수 있다.
- Endpoint별 timestamp semantics가 다를 수 있다.
- Local machine clock, network latency, exchange server timestamp, packet `created_at` 기준이 서로 다를 수 있다.
- Negative `data_age_ms`는 그 자체로 trading edge가 아니다.
- Negative `data_age_ms`는 그 자체로 adapter failure도 아니다.
- 하지만 해석 정책이 없으면 strategy별 ad-hoc 해석이 생길 수 있다.

Policy risk:

- 같은 timestamp/data-age 현상이 strategy마다 다르게 해석될 수 있다.
- Small clock skew, endpoint timestamp semantics, true stale data, schema/type issue가 같은 `data_age_ms` field 안에서 섞일 수 있다.
- Watch item을 trading signal처럼 오해하면 안 된다.
- Watch item을 adapter failure처럼 오해해도 안 된다.
- Raw evidence를 조용히 clamp/normalize하면 future policy analysis에 필요한 근거를 잃을 수 있다.

## 3. Current evidence recap

### `mark_orderbook_gap_hunt_v0`

Current evidence recap:

- Binance / Bybit / OKX baseline complete.
- Bybit negative `data_age_ms` watch evidence existed.
- OKX negative `data_age_ms` and `index_price=None` watch items existed.
- Comparative summary complete.
- Current dashboard/Council status: `NO_EDGE_ARCHIVE` + `POLICY_REVIEW`.
- Timestamp/data-age watch items are separate from OKX index/reference semantics.
- This evidence does not justify active promotion, alerting, Council auto-call, or execution.

### `spot_futures_basis_v0`

Current evidence recap:

- Binance + Bybit baseline complete.
- Bybit collect/sampling path succeeded.
- `negative_data_age_watch` may appear depending timestamp alignment.
- Top-of-book/depth/VWAP and timestamp items are policy review items.
- Current dashboard/Council status: `NO_EDGE_ARCHIVE` + `POLICY_REVIEW`.
- This evidence does not justify active promotion, alerting, Council auto-call, or execution.

### Dashboard / Council criteria

Current evidence recap:

- `timestamp_data_age_watch` and `negative_data_age_watch` are watch item taxonomy entries.
- Council handoff status for affected strategies includes `POLICY_REVIEW`.
- The manual dashboard records evidence inventory; it does not create runtime behavior.
- Council criteria interprets dashboard rows; it does not create Council auto-call or execution.

## 4. Timestamp terminology

Candidate terminology definitions:

- `exchange_timestamp`: timestamp supplied by an exchange or venue response.
- `endpoint_timestamp`: endpoint-specific timestamp, whose semantics may differ by endpoint and venue.
- `orderbook_timestamp`: timestamp associated with orderbook/depth data or orderbook update time.
- `mark_price_timestamp`: timestamp associated with mark-price or premium-index response data.
- `local_fetch_started_at`: local timestamp captured before a public-read-only fetch begins.
- `local_fetch_completed_at`: local timestamp captured after a public-read-only fetch completes.
- `packet_created_at`: local timestamp associated with packet construction or summary creation.
- `data_age_ms`: observed age between a local reference timestamp and a source data timestamp.
- `latency_ms`: measured elapsed time for fetch/collection path, distinct from source data age.
- `max_data_age_ms`: configured or planned freshness threshold for acceptable source age.
- `timestamp_skew_ms`: difference between local reference time and exchange/endpoint timestamp that may indicate clock or semantics skew.
- `timestamp_data_age_watch`: watch marker for timestamp/data-age interpretation issue.
- `negative_data_age_watch`: watch marker for negative `data_age_ms` or future-looking source timestamp.
- `stale_data_watch`: watch marker for stale positive age above an accepted freshness threshold.

This PR does not rename fields, change schemas, change parser outputs, or add new fields. These are terminology definitions only.

## 5. Policy options

### Option A: Raw preserve only

Description:

- Preserve raw `data_age_ms` exactly as observed.
- Preserve negative values instead of hiding them.
- Keep readiness behavior unchanged.

Pros:

- Best evidence fidelity.
- Lowest implementation and behavior-change risk.
- Keeps future clock-skew analysis possible.

Cons:

- User interpretation can be harder without display guidance.
- Small negative skew and large negative skew may look equally concerning without a policy layer.

### Option B: Display-only clamp

Description:

- Preserve raw value.
- Add a display-only field such as `display_data_age_ms=max(0, data_age_ms)` in a future UI/summary layer.
- Do not change readiness behavior.

Pros:

- Easier for humans to read in summary/dashboard contexts.
- Can reduce confusion around negative age display.

Cons:

- May create misunderstanding that raw evidence has been fixed or hidden.
- Requires careful naming and source-of-truth rules.
- Not implemented in this PR.

### Option C: Tolerance band warning-only

Description:

- Treat small negative skew as warning-only candidate.
- Preserve raw values.
- Keep readiness and freshness pass/fail behavior unchanged.

Pros:

- Gives reviewers a shared policy vocabulary.
- Separates minor timestamp alignment issues from data sufficiency failures.
- Fits dashboard/Council `POLICY_REVIEW` classification.

Cons:

- Requires evidence-based tolerance values before implementation.
- Requires tests to avoid accidentally changing readiness decisions.
- Not implemented in this PR.

### Option D: Readiness-affecting policy

Description:

- Connect large negative skew or stale positive age to readiness downgrade in a future behavior-changing implementation.

Pros:

- Stronger data quality enforcement if evidence proves the policy is correct.

Cons:

- High behavior-change risk.
- Could alter strategy readiness outcomes.
- Requires separate evidence, approval, and tests.
- This planning PR forbids implementation of readiness-affecting policy.

## 6. Recommended policy direction

Recommended direction:

- Short term: Option A + Option C planning.
- Preserve raw `data_age_ms`.
- Preserve negative `data_age_ms`.
- Keep `negative_data_age_watch`.
- Keep `timestamp_data_age_watch`.
- No clamp.
- No silent normalization.
- No readiness behavior change.
- No freshness behavior change.
- No active promotion.
- No alert.
- No Council auto-call.
- No execution.
- Future implementation, if approved, should start with warning-only behavior before any readiness-affecting policy.

Rationale:

- Raw evidence is needed to distinguish clock skew, endpoint semantics, collection timing, and stale data.
- Warning-only classification fits current dashboard/Council `POLICY_REVIEW` posture.
- Behavior-changing timestamp policy should wait for separate evidence and approval.

## 7. Proposed policy classification

Proposed dashboard/Council classification:

- Small negative `data_age_ms`: `POLICY_REVIEW` / warning-only candidate.
- Repeated negative `data_age_ms` with parser OK and samples OK: not failure, but policy watch.
- Stale positive `data_age_ms` above `max_data_age_ms`: future `NEED_DATA_TRIAGE` candidate.
- Schema validation failure due to fractional ms type: `NEED_DATA_TRIAGE` / bugfix path.
- Missing timestamp: `NEED_DATA_TRIAGE`.
- Endpoint timestamp semantics unknown: `POLICY_REVIEW`.
- Generated JSON artifact containing raw values: evidence summary only; not committed.

Interpretation notes:

- `POLICY_REVIEW` means human policy interpretation is needed; it does not mean trading edge.
- `NEED_DATA_TRIAGE` means data quality/source contract needs attention; it does not mean execution permission.
- Negative `data_age_ms` alone should not move a strategy toward active promotion.

## 8. What must not happen

What must not happen:

- Negative `data_age_ms`를 trading edge로 해석하지 않는다.
- Negative `data_age_ms`를 자동 `ENTER` / `WATCH`로 해석하지 않는다.
- Timestamp watch item이 alert를 trigger하지 않는다.
- Timestamp watch item이 Council auto-call을 trigger하지 않는다.
- Timestamp watch item이 execution을 trigger하지 않는다.
- Raw value를 조용히 clamp/normalize하지 않는다.
- Generated JSON을 source-of-truth로 commit하지 않는다.
- Timestamp policy를 active strategy promotion 근거로 사용하지 않는다.
- Timestamp policy를 private/account/order feasibility 근거로 사용하지 않는다.

## 9. Future implementation PR slices

Proposed future PR sequence:

1. Timestamp policy constants / naming docs-only or test-fixture planning.
2. Summary-layer watch count strengthening, behavior unchanged.
3. Dashboard update to include timestamp policy status, docs-only.
4. Warning-only implementation with mocked/unit tests, no readiness decision change.
5. User-local smoke/evidence update.
6. Readiness-affecting policy only after separate approval and stronger evidence.

Guardrails for any future implementation:

- Keep raw timestamp/data-age evidence available.
- Add tests proving readiness decision does not change for warning-only implementation.
- Forbid private API, account state, order feasibility, alerting, Council auto-call, and execution.
- Do not commit generated market JSON.

## 10. Relationship to dashboard and Council criteria

Relationship:

- Dashboard records `timestamp_data_age_watch` / `negative_data_age_watch` as watch items.
- Council criteria classifies them as `POLICY_REVIEW` unless they cause data sufficiency failure.
- Timestamp policy does not create Council auto-call.
- Timestamp policy does not create alert/execution behavior.
- Future dashboard updates may include `timestamp_policy_status` as a manual docs-only column.
- Any future Council review packet or policy implementation requires separate planning/approval.

## 11. Explicitly not doing now

Explicitly not doing in this PR:

- Timestamp policy implementation 없음.
- Schema change 없음.
- Parser field rename 없음.
- Readiness behavior 변경 없음.
- Freshness threshold 변경 없음.
- Clamp/normalize 구현 없음.
- Dashboard update 없음.
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

## 12. OKX deferred scope note

OKX scope note:

- `spot_futures_basis_v0` OKX는 future expansion으로 defer.
- 이는 scope control이지 permanent rejection이 아니다.
- 이번 PR에서는 OKX research/adapter/config를 만들지 않는다.
- `mark_orderbook_gap_hunt_v0` OKX index/reference semantics는 별도 watch item으로 유지한다.

## 13. No-trade compliance

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

## 14. Generated JSON commit 금지

Generated JSON policy 확인:

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- Timestamp policy evidence는 generated JSON 원본이 아니라 handoff evidence summary와 dashboard row를 기반으로 해야 함.
- 이번 PR에는 generated JSON을 추가하지 않음.

## 15. Rollback plan

Rollback plan:

- Docs-only PR이므로 revert하고 이 handoff 문서 1개를 제거하면 된다.
- Code/config/registry/runtime/parser/readiness/test/fixture/generated-data rollback은 필요 없다.
- Confirm GitHub Files changed contains only this handoff document after rollback.
- Re-run required validation commands if rollback evidence is requested.

## 16. Next PR candidates

다음 PR 후보:

1. Depth/VWAP Planning v0.
2. Next Experimental Strategy Selection v0.
3. Optional dashboard timestamp policy status update.
4. Optional dashboard schema tests / generated dashboard planning later.
