# Spot-Futures Basis Bybit Parser / Source Mapping Implementation with Mocked Unit Tests v0

## 1. 작업 목적

이 문서는 `spot_futures_basis_v0`의 Bybit Spot BTCUSDT + Bybit USDT linear perpetual BTCUSDT mocked fixture payload dict를 common normalized source contract에 맞는 normalized observation dict로 변환하는 pure parser/source mapping 구현 결과를 기록한다.

목적:

- Bybit deterministic mocked fixture payload를 normalized `SpotObservation` / `PerpObservation` 후보 dict로 변환한다.
- Bybit-specific response/category/metadata 차이를 parser/source boundary에 가둔다.
- Binance-only strategy가 되지 않도록 Bybit를 common source contract에 맞춘다.
- Parser/source mapping은 pure dict parser이며 live endpoint 호출, file read/write behavior, adapter/config/registry/runtime behavior를 추가하지 않는다.
- `NO_TRADE_ONLY`를 유지한다.

## 2. 변경 파일

| File | Change |
| --- | --- |
| `src/market_data/parsers/spot_futures_basis.py` | Added pure Bybit spot/perp parser helpers and venue-neutral source bundle venue derivation while preserving Binance behavior. |
| `tests/test_spot_futures_basis_bybit_mocked_parser.py` | Added mocked/unit tests for Bybit fixture parsing, missing-field behavior, context-only market fields, no-trade bundle metadata, no-private guardrails, and no file/network parser behavior. |
| `docs/pr_handoffs/spot_futures_basis_bybit_parser_source_mapping_2026_06_05.md` | Added this handoff evidence document. |

## 3. Bybit parser/source mapping summary

Implemented pure parser helpers:

- `parse_bybit_spot_observation(...)`
- `parse_bybit_perp_observation(...)`

Parser behavior:

- Accepts already-loaded public mocked fixture dictionaries.
- Does not import `requests`.
- Does not read files.
- Does not write files.
- Does not call network endpoints.
- Does not handle private API, credentials, account, balance, position, order, cancel, withdraw, deposit, transfer, execution, alert, Council auto-call, or auto-trading behavior.
- Records missing/invalid source fields in `required_missing_fields` and `parser_warnings`.
- Sets `parser_normalized_status=OK` when `required_missing_fields` is empty.
- Sets `parser_normalized_status=NEED_DATA` when required fields are missing.
- Preserves Bybit `retCode`, `retMsg`, and `time` envelope context in source-envelope metadata.
- Preserves `category=spot` vs `category=linear` as product semantics.
- Keeps `lastPrice` as weak context only.
- Keeps `markPrice`, `indexPrice`, and `fundingRate` as context only.
- Uses orderbook top-of-book as preferred executable top-of-book source, with ticker bid/ask fallback when orderbook levels are unavailable.
- Uses Bybit orderbook `ts` as the primary timestamp candidate for `data_age_ms` when `created_at_utc` is provided.
- Does not clamp negative `data_age_ms`.

## 4. SpotObservation mapping coverage

Bybit Spot parser maps:

| Normalized field | Mapping |
| --- | --- |
| `venue_id` | `bybit` |
| `venue_name` | `Bybit Spot` |
| `market_type` | `spot` |
| `category` | `spot` |
| `symbol` | Bybit orderbook `result.s`, ticker symbol, or instruments symbol |
| `base_asset` | Spot instruments `baseCoin` |
| `quote_asset` | Spot instruments `quoteCoin` |
| `best_bid` / `best_ask` | Preferred from orderbook top level; ticker bid/ask fallback if orderbook unavailable |
| `best_bid_qty` / `best_ask_qty` | Preferred from orderbook top level; ticker size fallback if orderbook unavailable |
| `bid_qty_unit` / `ask_qty_unit` | `base_asset` |
| `depth_bids` / `depth_asks` | Bybit orderbook `b` / `a` levels |
| `last_price` | Ticker `lastPrice`, weak context only |
| `last_price_role` | `weak_context_only_not_executable` |
| `tick_size` | Spot instruments `priceFilter.tickSize` |
| `step_size` | Spot instruments `lotSizeFilter.basePrecision` or equivalent candidate |
| `min_order_size` | Spot instruments `lotSizeFilter.minOrderQty` |
| `min_notional` | Spot instruments `lotSizeFilter.minOrderAmt` or equivalent candidate |
| `raw_endpoint_ids` | Bybit spot ticker/orderbook/instruments endpoint ids |
| `data_age_ms` | Computed from orderbook `ts` and `created_at_utc` when available; negative values preserved |
| `latency_ms` | Caller-provided mocked latency value |
| `parser_normalized_status` | `OK` or `NEED_DATA` based on missing required fields |
| `required_missing_fields` | Stable `spot_*` missing names, including `spot_min_notional_missing` |
| `parser_warnings` | Last-price weak context, product semantics, category/timestamp/metadata warnings |

Spot missing-field behavior:

- Missing executable bid/ask from both orderbook and ticker yields `NEED_DATA` with `spot_bid_missing` and `spot_ask_missing`.
- Missing `minOrderAmt` / min-notional equivalent yields `NEED_DATA` with `spot_min_notional_missing`.
- `lastPrice` is never used as executable bid/ask.

## 5. PerpObservation mapping coverage

Bybit linear perp parser maps:

| Normalized field | Mapping |
| --- | --- |
| `venue_id` | `bybit` |
| `venue_name` | `Bybit Derivatives V5` |
| `market_type` | `perp` |
| `category` | `linear` |
| `symbol` | Bybit orderbook `result.s`, ticker symbol, or instruments symbol |
| `base_asset` | Linear instruments `baseCoin` |
| `quote_asset` | Linear instruments `quoteCoin` |
| `settlement_asset` | Linear instruments `settleCoin` |
| `margin_asset` | Linear instruments `settleCoin` for this mocked USDT linear fixture |
| `contract_type` | Linear instruments `contractType` |
| `best_bid` / `best_ask` | Preferred from orderbook top level; ticker bid/ask fallback if orderbook unavailable |
| `best_bid_qty` / `best_ask_qty` | Preferred from orderbook top level; ticker size fallback if orderbook unavailable |
| `bid_qty_unit` / `ask_qty_unit` | `base_or_contract_quantity` |
| `depth_bids` / `depth_asks` | Bybit linear orderbook `b` / `a` levels |
| `last_price` | Ticker `lastPrice`, weak context only |
| `mark_price` | Ticker `markPrice`, context only |
| `index_price` | Ticker `indexPrice`, context only |
| `funding_rate` | Ticker `fundingRate`, context only |
| `next_funding_time` | Ticker `nextFundingTime` |
| `funding_interval` | Instruments `fundingInterval` |
| `tick_size` | Linear instruments `priceFilter.tickSize` |
| `step_size` | Linear instruments `lotSizeFilter.qtyStep` |
| `min_order_size` | Linear instruments `lotSizeFilter.minOrderQty` |
| `min_notional` | Linear instruments `lotSizeFilter.minNotionalValue` |
| `raw_endpoint_ids` | Bybit linear ticker/orderbook/instruments endpoint ids |
| `data_age_ms` | Computed from orderbook `ts` and `created_at_utc` when available; negative values preserved |
| `latency_ms` | Caller-provided mocked latency value |
| `parser_normalized_status` | `OK` or `NEED_DATA` based on missing required fields |
| `required_missing_fields` | Stable `perp_*` missing names for executable source and metadata gaps |
| `parser_warnings` | Mark/index/funding context-only, funding interval, last-price weak context, product semantics warnings |

Perp missing-field behavior:

- Missing executable bid/ask from both orderbook and ticker yields `NEED_DATA` with `perp_bid_missing` and `perp_ask_missing`.
- `markPrice`, `indexPrice`, and `fundingRate` remain context-only and do not replace executable bid/ask.
- `fundingInterval=480` is preserved via `funding_interval=480` parser warning candidate.

## 6. Source bundle / no-trade metadata coverage

`build_spot_futures_basis_source_bundle(...)` remains the common bundle helper and now derives `source_venue_id` from matching spot/perp observation `venue_id` values.

Bybit source bundle tests verify:

- `strategy_family=spot_futures_basis`.
- `strategy_id=spot_futures_basis_v0`.
- `source_venue_id=bybit`.
- `comparison_type=same_exchange_spot_perp_basis`.
- `no_trade_only=True`.
- `execution_policy=NO_TRADE_ONLY`.
- Assumptions preserve public no-key endpoints only, analysis-only parser output, no private API, no trading behavior, and mark price is not executable.

## 7. Tests added

Added `tests/test_spot_futures_basis_bybit_mocked_parser.py`.

Test coverage:

- `test_parse_bybit_spot_observation_from_fixtures`
- `test_parse_bybit_perp_observation_from_fixtures`
- `test_bybit_spot_missing_bid_ask_reports_need_data`
- `test_bybit_spot_missing_min_notional_reports_need_data`
- `test_bybit_perp_mark_index_funding_do_not_replace_executable_bid_ask`
- `test_bybit_source_bundle_no_trade_metadata`
- `test_bybit_parser_output_has_no_private_or_execution_fields`
- `test_bybit_parser_module_no_file_or_network_behavior`

Existing Binance parser/readiness/packet/collect/sampling tests continue to pass.

## 8. Bybit-specific watch items

Watch items preserved for future parser/adapter work:

- `category=spot` vs `category=linear`.
- `retCode` / `retMsg` envelope.
- Nested `result.list`.
- `funding_interval=480`.
- Negative `data_age_ms` / timestamp clock-skew watch.
- Qty unit semantics.
- `minOrderQty` / `minNotionalValue` / `minOrderAmt` interpretation.
- Same `BTCUSDT` symbol but different product semantics.
- Top-of-book liquidity is not fill feasibility.
- Mark/index/funding context is not executable basis.

## 9. Explicitly not implemented

This PR explicitly does not implement:

- Readiness threshold 변경 없음.
- Packet builder 변경 없음.
- Adapter 구현 없음.
- Config/registry 변경 없음.
- Live endpoint 호출 없음.
- `collect_market_data` 실행 없음.
- `sample_market_data` 실행 없음.
- Generated JSON 생성 없음.
- Private API 없음.
- Credentials 없음.
- Account/balance/position/order/cancel/withdraw/deposit/transfer 없음.
- Execution 없음.
- Alert 없음.
- Council auto-call 없음.
- Auto-trading 없음.
- OKX implementation/research 없음.

## 10. OKX deferred scope note

Scope note:

- 이번 `spot_futures_basis_v0` cycle은 Binance + Bybit까지만 진행한다.
- OKX는 future expansion으로 defer한다.
- This is scope control, not permanent rejection.
- This PR creates no OKX file, no OKX fixture, no OKX parser, no OKX adapter, and no OKX config/registry entry.

## 11. No-trade compliance

No-trade compliance confirmation:

- Active strategy promotion 없음.
- `spot_futures_basis_v0` active 승격 없음.
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
- `NO_TRADE_ONLY` 유지.

## 12. Generated JSON commit 금지 확인

Generated JSON policy:

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- 이번 PR은 deterministic mocked fixture를 읽는 tests only이며 generated JSON을 추가하지 않음.
- Future Bybit smoke/sampling output은 evidence 요약 후 삭제해야 함.

## 13. Rollback plan

Rollback plan:

- Revert this PR and remove the Bybit parser/source mapping additions, Bybit parser mocked/unit test file, and this handoff document.
- Adapter/config/registry/readiness/packet-builder/runtime rollback is not needed because none were changed.
- Generated-data rollback is not needed because no generated packet/sampling JSON was added.

## 14. 다음 PR 후보

Recommended next PR candidates:

1. Bybit public-read-only adapter implementation, mocked/unit tests.
2. Bybit registry/config no activation.
3. Bybit user-local collect smoke.
4. Bybit collect smoke evidence docs-only.
5. Bybit 3-sample sampling evidence.
6. OKX public source research against common contract as future expansion.
