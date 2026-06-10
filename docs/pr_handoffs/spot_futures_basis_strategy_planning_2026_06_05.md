# Spot-Futures Basis Strategy Planning v0

## 1. 작업 목적

이 문서는 `mark_orderbook_gap_hunt_v0` 3-venue hardening 이후 다음 experimental strategy 후보인 `spot_futures_basis_v0`를 planning-first로 정의하는 docs-only planning handoff다.

Scope:

- `spot_futures_basis_v0`를 다음 experimental strategy 후보로 planning-only 정의한다.
- 이 문서는 implementation이 아니라 planning이다.
- 현재 active strategy는 `cross_exchange_spot_spread_v1`로 유지한다.
- `spot_futures_basis_v0`는 proposed / experimental / non-active / `NO_TRADE_ONLY` 후보로만 정의한다.
- generated packet/sampling JSON은 smoke artifact이며 commit하지 않는다.

This PR does not implement adapters, parsers, readiness helpers, registry/config entries, endpoint calls, runtime behavior, alerting, Council auto-call, execution, or active strategy promotion.

## 2. Strategy definition

- `strategy_family`: `spot_futures_basis`
- `strategy_id`: `spot_futures_basis_v0`
- `status`: proposed / experimental / non-active / `NO_TRADE_ONLY`
- Core concept: observe basis between a spot market reference and a futures/perpetual market reference.
- Basis is not automatically an executable edge.
- `WATCH` / `REJECT` / `NEED_DATA` are analysis-only labels.
- Mark price, last price, bid/ask, and VWAP have different meanings and must not be conflated.
- Any future packet must remain public-read-only and analysis-only unless a separate explicitly approved governance change exists.

## 3. Initial scope proposal

Recommended initial planning scope:

- Asset: BTC
- Quote: USDT
- First planning target: Binance spot `BTCUSDT` vs Binance USDM `BTCUSDT` perpetual.
- Later candidates:
  - Bybit spot/perp
  - OKX spot/swap

Scope boundaries for this PR:

- No endpoint research is implemented in this PR.
- No endpoint is called in this PR.
- No adapter/parser/readiness/registry/config implementation is added in this PR.
- No generated sampling JSON is added in this PR.

Rationale for a Binance-first planning target:

- A same-venue spot/perp pair can reduce cross-venue interpretation noise for the first planning slice.
- Binance naming and public market data patterns are already familiar from prior mark/orderbook work.
- Same-venue planning still requires careful symbol, unit, and reference-price semantics review before implementation.

## 4. Candidate data inputs

The following are candidate public-read-only inputs for future research and implementation planning only. This PR does not implement or call any of them:

- Spot best bid / ask.
- Spot orderbook depth.
- Spot last price or mid price, with last price treated only as weak context and never as standalone executable evidence.
- Futures/perp mark price.
- Futures/perp best bid / ask.
- Futures/perp orderbook depth.
- Instrument metadata.
- Contract value / lot size / tick size / min order size.
- Funding rate / next funding time, while keeping funding context distinct from basis.
- Timestamp / latency / `data_age_ms` fields.
- Optional fee/slippage buffer assumptions for analysis-only net-basis estimates.

Input interpretation guardrails:

- Spot and perp symbols must be explicitly mapped.
- Spot quote currency and perp settlement/margin/reference currency must be checked for comparability.
- Futures/perp contract unit, base asset unit, and notional conventions must be venue-specific.
- Mark price is context, not an executable price.
- Last price is weak context, not an executable price.
- Bid/ask or VWAP-based comparisons are stronger candidates for executable-basis context, but this project remains `NO_TRADE_ONLY`.

## 5. Candidate formulas

The following formulas are planning candidates only. They are not implemented by this PR and do not define production thresholds.

Basic mid candidates:

```text
spot_mid = (spot_bid + spot_ask) / 2
perp_mid = (perp_bid + perp_ask) / 2
mid_basis_pct = ((perp_mid - spot_mid) / spot_mid) * 100
```

Directional gross basis candidates:

```text
long_spot_short_perp_gross_pct = ((perp_bid - spot_ask) / spot_ask) * 100
long_perp_short_spot_gross_pct = ((spot_bid - perp_ask) / perp_ask) * 100
```

Estimated net basis candidate:

```text
estimated_net_basis_pct = gross_basis_pct - fee_slippage_buffer_pct
```

Formula guardrails:

- Last-price-only basis is forbidden as a decision basis and may only be weak context.
- Mark-price basis is context and is not executable basis.
- Executable basis candidates should use spot ask / spot bid and perp bid / perp ask, or future VWAP-based depth estimates.
- This PR does not set actual thresholds.
- Positive gross basis may become non-positive after fees, slippage, spread, and depth assumptions.
- Formula naming must make direction explicit to avoid confusing long-spot/short-perp with long-perp/short-spot context.

## 6. Required readiness questions

A future readiness helper should answer at least these questions before any candidate is considered analysis-ready:

- Is the spot/futures symbol mapping correct?
- Are the spot quote and perp settlement/reference currency comparable?
- Are contract unit, base asset unit, and notional interpretation correct?
- Do spot ask / perp bid or perp ask / spot bid exist for directional basis checks?
- Is orderbook depth sufficient for the intended analysis size or VWAP context?
- Are timestamps fresh enough, and are stale timestamp / clock-skew watch items preserved?
- Is net basis positive after fee/slippage/buffer assumptions?
- Is funding context kept distinct from basis context?
- Is mark price not being treated as executable price?
- Is last price not being treated as executable price?
- What are the `required_missing_fields`?
- Are no-trade assumptions preserved?
- Does the candidate remain public-read-only and analysis-only?
- Are venue-specific response shapes, symbol formats, and units explicitly preserved?

## 7. Risk assessment

Key risks:

- Spot/futures symbol mapping errors can produce invalid basis observations.
- Contract unit / lot size / notional interpretation errors can distort basis and size assumptions.
- Mark price can be misread as an executable price.
- Last price can create a stale or non-executable basis illusion.
- Orderbook depth may be insufficient even when top-of-book basis looks positive.
- Stale timestamp / clock skew can distort cross-market comparisons.
- Funding rate and basis can be confused, especially around funding windows.
- Positive gross basis may not be a positive net edge after fees, slippage, spread, and depth.
- Public endpoint response shapes differ across venues and products.
- A visible basis does not validate actual position entry, borrow/margin, order placement, or execution feasibility without private APIs, which remain forbidden.
- False positives are likely if the strategy uses mark price, last price, or thin top-of-book quotes without depth context.

## 8. OpportunityPacket fit

A future `spot_futures_basis_v0` OpportunityPacket could fit the existing analysis-only packet pattern, but this PR does not implement it.

Potential observations:

- `spot_observation`
- `futures_or_perp_observation`

Potential candidate:

- `spot_futures_basis_observation`

Potential direction labels:

- `analysis_only_long_spot_short_perp_basis`
- `analysis_only_long_perp_short_spot_basis`

Potential metrics:

- `spot_bid`
- `spot_ask`
- `perp_bid`
- `perp_ask`
- `spot_mid`
- `perp_mid`
- `gross_basis_pct`
- `estimated_net_basis_pct`
- `fee_slippage_buffer_pct`
- `funding_rate`
- `basis_context_type`
- `spot_data_age_ms`
- `perp_data_age_ms`
- `required_missing_fields`

Potential assumptions:

- `public no-key endpoints only`
- `analysis-only packet`
- `no private API`
- `no trading behavior`
- `mark price is not executable`
- `last price is weak context only`
- `basis observation is not an execution instruction`
- `WATCH / REJECT / NEED_DATA are analysis-only labels`

## 9. Proposed PR sequence

Recommended small-slice PR sequence:

1. PR 1: Spot-Futures Basis Strategy Planning v0
2. PR 2: Binance public source / endpoint research docs-only
3. PR 3: mocked parser fixture planning
4. PR 4: readiness policy planning
5. PR 5: first mocked parser/readiness implementation, `NO_TRADE_ONLY`
6. PR 6: registry/config planning, no activation
7. PR 7: user-local public-read-only collect smoke
8. PR 8: 3-sample sampling evidence
9. PR 9: 30-sample extended evidence

Sequence guardrails:

- PR 2 should document endpoint candidates before any code is written.
- PR 3 and PR 4 should lock fixture/readiness semantics before implementation.
- PR 5 must be mocked/unit-test-first and `NO_TRADE_ONLY`.
- PR 6 must not activate the strategy.
- PR 7 through PR 9 must keep generated JSON artifacts out of git unless explicitly approved.

## 10. Explicitly not doing now

This PR explicitly does not do any of the following:

- Adapter implementation.
- Parser implementation.
- Readiness helper implementation.
- Registry/config change.
- Active strategy change.
- `spot_futures_basis_v0` active promotion.
- Live endpoint call.
- Generated JSON creation or commit.
- Private API use.
- Credentials/API keys/secrets/tokens use.
- Account/balance/position lookup.
- Order/cancel.
- Withdrawal/deposit/transfer.
- Execution.
- Alerting.
- Council auto-call.
- Auto-trading.
- Timestamp policy implementation.
- OKX index endpoint implementation.

## 11. No-trade compliance

This planning PR preserves no-trade posture:

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
- Parser behavior change: no
- Readiness threshold change: no
- Live endpoint call: no
- Generated JSON commit: no
- `NO_TRADE_ONLY` preserved: yes

## 12. Generated JSON commit 금지

Generated packet/sampling files remain smoke artifacts only and must not be committed:

- `data/market_samples/*.json`
- `data/generated_packets/*.json`

This PR intentionally adds only this planning handoff document and does not add generated JSON.

## 13. Rollback plan

Rollback path:

1. Revert this docs-only planning PR.
2. Remove `docs/pr_handoffs/spot_futures_basis_strategy_planning_2026_06_05.md`.
3. No code/config/registry/runtime/parser/readiness/generated-data rollback is required.

## 14. Next PR candidates

Recommended order after this planning PR:

1. Binance public source / endpoint research docs-only
2. Mocked parser fixture planning
3. Readiness policy planning
4. First mocked implementation, `NO_TRADE_ONLY`
5. User-local public-read-only smoke evidence
