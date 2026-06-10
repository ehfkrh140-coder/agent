# Depth / VWAP Packet Context Integration v0

## 1. 작업 목적

이 문서는 Depth/VWAP pure helper와 mocked fixture contract tests 이후, VWAP context를 `spot_futures_basis_v0` packet/candidate extensions에 diagnostics-only로 붙이는 첫 bounded implementation sprint를 기록한다.

Purpose:

- `src/market_data/depth_vwap.py` helper 결과를 직접 판단에 쓰지 않고, optional diagnostics/context로만 노출한다.
- `spot_futures_basis_v0` packet builder가 명시적인 `target_size` 또는 `target_notional`을 받은 경우에만 Depth/VWAP context를 생성할 수 있게 한다.
- Default packet builder path는 기존과 동일하게 `depth_vwap_context`를 만들지 않는다.
- Readiness behavior unchanged.
- `estimated_net_basis_pct`, `readiness_status`, `recommended_default_decision`, `required_missing_fields`, `readiness_pass` unchanged.
- Sampling behavior unchanged.
- Adapter live path unchanged unless explicit target is passed by a future approved caller.
- `NO_TRADE_ONLY` 유지.

This PR is not a VWAP-adjusted decision PR. It only adds analysis-only context placement.

## 2. 변경 파일

Changed files:

- `src/market_data/depth_vwap_context.py`
- `src/market_data/spot_futures_basis_packet_builder.py`
- `tests/test_depth_vwap_context.py`
- `tests/test_spot_futures_basis_vwap_context.py`
- `docs/pr_handoffs/depth_vwap_packet_context_integration_2026_06_05.md`

No adapter, parser, readiness, sampling, fixture, config, registry, tool, dashboard, generated JSON, or OKX implementation files were changed.

## 3. 구현 요약

Implementation summary:

- Added `src/market_data/depth_vwap_context.py` as a pure context module.
- The context module imports only the existing Depth/VWAP pure helper and standard library.
- Added `extract_depth_levels_from_observation(observation, *, side)` to find depth levels from supported observation shapes:
  - `observation["depth"]["bids"]` / `observation["depth"]["asks"]`
  - `observation["orderbook_depth"]["bids"]` / `observation["orderbook_depth"]["asks"]`
  - `observation["bid_levels"]` / `observation["ask_levels"]`
  - `observation["depth_bids"]` / `observation["depth_asks"]`
  - explicit `observation["liquidity"]["depth_levels"]` by side when available
- Added `build_observation_vwap_context(...)` to calculate ask/bid VWAP diagnostics for a single observation only when a target is provided.
- Added `build_spot_futures_basis_vwap_context(...)` to build spot/perp VWAP diagnostics and direction summaries.
- Updated `build_spot_futures_basis_opportunity_packet(...)` with optional `target_size`, `target_notional`, and `depth_vwap_context` inputs.
- Added packet-level placement at `packet.extensions.depth_vwap_context` only when explicit context/target is supplied.
- Added candidate-level placement at `candidate.extensions.depth_vwap_context` as a relevant direction summary only when explicit context/target is supplied.
- Default behavior remains unchanged: no target means no packet/candidate `depth_vwap_context` is attached by the packet builder default path.

## 4. 쉬운 예시

쉬운 예시:

- Top-of-book ask만 보면 가격 100에 수량 1개가 보일 수 있다.
- 사용자가 분석용으로 target size 5를 가정하면 100에 5개를 모두 살 수 있다고 착각할 수 있다.
- 실제 public depth가 100에 1개, 101에 2개, 102에 2개라면 VWAP-style average는 101.2가 된다.
- 이 PR의 VWAP context는 이런 평균 예상가와 depth coverage를 packet/candidate extensions에 참고 정보로 담을 수 있게 한다.
- 하지만 이 참고 정보는 매매 신호가 아니다.
- It is not ENTER, not alert, not Council auto-call, not execution, and not account-specific fill feasibility.

## 5. Context output fields

Top-level context fields:

- `behavior: "diagnostics_only"`
- `no_trade_only: true`
- `execution_policy: "NO_TRADE_ONLY"`
- `target_size`
- `target_notional`
- `spot`
- `perp`
- `directions`
- `warnings`

Spot/perp context fields:

- `ask_vwap_result`
- `bid_vwap_result`
- `depth_available`
- `ask_levels_available`
- `bid_levels_available`
- `warnings`

Direction context fields:

- `directions.long_spot_short_perp.spot_vwap_ask`
- `directions.long_spot_short_perp.perp_vwap_bid`
- `directions.long_spot_short_perp.depth_coverage_pct`
- `directions.long_spot_short_perp.insufficient_depth`
- `directions.long_spot_short_perp.context_only: true`
- `directions.long_perp_short_spot.perp_vwap_ask`
- `directions.long_perp_short_spot.spot_vwap_bid`
- `directions.long_perp_short_spot.depth_coverage_pct`
- `directions.long_perp_short_spot.insufficient_depth`
- `directions.long_perp_short_spot.context_only: true`

Target policy:

- If neither `target_size` nor `target_notional` is provided, context builders return warning `depth_vwap_target_not_provided` and do not compute VWAP.
- If both are provided, `target_size` is preferred and warning `target_size_preferred_over_target_notional` is recorded.
- Target values are analysis parameters only and must not imply order intent.

## 6. Packet/candidate extension placement

Placement:

- `packet.extensions.depth_vwap_context` contains the full spot/perp/direction diagnostics-only context.
- `candidate.extensions.depth_vwap_context` contains a direction-focused summary with:
  - `behavior`
  - `no_trade_only`
  - `execution_policy`
  - `target_size`
  - `target_notional`
  - `directions`
  - `context_only: true`
  - `warnings`
  - analysis-only assumptions

Semantics preserved:

- VWAP context is analysis-only.
- VWAP context is not execution permission.
- VWAP context does not prove fill feasibility.
- Top-of-book liquidity is not fill feasibility.
- `NO_TRADE_ONLY` remains preserved.

## 7. Behavior unchanged proof

Behavior unchanged proof:

- `readiness_status` unchanged.
- `recommended_default_decision` unchanged.
- `estimated_net_basis_pct` unchanged.
- `required_missing_fields` unchanged.
- `readiness_pass` unchanged.
- Sampling behavior unchanged because `src/market_data/sampling.py` was not modified.
- Adapter live path unchanged because adapters were not modified and default packet builder calls without explicit target do not attach VWAP context.
- Existing packet builder validation remains pass-through validation for `spot_futures_basis` packet dicts.
- Existing `tests/test_spot_futures_basis_packet_builder.py` and `tests/test_spot_futures_basis_collect_path.py` continue passing.

## 8. Tests added

Added tests:

- `tests/test_depth_vwap_context.py`
  - Extracts levels from `observation["depth"]["asks"]` / `observation["depth"]["bids"]`.
  - Extracts levels from `observation["orderbook_depth"]`.
  - Extracts levels from `bid_levels` / `ask_levels`.
  - Missing depth returns warning and no exception.
  - `target_size` computes ask/bid context.
  - `target_notional` computes context.
  - Both target values prefer size with warning.
  - Source bundle spot/perp context computes both directions.
  - Insufficient depth propagates into direction context.
  - Context output has no private/account/order keys.
  - Module structural guardrail confirms no requests/http/file/env imports.
  - Generated JSON paths are not created or referenced.
  - No target returns `depth_vwap_target_not_provided` warning.
  - VWAP context is `diagnostics_only` and `NO_TRADE_ONLY`.
- `tests/test_spot_futures_basis_vwap_context.py`
  - Packet builder default path remains behavior unchanged and validates.
  - Explicit `target_size` adds `packet.extensions.depth_vwap_context`.
  - Candidate extension context is present with `context_only: true`.
  - `readiness_status`, `recommended_default_decision`, `estimated_net_basis_pct`, `required_missing_fields`, and `readiness_pass` remain unchanged after adding VWAP context.
  - WATCH no-trade path preserves WATCH is not ENTER and no execution.
  - Generated JSON is not created.
  - New context tests do not import adapters/parsers/readiness/sampling.
- Existing `tests/test_depth_vwap.py` still passes.
- Existing `tests/test_depth_vwap_mocked_fixtures.py` still passes.
- Existing `tests/test_spot_futures_basis_packet_builder.py` still passes.
- Existing `tests/test_spot_futures_basis_collect_path.py` still passes.

## 9. No file/network/private/execution guardrails

Guardrails:

- No `requests`, `aiohttp`, or `httpx` import.
- No network calls.
- No file I/O in the context module.
- No env var lookup.
- No credential/config/registry lookup.
- No adapter import.
- No parser import in the context module.
- No readiness import in the context module.
- No sampling import.
- No private API.
- No account/balance/position lookup.
- No order/cancel/withdraw/deposit/transfer behavior.
- No alert, Council auto-call, execution, or auto-trading behavior.

## 10. Explicitly not doing now

Explicitly not doing now:

- VWAP-adjusted readiness 없음.
- `estimated_net_basis_pct`를 VWAP로 재계산하지 않음.
- `recommended_default_decision` 변경 없음.
- `readiness_status` 변경 없음.
- `readiness_pass` 변경 없음.
- Sampling summary context support 없음.
- Dashboard update 없음.
- Adapter 연결 없음.
- Parser 연결 없음.
- Readiness module 변경 없음.
- Live endpoint 호출 없음.
- Generated JSON 생성 없음.
- Council auto-call 없음.
- Alert 없음.
- Execution 없음.
- Active strategy 변경 없음.
- OKX adapter/config/research 구현 없음.

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
- Tests do not create generated JSON.
- 이번 PR에는 generated JSON을 추가하지 않음.

## 13. Rollback plan

Rollback plan:

1. Revert this PR.
2. Remove `src/market_data/depth_vwap_context.py`.
3. Remove `tests/test_depth_vwap_context.py`.
4. Remove `tests/test_spot_futures_basis_vwap_context.py`.
5. Revert the optional integration in `src/market_data/spot_futures_basis_packet_builder.py`.
6. Remove `docs/pr_handoffs/depth_vwap_packet_context_integration_2026_06_05.md`.
7. No config/runtime/generated-data rollback is needed.
8. Re-run required validation commands if rollback evidence is requested.

## 14. Next PR candidates

다음 PR 후보:

1. Sampling summary context support, behavior unchanged.
2. Dashboard depth/VWAP policy status update.
3. Next Experimental Strategy Selection v0.
4. VWAP-adjusted readiness policy only after separate approval and stronger evidence.
