# Spot-Futures Basis First Mocked Fixture Files and Contract Tests v0

## 1. 작업 목적

이 문서는 `spot_futures_basis_v0`의 첫 Binance Spot `BTCUSDT` + Binance USDⓈ-M Futures `BTCUSDT` Perp mocked fixture files와 fixture contract tests를 추가한 handoff다.

Purpose:

- Binance Spot / Binance USDⓈ-M Futures source response shape 후보를 deterministic mocked fixture로 고정한다.
- Future parser/readiness implementation 전에 fixture source contract와 no-private/no-generated guardrail을 unit tests로 확인한다.
- 이번 PR은 live data collection이 아니다.
- 이번 PR은 generated JSON을 fixture로 commit하지 않는다.
- 이번 PR은 parser/readiness/adapter/config/registry/runtime 구현을 하지 않는다.
- `NO_TRADE_ONLY`를 유지한다.

## 2. 변경 파일

Fixture files:

- `tests/fixtures/market_data/spot_futures_basis/binance_spot_book_ticker_btcusdt.json`
- `tests/fixtures/market_data/spot_futures_basis/binance_spot_depth_btcusdt.json`
- `tests/fixtures/market_data/spot_futures_basis/binance_spot_exchange_info_btcusdt.json`
- `tests/fixtures/market_data/spot_futures_basis/binance_futures_book_ticker_btcusdt.json`
- `tests/fixtures/market_data/spot_futures_basis/binance_futures_depth_btcusdt.json`
- `tests/fixtures/market_data/spot_futures_basis/binance_futures_premium_index_btcusdt.json`
- `tests/fixtures/market_data/spot_futures_basis/binance_futures_exchange_info_btcusdt.json`

Test file:

- `tests/test_spot_futures_basis_mocked_fixtures.py`

Handoff:

- `docs/pr_handoffs/spot_futures_basis_first_mocked_fixture_files_2026_06_05.md`

## 3. Fixture files added

Added seven deterministic mocked Binance fixture files:

1. `binance_spot_book_ticker_btcusdt.json`
   - `symbol`, `bidPrice`, `bidQty`, `askPrice`, `askQty`
2. `binance_spot_depth_btcusdt.json`
   - `lastUpdateId`, `bids`, `asks`
   - At least two bid and ask levels
3. `binance_spot_exchange_info_btcusdt.json`
   - `symbols`, `symbol`, `status`, `baseAsset`, `quoteAsset`, `filters`
   - Mocked `PRICE_FILTER`, `LOT_SIZE`, `MIN_NOTIONAL`
4. `binance_futures_book_ticker_btcusdt.json`
   - `symbol`, `bidPrice`, `bidQty`, `askPrice`, `askQty`, `time`
5. `binance_futures_depth_btcusdt.json`
   - `lastUpdateId`, `E`, `T`, `bids`, `asks`
   - At least two bid and ask levels
6. `binance_futures_premium_index_btcusdt.json`
   - `symbol`, `markPrice`, `indexPrice`, `lastFundingRate`, `interestRate`, `nextFundingTime`, `time`
7. `binance_futures_exchange_info_btcusdt.json`
   - `symbols`, `symbol`, `status`, `baseAsset`, `quoteAsset`, `marginAsset`, `contractType`, `filters`
   - Mocked `PRICE_FILTER`, `LOT_SIZE`, `MIN_NOTIONAL`

## 4. Fixture design summary

The fixtures are deterministic hand-written mocked samples:

- They use synthetic numeric strings.
- They are internally coherent enough for future parser tests.
- Spot and futures symbols are both `BTCUSDT`, while future parser/readiness work must still treat spot/perp product semantics separately.
- Spot depth and futures depth include two bid levels and two ask levels.
- Futures premium index includes mark/index/funding context only; these fields are not executable prices.
- Mock timestamps are deterministic fixture values and do not imply live capture.
- No `generated_at` field is included.

## 5. Contract coverage

The fixture set covers the first mocked source contract surface for `spot_futures_basis_v0`:

- Spot top-of-book context: spot book ticker fixture
- Spot depth / future VWAP context: spot depth fixture
- Spot metadata/rules context: spot exchange info fixture
- Perp top-of-book context: futures book ticker fixture
- Perp depth / future VWAP context: futures depth fixture
- Mark/index/funding context: futures premium index fixture
- Perp metadata/rules context: futures exchange info fixture

The tests verify fixture shape only. They do not parse these fixtures into production normalized observations yet.

## 6. No-private / no-generated guardrails

Guardrails preserved:

- No live endpoint call.
- No generated live JSON fixture commit.
- No `data/market_samples/*.json` copy.
- No `data/generated_packets/*.json` copy.
- No API keys, secrets, tokens, balances, positions, account IDs, order IDs, trade IDs, order/cancel fields, withdrawal/deposit/transfer fields, or private-key fields in fixtures.
- Fixture paths are under `tests/fixtures/market_data/spot_futures_basis` only.

## 7. Unit test summary

Added `tests/test_spot_futures_basis_mocked_fixtures.py`.

The tests verify:

- All seven fixture files exist and parse as JSON.
- Required top-level fields exist for each fixture.
- Spot and futures symbols are `BTCUSDT`.
- Depth fixtures contain at least two bid and ask levels.
- Spot and futures exchangeInfo fixtures contain `symbols` arrays and mocked filters.
- Futures premiumIndex contains `markPrice`, `indexPrice`, `lastFundingRate`, and `nextFundingTime`.
- No forbidden private/account/execution key substrings appear anywhere in fixture keys.
- Fixture paths are under `tests/fixtures/market_data/spot_futures_basis`, not `data/market_samples` or `data/generated_packets`.
- The tests do not import or call production parsers.

## 8. Explicitly not implemented

This PR explicitly does not implement:

- Parser implementation.
- Readiness implementation.
- Adapter implementation.
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

This mocked fixture / unit-test PR preserves no-trade posture:

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
- Parser/readiness/adapter implementation: no
- Generated JSON usage: no
- `NO_TRADE_ONLY` preserved: yes

## 10. Generated JSON commit 금지 확인

Generated packet/sampling files remain smoke artifacts only and must not be committed:

- `data/market_samples/*.json`
- `data/generated_packets/*.json`

This PR:

- Does not commit `data/market_samples` changes.
- Does not commit `data/generated_packets` changes.
- Does not use live generated JSON as fixture.
- Adds only deterministic mocked fixture JSON under `tests/fixtures/market_data/spot_futures_basis`.

## 11. Rollback plan

Rollback path:

1. Revert this mocked fixture / unit-test PR.
2. Remove the seven fixture JSON files under `tests/fixtures/market_data/spot_futures_basis`.
3. Remove `tests/test_spot_futures_basis_mocked_fixtures.py`.
4. Remove `docs/pr_handoffs/spot_futures_basis_first_mocked_fixture_files_2026_06_05.md`.
5. No source/config/registry/runtime/parser/readiness/generated-data rollback is required.

## 12. 다음 PR 후보

Recommended order:

1. First mocked parser/readiness implementation, `NO_TRADE_ONLY`
2. Registry/config planning, no activation
3. User-local public-read-only collect smoke
4. 3-sample sampling evidence
5. 30-sample extended evidence
