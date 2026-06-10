# Spot-Futures Basis Bybit Mocked Fixture Planning v0

## 1. 작업 목적

이 문서는 `spot_futures_basis_v0`의 Bybit Spot BTCUSDT + Bybit USDT linear perpetual BTCUSDT mocked fixture/test design을 구현 전에 고정하기 위한 docs-only planning handoff이다.

목적:

- Bybit public source research 이후, 구현 전에 mocked fixture/test design을 고정한다.
- Bybit-specific endpoint/response 차이를 source adapter/parser boundary에 가둔다.
- Strategy formula/readiness/candidate mapping은 common layer를 재사용한다.
- 이번 PR은 fixture planning이며 implementation이 아니다.
- `NO_TRADE_ONLY`를 유지한다.

Scope guardrails:

- 이 PR에서는 fixture JSON을 생성하지 않는다.
- Bybit endpoint를 호출하지 않는다.
- Parser/readiness/packet builder/adapter/config/registry/tests를 구현하거나 변경하지 않는다.
- Generated packet/sampling JSON을 생성하거나 commit하지 않는다.
- Private API, credentials, account/balance/position lookup, order/cancel, withdrawal/deposit/transfer, execution, alert, Council auto-call, auto-trading을 추가하지 않는다.

## 2. Binance reference fixture pattern recap

Binance reference fixture workflow recap:

- Binance는 fixture planning → deterministic fixture files → parser → readiness → pure packet builder → public-read-only adapter → collect/sampling evidence 순서로 진행했다.
- Bybit도 같은 mocked-first sequence를 따른다.
- Live/generated JSON을 fixture로 commit하지 않는다.
- Future fixture는 hand-written 또는 sanitized mocked sample이어야 한다.
- Fixture는 parser/readiness edge cases를 재현하기 위해 작고 결정적이어야 한다.
- User-local smoke/sampling generated JSON은 evidence summary만 docs에 기록하고 raw generated JSON은 삭제해야 한다.

Bybit fixture planning implication:

- Public source research에서 확인한 Bybit V5 response envelope와 category-specific fields를 deterministic mocked samples로 고정한 뒤 parser/source mapping을 구현한다.
- Fixture contract tests가 먼저 Bybit response shape, public-only fields, no-trade guardrails, generated JSON ban을 검증해야 한다.
- Fixture planning은 Binance assumptions를 그대로 복사하지 않고 Bybit category/metadata/qty semantics를 명시적으로 분리한다.

## 3. Bybit target scope

| Field | Value |
| --- | --- |
| `source_venue_id` | `bybit` |
| Spot market | Bybit Spot BTCUSDT |
| Perp market | Bybit USDT linear perpetual BTCUSDT |
| `comparison_type` | `same_exchange_spot_perp_basis` |
| `strategy_family` | `spot_futures_basis` |
| `strategy_id` | `spot_futures_basis_v0` |
| Status | `proposed / experimental / non-active / NO_TRADE_ONLY` |

Target scope notes:

- The target comparison is same-exchange spot/perp basis.
- The same symbol string `BTCUSDT` must not collapse spot and linear perp product semantics.
- Bybit `category=spot` and `category=linear` must remain distinct in fixtures, parser tests, diagnostics, and normalized observations.
- This planning does not activate `spot_futures_basis_v0`.

## 4. Proposed fixture files

Future implementation PR fixture candidates:

| Future fixture path | Purpose | Created in this PR? |
| --- | --- | --- |
| `tests/fixtures/market_data/spot_futures_basis/bybit_spot_ticker_btcusdt.json` | Mock Bybit V5 spot ticker/top-of-book source response | No |
| `tests/fixtures/market_data/spot_futures_basis/bybit_spot_orderbook_btcusdt.json` | Mock Bybit V5 spot orderbook source response with at least two levels | No |
| `tests/fixtures/market_data/spot_futures_basis/bybit_spot_instruments_info_btcusdt.json` | Mock Bybit V5 spot instruments metadata source response | No |
| `tests/fixtures/market_data/spot_futures_basis/bybit_linear_ticker_btcusdt.json` | Mock Bybit V5 linear perp ticker/top-of-book plus mark/index/funding context | No |
| `tests/fixtures/market_data/spot_futures_basis/bybit_linear_orderbook_btcusdt.json` | Mock Bybit V5 linear perp orderbook source response with at least two levels | No |
| `tests/fixtures/market_data/spot_futures_basis/bybit_linear_instruments_info_btcusdt.json` | Mock Bybit V5 linear perp contract metadata source response | No |
| `tests/fixtures/market_data/spot_futures_basis/bybit_linear_funding_history_btcusdt.json` | Optional funding context fixture if future parser planning requires historical funding context | No |

Fixture file policy:

- This PR does not create fixture JSON files.
- Live generated JSON must not be committed as a fixture.
- Future fixtures must be deterministic hand-written or sanitized mocked samples.
- Future fixture review should verify all source responses contain only public market-data fields.
- Future fixture review should reject credentials, private endpoint responses, account/balance/position/order/cancel/withdraw/deposit/transfer fields, generated sampling output, and generated packet output.

## 5. Fixture source-response design

### Bybit common V5 response envelope

Every Bybit mocked source-response fixture should preserve the common V5 envelope:

- `retCode`
- `retMsg`
- `result`
- `retExtInfo`
- `time`

Envelope test expectations:

- `retCode=0` and `retMsg=OK` should be included in happy-path fixtures.
- Non-zero `retCode` / non-`OK` `retMsg` should be reserved for future error-path fixture planning.
- Parser diagnostics should preserve `retCode`, `retMsg`, and endpoint id.
- `time` should be deterministic and should allow data-age tests without live clock dependency.

### Spot ticker fixture

Required mocked shape:

- `result.category=spot`.
- `result.list[0].symbol=BTCUSDT`.
- `result.list[0].bid1Price` and `result.list[0].bid1Size`, or documented equivalent if future verification shows spot ticker differs.
- `result.list[0].ask1Price` and `result.list[0].ask1Size`, or documented equivalent if future verification shows spot ticker differs.
- `result.list[0].lastPrice` may be included as weak context only.
- Optional public context fields such as `volume24h` / `turnover24h` may be included only if useful for diagnostics.

Parser risk:

- If Bybit spot ticker response does not provide bid/ask for the selected symbol in a future verified shape, parser tests should force `NEED_DATA` rather than falling back to `lastPrice` as executable basis.
- Numeric fields should remain strings in fixture source shape to match exchange-style public responses and test parser coercion.

### Spot orderbook fixture

Required mocked shape:

- `result.s=BTCUSDT` or documented symbol equivalent.
- `result.b` / bids with at least two levels.
- `result.a` / asks with at least two levels.
- `result.ts` deterministic timestamp.
- `result.u` update id if available.
- `result.seq` if available.
- `result.cts` only if present/verified for spot; otherwise mark as `needs_follow_up_verification` and do not make it required.

Parser risk:

- Bids/asks are array-of-array string numerics.
- Tests should verify bid/ask side preservation and avoid assuming fill feasibility from top-of-book depth.

### Spot instruments-info fixture

Required mocked shape:

- `result.category=spot`.
- `result.list[0].symbol=BTCUSDT`.
- `result.list[0].baseCoin=BTC`.
- `result.list[0].quoteCoin=USDT`.
- `result.list[0].status` with a trading/active value.
- `result.list[0].priceFilter.tickSize`.
- `result.list[0].lotSizeFilter.basePrecision` / `quotePrecision` or documented equivalent.
- `result.list[0].lotSizeFilter.minOrderQty`.
- `result.list[0].lotSizeFilter.minOrderAmt` or min-notional equivalent if available.
- Unknown or version-sensitive metadata fields should be marked `needs_follow_up_verification` in future fixture/test notes.

Parser risk:

- Bybit spot metadata may not use Binance-style `MIN_NOTIONAL` names.
- `minOrderAmt` likely maps to `min_notional`, while `minOrderQty` maps to min order size.
- `basePrecision` is not automatically the same as executable step size; future parser tests should document whether it is preserved as precision or derived into `step_size`.

### Linear ticker fixture

Required mocked shape:

- `result.category=linear`.
- `result.list[0].symbol=BTCUSDT`.
- `result.list[0].bid1Price` and `result.list[0].bid1Size`.
- `result.list[0].ask1Price` and `result.list[0].ask1Size`.
- `result.list[0].markPrice`.
- `result.list[0].indexPrice`.
- `result.list[0].fundingRate`.
- `result.list[0].nextFundingTime`.
- `result.list[0].openInterest` may be included as public context if present.
- `result.list[0].lastPrice` may be included as weak context only.

Parser risk:

- Mark/index/funding/last price must remain context-only.
- Bid/ask top-of-book fields are the executable-context candidates for formula tests.
- Funding interval context may come from ticker or instruments-info depending future parser design.

### Linear orderbook fixture

Required mocked shape:

- `result.s=BTCUSDT`.
- `result.b` / bids with at least two levels.
- `result.a` / asks with at least two levels.
- `result.ts` deterministic timestamp.
- `result.u` update id if available.
- `result.seq` if available.
- `result.cts` if available.

Parser risk:

- `ts` and `cts` may have different semantics.
- Tests should preserve raw timestamp evidence and allow negative `data_age_ms` watch behavior rather than hiding it.

### Linear instruments-info fixture

Required mocked shape:

- `result.category=linear`.
- `result.list[0].symbol=BTCUSDT`.
- `result.list[0].contractType=LinearPerpetual`.
- `result.list[0].baseCoin=BTC`.
- `result.list[0].quoteCoin=USDT`.
- `result.list[0].settleCoin=USDT` if present.
- `result.list[0].priceFilter.tickSize`.
- `result.list[0].lotSizeFilter.qtyStep`.
- `result.list[0].lotSizeFilter.minOrderQty`.
- `result.list[0].lotSizeFilter.minNotionalValue` or documented equivalent.
- `result.list[0].fundingInterval` if present.

Parser risk:

- `minNotionalValue` should map to perp `min_notional`, not spot `minOrderAmt`.
- `qtyStep` should map to linear perp `step_size`.
- `contractType` and `category` must be preserved to prevent product-semantics mismatch.

## 6. Expected normalized SpotObservation

Future parser tests should expect a Bybit spot normalized observation with fields equivalent to:

| Normalized field | Expected value / source |
| --- | --- |
| `venue_id` | `bybit` |
| `venue_name` | `Bybit Spot` |
| `market_type` | `spot` |
| `symbol` | `BTCUSDT` |
| `base_asset` | `BTC` |
| `quote_asset` | `USDT` |
| `best_bid` / `best_ask` | From spot ticker bid/ask fields |
| `best_bid_qty` / `best_ask_qty` | From spot ticker bid/ask size fields |
| `bid_qty_unit` / `ask_qty_unit` | Base asset quantity candidate; mark exact semantics `needs_follow_up_verification` until fixture implementation |
| `depth_bids` / `depth_asks` | At least two levels from spot orderbook fixture |
| `tick_size` | From spot instruments `priceFilter.tickSize` |
| `step_size` or qty precision | From spot `lotSizeFilter.basePrecision` or future verified equivalent |
| `min_order_size` | From spot `lotSizeFilter.minOrderQty` |
| `min_notional` | From spot `lotSizeFilter.minOrderAmt` or future verified min-notional equivalent |
| `raw_endpoint_ids` | Spot ticker/orderbook/instruments fixture endpoint ids |
| `data_age_ms` | Deterministic parser/adaptor timestamp calculation; raw negative evidence preserved if applicable |
| `latency_ms` | Deterministic mocked latency value or adapter-injected measurement |
| `parser_normalized_status` | `OK` for complete happy-path fixture; `NEED_DATA` for missing required source fields |
| `required_missing_fields` | Empty for happy path; explicit `spot_*` names for missing top-of-book/metadata cases |
| `parser_warnings` | Category mismatch, timestamp clock-skew, min-notional ambiguity, non-trading status, or last-price-only warning when applicable |

## 7. Expected normalized PerpObservation

Future parser tests should expect a Bybit linear perp normalized observation with fields equivalent to:

| Normalized field | Expected value / source |
| --- | --- |
| `venue_id` | `bybit` |
| `venue_name` | `Bybit Derivatives V5` |
| `market_type` | `perp` |
| `symbol` | `BTCUSDT` |
| `base_asset` | `BTC` |
| `quote_asset` | `USDT` |
| `settlement_asset` | `USDT` if present from `settleCoin` |
| `margin_asset` | `USDT` if future parser maps margin to settlement asset; mark `needs_follow_up_verification` |
| `category` | `linear` |
| `contract_type` | `LinearPerpetual` |
| `best_bid` / `best_ask` | From linear ticker bid/ask fields |
| `best_bid_qty` / `best_ask_qty` | From linear ticker bid/ask size fields |
| `bid_qty_unit` / `ask_qty_unit` | Linear contract/base quantity candidate; exact semantics require fixture/parser note |
| `depth_bids` / `depth_asks` | At least two levels from linear orderbook fixture |
| `mark_price` | From linear ticker `markPrice` |
| `index_price` | From linear ticker `indexPrice` |
| `funding_rate` | From linear ticker `fundingRate` |
| `next_funding_time` | From linear ticker `nextFundingTime` |
| `tick_size` | From linear instruments `priceFilter.tickSize` |
| `step_size` | From linear instruments `lotSizeFilter.qtyStep` |
| `min_order_size` | From linear instruments `lotSizeFilter.minOrderQty` |
| `min_notional` | From linear instruments `lotSizeFilter.minNotionalValue` or equivalent |
| `raw_endpoint_ids` | Linear ticker/orderbook/instruments fixture endpoint ids |
| `data_age_ms` | Deterministic parser/adaptor timestamp calculation; raw negative evidence preserved if applicable |
| `latency_ms` | Deterministic mocked latency value or adapter-injected measurement |
| `parser_normalized_status` | `OK` for complete happy-path fixture; `NEED_DATA` for missing required source fields |
| `required_missing_fields` | Empty for happy path; explicit `perp_*` names for missing top-of-book/metadata cases |
| `parser_warnings` | Mark/index/funding context-only warning, funding interval warning, category mismatch, timestamp clock-skew, or non-trading status |

## 8. Formula test cases

Future Bybit fixture/parser/readiness tests should include these cases:

| Case | Input shape | Expected readiness / reason | Notes |
| --- | --- | --- | --- |
| Case A | No positive gross executable basis | `REJECT / no_positive_gross_basis` | Both executable directions are zero/negative before fee buffer. |
| Case B | Positive gross but negative net after fee/slippage buffer | `REJECT / non_positive_estimated_net_basis` | Confirms fee/slippage buffer remains common logic. |
| Case C | Positive net basis | `WATCH`, still `NO_TRADE_ONLY` | WATCH is analysis-only and must not become ENTER/execution/alert/Council auto-call. |
| Case D | Missing spot bid/ask | `NEED_DATA` | Last price must not substitute for executable top-of-book. |
| Case E | Missing spot metadata / `min_notional` | `NEED_DATA` | Confirms Bybit `minOrderAmt`/equivalent metadata is required. |
| Case F | Mark/index/funding only without executable bid/ask | `NEED_DATA` or `REJECT`, but never `WATCH` | Context-only fields cannot create executable basis. |
| Case G | Same `BTCUSDT` symbol but category mismatch | `NEED_DATA / product_semantics_mismatch` warning candidate | Confirms `category=spot` and `category=linear` separation. |
| Case H | Negative `data_age_ms` | Raw preserve / watch item, no clamp | Confirms evidence is not hidden by timestamp coercion. |
| Case I | Funding interval warning | Warning preserved, no trading signal | Confirms funding interval context does not alter execution posture. |

## 9. Guardrail tests

Future test PR guardrails:

- No private/account/order fields in fixtures.
- No credentials.
- No generated live JSON fixture.
- No `lastPrice` as executable basis.
- No `markPrice`, `indexPrice`, or `fundingRate` as executable basis.
- `WATCH` is not `ENTER`.
- No alert/Council auto-call/execution.
- No active strategy promotion.
- No config/registry activation.
- `retCode` / `retMsg` diagnostics preserved.
- `category=spot` vs `category=linear` preserved.
- Required missing fields use stable `spot_*` and `perp_*` naming without double-prefixing.
- Generated packet/sampling paths are not written by mocked fixture tests.

## 10. Reuse from Binance implementation

Reusable from Binance implementation:

- Common basis formula.
- Readiness helper policy.
- Packet builder shape.
- Sampling/evidence workflow.
- `NO_TRADE_ONLY` assumptions.
- Generated JSON commit ban.
- Fixture contract test style.
- Parser status / required missing fields / parser warnings pattern.
- Public-read-only adapter evidence boundaries.

Do not reuse blindly / use with caution:

- Binance endpoint paths.
- Binance `exchangeInfo` filter names.
- Binance base/futures metadata assumptions.
- Binance `min_notional` filter shape.
- Binance-specific parser modes.
- Same symbol means same product assumption.
- Binance-specific timestamp/update-id semantics.
- Binance fixture numeric values as Bybit evidence.

## 11. Bybit-specific watch items

Bybit-specific watch items:

- `category=spot` vs `category=linear`.
- `retCode` / `retMsg` diagnostics.
- Nested `result.list` shape.
- `funding_interval=480` or funding interval warning candidate.
- Negative `data_age_ms` / timestamp clock-skew watch.
- Qty unit semantics.
- `minOrderQty` / `minNotionalValue` field uncertainty.
- Spot `minOrderAmt` / precision vs step-size uncertainty.
- Same `BTCUSDT` symbol but different product semantics.
- Top-of-book liquidity is not fill feasibility.
- Mark/index/funding context is not executable basis.

## 12. Explicitly not doing now

This PR explicitly does not do the following:

- Fixture JSON creation 없음.
- Tests 생성 없음.
- Parser 구현 없음.
- Readiness 변경 없음.
- Packet builder 변경 없음.
- Adapter 구현 없음.
- Config/registry 변경 없음.
- Live endpoint 호출 없음.
- `collect_market_data` 실행 없음.
- `sample_market_data` 실행 없음.
- Generated JSON 생성/commit 없음.
- Private API 없음.
- Credentials 없음.
- Account/balance/position/order/cancel/withdraw/deposit/transfer 없음.
- Execution 없음.
- Alert 없음.
- Council auto-call 없음.
- Auto-trading 없음.

## 13. No-trade compliance

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

## 14. Generated JSON commit 금지

Generated JSON policy:

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- Future user-local Bybit smoke/sampling output은 evidence 요약 후 삭제해야 함.
- 이번 PR에는 generated JSON을 추가하지 않음.
- Future fixture PR must not copy raw generated live JSON into fixtures; fixtures must be deterministic hand-written or sanitized mocked samples.

## 15. Rollback plan

Rollback plan:

- Docs-only PR이므로 revert하고 `docs/pr_handoffs/spot_futures_basis_bybit_mocked_fixture_planning_2026_06_05.md` handoff 문서 1개를 제거하면 된다.
- Code/config/registry/runtime/parser/readiness/test/fixture/generated-data rollback은 필요 없다.
- No generated packet/sampling JSON was added, so no generated-data rollback is needed.

## 16. Next PR candidates

Recommended next PR candidates:

1. Bybit mocked fixture files + fixture contract tests.
2. Bybit parser/source mapping implementation, mocked/unit tests.
3. Bybit public-read-only adapter implementation, mocked/unit tests.
4. Bybit registry/config no activation.
5. Bybit user-local collect smoke.
6. OKX public source research against common contract.
