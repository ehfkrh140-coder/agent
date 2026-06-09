# Spot-Futures Basis OpportunityPacket Mapping Planning v0

## 1. 작업 목적

이 문서는 live adapter 구현 전에 `spot_futures_basis_v0`의 source bundle / readiness result를 향후 OpportunityPacket observations, candidates, extensions에 어떻게 매핑할지 정의하는 docs-only mapping planning handoff다.

Purpose:

- Live adapter 구현 전에 `spot_futures_basis_v0`의 OpportunityPacket mapping boundary를 정의한다.
- Parser source bundle, readiness result, future packet observation/candidate 구조를 명시적으로 연결한다.
- Adapter + packet + registry를 한 PR에 묶지 않기 위한 planning이다.
- 현재 behavior는 유지한다.
- `NO_TRADE_ONLY`를 유지한다.
- 이번 PR에서는 code, tests, config, registry, adapter, OpportunityPacket implementation, packet builder, runtime behavior를 구현하지 않는다.

## 2. Current implementation recap

Current state:

- Parser helper exists: `src/market_data/parsers/spot_futures_basis.py`.
- Readiness helper exists: `src/strategy/spot_futures_basis_readiness.py`.
- Parser returns normalized spot observation, normalized perp observation, and source bundle.
- Readiness returns `readiness_status`, `recommended_default_decision`, `readiness_pass`, `metrics`, `warnings`, `required_missing_fields`, and `assumptions`.
- No OpportunityPacket creation exists yet for `spot_futures_basis_v0`.
- No adapter/live collect path exists yet.
- No registry/config integration exists yet.
- No active promotion exists.
- Binance is the first reference venue only, not a Binance-only strategy commitment.

## 3. Proposed OpportunityPacket identity

Future packet identity candidate, planning-only:

- `schema_version`: `opportunity_packet_v0` or the repo-standard current OpportunityPacket schema available at implementation time.
- `signal_type`: `spot_futures_basis`
- `strategy_family`: `spot_futures_basis`
- `strategy_id`: `spot_futures_basis_v0`
- `asset`: `BTC`
- `quote`: `USDT`
- `execution_policy`: `NO_TRADE_ONLY`
- `no_trade_only`: `true`
- `status`: experimental / non-active / analysis-only
- `source_venue_id`: `binance`
- `comparison_type`: `same_exchange_spot_perp_basis`

Boundaries:

- This identity is a planning candidate.
- This PR does not implement packet creation code.
- This PR does not implement a packet builder.
- This PR does not promote `spot_futures_basis_v0` to active.
- Future packet identity should remain venue-normalized so Bybit / OKX source mappings can reuse the same strategy-level packet contract.

## 4. Observation mapping

Future `observations` array candidate should contain one spot observation and one perp observation.

### Observation A: spot observation

Candidate fields:

- `observation_id`: `binance_spot_btcusdt_spot_futures_basis`
- `venue_id`: `binance`
- `venue_name`: Binance Spot
- `market_symbol`: `BTCUSDT`
- `instrument_type`: `spot`
- `bid`: mapped from normalized `best_bid`
- `ask`: mapped from normalized `best_ask`
- `bid_size`: mapped from normalized `best_bid_qty`
- `ask_size`: mapped from normalized `best_ask_qty`
- `tick`: mapped from normalized `tick_size`
- `step`: mapped from normalized `step_size`
- `timestamp_utc` or `update_id`: mapped from source timestamp fields when available, otherwise `book_update_id`
- `liquidity.orderbook_depth_available`: true when normalized `depth_bids` and `depth_asks` are present
- `data_quality.latency_ms`: mapped from normalized `latency_ms`
- `data_quality.data_age_ms`: mapped from normalized `data_age_ms`
- `data_quality.parser_normalized_status`: mapped from normalized `parser_normalized_status`

Spot observation `extensions` candidates:

- `market_type`: `spot`
- `base_asset`: `BTC`
- `quote_asset`: `USDT`
- `bid_qty_unit`: `base_asset`
- `ask_qty_unit`: `base_asset`
- `parser_normalized_status`
- `required_missing_fields`
- `raw_endpoint_ids`
- `book_update_id`
- `min_notional`

### Observation B: perp observation

Candidate fields:

- `observation_id`: `binance_usdm_btcusdt_perp_spot_futures_basis`
- `venue_id`: `binance`
- `venue_name`: Binance USDⓈ-M Futures
- `market_symbol`: `BTCUSDT`
- `instrument_type`: `linear_perpetual` or `perp`
- `bid`: mapped from normalized `best_bid`
- `ask`: mapped from normalized `best_ask`
- `bid_size`: mapped from normalized `best_bid_qty`
- `ask_size`: mapped from normalized `best_ask_qty`
- `mark_price`: mapped from normalized `mark_price`
- `index_price`: mapped from normalized `index_price`
- `derivatives.funding_rate_pct`: mapped from normalized `funding_rate`
- `derivatives.next_funding_time_utc`: mapped from normalized `next_funding_time`
- `tick`: mapped from normalized `tick_size`
- `step`: mapped from normalized `step_size`
- `timestamp_utc`: mapped from normalized `book_timestamp` or premium-index time when available
- `liquidity.orderbook_depth_available`: true when normalized `depth_bids` and `depth_asks` are present
- `data_quality.latency_ms`: mapped from normalized `latency_ms`
- `data_quality.data_age_ms`: mapped from normalized `data_age_ms`
- `data_quality.parser_normalized_status`: mapped from normalized `parser_normalized_status`

Perp observation `extensions` candidates:

- `market_type`: `perp`
- `base_asset`: `BTC`
- `quote_asset`: `USDT`
- `settlement_asset`: `USDT`
- `margin_asset`: `USDT`
- `contract_type`: `PERPETUAL`
- `bid_qty_unit`
- `ask_qty_unit`
- `parser_normalized_status`
- `required_missing_fields`
- `raw_endpoint_ids`
- `book_timestamp`
- `interest_rate`
- `min_notional`

Observation guardrails:

- `mark_price`, `index_price`, and `funding_rate` are context and are not executable basis.
- Spot and perp can share the `BTCUSDT` symbol string, but product semantics are different.
- Observation mapping must preserve parser warnings and missing-field evidence instead of silently dropping them.

## 5. Candidate mapping

Future `candidates` array should contain an analysis-only basis candidate.

Candidate fields:

- `candidate_id`: `binance_btcusdt_spot_futures_basis_candidate`
- `candidate_type`: `spot_futures_basis_observation`
- `strategy_family`: `spot_futures_basis`
- `strategy_id`: `spot_futures_basis_v0`
- `source_observation_id`: `binance_spot_btcusdt_spot_futures_basis`
- `target_observation_id`: `binance_usdm_btcusdt_perp_spot_futures_basis`
- `source_venue_id`: `binance`
- `target_venue_id`: `binance`
- `direction`: one of:
  - `analysis_only_long_spot_short_perp_basis`
  - `analysis_only_long_perp_short_spot_basis`
  - `analysis_only_no_positive_executable_basis`
- `gross_basis_pct`: mapped from readiness `selected_gross_basis_pct`
- `estimated_net_basis_pct`: mapped from readiness `estimated_net_basis_pct`
- `liquidity_pass`: mapped from readiness metrics
- `freshness_pass`: mapped from readiness metrics
- `comparability_pass`: mapped from readiness metrics
- `guard_pass`: true only when no-trade guardrails and metadata are intact; false or omitted if unresolved
- `required_missing_fields`: merged from parser observations and readiness result
- `assumptions`: merged from source bundle and readiness result
- `extensions.warnings`: mapped from readiness warnings and parser warnings

Candidate guardrails:

- Candidate labels are analysis-only and must not imply order intent.
- `readiness_pass=True` must not be treated as execution permission.
- `WATCH` must remain analysis-only and must not be converted to `ENTER`.

## 6. Metrics mapping

Readiness metrics should map either to `candidate.metrics` or explicit candidate fields, depending on repo-standard OpportunityPacket shape at implementation time.

Required metric mappings:

- `readiness_status`
- `recommended_default_decision`
- `readiness_pass`
- `spot_bid`
- `spot_ask`
- `perp_bid`
- `perp_ask`
- `spot_mid`
- `perp_mid`
- `mid_basis_pct`
- `long_spot_short_perp_gross_pct`
- `long_perp_short_spot_gross_pct`
- `selected_direction`
- `selected_gross_basis_pct`
- `fee_slippage_buffer_pct`
- `estimated_net_basis_pct`
- `parser_normalized_status`
- `comparability_pass`
- `freshness_pass`
- `liquidity_pass`

Metric guardrails:

- `readiness_pass=True` is not execution permission.
- `WATCH` is not `ENTER`.
- `estimated_net_basis_pct > 0` does not authorize execution.
- `mid_basis_pct` is context unless future policy explicitly promotes it.
- Mark/index/funding metrics are context and not executable basis.

## 7. Readiness / default decision mapping

Future packet readiness/default decision mapping:

- `REJECT` -> `recommended_default_decision=REJECT`, `readiness_pass=false`
- `NEED_DATA` -> `recommended_default_decision=NEED_DATA`, `readiness_pass=false`
- `WATCH` -> `recommended_default_decision=WATCH`, `readiness_pass=true`

No-trade qualifiers:

- `WATCH` remains analysis-only.
- `WATCH` must not trigger Council auto-call.
- `WATCH` must not trigger alert.
- `WATCH` must not trigger execution.
- Active promotion is forbidden.
- `recommended_default_decision` is a review label, not an execution command.

## 8. Assumptions and warning mapping

Future packet assumptions must include:

- Public no-key endpoints only.
- Analysis-only packet.
- No private API.
- No trading behavior.
- Mark price is not executable.
- Last price is weak context only if present.
- `WATCH` is not `ENTER`.
- `WATCH` does not trigger Council auto-call, alert, or execution.
- Spot/perp symbol string equality does not imply product equivalence.
- Funding rate is context, not basis decision alone.

Warning candidates:

- `no_positive_gross_basis`
- `non_positive_estimated_net_basis`
- `positive_net_basis_analysis_only`
- `mark_price_not_executable`
- `funding_rate_not_basis`
- `required_fields_missing`
- `parser_required_missing_fields_present`
- `parser_status_not_ok`
- `fee_slippage_buffer_missing_or_invalid`
- `quote_settlement_comparability_unresolved`
- `negative_data_age_watch`
- `stale_timestamp`
- `low_top_of_book_quantity`
- `depth_vwap_not_implemented`

Mapping guidance:

- Preserve parser warnings separately or tag their source when merging into candidate warnings.
- Preserve readiness warnings as candidate-level warnings because they explain why a candidate is `REJECT`, `NEED_DATA`, or `WATCH`.
- Do not drop `positive_net_basis_analysis_only`; it is the main reminder that positive net basis remains no-trade.

## 9. Detector metadata / provenance mapping

Future `detector_metadata` candidates:

- `detector_name`: `spot_futures_basis_packet_builder` or `binance_spot_futures_basis_adapter` candidate, depending on implementation boundary.
- `detector_version`: `v0`
- `generated_from`: `public_binance_spot_and_usdm_futures_book_ticker_depth_premium_index_exchange_info`
- `source_files` candidates:
  - `src/market_data/parsers/spot_futures_basis.py`
  - `src/strategy/spot_futures_basis_readiness.py`
  - future adapter path if added
  - future packet builder path if added

Provenance guardrails:

- Detector metadata must identify public/no-key source provenance.
- Detector metadata must not include credentials, account identifiers, order identifiers, or generated live JSON paths as committed fixtures.
- Future builder should record mocked/unit-test provenance separately from user-local live smoke evidence.

## 10. OpportunityPacket implementation options

### Option A: adapter returns source_bundle + readiness only first

- No packet yet.
- Simpler live smoke.
- Packet implementation later.
- Risk: source bundle and packet shape may drift.

### Option B: packet mapping implementation before live adapter

- Implement a pure packet builder from source_bundle + readiness using mocked tests.
- No live adapter yet.
- Safer consistency.
- More unit tests before smoke.
- Keeps no-trade metadata, assumptions, warnings, readiness, and metrics aligned before any public live call path.

### Option C: adapter + packet builder together

- Faster to live smoke.
- Larger PR.
- Higher coupling and rollback risk.
- Easier to blur adapter, packet, registry, and runtime boundaries.

Recommended direction:

- Prefer Option B: pure OpportunityPacket builder implementation from mocked source_bundle + readiness before live adapter.
- Reason: existing project pattern, review safety, no-trade metadata consistency, and lower rollback complexity.
- Do not implement Option B in this PR; this PR is planning-only.
- Do not choose Option C for the next PR because adapter + packet builder together is too coupled.

## 11. Proposed next PR sequence

Recommended sequence:

1. PR 1: OpportunityPacket mapping planning v0.
2. PR 2: Pure OpportunityPacket builder implementation, mocked/unit tests only.
3. PR 3: First public-read-only adapter implementation, mocked/unit tests only, no registry activation.
4. PR 4: Registry/config planning, no activation.
5. PR 5: User-local public-read-only collect smoke.
6. PR 6: Docs-only collect evidence.
7. PR 7: 3-sample sampling support.
8. PR 8: 3-sample sampling evidence.
9. PR 9: 30-sample extended evidence.

Sequencing guardrails:

- Do not combine adapter + packet + registry in one PR.
- Do not perform live endpoint calls in pure packet builder PR.
- Do not commit generated smoke JSON at any stage.
- Do not activate `spot_futures_basis_v0` during mapping, builder, adapter, or registry planning PRs.

## 12. Risk assessment

Key risks to manage:

- `WATCH` can be misunderstood as a trade signal.
- Packet fields can look like execution permission if no-trade wording is not preserved.
- Mark/index/funding context can be mistaken for executable basis.
- Spot/perp same symbol string can be mistaken for same product semantics.
- Going to live adapter without packet mapping increases source_bundle/packet drift risk.
- Bundling adapter + packet + registry in one PR makes rollback harder.
- Generated JSON can be accidentally committed if generated paths are not rechecked.
- Fee/slippage buffer assumptions can be mistaken for account-specific private fee tier data.
- Top-of-book liquidity can be mistaken for fill feasibility.

## 13. No-trade compliance

This docs-only mapping planning PR preserves no-trade posture:

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
- Live endpoint call: no
- OpportunityPacket implementation: no
- Packet builder implementation: no
- Adapter implementation: no
- Generated JSON usage: no
- `NO_TRADE_ONLY` preserved: yes

## 14. Generated JSON commit 금지

Generated packet/sampling files remain smoke artifacts only and must not be committed:

- `data/market_samples/*.json`
- `data/generated_packets/*.json`

This PR:

- Does not add generated JSON.
- Does not change `data/market_samples`.
- Does not change `data/generated_packets`.
- Does not perform live collection.

## 15. Rollback plan

Rollback path:

1. Revert this docs-only mapping planning PR.
2. Remove `docs/pr_handoffs/spot_futures_basis_opportunity_packet_mapping_planning_2026_06_05.md`.
3. No code/config/registry/runtime/parser/readiness/test/fixture/generated-data rollback is required.

## 16. Next PR candidates

Recommended order:

1. Pure OpportunityPacket builder implementation, mocked/unit tests only
2. First public-read-only adapter implementation, mocked/unit tests only
3. Registry/config planning, no activation
4. User-local public-read-only collect smoke
5. 3-sample sampling evidence
6. 30-sample extended evidence
