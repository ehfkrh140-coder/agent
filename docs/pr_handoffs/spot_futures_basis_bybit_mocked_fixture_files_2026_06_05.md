# Spot-Futures Basis Bybit Mocked Fixture Files + Fixture Contract Tests v0

## 1. 작업 목적

이 문서는 `spot_futures_basis_v0`의 Bybit Spot BTCUSDT + Bybit USDT linear perpetual BTCUSDT deterministic mocked fixture files와 fixture contract tests 추가 결과를 기록한다.

목적:

- Bybit public source research와 mocked fixture planning 이후, 향후 parser/source-mapping tests에 사용할 deterministic mocked fixture JSON을 추가한다.
- Bybit-specific endpoint/response 차이를 source adapter/parser boundary에 가둔다.
- Binance-only strategy가 되지 않도록 Bybit를 common normalized source contract에 맞춘다.
- 이번 PR은 fixture files + fixture contract tests PR이며 parser/readiness/packet builder/adapter/config/registry 구현이 아니다.
- Live endpoint 호출 없이 deterministic mocked fixtures만 추가한다.
- `NO_TRADE_ONLY`를 유지한다.

## 2. 변경 파일

| File | Purpose |
| --- | --- |
| `tests/fixtures/market_data/spot_futures_basis/bybit_spot_ticker_btcusdt.json` | Bybit V5 spot ticker/top-of-book deterministic mocked fixture |
| `tests/fixtures/market_data/spot_futures_basis/bybit_spot_orderbook_btcusdt.json` | Bybit V5 spot orderbook deterministic mocked fixture with two bid/ask levels |
| `tests/fixtures/market_data/spot_futures_basis/bybit_spot_instruments_info_btcusdt.json` | Bybit V5 spot instruments metadata deterministic mocked fixture |
| `tests/fixtures/market_data/spot_futures_basis/bybit_linear_ticker_btcusdt.json` | Bybit V5 linear ticker deterministic mocked fixture with top-of-book plus mark/index/funding context |
| `tests/fixtures/market_data/spot_futures_basis/bybit_linear_orderbook_btcusdt.json` | Bybit V5 linear orderbook deterministic mocked fixture with two bid/ask levels |
| `tests/fixtures/market_data/spot_futures_basis/bybit_linear_instruments_info_btcusdt.json` | Bybit V5 linear instruments metadata deterministic mocked fixture |
| `tests/test_spot_futures_basis_bybit_mocked_fixtures.py` | Fixture contract tests for Bybit deterministic mocked fixtures |
| `docs/pr_handoffs/spot_futures_basis_bybit_mocked_fixture_files_2026_06_05.md` | Handoff evidence for fixture files, contract coverage, guardrails, scope, rollback, and next steps |

## 3. Fixture files added

Added deterministic mocked fixture files:

- `bybit_spot_ticker_btcusdt.json`
- `bybit_spot_orderbook_btcusdt.json`
- `bybit_spot_instruments_info_btcusdt.json`
- `bybit_linear_ticker_btcusdt.json`
- `bybit_linear_orderbook_btcusdt.json`
- `bybit_linear_instruments_info_btcusdt.json`

Fixture file notes:

- The fixtures are deterministic mocked fixtures.
- The fixtures are not user-local generated JSON.
- The fixtures do not include `generated_at`, `captured_at`, or `live_endpoint_url` metadata.
- Optional funding history fixture was not added in this PR.
- Linear ticker fixture includes `fundingRate` and `nextFundingTime` context, so separate funding history is deferred until future parser planning requires it.

## 4. Fixture source-response design summary

All Bybit fixture files use the common V5 envelope:

- `retCode`
- `retMsg`
- `result`
- `retExtInfo`
- `time`

Envelope details:

- `retCode=0`.
- `retMsg=OK`.
- `time` is a deterministic mock timestamp.
- No live capture metadata is included.

Spot fixture design:

- Spot ticker preserves `result.category=spot`, `symbol=BTCUSDT`, `bid1Price`, `bid1Size`, `ask1Price`, `ask1Size`, and `lastPrice` as weak context only.
- Spot orderbook preserves `category=spot`, `s=BTCUSDT`, `b`, `a`, deterministic `ts`, `u`, and `seq`, with at least two bid/ask levels.
- Spot instruments-info preserves `category=spot`, `symbol=BTCUSDT`, `baseCoin=BTC`, `quoteCoin=USDT`, `status=Trading`, `priceFilter.tickSize`, `lotSizeFilter.basePrecision`, `quotePrecision`, `minOrderQty`, and `minOrderAmt`.

Linear fixture design:

- Linear ticker preserves `result.category=linear`, `symbol=BTCUSDT`, `bid1Price`, `bid1Size`, `ask1Price`, `ask1Size`, `lastPrice`, `markPrice`, `indexPrice`, `fundingRate`, `nextFundingTime`, and `openInterest` context.
- Linear orderbook preserves `category=linear`, `s=BTCUSDT`, `b`, `a`, deterministic `ts`, `u`, `seq`, and `cts`, with at least two bid/ask levels.
- Linear instruments-info preserves `category=linear`, `symbol=BTCUSDT`, `contractType=LinearPerpetual`, `status=Trading`, `baseCoin=BTC`, `quoteCoin=USDT`, `settleCoin=USDT`, `priceFilter.tickSize`, `lotSizeFilter.qtyStep`, `minOrderQty`, `minNotionalValue`, and `fundingInterval=480`.

Deterministic numeric design:

- Spot bid is lower than spot ask.
- Linear bid is lower than linear ask.
- Prices and quantities are positive.
- The default fixture prices produce positive gross basis for `long_spot_short_perp` but keep it below a realistic future fee/slippage buffer candidate, making the default set useful for a future positive-gross-but-negative-net parser/readiness case.
- The deterministic values are mocked and must not be represented as live captures.

## 5. Contract coverage

Fixture contract tests cover:

- All six Bybit fixture JSON files load successfully.
- Every fixture has the Bybit V5 top-level envelope.
- Every fixture has `retCode=0` and `retMsg=OK`.
- Fixture paths remain under `tests/fixtures/market_data/spot_futures_basis`.
- Fixture paths are not under `data/market_samples` or `data/generated_packets`.
- Spot fixtures preserve `category=spot` and `symbol=BTCUSDT`.
- Linear fixtures preserve `category=linear` and `symbol=BTCUSDT`.
- Spot and linear product semantics are separated even though both use `BTCUSDT`.
- Orderbook fixtures contain at least two bid and two ask levels.
- Ticker fixtures have coherent positive bid/ask prices and quantities.
- Linear ticker preserves `markPrice`, `indexPrice`, `fundingRate`, and `nextFundingTime` context.
- Linear instruments-info preserves `contractType=LinearPerpetual`, `priceFilter.tickSize`, `lotSizeFilter.qtyStep`, `minOrderQty`, `minNotionalValue`, and `fundingInterval`.
- Spot instruments-info preserves base/quote/status/tick/min-order/min-notional metadata candidates.
- Default fixture prices support a future positive-gross-but-negative-net formula case.

## 6. Product/category separation

Product/category separation is explicit:

- Spot fixtures use `category=spot`.
- Linear perp fixtures use `category=linear`.
- Both products use `symbol=BTCUSDT`, but the tests assert that the same symbol does not collapse product semantics.
- Spot instruments fixture does not include `contractType`.
- Linear instruments fixture includes `contractType=LinearPerpetual` and `settleCoin=USDT`.
- This separation is required so future parser/source mapping keeps Bybit-specific category semantics at the source boundary.

## 7. No-private / no-generated guardrails

Guardrails added in tests:

- Recursively scan fixture keys and string values for forbidden private/account/execution substrings:
  - `apiKey`
  - `secret`
  - `token`
  - `credential`
  - `account`
  - `balance`
  - `position`
  - `orderId`
  - `clientOrderId`
  - `cancel`
  - `withdraw`
  - `deposit`
  - `transfer`
  - `privateKey`
  - `execution_enabled`
  - `auto_trade`
  - `alert_enabled`
  - `council_auto_call`
- Public orderbook wording remains allowed because these are public market-data fixtures, not order placement semantics.
- Tests assert no `generated_at`, `captured_at`, or `live_endpoint_url` metadata.
- Tests assert no `data/market_samples` or `data/generated_packets` strings appear in fixture contents.
- Tests assert fixture paths are not generated artifact paths.

## 8. Tests added

Added `tests/test_spot_futures_basis_bybit_mocked_fixtures.py`.

Test coverage includes:

- Fixture existence and valid JSON parsing.
- Bybit V5 envelope validation.
- `retCode=0` / `retMsg=OK` validation.
- Fixture path scope validation.
- No-private/no-account/no-execution recursive content validation.
- No live capture metadata validation.
- No generated artifact path content validation.
- Spot category/symbol validation.
- Linear category/symbol validation.
- Spot/linear product semantics separation.
- Two-level orderbook shape validation.
- Coherent positive top-of-book numeric validation.
- Positive-gross-but-negative-net default price design validation.
- Linear context fields validation.
- Linear instruments metadata validation.
- Spot instruments metadata validation.

## 9. Explicitly not implemented

This PR explicitly does not implement:

- Parser 구현 없음.
- Readiness 변경 없음.
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

- 이번 `spot_futures_basis_v0` multi-venue cycle은 Binance + Bybit까지만 진행한다.
- OKX는 future expansion으로 defer한다.
- This is scope control, not a permanent rejection.
- This PR creates no OKX fixture, no OKX research document, no OKX parser, no OKX adapter, and no OKX config/registry entry.

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
- 이번 PR fixture들은 deterministic mocked fixtures이며 user-local generated JSON이 아님.
- Future Bybit smoke/sampling output은 evidence 요약 후 삭제해야 함.
- 이번 PR에는 generated JSON을 추가하지 않음.

## 13. Rollback plan

Rollback plan:

- Revert this PR and remove the six Bybit fixture JSON files, the Bybit fixture contract test file, and this handoff document.
- Parser/readiness/packet builder/adapter/config/registry/runtime rollback is not needed because none were changed.
- Generated-data rollback is not needed because no generated packet/sampling JSON was added.

## 14. 다음 PR 후보

Recommended next PR candidates:

1. Bybit parser/source mapping implementation, mocked/unit tests.
2. Bybit public-read-only adapter implementation, mocked/unit tests.
3. Bybit registry/config no activation.
4. Bybit user-local collect smoke.
5. Bybit collect smoke evidence docs-only.
6. OKX public source research against common contract as future expansion.
