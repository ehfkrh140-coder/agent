# Mark-Orderbook Gap Multi-Venue Comparative Summary v0

## 1. 작업 목적

이 문서는 Binance / Bybit / OKX `mark_orderbook_gap_hunt_v0`의 현재 evidence, 공통 구조, venue-specific boundary, watch items, no-trade 해석, 다음 선택지를 한 문서로 비교 정리하는 docs-only comparative summary handoff다.

Scope:

- Binance / Bybit / OKX `mark_orderbook_gap_hunt_v0` 현황을 한 문서로 비교한다.
- 이 문서는 implementation이 아니라 comparative summary다.
- 현재 adapter / parser / readiness / sampling behavior는 유지한다.
- `NO_TRADE_ONLY`를 유지한다.
- generated packet/sampling JSON은 smoke artifact이며 commit하지 않는다.

This PR does not implement timestamp policy, OKX index endpoint access, optional enrichment, parser behavior changes, readiness threshold changes, alerting, Council auto-call, execution, or active strategy promotion.

## 2. Strategy definition

- `strategy_family`: `mark_orderbook_gap_hunt`
- `strategy_id`: `mark_orderbook_gap_hunt_v0`
- `status`: experimental / non-active / `NO_TRADE_ONLY`
- Core comparison: mark price vs orderbook bid/ask.
- Mark price is not an executable price.
- `WATCH` / `REJECT` are analysis-only labels.
- `NO_PERSISTENT_EDGE`, `REJECT`, and `council_recommended=false` can be normal no-edge outcomes.

## 3. Evidence table

| Venue | Adapter / identifier | 30-sample evidence | Key result | Gap / watch metrics | Post-refactor smoke path | Known watch item |
| --- | --- | --- | --- | --- | --- | --- |
| Binance | `live_binance_mark_orderbook_gap_btcusdt` | complete; `samples_ok=30`; `samples_error=0`; `candidate_seen_count=30` | `persistence_status=NO_PERSISTENT_EDGE`; `council_recommended=false`; `positive_net_gap_count=0`; `readiness_status_counts.REJECT=30` | current comparative handoff records no critical venue-specific watch item | completed through shared helper/refactor regression and 3-venue user-local smoke evidence | none critical from current handoff |
| Bybit | `live_bybit_mark_orderbook_gap_btcusdt` | complete; `samples_ok=30`; `samples_error=0`; `candidate_seen_count=30` | `persistence_status=NO_PERSISTENT_EDGE`; `council_recommended=false`; `positive_net_gap_count=0`; `readiness_status_counts.REJECT=30` | `positive_gross_gap_count=25`; `max_gross_gap_pct=0.023012054161426362`; `max_estimated_net_gap_pct=-0.17698794583857363`; `avg_estimated_net_gap_pct=-0.19653008998817884`; `timestamp_data_age_watch_count=21`; `negative_data_age_observed=true`; `index_price_null_observed=false`; `stale_assumption_wording_observed=false` | completed through shared helper/refactor regression and 3-venue user-local smoke evidence | negative `data_age_ms` timestamp / clock-skew watch item |
| OKX | `live_okx_mark_orderbook_gap_btc_usdt_swap` | complete; `samples_ok=30`; `samples_error=0`; `candidate_seen_count=30` | `persistence_status=NO_PERSISTENT_EDGE`; `council_recommended=false`; `positive_net_gap_count=0`; `readiness_status_counts.REJECT=30` | `positive_gross_gap_count=28`; `max_gross_gap_pct=0.02771747402488164`; `max_estimated_net_gap_pct=-0.17228252597511837`; `avg_estimated_net_gap_pct=-0.19391529014802814`; `timestamp_data_age_watch_count=30`; `negative_data_age_observed=true`; `index_price_null_count=30`; `index_price_null_observed=true`; `stale_assumption_wording_observed=false` | completed through shared helper/refactor regression and 3-venue user-local smoke evidence | negative `data_age_ms` timestamp / clock-skew watch item; `index_price=None` OKX index/reference semantics watch item |

Interpretation:

- All three venue baselines show successful sampling/candidate observation at the documented evidence level.
- The evidence is sampling/analysis evidence, not profitable edge proof.
- The evidence is not persistent edge proof.
- Positive gross gap does not imply positive net gap, executable edge, or readiness pass.

## 4. Common structure

The three venue adapters now share the following analysis-only structure and expectations:

- Public no-key endpoints only.
- Analysis-only packet.
- Experimental / non-active / `no_trade_only` metadata.
- `execution_policy=NO_TRADE_ONLY`.
- `diagnostics_count=3` in the adapter regression baseline.
- `parser_normalized_status=OK` in the successful evidence path.
- `required_missing_fields=[]` in the successful evidence path.
- `readiness_status=REJECT` in the evidence baseline.
- `council_recommended=false` in the evidence baseline.
- `generated_from` / `source_files` metadata remains part of packet provenance.
- Assumptions include `public no-key endpoints only`, `analysis-only packet`, `no private API`, and `no trading behavior`.
- Shared metadata, diagnostics, and readiness/candidate mapping helpers are intended to reduce repetition without hiding venue-specific semantics.

## 5. Venue-specific boundaries

### Binance

- Binance USDM endpoint / symbol / response semantics must remain venue-specific.
- Symbol naming remains `BTCUSDT`.
- Size unit remains base-asset style for the current baseline.
- Binance-specific parser mode remains venue-specific.
- Binance should not inherit Bybit `retCode` / `retMsg` semantics or OKX `code` / `msg` semantics.

### Bybit

- Bybit V5 `category=linear` semantics remain venue-specific.
- Symbol naming remains `BTCUSDT`.
- `retCode` / `retMsg` diagnostics must remain visible.
- `funding_interval=480` warning remains tied to current Bybit fixture/evidence expectations.
- Negative `data_age_ms` remains a timestamp / clock-skew watch item.
- Size unit remains base-asset style for the current baseline.
- Index price is provided in the current Bybit evidence, so Bybit must not inherit OKX `index_price=None` semantics.

### OKX

- OKX `instType=SWAP` / `instId=BTC-USDT-SWAP` semantics remain venue-specific.
- `code` / `msg` diagnostics must remain visible.
- Size unit remains contracts.
- `contract_value`, `contract_multiplier`, `lot_size`, and `min_order_size` semantics remain venue-specific.
- `index_price=None` remains an OKX index/reference semantics watch item.
- Negative `data_age_ms` remains a timestamp / clock-skew watch item.
- OKX must not synthesize, infer, or backfill index price from mark price, orderbook midpoint, last price, or any other derived value.

## 6. Watch items

Current watch items and interpretation:

- Bybit negative `data_age_ms`: timestamp / clock-skew watch item.
- OKX negative `data_age_ms`: timestamp / clock-skew watch item.
- OKX `index_price=None`: OKX index/reference semantics watch item.
- Positive gross gap with negative estimated net gap can still be a normal no-edge `REJECT` result.
- `NO_PERSISTENT_EDGE` does not mean adapter failure.
- `council_recommended=false` does not mean sampling failure.
- Watch items do not justify active promotion, alerting, Council auto-call, execution, or strategy registry changes.

## 7. Policy documents already created

The following handoff/planning documents already exist for this strategy track:

- `docs/pr_handoffs/mark_orderbook_gap_timestamp_clock_skew_policy_planning_2026_06_05.md`
  - Separates Bybit / OKX negative `data_age_ms` into timestamp / clock-skew policy planning.
- `docs/pr_handoffs/mark_orderbook_gap_okx_index_reference_semantics_planning_2026_06_05.md`
  - Separates OKX `index_price=None` into OKX index/reference semantics planning.
- `docs/pr_handoffs/mark_orderbook_gap_venue_adapter_commonization_planning_2026_06_05.md`
  - Documents commonization candidates and venue-specific boundaries.
- `docs/pr_handoffs/mark_orderbook_gap_shared_metadata_wording_helper_2026_06_05.md`
  - Records shared metadata/assumptions helper work.
- `docs/pr_handoffs/mark_orderbook_gap_shared_diagnostics_builder_helper_2026_06_05.md`
  - Records shared diagnostics helper work.
- `docs/pr_handoffs/mark_orderbook_gap_shared_readiness_candidate_mapping_helper_2026_06_05.md`
  - Records shared readiness/candidate mapping helper work.
- `docs/pr_handoffs/mark_orderbook_gap_venue_specific_adapter_regression_tests_2026_06_05.md`
  - Records venue-specific regression test hardening.
- `docs/pr_handoffs/mark_orderbook_gap_post_refactor_user_local_smoke_evidence_2026_06_05.md`
  - Records post-refactor user-local smoke evidence.
- `docs/pr_handoffs/mark_orderbook_gap_bybit_okx_extended_sampling_evidence_2026_06_05.md`
  - Records Bybit / OKX 30-sample extended evidence.

## 8. Current recommendation

Recommended current stance:

- Treat `mark_orderbook_gap_hunt_v0` as having completed a 3-venue baseline / hardening phase.
- Keep `mark_orderbook_gap_hunt_v0` experimental / non-active / `NO_TRADE_ONLY`.
- Do not promote it to active strategy.
- Do not implement execution, alerting, or Council auto-call.
- Do not implement timestamp policy yet.
- Do not implement OKX optional index/reference enrichment yet.
- Keep generated sampling JSON out of git.
- The next large candidate is next experimental strategy planning or separate docs-only research.

## 9. No-trade compliance

This comparative summary PR preserves no-trade posture:

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
- OKX index endpoint implementation: no
- Optional enrichment implementation: no
- Generated JSON commit: no
- `NO_TRADE_ONLY` preserved: yes

## 10. Generated JSON commit 금지

Generated packet/sampling files remain smoke artifacts only and must not be committed:

- `data/market_samples/*.json`
- `data/generated_packets/*.json`

This PR intentionally adds only this comparative summary handoff document and does not add generated JSON.

## 11. Rollback plan

Rollback path:

1. Revert this docs-only comparative summary PR.
2. Remove `docs/pr_handoffs/mark_orderbook_gap_multi_venue_comparative_summary_2026_06_05.md`.
3. No code/config/registry/runtime/parser/readiness/generated-data rollback is required.

## 12. Next PR candidates

Recommended order after this comparative summary PR:

1. Next experimental strategy planning
2. Optional OKX index/reference source research docs-only
3. Timestamp policy implementation v0, only after separate approval
4. Strategy evidence dashboard / journal summary planning
5. Council review handoff criteria planning
