# Spot-Futures Basis First Mocked Readiness Implementation v0

## 1. 작업 목적

이 문서는 `spot_futures_basis_v0`의 첫 mocked readiness implementation handoff다.

Purpose:

- Parser output/source bundle을 입력으로 받아 `REJECT` / `NEED_DATA` / `WATCH` readiness result dict를 생성한다.
- Mocked/unit-test only로 formula, status policy, warnings, assumptions를 고정한다.
- 이번 PR은 live endpoint 호출이 아니다.
- 이번 PR은 OpportunityPacket 생성이 아니다.
- 이번 PR은 adapter/live collect, registry/config 변경, active promotion을 하지 않는다.
- `NO_TRADE_ONLY`를 유지한다.

## 2. 변경 파일

Changed files:

- `src/strategy/spot_futures_basis_readiness.py`
- `tests/test_spot_futures_basis_mocked_readiness.py`
- `docs/pr_handoffs/spot_futures_basis_first_mocked_readiness_implementation_2026_06_05.md`

Unchanged by design:

- Existing fixture JSON files
- `src/market_data/parsers/spot_futures_basis.py`
- `src/market_data/adapters/`
- `config/`
- `data/market_samples/`
- `data/generated_packets/`

## 3. Readiness implementation summary

Added `src/strategy/spot_futures_basis_readiness.py` with one public helper:

- `evaluate_spot_futures_basis_readiness(source_bundle, *, fee_slippage_buffer_pct=0.20, max_data_age_ms=None) -> dict`

The helper:

- Consumes parser source bundle output only.
- Reads `spot_observation` and `perp_observation` from the bundle.
- Returns `strategy_family`, `strategy_id`, `readiness_status`, `readiness_pass`, `recommended_default_decision`, `required_missing_fields`, `warnings`, `assumptions`, `metrics`, `no_trade_only`, and `execution_policy`.
- Does not perform file reads or network calls.
- Does not create OpportunityPacket.
- Does not register an adapter or strategy.
- Does not trigger alert, Council auto-call, or execution.

## 4. Formula coverage

The readiness helper computes:

- `spot_mid = (spot_bid + spot_ask) / 2`
- `perp_mid = (perp_bid + perp_ask) / 2`
- `mid_basis_pct = ((perp_mid - spot_mid) / spot_mid) * 100`
- `long_spot_short_perp_gross_pct = ((perp_bid - spot_ask) / spot_ask) * 100`
- `long_perp_short_spot_gross_pct = ((spot_bid - perp_ask) / perp_ask) * 100`
- `selected_gross_basis_pct = max(long_spot_short_perp_gross_pct, long_perp_short_spot_gross_pct, 0)`
- `estimated_net_basis_pct = selected_gross_basis_pct - fee_slippage_buffer_pct`

Direction labels:

- `analysis_only_long_spot_short_perp_basis`
- `analysis_only_long_perp_short_spot_basis`
- `analysis_only_no_positive_executable_basis`

## 5. Status policy coverage

Implemented first mocked readiness status policy:

- `NEED_DATA`
  - Required executable bid/ask or qty fields are missing.
  - Parser `required_missing_fields` are present.
  - Parser status is not `OK`.
  - Quote / settlement / margin comparability is unresolved.
  - Fee/slippage buffer is invalid.
- `REJECT`
  - Required executable fields are present and parser data is usable, but no positive gross executable basis exists.
  - Or positive gross basis exists but `estimated_net_basis_pct <= 0` after buffer.
  - `REJECT` is not adapter failure.
- `WATCH`
  - Positive selected gross basis exists.
  - `estimated_net_basis_pct > 0` after buffer.
  - Required fields are present.
  - Comparability, freshness, and liquidity checks pass.
  - `WATCH` remains analysis-only and `NO_TRADE_ONLY`.

Decision defaults:

- `REJECT -> recommended_default_decision="REJECT", readiness_pass=False`
- `NEED_DATA -> recommended_default_decision="NEED_DATA", readiness_pass=False`
- `WATCH -> recommended_default_decision="WATCH", readiness_pass=True`

`readiness_pass=True` is not execution permission.

## 6. Warning taxonomy coverage

Warnings implemented when applicable:

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

Assumptions also preserve `last price is weak context only if present` and `WATCH is not ENTER`.

## 7. Tests added

Added `tests/test_spot_futures_basis_mocked_readiness.py`.

The tests verify:

- Existing seven Binance mocked fixture JSON files are loaded through the existing parser helpers.
- Default fixture readiness returns `REJECT` or `WATCH` with no-trade assumptions and formula metrics.
- No-positive gross basis returns `REJECT` with `no_positive_gross_basis`.
- Positive gross but negative net returns `REJECT` with `non_positive_estimated_net_basis`.
- Positive net basis returns `WATCH`, `readiness_pass=True`, and `positive_net_basis_analysis_only` while preserving `NO_TRADE_ONLY`.
- Missing executable fields return `NEED_DATA` with `required_fields_missing`.
- Parser missing fields/status return `NEED_DATA` with parser warnings.
- Mark/index/funding context cannot substitute for executable bid/ask.
- Readiness output contains no forbidden private/account/execution keys.

## 8. Explicitly not implemented

This PR explicitly does not implement:

- OpportunityPacket creation.
- Adapter/live collect.
- Registry/config changes.
- Active strategy changes.
- `spot_futures_basis_v0` active promotion.
- Live endpoint calls.
- Generated JSON usage.
- Private API usage.
- Credentials/API keys/secrets/tokens usage.
- Account/balance/position lookup.
- Order/cancel.
- Withdrawal/deposit/transfer.
- Execution.
- Alerting.
- Council auto-call.
- Auto-trading.

## 9. No-trade compliance

This mocked readiness implementation PR preserves no-trade posture:

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
- Source runtime live behavior change: no
- Live endpoint call: no
- Adapter implementation: no
- OpportunityPacket creation: no
- Generated JSON usage: no
- `NO_TRADE_ONLY` preserved: yes

## 10. Generated JSON commit 금지 확인

Generated packet/sampling files remain smoke artifacts only and must not be committed:

- `data/market_samples/*.json`
- `data/generated_packets/*.json`

This PR:

- Does not commit `data/market_samples` changes.
- Does not commit `data/generated_packets` changes.
- Does not use generated JSON.
- Uses only existing deterministic mocked fixture files under `tests/fixtures/market_data/spot_futures_basis`.

## 11. Rollback plan

Rollback path:

1. Revert this mocked readiness implementation PR.
2. Remove `src/strategy/spot_futures_basis_readiness.py`.
3. Remove `tests/test_spot_futures_basis_mocked_readiness.py`.
4. Remove `docs/pr_handoffs/spot_futures_basis_first_mocked_readiness_implementation_2026_06_05.md`.
5. No parser/adapter/config/registry/runtime/generated-data rollback is required.

## 12. 다음 PR 후보

Recommended order:

1. Registry/config planning, no activation
2. User-local public-read-only collect smoke
3. 3-sample sampling evidence
4. 30-sample extended evidence
5. Strategy Evidence Dashboard / Journal Summary Planning
