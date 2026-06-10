# Depth / VWAP Sampling Summary Context Support v0

## 1. 작업 목적

이 문서는 Depth/VWAP packet context integration 이후, `run_market_sampling(...)` summary가 packet/candidate extensions에 이미 존재하는 `depth_vwap_context`를 analysis-only diagnostics로 집계하게 한 broader bounded implementation sprint를 기록한다.

Purpose:

- Sampling summary가 `depth_vwap_context` seen/missing, behavior, target, warning, insufficient depth, ask/bid slippage context를 집계한다.
- Readiness behavior unchanged.
- `recommended_default_decision`, `estimated_net_gap_pct`, `positive_net_gap_count`, `readiness_pass_count`, `persistence_status`, `council_recommended` 정책 unchanged.
- `NO_TRADE_ONLY` 유지.
- This PR is not a VWAP-adjusted readiness PR.
- This PR is not execution, alert, Council auto-call, active promotion, live collection, or generated JSON persistence.

## 2. 변경 파일

Changed files:

- `src/market_data/sampling.py`
- `tests/test_depth_vwap_sampling_context.py`
- `docs/pr_handoffs/depth_vwap_sampling_summary_context_support_2026_06_05.md`

No adapter, parser, readiness, packet builder, Depth/VWAP helper, Depth/VWAP context builder, fixture, config, registry, tool, dashboard, generated JSON, or OKX implementation files were changed.

## 3. 구현 요약

Implementation summary:

- Added per-sample extraction of `depth_vwap_context` in `src/market_data/sampling.py`.
- Lookup order:
  1. `best_candidate.extensions.depth_vwap_context`
  2. `opportunity_packet.candidates[0].extensions.depth_vwap_context`
  3. `opportunity_packet.extensions.depth_vwap_context`
- Added per-sample fields:
  - `depth_vwap_context_seen`
  - `depth_vwap_insufficient_depth`
  - `depth_vwap_context_behavior`
  - `depth_vwap_warnings`
  - `depth_vwap_target_size`
  - `depth_vwap_target_notional`
- Added summary fields:
  - `depth_vwap_context_seen_count`
  - `depth_vwap_context_missing_count`
  - `depth_vwap_context_behavior_counts`
  - `depth_vwap_insufficient_depth_count`
  - `depth_vwap_target_size_seen_count`
  - `depth_vwap_target_notional_seen_count`
  - `depth_vwap_context_only_count`
  - `depth_vwap_warning_counts`
  - `max_depth_vwap_ask_slippage_pct`
  - `max_depth_vwap_bid_slippage_pct`
  - `avg_depth_vwap_ask_slippage_pct`
  - `avg_depth_vwap_bid_slippage_pct`
- Numeric aggregation safely accepts Decimal/string/int/float-like values by reusing safe float conversion.
- Warning aggregation recursively collects `warnings` from context, spot, perp, and direction-level dictionaries.
- Insufficient depth aggregation recursively treats any `insufficient_depth: true` as sample-level insufficient depth.
- Missing context is safe: `depth_vwap_context_seen=false`, missing count increments, slippage max/avg remain `None` when no values exist.
- Malformed context is safe: sampling does not crash and records `depth_vwap_context_malformed` warning.

## 4. 쉬운 예시

쉬운 예시:

- Sample 3개 중 2개에 VWAP context가 있으면 `depth_vwap_context_seen_count=2`.
- 1개 sample에서 `insufficient_depth=true`가 관찰되면 `depth_vwap_insufficient_depth_count=1`.
- Ask slippage values가 `0.01`, `0.03`이면 `max_depth_vwap_ask_slippage_pct=0.03`, `avg_depth_vwap_ask_slippage_pct=0.02`가 된다.
- 이 숫자는 참고 정보이지 매매 신호가 아니다.
- It is not ENTER, not execution permission, not fill feasibility proof, not Council auto-call trigger, not alert trigger, and not active promotion evidence.

## 5. Behavior unchanged proof

Behavior unchanged proof:

- `readiness_status` unchanged.
- `readiness_pass` unchanged.
- `recommended_default_decision` unchanged.
- `estimated_net_gap_pct` unchanged.
- `estimated_net_basis_pct` unchanged where present in packet/candidate metrics.
- `positive_net_gap_count` unchanged.
- `readiness_pass_count` unchanged.
- `persistence_status` unchanged.
- `council_recommended` unchanged.
- `council_reason` policy unchanged.
- `required_missing_fields` unchanged.
- `parser_normalized_status` unchanged.
- Generated JSON not created.
- Live endpoint not called.

## 6. Tests added

Added `tests/test_depth_vwap_sampling_context.py` with mocked/unit tests covering:

- Summary seen count.
- Summary missing count.
- Behavior counts with `diagnostics_only`.
- Insufficient depth aggregation.
- Target size seen count.
- Target notional seen count.
- Warning aggregation from top-level, spot, perp, and direction warnings.
- Max/avg ask slippage aggregation.
- Max/avg bid slippage aggregation.
- Per-sample `depth_vwap_context_seen` fields.
- Per-sample missing-context safety.
- Readiness status unchanged.
- Recommended default decision unchanged.
- Estimated net gap unchanged.
- Positive net gap count unchanged.
- Readiness pass count unchanged.
- Persistence status and Council recommendation unchanged.
- No private/account/order/execution guardrail.
- Generated JSON guardrail.
- Existing no-context sampling behavior remains safe.
- WATCH path remains WATCH is not ENTER and no execution.
- Malformed `depth_vwap_context` does not crash sampling and records warning/missing safely.
- Packet-level context lookup is supported.

Existing tests verified in this PR:

- `tests/test_depth_vwap.py`
- `tests/test_depth_vwap_mocked_fixtures.py`
- `tests/test_depth_vwap_context.py`
- `tests/test_spot_futures_basis_vwap_context.py`
- `tests/test_spot_futures_basis_sampling.py`
- Full `python -m unittest discover -s tests`

## 7. No private/execution/generated JSON guardrails

Guardrails:

- Tests use a small fake adapter only.
- Tests do not import live adapters.
- Tests do not call live endpoints.
- Tests use `output_path=None`.
- Tests use `also_save_packets=False`.
- Tests use `interval_seconds=0` and no-op sleep.
- Tests do not create generated JSON files.
- Sampling additions do not introduce private API, credentials, account/balance/position lookup, order/cancel, withdrawal/deposit/transfer, alert, Council auto-call, execution, or auto-trading.

## 8. Explicitly not doing now

Explicitly not doing now:

- VWAP-adjusted readiness 없음.
- Packet builder change 없음.
- Adapter 연결 없음.
- Parser 연결 없음.
- Readiness 연결 없음.
- Dashboard update 없음.
- Live endpoint 호출 없음.
- Generated JSON 생성 없음.
- Council auto-call 없음.
- Alert 없음.
- Execution 없음.
- Active strategy 변경 없음.
- OKX implementation 없음.

## 9. No-trade compliance

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

## 10. Generated JSON commit 금지

Generated JSON policy 확인:

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- Tests do not create generated JSON.
- 이번 PR에는 generated JSON을 추가하지 않음.

## 11. Rollback plan

Rollback plan:

1. Revert this PR.
2. Revert `src/market_data/sampling.py` summary additions.
3. Remove `tests/test_depth_vwap_sampling_context.py`.
4. Remove `docs/pr_handoffs/depth_vwap_sampling_summary_context_support_2026_06_05.md`.
5. No config/runtime/generated-data rollback is needed.
6. Re-run required validation commands if rollback evidence is requested.

## 12. Next PR candidates

다음 PR 후보:

1. Dashboard depth/VWAP policy status update.
2. Next Experimental Strategy Selection v0.
3. VWAP-adjusted readiness policy only after separate approval and stronger evidence.
4. Optional generated dashboard planning later.

## 13. Self-audit checklist

Self-audit checklist:

- [x] Did not change readiness behavior.
- [x] Did not change estimated_net_gap_pct.
- [x] Did not change persistence_status.
- [x] Did not change council_recommended.
- [x] Did not modify adapters/parsers/readiness/packet builder.
- [x] Did not call live endpoints.
- [x] Did not create generated JSON.
- [x] Preserved NO_TRADE_ONLY.
- [x] Added at least 15 sampling context tests.
- [x] Existing no-context sampling behavior remains safe.
- [x] VWAP context is diagnostics-only.
