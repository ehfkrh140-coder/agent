# Spot-Futures Basis Pure OpportunityPacket Builder Implementation v0

## 1. 작업 목적

이 PR은 `spot_futures_basis_v0`의 parser `source_bundle`과 readiness result를 입력으로 받아 `opportunity_packet_v0` compatible dict를 반환하는 standalone pure packet builder를 추가한다.

Purpose:

- Mapping planning 이후 첫 pure OpportunityPacket builder를 구현한다.
- Existing parser/readiness output을 packet observations, candidates, extensions, detector metadata로 연결한다.
- Mocked/unit-test only로 검증한다.
- Live adapter, registry/config, collect path, runtime live behavior는 연결하지 않는다.
- `NO_TRADE_ONLY`를 유지한다.

## 2. 변경 파일

Changed files:

- `src/market_data/spot_futures_basis_packet_builder.py`
- `tests/test_spot_futures_basis_packet_builder.py`
- `docs/pr_handoffs/spot_futures_basis_pure_opportunity_packet_builder_2026_06_05.md`

Not changed:

- Existing fixture JSON files
- `src/market_data/adapters/`
- `config/` or registry files
- `data/market_samples/`
- `data/generated_packets/`

## 3. Packet builder implementation summary

Added `build_spot_futures_basis_opportunity_packet(source_bundle, readiness_result, *, created_at_utc, packet_id=None)` in `src/market_data/spot_futures_basis_packet_builder.py`.

Builder behavior:

- Accepts dict inputs only.
- Returns a dict only.
- Emits top-level `schema_version="opportunity_packet_v0"`.
- Emits deterministic `packet_id` when not supplied, using `source_venue_id`, `strategy_id`, and `created_at_utc`.
- Emits `asset="BTC"`, `quote="USDT"`, `signal_type="spot_futures_basis"`, `strategy_family="spot_futures_basis"`, and `strategy_id="spot_futures_basis_v0"`.
- Emits exactly two observations: spot and perp.
- Emits exactly one analysis-only candidate.
- Emits detector metadata for parser/readiness/builder source files.
- Emits top-level extensions with `no_trade_only=True`, `execution_policy="NO_TRADE_ONLY"`, `status="experimental_non_active_no_trade_only"`, assumptions, readiness summary, and parser source-bundle summary.

Purity guardrails:

- No `requests` import.
- No network call.
- No file read/write.
- No `data/market_samples` reference.
- No `data/generated_packets` reference.
- No adapter registration.
- No strategy registry/config change.
- No alert, Council auto-call, or execution behavior.

## 4. Observation mapping coverage

Spot observation mapping covers:

- `observation_id="binance_spot_btcusdt_spot_futures_basis"`
- `venue_id="binance"`
- `venue_name="Binance Spot"`
- `market_symbol="BTCUSDT"`
- `instrument_type="spot"`
- `region="GLOBAL"`
- bid/ask/bid_size/ask_size from parser best bid/ask fields
- tick/step from parser metadata
- liquidity orderbook-depth availability from parser depth arrays
- data quality latency/data-age fields
- health API status flags
- extensions for market type, base/quote asset, qty units, parser status, required missing fields, raw endpoint ids, book update id, and min notional

Perp observation mapping covers:

- `observation_id="binance_usdm_btcusdt_perp_spot_futures_basis"`
- `venue_id="binance"`
- `venue_name="Binance USDⓈ-M Futures"`
- `market_symbol="BTCUSDT"`
- `instrument_type="linear_perpetual"`
- `region="GLOBAL"`
- bid/ask/bid_size/ask_size from parser best bid/ask fields
- mark/index/funding context under observation and derivatives fields
- tick/step from parser metadata
- timestamp/data quality fields
- health API status flags
- extensions for market type, base/quote/settlement/margin asset, contract type, qty units, parser status, required missing fields, raw endpoint ids, book timestamp, interest rate, and min notional

Observation no-trade interpretation:

- Mark price, index price, and funding rate are context, not executable basis.
- Spot/perp shared `BTCUSDT` symbol string does not imply identical product semantics.

## 5. Candidate mapping coverage

Candidate mapping covers:

- `candidate_id="binance_btcusdt_spot_futures_basis_candidate"`
- `candidate_type="spot_futures_basis_observation"`
- `strategy_family="spot_futures_basis"`
- `strategy_id="spot_futures_basis_v0"`
- Spot observation id as source observation.
- Perp observation id as target observation.
- `source_venue_id="binance"`
- `target_venue_id="binance"`
- Direction from readiness metrics `selected_direction`.
- `gross_gap_pct` from readiness metrics `selected_gross_basis_pct`.
- `estimated_net_gap_pct` from readiness metrics `estimated_net_basis_pct`.
- Liquidity/freshness pass-through from readiness metrics.
- `guard_pass` only when no-trade guardrails remain intact.
- Required missing fields from readiness result.
- Assumptions merged from source bundle, readiness result, and packet-specific assumptions.
- Warnings in candidate extensions.
- Candidate extensions preserve `no_trade_only=True` and `execution_policy="NO_TRADE_ONLY"`.

Candidate no-trade interpretation:

- Candidate output is analysis-only.
- `readiness_pass=True` is not execution permission.
- `WATCH` is not `ENTER`.

## 6. Metrics / readiness mapping coverage

Candidate metrics include:

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

Readiness/default decision mapping:

- `REJECT` remains `recommended_default_decision="REJECT"`, `readiness_pass=False`.
- `NEED_DATA` remains `recommended_default_decision="NEED_DATA"`, `readiness_pass=False`.
- `WATCH` remains `recommended_default_decision="WATCH"`, `readiness_pass=True`.

No-trade qualifier:

- `WATCH` remains analysis-only and does not trigger Council auto-call, alert, or execution.

## 7. Assumptions / warnings / detector metadata coverage

Packet and candidate assumptions include:

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

Warnings coverage:

- Readiness warnings pass through to candidate `extensions.warnings`.
- Parser missing fields and readiness missing fields remain visible through observation extensions and candidate required-missing-fields.

Detector metadata includes:

- `detector_name="spot_futures_basis_packet_builder"`
- `detector_version="v0"`
- `generated_from="mocked_binance_spot_and_usdm_futures_source_bundle"`
- Parser source file path
- Readiness source file path
- Builder source file path

## 8. Tests added

Added `tests/test_spot_futures_basis_packet_builder.py`.

Coverage:

- Builds packet from deterministic mocked Binance fixtures through existing parser and readiness helpers.
- Verifies top-level packet fields and deterministic packet id behavior.
- Verifies spot/perp observation mapping.
- Verifies candidate mapping and metrics pass-through.
- Verifies `WATCH` remains no-trade and analysis-only.
- Verifies `NEED_DATA` packet propagation.
- Recursively checks for forbidden private/account/order/cancel/withdraw/deposit/transfer key substrings, while allowing the schema-required `orderbook_depth_available` field.
- Structurally verifies no `requests`, no generated data path references, and no file-open/path construction in the builder module.

## 9. Explicitly not implemented

This PR explicitly does not implement:

- Adapter/live collect
- Registry/config changes
- Active strategy changes
- Live endpoint calls
- Generated JSON file creation
- Private API
- Account/balance/position/order/cancel/withdraw/deposit/transfer handling
- Execution
- Alert
- Council auto-call
- Auto-trading
- Runtime live behavior changes

## 10. No-trade compliance

No-trade compliance for this PR:

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
- Generated JSON file creation: no
- `NO_TRADE_ONLY` preserved: yes

## 11. Generated JSON commit 금지 확인

Generated packet/sampling files remain smoke artifacts only and must not be committed:

- `data/market_samples/*.json`
- `data/generated_packets/*.json`

This PR:

- Does not add generated JSON.
- Does not change `data/market_samples`.
- Does not change `data/generated_packets`.
- Builder returns a dict only and writes no files.

## 12. Rollback plan

Rollback path:

1. Revert this packet-builder PR.
2. Remove `src/market_data/spot_futures_basis_packet_builder.py`.
3. Remove `tests/test_spot_futures_basis_packet_builder.py`.
4. Remove `docs/pr_handoffs/spot_futures_basis_pure_opportunity_packet_builder_2026_06_05.md`.
5. No adapter/config/registry/runtime/generated-data rollback is required.

## 13. 다음 PR 후보

Recommended order:

1. First public-read-only adapter implementation, mocked/unit tests only
2. Registry/config planning, no activation
3. User-local public-read-only collect smoke
4. 3-sample sampling evidence
5. 30-sample extended evidence
