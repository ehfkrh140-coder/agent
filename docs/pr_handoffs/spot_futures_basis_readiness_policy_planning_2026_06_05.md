# Spot-Futures Basis Readiness Policy Planning v0

## 1. 작업 목적

이 문서는 `spot_futures_basis_v0`의 future readiness helper가 `REJECT` / `NEED_DATA` / `WATCH`를 어떤 조건에서 반환해야 하는지 implementation 전에 정의하는 docs-only readiness policy planning handoff다.

Scope:

- `spot_futures_basis_v0`의 readiness policy를 implementation 전에 정의한다.
- Future parser/readiness tests가 무엇을 기대해야 하는지 정한다.
- 이 문서는 implementation이 아니라 planning이다.
- Fixture 파일도 생성하지 않는다.
- `NO_TRADE_ONLY`를 유지한다.
- Generated packet/sampling JSON은 smoke artifact이며 commit하지 않는다.

This PR does not implement readiness helpers, parsers, adapters, fixture JSON, tests, registry/config entries, endpoint calls, runtime behavior, generated data, alerts, Council auto-call, execution, or active strategy promotion.

## 2. Scope

Initial readiness policy target:

- `strategy_family`: `spot_futures_basis`
- `strategy_id`: `spot_futures_basis_v0`
- `status`: proposed / experimental / non-active / `NO_TRADE_ONLY`
- First reference venue: Binance Spot `BTCUSDT` vs Binance USDⓈ-M `BTCUSDT` Perp
- Common contract: `SpotObservationNormalized` + `PerpObservationNormalized`
- `candidate_type`: `spot_futures_basis_observation`

Boundary:

- Binance is the first reference venue only.
- Readiness policy should remain strategy-common and venue-neutral where possible.
- Venue-specific source layers should supply normalized observations and warnings, not make strategy decisions.

## 3. Readiness status definitions

### `REJECT`

Use `REJECT` when the candidate is analyzable enough to conclude no acceptable analysis-stage basis exists.

Candidate conditions:

- Required executable fields are present.
- `parser_normalized_status` is `OK` or otherwise usable.
- No positive gross executable basis exists.
- Or positive gross basis exists but `estimated_net_basis_pct <= 0` after fee/slippage buffer.
- Or guardrails say this is analysis-only no-edge.

Interpretation:

- `REJECT` is not adapter failure.
- `REJECT` can be a normal no-edge outcome.
- `REJECT` must not trigger execution, alerting, Council auto-call, or active promotion.

### `NEED_DATA`

Use `NEED_DATA` when the candidate cannot be evaluated safely because required data or comparability context is missing or unresolved.

Candidate conditions:

- Required executable bid/ask fields are missing.
- Symbol mapping is ambiguous.
- Quote/settlement comparability is unresolved.
- Metadata required for unit/notional interpretation is missing.
- Stale timestamp policy requires more data.
- Only weak context such as last price or mark price exists.
- `parser_normalized_status` indicates missing required data.

Interpretation:

- `NEED_DATA` is an analysis-stage data sufficiency label.
- `NEED_DATA` is not permission to call private APIs.
- `NEED_DATA` should preserve `required_missing_fields` and warnings for reviewer diagnosis.

### `WATCH`

Use `WATCH` only when a candidate has enough public-read-only evidence to merit analysis attention.

Candidate conditions:

- Positive `estimated_net_basis_pct` exists after fee/slippage buffer.
- Required executable fields are present.
- Comparability checks pass.
- Freshness checks pass.
- Liquidity/depth policy, if implemented later, passes or is explicitly marked as not yet implemented.

Interpretation:

- `WATCH` remains analysis-only.
- `WATCH` is not `ENTER`.
- `WATCH` is not a trading signal.
- `WATCH` remains `NO_TRADE_ONLY`.
- No Council auto-call, alert, execution, or active promotion is allowed from `WATCH`.

## 4. Required executable fields

Future readiness should require different executable-field sets by direction.

### Long spot / short perp direction

Minimum required fields:

- `spot_ask`
- `spot_ask_qty`
- `perp_bid`
- `perp_bid_qty`
- `spot_symbol`
- `perp_symbol`
- `quote_asset`
- `settlement_asset` or `margin_asset`
- `fee_slippage_buffer_pct`
- Timestamps / `data_age_ms` fields
- Metadata needed for unit/notional interpretation

Readiness meaning:

- This direction estimates whether buying spot at ask and selling perp at bid has positive gross/net basis.
- Mark price, index price, or last price cannot substitute for missing `spot_ask` or `perp_bid`.

### Long perp / short spot direction

Minimum required fields:

- `perp_ask`
- `perp_ask_qty`
- `spot_bid`
- `spot_bid_qty`
- `spot_symbol`
- `perp_symbol`
- `quote_asset`
- `settlement_asset` or `margin_asset`
- `fee_slippage_buffer_pct`
- Timestamps / `data_age_ms` fields
- Metadata needed for unit/notional interpretation

Readiness meaning:

- This direction estimates whether buying perp at ask and selling spot at bid has positive gross/net basis.
- Mark price, index price, or last price cannot substitute for missing `perp_ask` or `spot_bid`.

## 5. Required missing fields policy

Candidate `required_missing_fields` values should be explicit and reviewer-readable. Planning candidates:

- `spot_bid_missing`
- `spot_ask_missing`
- `perp_bid_missing`
- `perp_ask_missing`
- `spot_bid_qty_missing`
- `spot_ask_qty_missing`
- `perp_bid_qty_missing`
- `perp_ask_qty_missing`
- `spot_symbol_missing`
- `perp_symbol_missing`
- `quote_asset_missing`
- `settlement_asset_missing`
- `margin_asset_missing`
- `symbol_mapping_unresolved`
- `unit_conversion_unresolved`
- `spot_metadata_missing`
- `perp_metadata_missing`
- `fee_slippage_buffer_missing`
- `timestamp_missing`
- `stale_timestamp_policy_unresolved`

Policy notes:

- Missing executable bid/ask fields should usually lead to `NEED_DATA` unless future policy explicitly maps a case to `REJECT`.
- Missing metadata required for unit/notional interpretation should preserve the specific missing metadata key where possible.
- Optional context fields such as mark/index/funding should not be treated as required executable fields unless a future policy explicitly changes that.

## 6. Formula policy

### Context formulas

These formulas provide context only:

```text
spot_mid = (spot_bid + spot_ask) / 2
perp_mid = (perp_bid + perp_ask) / 2
mid_basis_pct = ((perp_mid - spot_mid) / spot_mid) * 100
```

Context guardrails:

- `mid_basis_pct` is context only.
- Mark basis is context only.
- Last price basis is weak context only.
- Context formulas cannot by themselves produce executable basis readiness.

### Executable directional formulas

Executable-basis candidates should use bid/ask or future VWAP-based fields:

```text
long_spot_short_perp_gross_pct = ((perp_bid - spot_ask) / spot_ask) * 100
long_perp_short_spot_gross_pct = ((spot_bid - perp_ask) / perp_ask) * 100
selected_gross_basis_pct = max(direction candidates)
estimated_net_basis_pct = selected_gross_basis_pct - fee_slippage_buffer_pct
```

Formula guardrails:

- Executable basis must be based on bid/ask or future VWAP-based estimates.
- This PR does not implement thresholds.
- This PR does not set production values.
- Direction labels must remain explicit so long-spot/short-perp and long-perp/short-spot are not confused.

## 7. Fee / slippage / buffer policy

Planning-only policy:

- `fee_slippage_buffer_pct` must be an explicit assumption.
- If gross basis is positive but buffer-adjusted net basis is `<= 0`, readiness should be `REJECT`.
- If `estimated_net_basis_pct > 0`, the candidate may be `WATCH`, but `NO_TRADE_ONLY` remains mandatory.
- Future PRs need config/planning approval before selecting buffer values.
- Actual fee tier, account tier, private account data, balances, positions, or execution data must not be used.
- Buffer assumptions should be visible in candidate metrics and assumptions.

## 8. Comparability policy

Future readiness should check these comparability requirements:

- Spot/perp symbol mapping is explicit.
- Base asset is the same.
- Quote / settlement / margin assets are comparable.
- Product type is explicit: spot vs perp.
- Contract unit or base-asset unit is explicit.
- Quantity unit is explicit.
- Min order / min notional interpretation is explicit.
- Spot and perp status are trading/active if metadata is available.
- Same symbol string does not imply product equivalence.
- Venue-specific metadata is preserved and not silently flattened.

Comparability failure should usually produce `NEED_DATA` with a specific warning or missing-field entry unless a future policy explicitly maps it to `REJECT`.

## 9. Freshness / timestamp policy

Planning-only policy:

- Timestamps should be preserved raw.
- `data_age_ms` should not be silently clamped.
- Stale timestamp may lead to `NEED_DATA` in a future policy.
- Negative `data_age_ms` should be preserved as a watch item until policy implementation.
- No freshness behavior is implemented in this PR.
- Timestamp policy can reuse style from `mark_orderbook_gap_hunt_v0` planning, but not concrete values without new spot-futures evidence.
- Freshness warnings should not hide raw timestamp evidence.

## 10. Warning taxonomy

Future readiness/parser warnings may include:

- `no_positive_gross_basis`
- `non_positive_estimated_net_basis`
- `positive_net_basis_analysis_only`
- `mark_price_not_executable`
- `last_price_weak_context_only`
- `funding_rate_not_basis`
- `symbol_mapping_unresolved`
- `product_semantics_mismatch`
- `unit_conversion_unresolved`
- `metadata_missing`
- `stale_timestamp`
- `negative_data_age_watch`
- `low_top_of_book_quantity`
- `depth_vwap_not_implemented`
- `fee_slippage_buffer_missing`
- `quote_settlement_comparability_unresolved`

Taxonomy guardrails:

- Warning strings should remain stable enough for tests.
- Warnings should not imply execution or order intent.
- Warnings should separate missing data from no-edge conclusions.

## 11. Formula test case expectations

Connect the mocked fixture planning cases to readiness policy as follows.

### Case A: no gross executable basis

- Expected status: `REJECT`
- Warning: `no_positive_gross_basis`
- Rationale: required executable fields are present, but no positive gross basis exists.

### Case B: positive gross but negative net

- Expected status: `REJECT`
- Warning: `non_positive_estimated_net_basis`
- Rationale: gross basis is positive but estimated net basis is not positive after buffer.

### Case C: positive net basis, still NO_TRADE_ONLY

- Expected status: `WATCH`
- Warning or assumption: `positive_net_basis_analysis_only`
- Council auto-call / alert / execution forbidden.
- Rationale: candidate may merit analysis attention, but not trading.

### Case D: missing metadata

- Expected status: `NEED_DATA` or `REJECT` depending missing field severity.
- `required_missing_fields` populated.
- Rationale: unit/notional/symbol comparability may be unresolved.

### Case E: stale timestamp

- Expected status: `NEED_DATA` or `REJECT` depending future freshness policy.
- Warning: `stale_timestamp`
- Rationale: timestamp policy must be explicit before stale data can be interpreted safely.

### Case F: mark-only context

- Expected status: `NEED_DATA` or `REJECT`.
- `required_missing_fields` for executable bid/ask.
- Warning: `mark_price_not_executable`
- Rationale: mark/index context cannot replace executable bid/ask fields.

## 12. OpportunityPacket readiness mapping

Future candidate/readiness mapping should expose these fields:

- `readiness_status`
- `recommended_default_decision`
- `readiness_pass`
- `gross_basis_pct`
- `estimated_net_basis_pct`
- `fee_slippage_buffer_pct`
- `required_missing_fields`
- `warnings`
- `assumptions`
- `comparability_pass`
- `freshness_pass`
- `liquidity_pass` or `depth_pass`
- `parser_normalized_status`

Decision defaults:

- `REJECT` -> `recommended_default_decision=REJECT`
- `NEED_DATA` -> `recommended_default_decision=NEED_DATA`
- `WATCH` -> `recommended_default_decision=WATCH`, but analysis-only

Mapping guardrails:

- `WATCH` is not `ENTER`.
- `readiness_pass` must not be treated as execution permission.
- Candidate assumptions must include public-read-only, analysis-only, no private API, and no trading behavior wording.

## 13. Explicitly not doing now

This PR explicitly does not do any of the following:

- Readiness helper implementation.
- Parser implementation.
- Adapter implementation.
- Fixture JSON creation.
- Tests creation.
- Config/registry change.
- Active strategy change.
- `spot_futures_basis_v0` active promotion.
- Live endpoint call.
- Generated JSON creation or commit.
- Private API use.
- Credentials/API keys/secrets/tokens use.
- Account/balance/position lookup.
- Order/cancel.
- Withdrawal/deposit/transfer.
- Execution.
- Alerting.
- Council auto-call.
- Auto-trading.

## 14. No-trade compliance

This readiness policy planning PR preserves no-trade posture:

- Active strategy promotion: no
- `spot_futures_basis_v0` active promotion: no
- Private API: no
- Credentials/API keys/secrets/tokens: no
- Account/balance/position lookup: no
- Order/cancel: no
- Withdrawal/deposit/transfer: no
- Auto-trading: no
- Council auto-call: no
- Alert: no
- Execution: no
- Config/registry change: no
- Source/runtime behavior change: no
- Fixture JSON creation: no
- Test file creation: no
- Live endpoint call: no
- Generated JSON commit: no
- `NO_TRADE_ONLY` preserved: yes

## 15. Generated JSON commit 금지

Generated packet/sampling files remain smoke artifacts only and must not be committed:

- `data/market_samples/*.json`
- `data/generated_packets/*.json`

Additional fixture guardrail:

- Live generated JSON must not be committed as fixture.
- This PR intentionally adds only this readiness policy planning handoff document and does not add generated JSON.

## 16. Rollback plan

Rollback path:

1. Revert this docs-only readiness policy planning PR.
2. Remove `docs/pr_handoffs/spot_futures_basis_readiness_policy_planning_2026_06_05.md`.
3. No code/config/registry/runtime/parser/readiness/test/fixture/generated-data rollback is required.

## 17. Next PR candidates

Recommended order after this readiness policy planning PR:

1. First mocked fixture files and parser unit test planning
2. First mocked parser/readiness implementation, `NO_TRADE_ONLY`
3. Registry/config planning, no activation
4. User-local public-read-only collect smoke
5. 3-sample sampling evidence
