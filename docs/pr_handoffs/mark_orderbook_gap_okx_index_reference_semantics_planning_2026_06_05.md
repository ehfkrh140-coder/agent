# Mark-Orderbook Gap OKX Index / Reference Semantics Planning v0

## 1. 작업 목적

이 문서는 OKX `mark_orderbook_gap_hunt_v0` evidence에서 반복 관찰된 `index_price=None` watch item을 향후 어떤 정책으로 해석하고 다룰지 정리하는 planning-only handoff다.

Scope:

- OKX `index_price=None` watch item을 정책적으로 정리한다.
- 이 문서는 implementation이 아니라 planning이다.
- 현재 adapter / parser / readiness / sampling behavior는 유지한다.
- OKX index/reference endpoint는 구현하지 않는다.
- Optional enrichment, synthetic index fill, readiness behavior change는 구현하지 않는다.
- `NO_TRADE_ONLY`를 유지한다.
- generated packet/sampling JSON은 smoke artifact이며 commit하지 않는다.

This PR does not implement OKX index endpoint access, optional index/reference enrichment, parser behavior changes, readiness threshold changes, alerting, Council auto-call, execution, or active strategy promotion.

## 2. Evidence baseline

Current evidence baseline:

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains experimental / non-active / `NO_TRADE_ONLY`.
- Binance / Bybit / OKX all have `mark_orderbook_gap_hunt_v0` baseline coverage and 30-sample evidence.
- OKX 30-sample evidence:
  - `adapter_id=live_okx_mark_orderbook_gap_btc_usdt_swap`
  - `samples_ok=30`
  - `samples_error=0`
  - `candidate_seen_count=30`
  - `persistence_status=NO_PERSISTENT_EDGE`
  - `council_recommended=false`
  - `readiness_status_counts.REJECT=30`
  - `index_price_null_count=30`
  - `index_price_null_observed=true`
  - `required_missing_fields=[]`
  - `parser_normalized_status=OK`
  - `positive_net_gap_count=0`
- Post-refactor 3-sample user-local smoke evidence for OKX also completed successfully:
  - `samples_ok=3`
  - `samples_error=0`
  - `NO_PERSISTENT_EDGE`
  - `council_recommended=false`
- Timestamp / negative `data_age_ms` is separated into the PR #122 timestamp / clock-skew policy track.
- OKX `index_price=None` is not treated as a timestamp issue in this planning document.

Interpretation of this baseline:

- The OKX sampling path is functioning for the observed public-read-only mark/orderbook/instrument path.
- The evidence does not prove profitable edge.
- The evidence does not prove persistent edge.
- `NO_PERSISTENT_EDGE`, `REJECT`, and `council_recommended=false` can be normal no-edge outcomes.
- `index_price=None` should be handled as an OKX index/reference semantics watch item, not as an immediate parser/readiness blocker.

## 3. Problem statement

OKX `index_price=None` can mean the current OKX adapter endpoint combination does not provide a directly usable index/reference price in the packet path.

Current OKX mark-orderbook-gap path uses public read-only data for:

- mark price context;
- orderbook bid/ask context;
- instrument metadata context.

This endpoint combination can provide mark price, top-of-book bid/ask, and instrument metadata while still leaving `index_price=None`. That observation has several implications:

- `index_price=None` is not necessarily a parser failure.
- If `required_missing_fields=[]`, current Mark-Orderbook Gap candidate creation can still proceed.
- The current `mark_orderbook_gap_hunt_v0` comparison is mark price versus orderbook bid/ask, so index price is not currently a required input.
- Index/reference price may still be useful later as an optional sanity check, explanatory context, or diagnostics reference.
- An absent index/reference price must not be replaced with a synthetic value.
- Mark price, index price, and executable orderbook prices have different roles and must not be conflated.

The policy problem is therefore whether OKX index/reference data should remain absent-but-preserved, be optionally enriched for diagnostics, or eventually affect readiness behavior after explicit evidence and approval.

## 4. Current interpretation

Current interpretation should remain conservative:

- OKX `index_price=None` is currently a watch item, not a blocker.
- If `parser_normalized_status=OK`, packet creation is successful for the current analysis-only pipeline.
- If `required_missing_fields=[]`, current readiness input requirements are satisfied.
- `readiness_status=REJECT` can be explained by no positive net edge / no persistent edge, not by `index_price=None` alone.
- `index_price=None` remains an OKX index/reference semantics watch item.
- The adapter/parser must not synthesize, backfill, or infer an index price.
- The absence of `index_price` must not be silently converted into zero, mark price, last price, midpoint, or any other derived value.
- Timestamp / negative `data_age_ms` remains a separate policy track and should not be mixed with index/reference semantics.

This planning document does not change current behavior.

## 5. Policy options

### Option A: preserve None

Description:

- Preserve `index_price=None` exactly as observed.
- Keep current readiness behavior unchanged.
- Keep `index_price_null_observed` / `index_price_null_count` or equivalent summary/watch labeling when observed.
- Document it as an OKX index/reference semantics watch item.

Pros:

- Lowest behavior-change risk.
- Preserves evidence fidelity.
- Avoids synthetic or misleading reference values.
- Matches current evidence where OKX packets can be created with `required_missing_fields=[]`.

Cons:

- Reviewers may need explicit wording explaining why `index_price=None` is not a failure.
- No additional index/reference sanity context is available yet.

### Option B: optional reference enrichment

Description:

- Research a separate OKX public index/reference endpoint candidate.
- Consider adding index/reference price as optional enrichment only.
- Keep current readiness behavior and required fields unchanged.
- Preserve `index_price=None` if optional enrichment is unavailable or inconclusive.

Pros:

- Could provide additional reference context without changing decisions.
- Allows explicit fixture and smoke evidence before any behavior change.

Cons:

- Adds endpoint semantics and failure modes that require venue-specific handling.
- Must not be allowed to become an implicit required field.
- Requires tests to ensure no synthetic fill or readiness behavior change.

### Option C: diagnostics-only reference check

Description:

- Even if an index/reference endpoint is added later, use it only for diagnostics/reference context at first.
- Do not make index/reference price a candidate required input.
- Consider an index-reference mismatch warning only in a separate PR.
- Keep readiness decisions unchanged.

Pros:

- Adds observability while limiting behavior risk.
- Keeps mark/orderbook candidate creation independent from optional reference data.
- Creates a safer path to compare mark/reference semantics before changing readiness.

Cons:

- Additional diagnostics can still be misread as decision logic if wording is weak.
- Requires careful separation between candidate metrics and reference-only diagnostics.

### Option D: readiness-affecting index policy

Description:

- Connect `index_price` absence or mark/index divergence to readiness warning or fail behavior.
- Potentially classify missing index/reference context as `NEED_DATA`, warning, or stronger `REJECT` in future.

Pros:

- Could eventually improve reference sanity checks if evidence shows index/reference context is required.

Cons:

- This is behavior-changing and must not be implemented in this planning PR.
- Requires dedicated evidence, mocked tests, user-local smoke evidence, and explicit policy approval.
- Risks rejecting otherwise valid current OKX packets.
- Risks conflating mark price, index/reference price, and executable price semantics.

## 6. Recommended policy direction

Recommended direction:

- Short term: keep Option A.
- Preserve `index_price=None` exactly as observed.
- Maintain current readiness behavior.
- Do not implement an OKX index/reference endpoint yet.
- Do not add optional enrichment in this planning PR.
- Do not connect `index_price` absence to readiness fail.
- Do not synthesize, infer, or backfill index price.
- If a future implementation is approved, start with optional enrichment / diagnostics-only behavior before any decision-affecting policy.
- Keep timestamp / negative `data_age_ms` in the separate timestamp / clock-skew policy track.

Recommended non-goals for the next implementation step:

- No hidden conversion from `None` to zero, mark price, last price, midpoint, or other derived value.
- No venue-agnostic index/reference semantics that erase OKX-specific behavior.
- No execution, alert, Council auto-call, or strategy promotion based on index/reference enrichment.

## 7. Implementation boundaries for future PR

Future implementation should be split into small PR slices after this planning is reviewed:

### PR A: OKX public index/reference endpoint source research docs-only

- Identify candidate OKX public index/reference endpoints and response semantics.
- Document rate-limit and response-shape considerations.
- Do not implement endpoint calls.

### PR B: mocked fixture for optional OKX index/reference payload

- Add mocked fixture expectations for optional index/reference payloads.
- Include missing/null/error response cases.
- Keep runtime behavior unchanged.

### PR C: parser optional field enrichment, readiness behavior unchanged

- If approved, add optional parser enrichment for index/reference data.
- Preserve `required_missing_fields=[]` behavior for the current mark/orderbook path.
- Ensure absence of optional index/reference data does not fail packet creation.

### PR D: diagnostics/reference warning only, no decision change

- Add diagnostics/reference warning only after fixture-backed review.
- Keep `readiness_status`, `recommended_default_decision`, and thresholds unchanged.
- Add tests proving no decision change.

### PR E: user-local smoke / sampling evidence update

- After any optional enrichment implementation, request user-local public-read-only smoke evidence.
- Do not commit generated JSON artifacts unless explicitly approved.

## 8. Risks

Key risks:

- Treating `index_price=None` as parser failure could over-reject otherwise normal OKX packets.
- Creating synthetic `index_price` could distort evidence and hide endpoint semantics.
- Connecting index/reference data directly to readiness is behavior-changing and carries high regression risk.
- Confusing mark price and index/reference price can overstate a trade signal.
- Mark price is not executable price, so index/reference enrichment must not be used to justify execution.
- OKX contract unit, lot size, contract value, and index/reference semantics must not be mixed into one generic interpretation.
- Optional enrichment can accidentally become a required dependency if tests and wording are not explicit.

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
- OKX index endpoint implementation: no
- Optional enrichment implementation: no
- Synthetic index price fill implementation: no
- Timestamp policy implementation: no
- Freshness behavior change: no
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
2. Remove `docs/pr_handoffs/mark_orderbook_gap_okx_index_reference_semantics_planning_2026_06_05.md`.
3. No code/config/registry/runtime/parser/readiness/generated-data rollback is required.

## 12. Next PR candidates

Recommended order after this planning PR:

1. Mark-Orderbook Gap multi-venue comparative summary
2. Optional OKX index/reference source research docs-only
3. Timestamp policy implementation v0, only after planning approval
4. 이후 후보: next experimental strategy planning
