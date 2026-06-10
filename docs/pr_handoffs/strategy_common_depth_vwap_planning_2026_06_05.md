# Strategy-Common Depth / VWAP Planning v0

## 1. 작업 목적

이 문서는 `mark_orderbook_gap_hunt_v0`와 `spot_futures_basis_v0`에서 반복적으로 드러난 top-of-book 중심 evidence의 한계를 strategy-common 관점에서 정리하고, 향후 depth / VWAP / size simulation을 어떤 순서로 설계, 테스트, 구현할지 planning-only로 기록한다.

Scope:

- Top-of-book bid/ask만 보는 현재 한계를 정리한다.
- Depth / VWAP / size simulation을 strategy-common future enhancement로 설계한다.
- 이번 문서는 implementation이 아니라 planning이다.
- `NO_TRADE_ONLY`를 유지한다.
- Active strategy는 `cross_exchange_spot_spread_v1`로 유지한다.
- Parser, readiness, packet, sampling, registry, config, runtime behavior는 변경하지 않는다.

This PR does not implement Depth/VWAP, change readiness behavior, change parser/schema fields, call live endpoints, commit generated JSON, add alerts, create Council auto-call, or enable execution.

## 2. 아주 쉬운 예시

초보자용 예시:

- 어떤 시장의 top-of-book ask가 100원이고, 그 가격에 걸린 수량이 1개뿐이라고 가정한다.
- 내가 1개만 산다면 100원에 살 수 있다고 추정할 수 있다.
- 하지만 내가 5개를 사려면 100원에 5개가 모두 체결된다고 볼 수 없다.
- Orderbook ask depth가 다음과 같다고 가정한다.

| ask price | available quantity | cost if consumed |
| ---: | ---: | ---: |
| 100원 | 1개 | 100원 |
| 101원 | 2개 | 202원 |
| 102원 | 2개 | 204원 |

5개를 모두 사려면 총 비용은 `100 + 202 + 204 = 506원`이다.

VWAP-style estimate:

```text
vwap_ask = total_cost / total_quantity
         = 506 / 5
         = 101.2원
```

해석:

- Top-of-book만 보면 buy price가 100원처럼 보인다.
- Depth를 반영하면 5개 buy estimate는 101.2원이다.
- 따라서 top-of-book만 보면 gross gap / basis를 과대평가할 수 있다.
- 이 계산은 execution이 아니라 public orderbook 기반 analysis quality improvement 후보이다.

## 3. Problem statement

Problem statement:

- Top-of-book liquidity is not fill feasibility.
- Bid/ask top level만으로는 target size 체결 가능성을 알 수 없다.
- Orderbook depth가 없거나 depth를 쓰지 않으면 gross gap / basis를 과대평가할 수 있다.
- Mark price, index price, funding rate, last price는 executable price가 아니다.
- Private API 없이 실제 account-specific fill, balance, margin, position feasibility는 확인할 수 없다.
- 따라서 depth/VWAP는 execution이 아니라 public-data-based analysis quality improvement다.

Concrete failure modes if top-of-book is overread:

- Top ask에 아주 작은 quantity만 있어도 전체 target size가 그 가격에 체결된다고 오해할 수 있다.
- Spot side는 충분해 보여도 perp side depth가 부족하면 pair trade basis가 사라질 수 있다.
- Perp contract unit conversion이 틀리면 target size 자체가 잘못 계산될 수 있다.
- Gross top-of-book edge가 수수료, buffer, slippage, depth consumption 이후 negative net estimate로 바뀔 수 있다.
- Public orderbook depth가 있다고 해도 account-specific order placement 가능성을 증명하지 않는다.

## 4. Current evidence recap

### `mark_orderbook_gap_hunt_v0`

Current evidence recap:

- Binance / Bybit / OKX baseline complete.
- Comparative summary complete.
- `REJECT` / `NO_PERSISTENT_EDGE` 반복.
- Mark price is not executable.
- Public orderbook diagnostics may include depth levels, but the current candidate does not use full depth/VWAP for readiness.
- Current dashboard/Council status: `NO_EDGE_ARCHIVE` + `POLICY_REVIEW`.
- Current evidence does not justify active promotion, alerting, Council auto-call, or execution.

### `spot_futures_basis_v0`

Current evidence recap:

- Binance + Bybit baseline complete.
- Comparative summary complete.
- `REJECT` / `NO_PERSISTENT_EDGE` 반복.
- Top-of-book bid/ask is used for current basis estimate.
- Depth/VWAP is not implemented.
- Current dashboard/Council status: `NO_EDGE_ARCHIVE` + `POLICY_REVIEW`.
- Current evidence does not justify active promotion, alerting, Council auto-call, or execution.

### Dashboard / Council

Current evidence recap:

- `depth_vwap_not_implemented` is a watch item.
- `top_of_book_liquidity_not_fill_feasibility` is a watch item.
- Affected strategies include `POLICY_REVIEW`.
- Dashboard remains evidence inventory.
- Council criteria interprets dashboard rows; it does not create Council auto-call or execution.

## 5. Depth / VWAP terminology

Candidate terminology definitions:

- `orderbook_depth`: ordered bid/ask levels beyond the top level.
- `top_of_book`: best bid and best ask only.
- `bid_levels`: price/quantity levels available for selling into bids, typically sorted best bid downward.
- `ask_levels`: price/quantity levels available for buying from asks, typically sorted best ask upward.
- `level_price`: price at one orderbook level.
- `level_quantity`: available quantity at one orderbook level.
- `quantity_unit`: unit for `level_quantity`, such as base asset, quote notional, contracts, or venue-specific lot units.
- `notional`: price multiplied by resolved quantity, expressed in quote currency after required conversion.
- `target_size`: base or contract quantity to simulate.
- `target_notional`: quote-currency notional to simulate.
- `executable_quantity`: public-depth quantity that can be consumed in a simulated side, before account-specific checks.
- `vwap_bid`: simulated average sell price when consuming bid levels.
- `vwap_ask`: simulated average buy price when consuming ask levels.
- `vwap_mid_context`: context-only midpoint derived from `vwap_bid` and `vwap_ask`, not an executable price.
- `slippage_pct`: difference between top-of-book price and VWAP estimate as a percentage.
- `depth_coverage_pct`: percentage of target size/notional covered by available public depth.
- `insufficient_depth`: marker that public depth did not cover the target size/notional.
- `depth_levels_used`: count of orderbook levels consumed in the simulation.
- `size_or_notional_resolved`: marker that target size or target notional was resolved with explicit unit semantics.

This PR does not rename fields, change schemas, add parser fields, or add packet fields. These are terminology definitions only.

## 6. Strategy-specific application

### A. `mark_orderbook_gap_hunt_v0`

Current:

- Current evidence observes mark price vs top-of-book bid/ask gap.
- Mark price is a reference/context price and remains non-executable.
- Current readiness does not use a full target-size VWAP simulation.

Problem:

- Top ask/bid alone cannot determine whether a target size can be bought or sold at that price.
- A positive top-level gap can disappear after consuming multiple levels.
- Public depth can improve analysis, but it still cannot prove account-specific fill feasibility.

Future candidate application:

- For `long_gap`, future diagnostics could use `vwap_ask` because the simulated action is buying from asks.
- For `short_gap`, future diagnostics could use `vwap_bid` because the simulated action is selling into bids.
- `mark_price` remains context only and must not be treated as executable.
- Depth/VWAP context may reduce overestimation of gross gap.
- Depth/VWAP availability must not create execution permission.
- Any readiness-affecting change must be separate from diagnostics-only planning and require approval.

Example planning scenario:

- Top ask is 100.00 with 0.01 BTC.
- Mark context is 100.50.
- Target simulation is 0.10 BTC.
- If the next ask levels produce `vwap_ask=100.42`, the apparent top-of-book gap shrinks materially.
- This may remain a diagnostics/context field first, without changing readiness.

### B. `spot_futures_basis_v0`

Current:

- Current evidence observes spot ask vs perp bid and perp ask vs spot bid top-of-book basis.
- Funding, mark, and index are context fields, not executable basis.
- Depth/VWAP is not implemented.

Problem:

- Spot and perp each have their own depth and quantity unit semantics.
- Perp contract units can differ by venue.
- A positive top-of-book basis can disappear if either leg has insufficient depth.
- Unit conversion errors can create false depth coverage or false insufficient-depth signals.

Future candidate application:

- Long spot / short perp:
  - Spot side uses `vwap_ask`.
  - Perp side uses `vwap_bid`.
- Long perp / short spot:
  - Perp side uses `vwap_ask`.
  - Spot side uses `vwap_bid`.
- Venue-specific unit conversion must remain explicit.
- Funding/mark/index remain context, not executable basis.
- Depth/VWAP context must not imply a trade instruction.
- Any VWAP-adjusted readiness policy requires separate approval and stronger evidence.

Example planning scenario:

- Spot top ask is 100.00 but only 0.02 BTC is available.
- Perp top bid is 100.20 with 0.10 BTC equivalent available.
- Target simulation is 0.10 BTC.
- Spot `vwap_ask` may become 100.18 after consuming deeper asks.
- The apparent top-of-book basis of 0.20 may become a near-zero or negative VWAP-adjusted context estimate before fees/buffer.

## 7. Venue-specific considerations

### Binance

Venue considerations:

- Spot depth and USDⓈ-M futures depth are separate products even when both use `BTCUSDT`.
- `BTCUSDT` uses the same symbol string but different product semantics across spot and futures.
- Quantity is likely base asset for spot/futures in the current planning context, but parser/tests must verify this explicitly before implementation.
- `exchangeInfo` filters, min notional, tick size, and step size matter for target size/notional interpretation.
- Future fixtures should include both shallow and multi-level depth examples.
- Future tests should verify that Binance spot and futures depth are not merged without product metadata.

### Bybit

Venue considerations:

- `category=spot` and `category=linear` must remain explicit.
- V5 orderbook shape must be parsed per category.
- `funding_interval=480` remains context and not executable basis.
- Quantity unit semantics must stay explicit.
- The orderbook category live-shape issue already observed and fixed in parser work should remain a fixture/test candidate for any depth/VWAP helper.
- Future tests should include spot vs linear target-size alignment and mixed string/decimal quantities.

### OKX

Venue considerations:

- This `spot_futures_basis_v0` cycle keeps OKX as future expansion.
- `mark_orderbook_gap_hunt_v0` OKX has contracts unit, `contract_value`, and `lot_size` semantics.
- `index_price=None` watch item remains separate from depth/VWAP.
- OKX depth/VWAP implementation would require explicit contract unit conversion.
- Future OKX tests should include contract quantity to base/quote notional conversion.
- OKX index/reference semantics must not be backfilled from depth, mark, last, or midpoint values.

## 8. Policy options

### Option A: Top-of-book only, keep as-is

Description:

- Keep current top-of-book bid/ask evidence flow.
- Do not add depth availability, VWAP, or size simulation.

Pros:

- Simple.
- Baselines already exist.
- No behavior-change risk.

Cons:

- Fill feasibility illusion remains.
- Gross gap / basis may be overestimated.
- Does not address `depth_vwap_not_implemented` watch item.

### Option B: Depth availability flag only

Description:

- Record whether orderbook depth exists and how many levels are present.
- Do not calculate VWAP.
- Do not change readiness behavior.

Pros:

- Safe first implementation candidate.
- Helps distinguish top-of-book-only evidence from multi-level evidence.
- Can be unit-tested with simple fixtures.

Cons:

- Does not estimate target-size average price.
- Does not quantify slippage.

### Option C: VWAP calculation as diagnostics/context only

Description:

- Calculate `vwap_bid` / `vwap_ask` for a target size or target notional.
- Add the result as diagnostics/context only.
- Do not change readiness decision.
- Preserve `NO_TRADE_ONLY`.

Pros:

- Improves analysis quality.
- Quantifies how top-of-book can overstate edge.
- Can be implemented as pure helper with mocked/unit tests.

Cons:

- Requires explicit unit conversion.
- Target size/notional policy must be defined.
- May be misread as execution feasibility unless wording is strict.

### Option D: VWAP-adjusted estimated net gap / basis

Description:

- Use VWAP in estimated net gap / basis calculations.

Pros:

- More realistic public-data estimate than top-of-book.

Cons:

- Behavior-changing possibility.
- Requires separate approval, tests, and evidence.
- Could alter readiness summaries and Council classification.

### Option E: Readiness-affecting depth policy

Description:

- Downgrade to `NEED_DATA` or `REJECT` when depth is insufficient.

Pros:

- Strict data quality enforcement.

Cons:

- Highest behavior-changing risk.
- Requires careful target-size governance.
- This planning PR forbids implementation.

## 9. Recommended policy direction

Recommended direction:

- Short term: Option B + Option C planning.
- First, treat depth availability and level count as summary/context.
- Next, evaluate a mocked/unit-test-based VWAP diagnostics-only helper.
- Preserve readiness behavior.
- No active promotion.
- No alert.
- No Council auto-call.
- No execution.
- Do not claim fill feasibility without private API and account-specific constraints.
- Defer VWAP-adjusted readiness to a much later separately approved phase with stronger evidence.

Rationale:

- Depth availability helps reviewers understand evidence quality with minimal behavior risk.
- VWAP diagnostics can show whether top-of-book edge survives public depth consumption.
- Diagnostics-only helper work can be pure, deterministic, and mocked-first.
- Readiness behavior should remain stable until evidence and review justify changing it.

## 10. Proposed formulas

Planning candidate formulas only.

### Ask-side buy VWAP

Process:

- Consume ask levels from best ask upward until `target_size` or `target_notional` is covered.
- Compute average price across consumed quantity.

Formula:

```text
vwap_ask = sum(price_i * qty_i) / sum(qty_i)
```

Example:

```text
asks = [(100, 1), (101, 2), (102, 2)]
target_size = 5
vwap_ask = (100*1 + 101*2 + 102*2) / 5 = 101.2
```

### Bid-side sell VWAP

Process:

- Consume bid levels from best bid downward until `target_size` or `target_notional` is covered.
- Compute average price across consumed quantity.

Formula:

```text
vwap_bid = sum(price_i * qty_i) / sum(qty_i)
```

### Depth coverage

Formula:

```text
depth_coverage_pct = filled_size / target_size * 100
insufficient_depth = filled_size < target_size
```

### Slippage

Formula:

```text
ask_slippage_pct = (vwap_ask - best_ask) / best_ask * 100
bid_slippage_pct = (best_bid - vwap_bid) / best_bid * 100
```

Planning constraints:

- Formulas are planning candidates only.
- No implementation in this PR.
- Quantity unit and contract conversion must be explicit.
- Formula output must not imply order intent or account-specific feasibility.

## 11. Test case candidates

Future mocked/unit test candidates:

1. Ask VWAP fully filled at first level: target size is less than or equal to best ask quantity, so `vwap_ask == best_ask` and `depth_levels_used=1`.
2. Ask VWAP consumes multiple levels: target size spans 100/101/102 ask levels and produces the expected weighted average.
3. Bid VWAP consumes multiple levels: target size spans multiple bid levels from best bid downward and computes the expected `vwap_bid`.
4. Insufficient ask depth: ask levels do not cover target size, `insufficient_depth=true`, and `depth_coverage_pct < 100`.
5. Insufficient bid depth: bid levels do not cover target size, `insufficient_depth=true`, and no readiness decision changes in diagnostics-only mode.
6. Zero or negative price rejected or classified as `NEED_DATA` candidate in future validation planning.
7. Zero or negative quantity ignored or classified as `NEED_DATA` candidate, with explicit test expectation chosen before implementation.
8. Mixed string/decimal input: prices and quantities arrive as strings and decimals but normalize deterministically in a pure helper.
9. Spot base-asset quantity case: Binance/Bybit spot quantity is treated as base asset and not quote notional.
10. OKX contracts quantity requires `contract_value` conversion before base/quote notional comparison.
11. Bybit linear quantity unit explicit case: `category=linear` quantity semantics remain explicit and separate from spot.
12. Top-of-book edge disappears after VWAP: positive best-level edge becomes zero after consuming depth.
13. Positive top-of-book but negative VWAP-adjusted net gap: VWAP plus fees/buffer would remove the apparent edge in context-only metrics.
14. `WATCH` remains analysis-only even if VWAP context is positive; no alert, Council auto-call, or execution is produced.
15. Generated JSON is not used as fixture; test fixture is hand-written or sanitized mocked sample.
16. Target notional simulation: helper consumes levels until quote notional threshold is covered rather than base quantity.
17. Partial final level consumption: final level is only partially consumed to meet target size exactly.
18. Empty depth arrays produce `depth_available=false` and `insufficient_depth=true` in diagnostics-only context.
19. Symbol/product mismatch fixture: spot BTCUSDT depth must not be paired with unrelated futures product depth.
20. Precision/rounding fixture: decimal precision remains deterministic and does not silently convert to binary float in expected test outputs.

## 12. Data model candidate

Planning-only field candidates:

- `depth_available`
- `depth_levels_used`
- `target_size`
- `target_notional`
- `target_size_unit`
- `target_notional_currency`
- `source_vwap_ask`
- `source_vwap_bid`
- `target_vwap_ask`
- `target_vwap_bid`
- `vwap_result`
- `insufficient_depth`
- `depth_coverage_pct`
- `ask_slippage_pct`
- `bid_slippage_pct`
- `size_or_notional_resolved`
- `depth_vwap_not_implemented`
- `top_of_book_liquidity_not_fill_feasibility`

Planning constraints:

- This PR does not change schemas.
- Future fields must not imply order intent.
- Future fields must be placed in diagnostics/context extensions first, not readiness-changing fields.
- Future fields must keep `NO_TRADE_ONLY` wording near any size simulation output.
- Missing fields should remain explicit rather than inferred from unrelated venue metadata.

## 13. Relationship to dashboard and Council criteria

Relationship:

- Dashboard records `depth_vwap_not_implemented` and `top_of_book_liquidity_not_fill_feasibility` as watch items.
- Council criteria classifies depth/VWAP issues as `POLICY_REVIEW` unless data sufficiency failure occurs.
- Depth/VWAP planning does not create Council auto-call.
- Depth/VWAP planning does not create alert/execution behavior.
- Future dashboard update may include `depth_vwap_policy_status` as a manual docs-only column.
- Council status or dashboard status must remain evidence classification, not order instruction.

## 14. What must not happen

What must not happen:

- Top-of-book positive edge를 fill-feasible edge로 해석하지 않는다.
- VWAP context를 trading signal로 해석하지 않는다.
- Depth availability를 order permission으로 해석하지 않는다.
- `MANUAL_REVIEW_CANDIDATE`도 `ENTER`가 아니다.
- Dashboard/Council status가 execution을 trigger하지 않는다.
- Generated JSON을 fixture/source-of-truth로 commit하지 않는다.
- Private API 없이 fill feasibility를 증명했다고 주장하지 않는다.
- VWAP diagnostics를 account-specific balance, margin, position, or order feasibility로 확장하지 않는다.
- Mark/index/funding/last price를 executable price로 바꾸어 해석하지 않는다.

## 15. Future implementation PR slices

Proposed future PR sequence:

1. Depth/VWAP fixture planning for common helper.
2. Mocked depth fixture files and fixture contract tests.
3. Pure VWAP helper implementation with mocked/unit tests, no strategy behavior change.
4. Add VWAP diagnostics/context fields to packet/candidate extensions, behavior unchanged.
5. Sampling summary context support, behavior unchanged.
6. User-local smoke/evidence update.
7. VWAP-adjusted readiness policy only after separate approval and stronger evidence.

Recommended guardrails for future PRs:

- Start with hand-written or sanitized mocked fixtures, not generated live JSON.
- Keep helper pure and deterministic.
- Keep target size/notional small and explicit in tests.
- Require venue-specific unit conversion tests before venue rollout.
- Keep readiness decisions unchanged until a separate approved PR.
- Record no-trade compliance in every follow-up.

## 16. Explicitly not doing now

Explicitly not doing in this PR:

- Depth/VWAP implementation 없음.
- VWAP helper 없음.
- Schema change 없음.
- Parser field rename 없음.
- Readiness behavior 변경 없음.
- Freshness threshold 변경 없음.
- Dashboard update 없음.
- Source/runtime behavior 변경 없음.
- Config/registry 변경 없음.
- Active strategy 변경 없음.
- Live endpoint 호출 없음.
- `sample_market_data` 실행 없음.
- `collect_market_data` 실행 없음.
- Generated market JSON 생성/commit 없음.
- Alert 없음.
- Council auto-call 없음.
- Execution 없음.
- Private API 없음.
- Credentials 없음.
- Account/balance/position/order/cancel/withdraw/deposit/transfer 없음.
- Auto-trading 없음.
- OKX `spot_futures_basis` implementation 없음.

## 17. OKX deferred scope note

OKX scope note:

- `spot_futures_basis_v0` OKX는 future expansion으로 defer.
- 이는 scope control이지 permanent rejection이 아니다.
- 이번 PR에서는 OKX research/adapter/config를 만들지 않는다.
- `mark_orderbook_gap_hunt_v0` OKX contract unit / index reference semantics는 별도 watch item으로 유지한다.
- OKX depth/VWAP planning requires explicit contract unit conversion before implementation.

## 18. No-trade compliance

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

## 19. Generated JSON commit 금지

Generated JSON policy 확인:

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- Depth/VWAP evidence는 generated JSON 원본이 아니라 handoff evidence summary와 dashboard row를 기반으로 해야 함.
- Future fixture must be hand-written or sanitized mocked sample, not live generated JSON.
- 이번 PR에는 generated JSON을 추가하지 않음.

## 20. Rollback plan

Rollback plan:

- Docs-only PR이므로 revert하고 이 handoff 문서 1개를 제거하면 된다.
- Code/config/registry/runtime/parser/readiness/test/fixture/generated-data rollback은 필요 없다.
- Confirm GitHub Files changed contains only this handoff document after rollback.
- Re-run required validation commands if rollback evidence is requested.

## 21. Self-audit checklist

Self-audit checklist:

- [x] Did not implement VWAP.
- [x] Did not change readiness behavior.
- [x] Did not change parser/schema.
- [x] Did not call live endpoints.
- [x] Did not create generated JSON.
- [x] Did not modify dashboard.
- [x] Preserved `NO_TRADE_ONLY`.
- [x] Included at least 10 test case candidates.
- [x] Included strategy-specific application for `mark_orderbook_gap_hunt_v0` and `spot_futures_basis_v0`.
- [x] Included venue-specific considerations for Binance, Bybit, OKX.

## 22. Next PR candidates

다음 PR 후보:

1. Next Experimental Strategy Selection v0.
2. Optional Depth/VWAP fixture planning for common helper.
3. Optional dashboard depth/VWAP policy status update.
4. Optional dashboard schema tests / generated dashboard planning later.
