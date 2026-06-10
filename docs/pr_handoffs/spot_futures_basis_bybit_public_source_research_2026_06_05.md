# Spot-Futures Basis Bybit Public Source Research against Common Contract v0

## 1. 작업 목적

이 문서는 Binance baseline 이후 `spot_futures_basis_v0`의 Bybit venue expansion을 준비하기 위한 docs-only public source research handoff이다.

목적:

- Binance baseline 이후 Bybit venue expansion을 위해 public source 후보를 조사한다.
- Bybit-specific endpoint/response 차이는 source adapter boundary에 가두고, strategy formula/readiness/candidate mapping은 common layer를 재사용한다.
- `spot_futures_basis_v0`가 Binance-only strategy로 굳어지지 않도록 common normalized source contract 기준으로 Bybit Spot BTCUSDT와 Bybit USDT linear perpetual BTCUSDT를 조사한다.
- 이번 PR은 implementation이 아니라 docs-only research다.
- `NO_TRADE_ONLY`를 유지한다.

Scope guardrails:

- Bybit endpoint를 실제 호출하지 않았다.
- Adapter/parser/readiness/packet-builder/fixture/config/registry/runtime behavior를 구현하거나 변경하지 않았다.
- Generated packet/sampling JSON을 생성하거나 commit하지 않았다.
- Private API, credentials, account/balance/position lookup, order/cancel, withdrawal/deposit/transfer, execution, alert, Council auto-call, auto-trading을 추가하지 않았다.

Official public documentation sources reviewed, without calling live endpoints:

- Bybit V5 Get Tickers: <https://bybit-exchange.github.io/docs/v5/market/tickers>
- Bybit V5 Get Orderbook: <https://bybit-exchange.github.io/docs/v5/market/orderbook>
- Bybit V5 Get Instruments Info: <https://bybit-exchange.github.io/docs/v5/market/instrument>
- Bybit V5 Get Funding Rate History: <https://bybit-exchange.github.io/docs/v5/market/history-fund-rate>
- Bybit V5 Get Bybit Server Time: <https://bybit-exchange.github.io/docs/v5/market/time>

## 2. Binance baseline recap

Binance reference venue status:

- Binance reference venue completed.
- Binance planning, mocked fixture files, parser, readiness, pure packet builder, public-read-only adapter, registry/config disabled entry, collect-path support, sampling mocked/unit support, and handoff evidence are complete.
- Initial collect smoke succeeded in saving an `opportunity_packet_v0` but returned `NEED_DATA` because spot `min_notional` metadata was missing and readiness propagated `spot_spot_min_notional_missing`.
- Collect retry after the Spot exchangeInfo `min_notional` live-shape follow-up succeeded with parser statuses `OK`, empty required missing fields, and no prior `min_notional` naming issue.
- User-local 3-sample sampling succeeded with `samples_ok=3`, `samples_error=0`, `REJECT=3`, and `NO_PERSISTENT_EDGE`.
- User-local 30-sample extended sampling succeeded with `samples_ok=30`, `samples_error=0`, parser `OK=30`, `required_missing_fields=0`, `REJECT=30`, and `NO_PERSISTENT_EDGE`.
- Binance 30-sample evidence is public-read-only path evidence only.
- Binance 30-sample evidence is not profitability proof.
- Binance 30-sample evidence is not persistent edge proof.
- `NO_TRADE_ONLY` remains in force.

## 3. Bybit target scope

Bybit target scope is planning-only:

| Field | Value |
| --- | --- |
| `source_venue_id` | `bybit` |
| Spot market | Bybit Spot BTCUSDT |
| Perp market | Bybit USDT linear perpetual BTCUSDT |
| `comparison_type` | `same_exchange_spot_perp_basis` |
| `strategy_family` | `spot_futures_basis` |
| `strategy_id` | `spot_futures_basis_v0` |
| Status | `proposed / experimental / non-active / NO_TRADE_ONLY` |

Bybit target scope interpretation:

- The target comparison is same-exchange spot/perp basis between Bybit Spot BTCUSDT and Bybit USDT linear perpetual BTCUSDT.
- Bybit spot/perp category differences must remain in the source adapter/parser boundary.
- Common formula/readiness/candidate semantics must not become Bybit-specific.
- This research does not activate `spot_futures_basis_v0`.

## 4. Candidate public endpoints

The following candidates are official Bybit V5 public market-data endpoints. They were reviewed from documentation only; this PR did not call them.

| Candidate | Path | Required params | Likely response fields | Role in common contract | Executable-context or context-only | Parser risk | Normalized mapping |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Spot ticker / book-ticker equivalent | `GET /v5/market/tickers` | `category=spot`, `symbol=BTCUSDT` | `result.category`, `result.list[].symbol`, `bid1Price`, `bid1Size`, `ask1Price`, `ask1Size`, `lastPrice`, `turnover24h`, `volume24h`, `usdIndexPrice` | Spot top-of-book snapshot and weak last-price context | Best bid/ask are executable-context candidates for top-of-book estimates; `lastPrice` is weak context only | Nested `result.list`; string numerics; `usdIndexPrice` is not required for basis; qty unit should be verified with mocked fixture | `SpotObservationNormalized` |
| Spot orderbook | `GET /v5/market/orderbook` | `category=spot`, `symbol=BTCUSDT`, optional `limit` | `result.s`, `b`, `a`, `ts`, `u`, `seq`, possibly `cts` in common response shape | Spot depth bids/asks, book timestamp/update id, and source freshness fields | Executable-context depth snapshot, but not fill feasibility proof | Array-of-arrays parsing; bid/ask sort assumptions; timestamp/data_age semantics; `limit` defaults differ by product and docs may drift | `SpotObservationNormalized` |
| Spot instruments info / symbol metadata | `GET /v5/market/instruments-info` | `category=spot`, `symbol=BTCUSDT` | `result.category`, `list[].symbol`, `baseCoin`, `quoteCoin`, `status`, `lotSizeFilter.basePrecision`, `quotePrecision`, `minOrderQty`, `minOrderAmt`, `maxOrderQty`, `maxOrderAmt`, `priceFilter.tickSize` | Spot symbol metadata for tick size, qty precision, min order qty, min notional/order amount | Context-only metadata; not executable basis | Spot uses `minOrderAmt` rather than Binance-style `minNotional`; `basePrecision`/`quotePrecision` vs step-size semantics need fixture verification | `SpotObservationNormalized` |
| Linear perp ticker | `GET /v5/market/tickers` | `category=linear`, `symbol=BTCUSDT` | `result.category`, `list[].symbol`, `bid1Price`, `bid1Size`, `ask1Price`, `ask1Size`, `lastPrice`, `indexPrice`, `markPrice`, `fundingRate`, `nextFundingTime`, `fundingIntervalHour`, `openInterest`, `turnover24h`, `volume24h` | Perp top-of-book plus mark/index/funding context | Best bid/ask are executable-context candidates for top-of-book estimates; mark/index/funding/last price are context-only | Same `BTCUSDT` symbol reused across products; `category=linear` must be correct; funding fields may be missing/empty for unexpected product state | `PerpObservationNormalized` |
| Linear perp orderbook | `GET /v5/market/orderbook` | `category=linear`, `symbol=BTCUSDT`, optional `limit` | `result.s`, `b`, `a`, `ts`, `u`, `seq`, `cts` | Perp depth bids/asks, book timestamp/update id, and source freshness fields | Executable-context depth snapshot, but not fill feasibility proof | Array-of-arrays parsing; `cts` matching-engine timestamp vs `ts`; data_age may be negative under clock skew; `limit` default differs from spot | `PerpObservationNormalized` |
| Linear perp instruments info | `GET /v5/market/instruments-info` | `category=linear`, `symbol=BTCUSDT` | `result.category`, `list[].symbol`, `contractType`, `status`, `baseCoin`, `quoteCoin`, `settleCoin`, `priceFilter.tickSize`, `lotSizeFilter.qtyStep`, `minOrderQty`, `minNotionalValue`, `maxOrderQty`, `maxMktOrderQty`, `fundingInterval`, `upperFundingRate`, `lowerFundingRate` | Perp contract metadata for tick size, qty step, min order qty, min notional, settlement, funding interval | Context-only metadata; not executable basis | Pagination/cursor defaults for linear universe; `minNotionalValue` naming; funding interval units; pre-market contract fields should not be assumed for BTCUSDT | `PerpObservationNormalized` |
| Funding history context | `GET /v5/market/funding/history` | `category=linear`, `symbol=BTCUSDT`; optional `startTime`, `endTime`, `limit` | `result.category`, `list[].symbol`, `fundingRate`, `fundingRateTimestamp` | Optional historical funding context if ticker funding context proves insufficient | Context-only; not executable basis | Not needed for first adapter if ticker supplies current `fundingRate` and `nextFundingTime`; time-window semantics need follow-up verification | `PerpObservationNormalized` extensions / diagnostics, `needs_follow_up_verification` |
| Server time / clock-skew context | `GET /v5/market/time` | none | `result.timeSecond`, `result.timeNano`, top-level `time` | Optional diagnostics for timestamp/data_age policy research | Context-only diagnostics | Adding this changes request count and latency profile; should be a later timestamp-policy PR, not first Bybit adapter slice | Diagnostics/extensions only, `needs_follow_up_verification` |

Endpoint notes:

- `GET /v5/market/tickers` is the likely source for Bybit spot/perp best bid/ask price and size. For linear perps, the same endpoint also provides mark/index/funding context candidates.
- `GET /v5/market/orderbook` is the likely source for public depth bids/asks and timestamp/update fields.
- `GET /v5/market/instruments-info` is the likely source for tick/step/min-order/min-notional metadata.
- Funding history and server time are optional context endpoints, not first-slice requirements, and should remain `needs_follow_up_verification` until a future mocked fixture/planning PR decides whether they are necessary.
- All endpoint candidates are public market-data endpoints in documentation; no private/account/order endpoint is part of this research.

## 5. Proposed Bybit normalized source contract mapping

### SpotObservationNormalized candidate mapping

Candidate mapping for Bybit Spot BTCUSDT:

| Normalized field | Proposed Bybit source |
| --- | --- |
| `venue_id` | `bybit` |
| `venue_name` | `Bybit Spot` |
| `market_type` | `spot` |
| `symbol` | `BTCUSDT` from `tickers.result.list[].symbol`, `orderbook.result.s`, or instruments `list[].symbol` |
| `base_asset` | `instruments-info(category=spot).result.list[].baseCoin` (`BTC`) |
| `quote_asset` | `instruments-info(category=spot).result.list[].quoteCoin` (`USDT`) |
| Best bid/ask and qty | `tickers(category=spot).result.list[].bid1Price`, `bid1Size`, `ask1Price`, `ask1Size` |
| Qty unit | Likely base asset quantity for spot; mark as `needs_follow_up_verification` in fixture planning |
| Book timestamp/update id | `orderbook(category=spot).result.ts`, `u`, `seq`; `cts` if present and verified |
| Depth bids/asks | `orderbook(category=spot).result.b`, `a` |
| Tick size | `instruments-info(category=spot).result.list[].priceFilter.tickSize` |
| Step/min order/min notional | `lotSizeFilter.basePrecision` or derived step candidate, `minOrderQty`, `minOrderAmt`; `quotePrecision` as quote precision context |
| `raw_endpoint_ids` | `bybit_v5_market_tickers_spot`, `bybit_v5_market_orderbook_spot`, `bybit_v5_market_instruments_info_spot` |
| `data_age_ms` / `latency_ms` | Adapter diagnostics from local monotonic/request timing plus response `time`/`ts` where policy allows |
| `parser_normalized_status` | `OK` only when required top-of-book, depth, and metadata fields are present and numeric |
| `required_missing_fields` | Missing top-of-book, symbol, depth, or metadata fields, using `spot_` prefix without double-prefixing |
| `parser_warnings` | Timestamp clock-skew, category mismatch, empty list, non-trading status, min-order/min-notional ambiguity |

### PerpObservationNormalized candidate mapping

Candidate mapping for Bybit USDT linear perpetual BTCUSDT:

| Normalized field | Proposed Bybit source |
| --- | --- |
| `venue_id` | `bybit` |
| `venue_name` | `Bybit Derivatives V5` |
| `market_type` | `perp` |
| `symbol` | `BTCUSDT` from `tickers.result.list[].symbol`, `orderbook.result.s`, or instruments `list[].symbol` |
| `base_asset` | `instruments-info(category=linear).result.list[].baseCoin` (`BTC`) |
| `quote_asset` | `instruments-info(category=linear).result.list[].quoteCoin` (`USDT`) |
| `settlement_asset` | `instruments-info(category=linear).result.list[].settleCoin` (`USDT`) if available |
| `margin_asset` | Likely same as `settleCoin` for USDT linear; mark as `needs_follow_up_verification` |
| `category` | `linear` |
| Contract type / instrument type | `instruments-info(category=linear).result.list[].contractType`, expected `LinearPerpetual` for BTCUSDT |
| Best bid/ask and qty | `tickers(category=linear).result.list[].bid1Price`, `bid1Size`, `ask1Price`, `ask1Size` |
| Qty unit | Contract/base quantity semantics require fixture verification |
| Book timestamp | `orderbook(category=linear).result.ts`, `u`, `seq`, `cts` |
| Depth bids/asks | `orderbook(category=linear).result.b`, `a` |
| Mark price | `tickers(category=linear).result.list[].markPrice` |
| Index price | `tickers(category=linear).result.list[].indexPrice` |
| Funding rate | `tickers(category=linear).result.list[].fundingRate`; optional historical context from `funding/history` if needed later |
| Next funding time | `tickers(category=linear).result.list[].nextFundingTime` |
| Tick size | `instruments-info(category=linear).result.list[].priceFilter.tickSize` |
| Step/min order/min notional | `lotSizeFilter.qtyStep`, `minOrderQty`, `minNotionalValue` |
| `raw_endpoint_ids` | `bybit_v5_market_tickers_linear`, `bybit_v5_market_orderbook_linear`, `bybit_v5_market_instruments_info_linear` |
| `data_age_ms` / `latency_ms` | Adapter diagnostics from local monotonic/request timing plus response `time`/`ts` where policy allows |
| `parser_normalized_status` | `OK` only when required top-of-book, depth, contract metadata, and numeric context fields are usable |
| `required_missing_fields` | Missing top-of-book, contract metadata, depth, or min-notional fields, using `perp_` prefix without double-prefixing |
| `parser_warnings` | Mark/index/funding context-only warning, timestamp clock-skew, funding interval warning, category mismatch, empty list, non-trading status |

## 6. Common formula reuse

Bybit should reuse the Binance/common basis logic rather than introducing venue-specific strategy math:

```text
long_spot_short_perp_gross_pct = ((perp_bid - spot_ask) / spot_ask) * 100
long_perp_short_spot_gross_pct = ((spot_bid - perp_ask) / perp_ask) * 100
estimated_net_basis_pct = selected_gross_basis_pct - fee_slippage_buffer_pct
```

Formula interpretation:

- The formulas are the same common logic already used for Binance spot/perp basis planning.
- The selected direction should be derived from executable top-of-book spot/perp bid/ask candidates, not mark/index/funding/last price.
- `markPrice`, `indexPrice`, `fundingRate`, `nextFundingTime`, and funding history are context only.
- Mark/index/funding context is not executable basis.
- `lastPrice` is weak context only and must not be used as executable basis.
- Top-of-book liquidity is not fill-feasibility proof.
- `estimated_net_basis_pct` remains analysis-only under `NO_TRADE_ONLY`.

## 7. Venue-specific boundaries

The following concerns should remain Bybit-specific and should not leak into common strategy math/readiness beyond normalized fields and warnings:

- `category=spot` vs `category=linear` request routing.
- `retCode` / `retMsg` / `retExtInfo` diagnostics.
- Same symbol string `BTCUSDT` reused across spot and linear products.
- Timestamp semantics from top-level `time`, ticker timestamps if present, orderbook `ts`, orderbook `cts`, and local request timing.
- Possible negative `data_age_ms` / clock-skew watch items.
- Funding interval warning possibility via `fundingInterval` or `fundingIntervalHour`.
- Tick/step/min order/min notional field names: spot `minOrderAmt` and `basePrecision`, linear `minNotionalValue` and `qtyStep`.
- Qty unit semantics for spot quantity vs linear contract/base quantity.
- Linear perp contract metadata such as `contractType`, `settleCoin`, `fundingInterval`, `upperFundingRate`, and `lowerFundingRate`.
- Bybit response shape and nested `result.list` structure.
- Empty list, non-zero `retCode`, non-`OK` `retMsg`, non-trading status, and pre-market/perpetual variants.

## 8. Watch items from prior Bybit work

Prior Bybit work in the `mark_orderbook_gap_hunt_v0` track produced reusable watch items for this venue expansion:

- Negative `data_age_ms` / timestamp clock-skew watch: Bybit public responses can produce local/remote timestamp ordering that requires warning-level handling rather than hiding raw evidence.
- Funding interval warning: Bybit funding interval metadata can be venue/product-specific; the parser should preserve interval context and warn if it is missing or unexpected.
- Public V5 `retCode` / `retMsg` diagnostics: source adapters should preserve public response diagnostics for reviewer evidence and debugging.
- Category-specific product semantics: `category=spot` and `category=linear` must be treated as distinct product spaces even when `symbol=BTCUSDT` matches.
- No private API / no trading behavior: prior Bybit work should remain public-read-only and analysis-only, with no private endpoint, account lookup, or order surface.

## 9. Risks

Bybit venue expansion risks:

- Same symbol `BTCUSDT` does not prove spot/perp product equivalence.
- Category parameter mistakes can silently mix `spot`, `linear`, `inverse`, or other products.
- Qty unit semantics may be misinterpreted between spot base quantity and linear perp contract/base quantity.
- `minNotional` / `minOrderAmt` / `minOrderQty` / `minNotionalValue` metadata mismatch can produce false `NEED_DATA` or false readiness.
- Mark/index/funding context can be mistaken for executable basis if the adapter/parser boundary is not explicit.
- Timestamp and `data_age_ms` values can be negative because of clock skew, response-time semantics, or local measurement policy.
- Endpoint response shape drift can break nested `result.list` parsing or field names.
- Top-of-book liquidity can be mistaken for fill feasibility.
- Codex or CI live network may see 403/network limits; future live smoke should be user-local and public-read-only.
- Generated live JSON can be mistaken for deterministic fixture data and accidentally committed.
- Public docs can change; mocked fixture planning should re-check official docs before writing fixture files.

## 10. Proposed future PR sequence for Bybit

Recommended Bybit sequence:

1. Bybit public source research docs-only.
2. Bybit mocked fixture planning.
3. Bybit mocked fixture files + fixture contract tests.
4. Bybit parser/source mapping implementation, mocked/unit tests.
5. Bybit readiness/packet builder compatibility tests if needed.
6. Bybit public-read-only adapter implementation, mocked/unit tests.
7. Registry/config no activation.
8. User-local collect smoke.
9. Docs-only collect evidence.
10. User-local 3-sample sampling evidence.
11. User-local 30-sample extended sampling evidence.

## 11. Explicitly not doing now

This PR explicitly does not do the following:

- Adapter implementation 없음.
- Parser implementation 없음.
- Readiness 변경 없음.
- Packet builder 변경 없음.
- Fixture JSON 생성 없음.
- Tests 생성 없음.
- Config/registry 변경 없음.
- Live endpoint 호출 없음.
- `sample_market_data` 실행 없음.
- `collect_market_data` 실행 없음.
- Generated JSON 생성/commit 없음.
- Private API 없음.
- Credentials 없음.
- Account/balance/position/order/cancel/withdraw/deposit/transfer 없음.
- Execution 없음.
- Alert 없음.
- Council auto-call 없음.
- Auto-trading 없음.

## 12. No-trade compliance

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

## 13. Generated JSON commit 금지

Generated JSON policy:

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- 이번 PR에는 generated JSON을 추가하지 않음.
- Future user-local Bybit smoke/sampling output은 evidence summary만 docs에 기록하고 원본 JSON은 삭제해야 함.
- Generated live JSON must not be copied into fixture directories unless a future PR explicitly converts it into deterministic mocked fixture data through review.

## 14. Rollback plan

Rollback plan:

- Docs-only PR이므로 revert하고 `docs/pr_handoffs/spot_futures_basis_bybit_public_source_research_2026_06_05.md` handoff 문서 1개를 제거하면 된다.
- Code/config/registry/runtime/parser/readiness/test/fixture/generated-data rollback은 필요 없다.
- No generated packet/sampling JSON was added, so no generated-data rollback is needed.

## 15. Next PR candidates

Recommended next PR candidates:

1. Bybit mocked fixture planning.
2. Bybit mocked fixture files + fixture contract tests.
3. Bybit parser/source mapping implementation, mocked/unit tests.
4. Bybit public-read-only adapter implementation, mocked/unit tests.
5. OKX public source research against common contract.
