# Depth / VWAP Mocked Fixture Files + Contract Tests v0

## 1. 작업 목적

이 문서는 Depth/VWAP pure helper 이후 realistic mocked fixture files and contract tests를 추가한 bounded implementation sprint를 기록한다.

Purpose:

- Binance / Bybit / OKX 스타일 public orderbook depth response shape에 가까운 deterministic mocked fixture JSON을 추가했다.
- Existing `src/market_data/depth_vwap.py` pure helper가 fixture에서 추출한 levels와 호환되는지 contract tests로 검증했다.
- 아직 strategy integration은 없다.
- Adapter, parser, readiness, packet builder, sampling, dashboard, config/registry에는 연결하지 않는다.
- `NO_TRADE_ONLY`를 유지한다.
- Active strategy는 `cross_exchange_spot_spread_v1`로 유지한다.

This PR does not implement adapter integration, parser integration, readiness behavior changes, packet builder changes, sampling changes, live endpoint calls, alerts, Council auto-call, or execution.

## 2. 변경 파일

Changed files:

- `tests/fixtures/market_data/depth_vwap/binance_spot_depth_btcusdt.json`
- `tests/fixtures/market_data/depth_vwap/binance_usdm_depth_btcusdt.json`
- `tests/fixtures/market_data/depth_vwap/bybit_spot_orderbook_btcusdt.json`
- `tests/fixtures/market_data/depth_vwap/bybit_linear_orderbook_btcusdt.json`
- `tests/fixtures/market_data/depth_vwap/okx_swap_books_btc_usdt_swap.json`
- `tests/test_depth_vwap_mocked_fixtures.py`
- `docs/pr_handoffs/depth_vwap_mocked_fixture_files_2026_06_05.md`

`src/market_data/depth_vwap.py` was not modified in this PR.

## 3. Fixture summary

Fixture summary:

- Binance spot depth:
  - File: `tests/fixtures/market_data/depth_vwap/binance_spot_depth_btcusdt.json`
  - Shape: `lastUpdateId`, `bids`, `asks`, plus public metadata-like `symbol`, `marketType`, `source`.
  - Levels: Binance style `["price", "qty"]`, at least 5 bids and 5 asks.
- Binance USDⓈ-M depth:
  - File: `tests/fixtures/market_data/depth_vwap/binance_usdm_depth_btcusdt.json`
  - Shape: `lastUpdateId`, `E`, `T`, `bids`, `asks`, plus public metadata-like `symbol`, `marketType`, `source`.
  - Levels: `["price", "qty"]`, at least 5 bids and 5 asks.
- Bybit spot orderbook:
  - File: `tests/fixtures/market_data/depth_vwap/bybit_spot_orderbook_btcusdt.json`
  - Shape: `retCode`, `retMsg`, `result.s`, `result.b`, `result.a`, `result.ts`, `result.u`, `result.seq`, `retExtInfo`, `time`.
  - Category is intentionally absent from `result` because V5 orderbook response body may not echo category.
- Bybit linear orderbook:
  - File: `tests/fixtures/market_data/depth_vwap/bybit_linear_orderbook_btcusdt.json`
  - Shape: `retCode`, `retMsg`, `result.s`, `result.b`, `result.a`, `result.ts`, `result.u`, `result.seq`, `result.cts`, `retExtInfo`, `time`.
  - Category is intentionally absent from `result`.
- OKX swap books:
  - File: `tests/fixtures/market_data/depth_vwap/okx_swap_books_btc_usdt_swap.json`
  - Shape: `code`, `msg`, `data[0].asks`, `data[0].bids`, `data[0].ts`, `data[0].seqId`.
  - Levels use OKX-style `["price", "size", "liquidation_orders", "order_count"]` shape.
  - Public metadata-like contract context includes `instId`, `instType`, `ctVal`, `ctValCcy`, and `lotSz`.

## 4. Fixture design summary

Fixture design:

- Fixtures are deterministic mocked samples.
- Fixtures are hand-written/sanitized, not live generated JSON.
- Fixtures represent public orderbook shape only.
- Fixtures do not include private/account/order/execution fields.
- Fixtures do not include `generated_at`, `captured_at`, API keys, secrets, tokens, account state, balances, positions, order identifiers, cancel, withdrawal, deposit, transfer, or execution flags.
- Fixtures live only under `tests/fixtures/market_data/depth_vwap`.
- Fixtures are not copied from `data/market_samples` or `data/generated_packets`.

## 5. Helper compatibility summary

Compatibility summary:

- Binance spot and Binance USDⓈ-M levels are directly compatible with `calculate_vwap_for_size` because they use `[price, qty]` pairs.
- Bybit spot and Bybit linear `result.a` / `result.b` levels are directly compatible with `calculate_vwap_for_size` because they use `[price, qty]` pairs.
- OKX book levels contain four values, so fixture contract tests explicitly take the first two elements, price and size, before calling the helper.
- OKX contract unit conversion is not solved in this PR.
- OKX `ctVal`, `ctValCcy`, and `lotSz` are recorded only as public metadata-like context for future unit-conversion planning.
- VWAP output remains analysis-only.
- Helper compatibility does not imply trading signal, execution permission, fill feasibility, or account-specific feasibility.

## 6. Tests added

Added `tests/test_depth_vwap_mocked_fixtures.py` with contract tests covering:

- Fixture file existence and JSON parsing.
- Fixture path constrained to `tests/fixtures/market_data/depth_vwap`.
- Fixture paths not under `data/generated_packets` or `data/market_samples`.
- Recursive forbidden field scan for private/account/order identifier/execution-related fields.
- Binance spot shape and helper compatibility.
- Binance USDⓈ-M shape and helper compatibility.
- Bybit spot shape, missing category acceptance, and helper compatibility.
- Bybit linear shape, missing category acceptance, `cts`, and helper compatibility.
- OKX swap shape and first-two-elements helper compatibility.
- OKX contract unit caveat: contract conversion is not claimed or solved.
- Cross-fixture ask VWAP consuming multiple levels.
- Cross-fixture bid VWAP consuming multiple levels.
- Cross-fixture insufficient depth with large target size.
- No adapter/parser/readiness/packet_builder/sampling imports in the fixture contract tests.
- No generated JSON files created by fixture tests.
- VWAP result does not assert execution permission or trading signal.

Existing `tests/test_depth_vwap.py` continues to cover pure helper behavior and remains unchanged.

## 7. No integration guardrails

No integration guardrails:

- Tests import only standard library modules and `src.market_data.depth_vwap`.
- Tests do not import adapters.
- Tests do not import parsers.
- Tests do not import readiness modules.
- Tests do not import packet builder.
- Tests do not import sampling.
- Tests do not call network.
- Tests do not create generated JSON files.
- Tests do not assert trading signal or execution permission.

## 8. Explicitly not integrated

Explicitly not integrated in this PR:

- Adapter 연결 없음.
- Parser 연결 없음.
- Readiness behavior 변경 없음.
- Packet builder 변경 없음.
- Sampling 변경 없음.
- Dashboard 변경 없음.
- Config/registry 변경 없음.
- Live endpoint 호출 없음.
- Strategy-specific integration 없음.
- Council runtime integration 없음.
- Alert integration 없음.
- Execution integration 없음.

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
- Fixtures are deterministic mocked files, not generated live JSON.
- Tests do not create generated JSON.
- 이번 PR에는 generated JSON을 추가하지 않음.

## 11. Rollback plan

Rollback plan:

1. Revert this PR.
2. Remove the five fixture JSON files under `tests/fixtures/market_data/depth_vwap`.
3. Remove `tests/test_depth_vwap_mocked_fixtures.py`.
4. Remove `docs/pr_handoffs/depth_vwap_mocked_fixture_files_2026_06_05.md`.
5. No config/runtime/generated-data rollback is needed.
6. Re-run required validation commands if rollback evidence is requested.

## 12. Next PR candidates

다음 PR 후보:

1. Add VWAP diagnostics/context fields to packet/candidate extensions, behavior unchanged.
2. Sampling summary context support, behavior unchanged.
3. Dashboard depth/VWAP policy status update.
4. Next Experimental Strategy Selection v0.
