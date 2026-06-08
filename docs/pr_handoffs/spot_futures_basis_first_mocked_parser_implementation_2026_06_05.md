# Spot-Futures Basis First Mocked Parser Implementation v0

## 1. 작업 목적

이 문서는 `spot_futures_basis_v0`의 첫 mocked parser implementation handoff다.

Purpose:

- Binance Spot `BTCUSDT` + Binance USDⓈ-M Futures `BTCUSDT` mocked fixture 7개를 입력으로 받아 common source contract planning에 맞는 normalized spot/perp observation 후보 dict를 생성한다.
- Parser-only helper를 추가하고 mocked/unit-test first로 검증한다.
- 이번 PR은 live endpoint 호출이 아니다.
- 이번 PR은 readiness status / `WATCH` / `REJECT` / `NEED_DATA` 판단 구현이 아니다.
- 이번 PR은 OpportunityPacket 생성, adapter/live collect, registry/config 변경, active promotion을 하지 않는다.
- `NO_TRADE_ONLY`를 유지한다.

## 2. 변경 파일

Changed files:

- `src/market_data/parsers/spot_futures_basis.py`
- `tests/test_spot_futures_basis_mocked_parser.py`
- `docs/pr_handoffs/spot_futures_basis_first_mocked_parser_implementation_2026_06_05.md`

Unchanged by design:

- Existing fixture JSON files
- `src/market_data/adapters/`
- `src/strategy/`
- `config/`
- `data/market_samples/`
- `data/generated_packets/`

## 3. Parser implementation summary

Added `src/market_data/parsers/spot_futures_basis.py` with three public helpers:

1. `parse_binance_spot_observation(...)`
   - Accepts mocked/already-fetched Binance Spot book ticker, depth, and exchangeInfo payload dictionaries.
   - Returns a normalized spot observation dict.

2. `parse_binance_perp_observation(...)`
   - Accepts mocked/already-fetched Binance USDⓈ-M Futures book ticker, depth, premiumIndex, and exchangeInfo payload dictionaries.
   - Returns a normalized perp observation dict.

3. `build_spot_futures_basis_source_bundle(...)`
   - Bundles normalized spot/perp observations into a no-trade, analysis-only source bundle.
   - Does not create an OpportunityPacket.
   - Does not emit readiness status or recommended default decision.

Implementation guardrails:

- No `requests` import.
- No network I/O.
- No fixture file reads inside the parser.
- No `data/market_samples` or `data/generated_packets` access.
- No private/account/order fields.
- No adapter or registry wiring.
- No readiness decision implementation.

## 4. Normalized spot observation coverage

`parse_binance_spot_observation` returns the following planning contract fields:

- `venue_id="binance"`
- `venue_name="Binance Spot"`
- `market_type="spot"`
- `symbol="BTCUSDT"`
- `base_asset="BTC"`
- `quote_asset="USDT"`
- `best_bid`
- `best_bid_qty`
- `best_ask`
- `best_ask_qty`
- `bid_qty_unit="base_asset"`
- `ask_qty_unit="base_asset"`
- `book_update_id`
- `depth_bids`
- `depth_asks`
- `tick_size`
- `step_size`
- `min_notional`
- `raw_endpoint_ids`
- `data_age_ms`
- `latency_ms`
- `parser_normalized_status`
- `required_missing_fields`
- `parser_warnings`

For the current deterministic fixtures, parser status is `OK` and `required_missing_fields=[]`.

## 5. Normalized perp observation coverage

`parse_binance_perp_observation` returns the following planning contract fields:

- `venue_id="binance"`
- `venue_name="Binance USDⓈ-M Futures"`
- `market_type="perp"`
- `symbol="BTCUSDT"`
- `base_asset="BTC"`
- `quote_asset="USDT"`
- `settlement_asset="USDT"`
- `margin_asset="USDT"`
- `contract_type="PERPETUAL"`
- `best_bid`
- `best_bid_qty`
- `best_ask`
- `best_ask_qty`
- `bid_qty_unit="base_asset"`
- `ask_qty_unit="base_asset"`
- `book_timestamp`
- `depth_bids`
- `depth_asks`
- `mark_price`
- `index_price`
- `funding_rate`
- `interest_rate`
- `next_funding_time`
- `tick_size`
- `step_size`
- `min_notional`
- `raw_endpoint_ids`
- `data_age_ms`
- `latency_ms`
- `parser_normalized_status`
- `required_missing_fields`
- `parser_warnings`

For the current deterministic fixtures, parser status is `OK` and `required_missing_fields=[]`.

## 6. Source bundle summary

`build_spot_futures_basis_source_bundle` returns:

- `strategy_family="spot_futures_basis"`
- `strategy_id="spot_futures_basis_v0"`
- `status="experimental_non_active_no_trade_only"`
- `spot_observation`
- `perp_observation`
- `source_venue_id="binance"`
- `comparison_type="same_exchange_spot_perp_basis"`
- `assumptions`
- `no_trade_only=true`
- `execution_policy="NO_TRADE_ONLY"`

Assumptions include:

- public no-key endpoints only
- analysis-only parser output
- no private API
- no trading behavior
- mark price is not executable
- last price is weak context only if present

## 7. Tests added

Added `tests/test_spot_futures_basis_mocked_parser.py`.

The tests verify:

- The seven existing mocked fixture JSON files load from `tests/fixtures/market_data/spot_futures_basis`.
- `parse_binance_spot_observation` returns expected spot normalized fields.
- `parse_binance_perp_observation` returns expected perp normalized fields.
- `build_spot_futures_basis_source_bundle` returns no-trade source bundle fields and assumptions.
- Parser outputs do not include `readiness_status` or `recommended_default_decision`.
- Parser outputs do not include OpportunityPacket `schema_version`.
- Parser outputs do not include private/account/order/cancel/withdraw/deposit/transfer keys.
- Invalid zero best bid is reported via `required_missing_fields` and `parser_warnings` without adding readiness decisions.

## 8. Explicitly not implemented

This PR explicitly does not implement:

- Readiness helper.
- `WATCH` / `REJECT` / `NEED_DATA` readiness judgment.
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

This mocked parser implementation PR preserves no-trade posture:

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
- Readiness implementation: no
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

1. Revert this mocked parser implementation PR.
2. Remove `src/market_data/parsers/spot_futures_basis.py`.
3. Remove `tests/test_spot_futures_basis_mocked_parser.py`.
4. Remove `docs/pr_handoffs/spot_futures_basis_first_mocked_parser_implementation_2026_06_05.md`.
5. No adapter/config/registry/runtime/readiness/generated-data rollback is required.

## 12. 다음 PR 후보

Recommended order:

1. Readiness helper planning-to-implementation bridge, mocked/unit-test only
2. First mocked readiness implementation, `NO_TRADE_ONLY`
3. Registry/config planning, no activation
4. User-local public-read-only collect smoke
5. 3-sample sampling evidence
