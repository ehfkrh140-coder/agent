# Mark-Orderbook Gap Timestamp / Clock-Skew Policy Planning v0

## 1. 작업 목적

이 문서는 Bybit / OKX `mark_orderbook_gap_hunt_v0` evidence에서 반복 관찰된 negative `data_age_ms` 및 timestamp/data-age watch item을 향후 어떤 정책으로 해석하고 다룰지 정리하는 planning-only handoff다.

Scope:

- Bybit / OKX negative `data_age_ms` watch item을 정책적으로 정리한다.
- 이 문서는 implementation이 아니라 planning이다.
- 현재 adapter / parser / readiness / sampling behavior는 유지한다.
- `NO_TRADE_ONLY`를 유지한다.
- generated packet/sampling JSON은 smoke artifact이며 commit하지 않는다.

This PR does not implement timestamp/data-age policy, clock-skew tolerance, freshness behavior changes, alerting, Council auto-call, execution, or active strategy promotion.

## 2. Evidence baseline

Current evidence baseline:

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains experimental / non-active / `NO_TRADE_ONLY`.
- Binance / Bybit / OKX all have `mark_orderbook_gap_hunt_v0` baseline coverage and 30-sample evidence.
- Bybit 30-sample evidence:
  - `samples_ok=30`
  - `samples_error=0`
  - `persistence_status=NO_PERSISTENT_EDGE`
  - `council_recommended=false`
  - negative `data_age_ms` was observed as a timestamp/data-age watch item.
  - `timestamp_data_age_watch_count=21` in the 30-sample evidence.
- OKX 30-sample evidence:
  - `samples_ok=30`
  - `samples_error=0`
  - `persistence_status=NO_PERSISTENT_EDGE`
  - `council_recommended=false`
  - negative `data_age_ms` was observed as a timestamp/data-age watch item.
  - `timestamp_data_age_watch_count=30` in the 30-sample evidence.
- OKX `index_price=None` is not a timestamp policy issue; it remains a separate OKX index/reference semantics watch item.
- Post-refactor 3-sample user-local smoke evidence confirms the sampling path remained healthy after PR #116~#119 refactors:
  - Binance: `samples_ok=3`, `samples_error=0`, `NO_PERSISTENT_EDGE`, `council_recommended=false`
  - Bybit: `samples_ok=3`, `samples_error=0`, `NO_PERSISTENT_EDGE`, `council_recommended=false`
  - OKX: `samples_ok=3`, `samples_error=0`, `NO_PERSISTENT_EDGE`, `council_recommended=false`

Interpretation of this baseline:

- The sampling pipeline is functioning for the observed public-read-only paths.
- The evidence does not prove profitable edge.
- The evidence does not prove persistent edge.
- `NO_PERSISTENT_EDGE`, `REJECT`, and `council_recommended=false` can be normal no-edge outcomes.
- The timestamp/data-age watch items should be handled separately from OKX index/reference semantics.

## 3. Problem statement

Negative `data_age_ms` means the observed exchange/reference timestamp appears newer than, or otherwise ahead of, the local timestamp basis used in packet creation. It can have several causes:

- Exchange timestamp appears to be in the future relative to local `created_at`.
- Local machine clock skew may make local time appear behind exchange time.
- Exchange server clock semantics may differ from local collection semantics.
- Venue-specific timestamp fields may represent different moments, such as mark-price update time, orderbook update time, server time, or endpoint-specific event time.
- Fetch order can matter: mark price, orderbook, funding, and instrument endpoints may be requested sequentially, while each response may carry a timestamp generated at a different moment.
- Network latency measurement basis can differ from the data timestamp basis.
- Negative `data_age_ms` alone does not imply a trading edge.
- Negative `data_age_ms` alone does not imply adapter failure when required fields are present and parser normalization succeeds.

The policy problem is therefore not whether negative `data_age_ms` exists, but how to preserve it as evidence, classify it as a watch condition, and decide whether any future tolerance or warning should affect display, summary, or readiness behavior.

## 4. Current interpretation

Current interpretation should remain conservative:

- If `parser_normalized_status=OK` and `required_missing_fields=[]`, packet creation can be considered successful for the current analysis-only pipeline.
- `readiness_status=REJECT` can be a normal no-edge result and does not necessarily indicate a timestamp failure.
- Negative `data_age_ms` is currently a watch item, not a blocker.
- `freshness_pass=true` can coexist with a separate timestamp/data-age watch marker if the current freshness criteria still pass.
- Raw negative `data_age_ms` should be preserved because it is useful evidence for later timestamp/clock-skew analysis.
- Clamping or normalizing negative values to zero would hide potentially important evidence.
- Timestamp/data-age interpretation must remain venue-aware because Bybit and OKX timestamp semantics may differ.

This planning document does not change current behavior.

## 5. Policy options

### Option A: raw preserve only

Description:

- Preserve negative `data_age_ms` exactly as observed.
- Keep `timestamp_data_age_watch=true` or equivalent summary/watch labeling when negative values are observed.
- Do not change readiness behavior.
- Do not clamp, normalize, or rewrite the value.

Pros:

- Maximum evidence fidelity.
- Lowest behavior-change risk.
- Easy to review because it does not affect parser/readiness decisions.

Cons:

- Reviewers and downstream summaries may need extra wording to avoid treating negative values as failures.
- Without tolerance bands, very small and very large negative values may be displayed similarly.

### Option B: display-only clamp

Description:

- Preserve `raw_data_age_ms` or equivalent raw evidence.
- Display `displayed_data_age_ms=max(0, data_age_ms)` only in UI or summary contexts.
- Do not change readiness behavior.

Pros:

- May reduce confusion in user-facing displays.
- Preserves raw value if the raw field is retained clearly.

Cons:

- Even display-only clamp can hide the operational meaning if reviewers see only the clamped value.
- Requires careful naming and tests to ensure raw evidence is not lost.
- Still introduces a new presentation policy and should not be implemented implicitly.

### Option C: tolerance band

Description:

- Define a small tolerance band, for example `-250ms <= data_age_ms <= max_data_age_ms`, as warning-only.
- Values slightly below zero remain watch-level evidence, not readiness blockers.
- Values more negative than the tolerance band could trigger stronger `timestamp_clock_skew_warning` wording.
- Readiness behavior remains unchanged until a separate explicitly approved implementation PR.

Pros:

- Separates small clock-skew noise from larger skew observations.
- Preserves raw negative values.
- Gives future summaries a clearer policy vocabulary.

Cons:

- Any threshold can become misleading if exchange-specific timestamp semantics differ.
- Requires fixture coverage and venue-specific review before implementation.
- The initial tolerance value should not be treated as universally valid without more evidence.

### Option D: readiness-affecting policy

Description:

- Connect very negative or very large positive `data_age_ms` values to freshness failure or readiness downgrade.
- Potentially convert large timestamp skew into `freshness_pass=false`, `NEED_DATA`, or stronger `REJECT` semantics.

Pros:

- Could protect future analysis from stale or inconsistent timestamps once the policy is evidence-backed.
- Makes timestamp quality more explicit in readiness decisions.

Cons:

- This is behavior-changing and must not be implemented in this planning PR.
- Requires dedicated evidence, tests, and review because it changes readiness interpretation.
- Risks over-blocking otherwise healthy public data paths.

## 6. Recommended policy direction

Recommended direction:

- Short term: use Option A plus Option C planning.
- Preserve raw negative `data_age_ms` exactly as observed.
- Maintain a separate `timestamp_data_age_watch` label/count in summaries.
- Document a small tolerance-band concept for future review, but do not implement it in this PR.
- Do not clamp or normalize negative `data_age_ms`.
- Do not change `freshness_pass` behavior before a dedicated implementation PR.
- Do not connect timestamp/data-age watch items to readiness decisions until separate evidence and regression tests exist.
- Keep OKX `index_price=None` out of timestamp policy; it belongs to a separate OKX index/reference semantics planning track.

Recommended non-goals for the next implementation step:

- No hidden conversion from negative values to zero.
- No venue-agnostic timestamp interpretation that erases Bybit / OKX differences.
- No execution, alert, Council auto-call, or strategy promotion based on timestamp policy.

## 7. Implementation boundaries for future PR

Future implementation should be split into small PR slices after this planning is reviewed:

### PR A: timestamp policy constants / docs-only test fixture expectation planning

- Define proposed naming and threshold vocabulary in docs or tests first.
- Keep runtime behavior unchanged.
- Decide whether tolerance names should be venue-neutral or venue-specific.

### PR B: parser output naming review

- Evaluate whether parser output should expose names such as `raw_data_age_ms`, `timestamp_skew_ms`, or `timestamp_data_age_watch`.
- Do not add fields without tests and migration notes.
- Preserve current raw values and venue-specific timestamp semantics.

### PR C: summary-layer watch count strengthening

- Strengthen sampling summary labels/counts for `timestamp_data_age_watch_count`.
- Keep readiness decisions unchanged.
- Keep generated JSON as local smoke artifacts unless explicitly approved for commit.

### PR D: readiness-layer warning only

- Add a large clock-skew warning only after fixture-backed review.
- Keep `readiness_status`, `recommended_default_decision`, and `freshness_pass` behavior unchanged in the first warning-only step.
- Add mocked/unit tests for Bybit and OKX negative data-age cases.

### PR E: user-local smoke / extended evidence update

- After any implementation PR, request user-local public-read-only smoke evidence.
- If behavior changes are later proposed, request extended evidence before considering readiness-impacting policy.

## 8. Risks

Key risks:

- Treating negative `data_age_ms` as an unconditional failure could over-block an otherwise healthy public data path.
- Silently clamping negative `data_age_ms` could hide evidence needed for clock-skew diagnosis.
- Connecting timestamp policy directly to readiness decisions is behavior-changing and carries high regression risk.
- Over-commonizing timestamp semantics across exchanges can erase venue-specific differences.
- OKX `index_price=None` could be conflated with timestamp policy even though it is a separate OKX index/reference semantics issue.
- Mark price is not executable price, so timestamp policy must not be used to justify a trade signal.
- Positive gross gap with negative estimated net gap can still be a normal no-edge result.

## 9. No-trade compliance

This planning PR preserves no-trade posture:

- Active strategy promotion: no
- `mark_orderbook_gap_hunt_v0` active promotion: no
- Council auto-call: no
- Alert: no
- Execution: no
- Private API: no
- Credentials/API keys/secrets/tokens: no
- Account/balance/position lookup: no
- Order/cancel: no
- Withdrawal/deposit/transfer: no
- Auto-trading: no
- Config/registry change: no
- Source/runtime behavior change: no
- Parser behavior change: no
- Readiness threshold change: no
- Timestamp policy implementation: no
- Clock-skew tolerance code implementation: no
- Freshness behavior change: no
- Negative `data_age_ms` clamp/normalize implementation: no
- OKX index endpoint implementation: no
- Generated JSON commit: no
- `NO_TRADE_ONLY` preserved: yes

## 10. Generated JSON commit 금지

Generated packet/sampling files remain smoke artifacts only and must not be committed:

- `data/market_samples/*.json`
- `data/generated_packets/*.json`

This PR intentionally adds only this planning handoff document and does not add generated JSON.

## 11. Rollback plan

Rollback path:

1. Revert this docs-only planning PR.
2. Remove `docs/pr_handoffs/mark_orderbook_gap_timestamp_clock_skew_policy_planning_2026_06_05.md`.
3. No code/config/registry/runtime/parser/readiness/generated-data rollback is required.

## 12. Next PR candidates

Recommended order after this planning PR:

1. OKX index/reference semantics planning
2. Mark-Orderbook Gap multi-venue comparative summary
3. Timestamp policy implementation v0, only after planning approval
4. 이후 후보: next experimental strategy planning
